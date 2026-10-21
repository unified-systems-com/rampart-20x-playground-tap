"""The teams bundle, the `team.responsible` stamps and the Teams page, read from the bundles as written
(`req-rampart-20x-playground-teams-*`, `req-rampart-20x-playground-page-teams-*`).

These tests read JSON and TOML only. What the Searches return, and how the page looks, is checked against a booted stack."""

from __future__ import annotations

import json
import re
import tomllib
import uuid
from collections import Counter
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
FILE = "teams.grift.json"
SLUG = "/playground/teams"
TABLE = "tap_web/panels/table_panel.html"
TEXT = "tap_web/panels/text_panel.html"
KEY = "team.responsible"
BELONGS = "BELONGS_TO_TEAM__identity_core"
LEADS = "LEADS_TEAM__identity_core"
HANDLES = ("git-serious", "devops", "engineering", "infra")
CHILDREN = ("devops", "engineering", "infra")
NAMES = {"git-serious": "git-serious", "devops": "DevOps", "engineering": "Engineering", "infra": "Infra"}

# The ownership table of the spec: every instance of a type carries the team's entity id. A host and an
# application flow are told apart by name, because their type holds both a stamped and an unstamped instance.
BY_TYPE = {
    "devops": [
        "github_core__github_workflow", "github_core__github_actions_run", "github_core__github_package",
        "github_core__github_package_version", "aws_core__aws_ecr_repository", "aws_core__aws_lambda",
        "aws_core__aws_s3_bucket", "aws_core__aws_codepipeline_pipeline", "aws_core__aws_codebuild_project",
        "aws_core__aws_iam_oidc_provider",
    ],
    "engineering": [
        "github_core__github_repository", "github_core__github_account", "computing_core__program",
        "computing_core__library", "computing_core__package", "computing_core__source_package",
        "computing_core__sbom_document", "computing_core__crypto_provider", "computing_core__operating_system",
    ],
    "infra": [
        "aws_core__aws_organization", "aws_core__aws_account", "aws_core__aws_vpc", "aws_core__aws_subnet",
        "aws_core__aws_internet_gateway", "aws_core__aws_alb", "aws_core__aws_ecs_cluster", "aws_core__aws_ecs_service",
        "aws_core__aws_ecs_task", "aws_core__aws_ecs_container", "aws_core__aws_rds_instance",
        "aws_core__aws_secrets_manager_secret", "aws_core__aws_kms_key", "aws_core__aws_route53_zone",
        "aws_core__aws_acm_certificate", "aws_core__aws_ec2_instance",
    ],
    "git-serious": ["compliance_core__compliance_boundary"],
}
BY_NAME = {
    ("computing_core__host", "git-serious web image"): "engineering",
    ("computing_core__host", "developer laptop"): "engineering",
    ("computing_core__host", "administrator workstation"): "infra",
    ("computing_core__application_flow", "code"): "devops",
    ("computing_core__application_flow", "source pull"): "devops",
    ("computing_core__application_flow", "customer data"): "engineering",
    ("computing_core__application_flow", "database"): "engineering",
    ("computing_core__application_flow", "administration"): "infra",
}
UNSTAMPED_TYPES = {
    "identity_core__human", "computing_core__os_user", "github_core__github_platform", "computing_core__file",
    "computing_core__public_key", "computing_core__private_key", "compliance_core__compliance_finding",
    "github_core__code_scanning_alert", "github_core__dependabot_alert",
}
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+")


def _batch(name: str = FILE) -> dict:
    return json.loads((GRIFT / name).read_text(encoding="utf-8"))["batches"][0]


def _all_nodes() -> list[dict]:
    nodes: list[dict] = []
    for path in sorted(GRIFT.glob("*.grift.json")):
        for batch in json.loads(path.read_text(encoding="utf-8"))["batches"]:
            nodes += batch["nodes"]
    return nodes


class TestTeamsBundle:
    def setup_method(self) -> None:
        self.batch = _batch()
        self.nodes = self.batch["nodes"]
        self.edges = self.batch["edges"]
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}
        self.teams = {n["node"]["handle"]: n for n in self.nodes if n["entity"]["entity_type"] == "identity_core__team"}
        self.humans = {n["node"]["handle"]: n for n in self.nodes if n["entity"]["entity_type"] == "identity_core__human"}

    def _edges(self, edge_type: str) -> list[dict]:
        return [e["edge"] for e in self.edges if e["edge"]["edge_type"] == edge_type]

    def test_four_teams_with_the_handles_names_and_descriptions(self) -> None:
        """`teams-1`."""
        assert tuple(self.teams) == HANDLES
        for handle, node in self.teams.items():
            assert node["node"]["name"] == node["entity"]["name"] == NAMES[handle]
            assert node["node"]["description"]
        assert self.teams["git-serious"]["node"]["description"] == (
            "The whole git-serious product team; the other three belong to it."
        )

    def test_the_three_teams_nest_under_git_serious_and_no_other_team_edge_exists(self) -> None:
        """`teams-2`."""
        team_ids = {n["entity"]["entity_id"] for n in self.teams.values()}
        team_to_team = [e for e in self._edges(BELONGS) if e["from_entity_id"] in team_ids]
        assert sorted((self.by_id[e["from_entity_id"]]["node"]["handle"], self.by_id[e["to_entity_id"]]["node"]["handle"])
                      for e in team_to_team) == sorted((h, "git-serious") for h in CHILDREN)
        assert not [e for e in self._edges(LEADS) if e["from_entity_id"] in team_ids]

    def test_thirteen_people_with_generic_names(self) -> None:
        """`teams-3`, `teams-4`."""
        assert len(self.humans) == 13
        expected = {"git-serious-lead": "git-serious Team Lead"}
        for handle in CHILDREN:
            expected[f"{handle}-lead"] = f"{NAMES[handle]} Team Lead"
            expected.update({f"{handle}-member-{i}": f"{NAMES[handle]} Member {i}" for i in (1, 2, 3)})
        assert {h: n["node"]["name"] for h, n in self.humans.items()} == expected
        assert all(n["entity"]["name"] == n["node"]["name"] for n in self.humans.values())

    def test_each_lead_leads_and_belongs_and_each_member_belongs(self) -> None:
        """`teams-3`: every person has exactly one BELONGS_TO_TEAM edge, a lead also one LEADS_TEAM edge."""
        people = {n["entity"]["entity_id"]: h for h, n in self.humans.items()}
        belongs = Counter()
        for e in self._edges(BELONGS):
            if e["from_entity_id"] in people:
                handle = people[e["from_entity_id"]]
                belongs[handle] += 1
                assert self.by_id[e["to_entity_id"]]["node"]["handle"] == re.sub(r"-(lead|member-\d)$", "", handle)
        assert belongs == Counter({h: 1 for h in self.humans})
        leads = {people[e["from_entity_id"]]: self.by_id[e["to_entity_id"]]["node"]["handle"] for e in self._edges(LEADS)}
        assert leads == {f"{h}-lead": h for h in HANDLES}
        assert len(self._edges(BELONGS)) == 3 + 13 and len(self._edges(LEADS)) == 4

    def test_no_real_person_email_or_account_appears(self) -> None:
        """`teams-4`."""
        for n in self.nodes:
            if n["entity"]["entity_type"] not in ("identity_core__human", "identity_core__team"):
                continue
            assert not EMAIL_RE.search(json.dumps(n)), n["entity"]["name"]
            assert set(n["node"]) <= {"handle", "name", "description"}

    def test_the_stamp_key_is_documented_with_no_value_nodes(self) -> None:
        """`teams-5`."""
        dims = [n for n in _all_nodes() if n["entity"]["entity_type"] == "dimension"]
        assert [n["entity"]["name"] for n in dims if n["entity"]["name"].startswith("team.")] == [KEY]
        node = next(n for n in self.nodes if n["entity"]["name"] == KEY)
        assert node["entity"]["entity_type"] == "dimension" and node["node"]["description"]
        assert "dcom" not in node["entity"]["dimensions"]

    def test_batch_is_named_and_keeps_a_unique_version_7_id_set(self) -> None:
        ids = [self.batch["batch_entity"]["entity_id"]]
        ids += [n["entity"]["entity_id"] for n in self.nodes] + [e["entity"]["entity_id"] for e in self.edges]
        assert len(ids) == len(set(ids)) and all(uuid.UUID(i).version == 7 for i in ids)
        other: set[str] = set()
        for path in GRIFT.glob("*.grift.json"):
            if path.name == FILE:
                continue
            for batch in json.loads(path.read_text(encoding="utf-8"))["batches"]:
                other.add(batch["batch_entity"]["entity_id"])
                other |= {n["entity"]["entity_id"] for n in batch["nodes"] if "entity_id" in n["entity"]}
                other |= {e["entity"]["entity_id"] for e in batch["edges"] if "entity_id" in e["entity"]}
        assert not other & set(ids)


class TestStamps:
    def setup_method(self) -> None:
        teams = {n["node"]["handle"]: n["entity"]["entity_id"] for n in _batch()["nodes"]
                 if n["entity"]["entity_type"] == "identity_core__team"}
        self.team_id = teams
        self.by_id = {v: k for k, v in teams.items()}
        self.nodes = _all_nodes()

    def _expected(self, entity: dict) -> str | None:
        kind, name = entity["entity_type"], entity["name"]
        if (kind, name) in BY_NAME:
            return BY_NAME[(kind, name)]
        for team, kinds in BY_TYPE.items():
            if kind in kinds:
                return team
        return None

    def test_every_instance_of_a_listed_type_carries_its_teams_id_and_nothing_else_does(self) -> None:
        """`teams-6`: the customer's computer, the OS users and the people stay unstamped."""
        stamped = Counter()
        for n in self.nodes:
            e = n["entity"]
            expected = self._expected(e)
            value = e["dimensions"].get(KEY)
            if expected is None:
                assert value is None, (e["entity_type"], e["name"])
            else:
                assert value == self.team_id[expected], (e["entity_type"], e["name"])
                stamped[expected] += 1
        assert stamped == Counter({"git-serious": 1, "devops": 14, "engineering": 305, "infra": 34})

    def test_the_unstamped_types_are_the_ones_the_spec_leaves_out(self) -> None:
        seen = {n["entity"]["entity_type"] for n in self.nodes if n["entity"]["dimensions"].get(KEY) is None}
        assert UNSTAMPED_TYPES <= seen
        customer = next(n for n in self.nodes if n["entity"]["name"] == "customer computer")
        assert KEY not in customer["entity"]["dimensions"]

    def test_every_stamp_value_is_a_seeded_team_id(self) -> None:
        """`teams-7`: a lowercase hyphenated uuid naming one of the four teams."""
        values = {n["entity"]["dimensions"][KEY] for n in self.nodes if KEY in n["entity"]["dimensions"]}
        assert values == set(self.team_id.values())
        assert all(v == v.lower() and str(uuid.UUID(v)) == v for v in values)


class TestManifest:
    def test_identity_core_floor_names_the_release_that_ships_teams_and_the_bundle_is_listed(self) -> None:
        """`teams-8`."""
        manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
        identity = next(d for d in manifest["depends_on"] if d["slug"] == "identity_core")
        assert identity["min_version"] == "0.1.5"
        assert manifest["grift"]["teams"] == "grift/teams.grift.json"
        for name in ("ci", "demo"):
            record = json.loads((PACKAGE_ROOT / "boot" / f"{name}.boot.json").read_text(encoding="utf-8"))
            entry = next(p for p in record["install"]["plugins"] if p["slug"] == "identity_core")
            assert entry["source"]["rev"] == "v0.1.5"
            assert entry["source"]["commit"] == "678b246bcc4390df504c9b24a6be132372162044"


class TestTeamsPage:
    def setup_method(self) -> None:
        self.batch = _batch()
        self.nodes = self.batch["nodes"]
        self.edges = self.batch["edges"]
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}
        self.page = next(n for n in self.nodes if n["entity"]["entity_type"] == "page")
        self.panels = {n["node"]["slug"]: n for n in self.nodes if n["entity"]["entity_type"] == "panel"}

    def _search_of(self, panel: dict) -> dict:
        links = [
            e for e in self.edges
            if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]
        ]
        assert len(links) == 1
        return self.by_id[links[0]["edge"]["to_entity_id"]]

    def _order(self) -> list[str]:
        columns = self.page["node"]["layout"]["columns"]
        return [row["panel-id"] for c in sorted(columns, key=lambda k: columns[k]["band"]) for row in columns[c]["rows"].values()]

    def test_the_page_is_routable_and_named_teams(self) -> None:
        """`page-teams-1`."""
        assert self.page["node"]["slug"] == SLUG
        assert self.page["node"]["name"] == self.page["entity"]["name"] == "Teams"
        assert all(a["entity"]["dimensions"] == {"tap.graph": "web"} for a in (self.page, *self.panels.values()))

    def test_a_title_then_the_teams_leaders_and_members_tables(self) -> None:
        """`page-teams-2`."""
        order = self._order()
        assert [self.panels[p]["node"]["view"] for p in order] == [TEXT, TABLE, TABLE, TABLE]
        assert [self.panels[p]["node"]["name"] for p in order] == ["Teams", "Teams", "Leaders", "Members"]

    def test_slots_and_page_panel_edges_match_exactly(self) -> None:
        slots = set(self._order())
        wired = {
            e["edge"]["properties"]["hotlink"]["value"]: e["edge"]["to_entity_id"]
            for e in self.edges if e["edge"]["edge_type"] == "USES_PANEL"
        }
        assert slots == set(wired) == set(self.panels)
        assert {self.by_id[i]["node"]["slug"] for i in wired.values()} == slots
        assert all(e["edge"]["properties"]["hotlink"] == {"model": "page", "spec": "page-panels", "value": e["edge"]["properties"]["hotlink"]["value"]}
                   for e in self.edges if e["edge"]["edge_type"] == "USES_PANEL")

    def test_each_table_reads_a_gryphon_search_and_names_only_returned_fields(self) -> None:
        """`page-teams-3`: Gryphon answers all three, so no module runner is used."""
        returned = {"Teams": {"entity_id", "name", "description"}, "Leaders": {"team", "entity_id", "name"},
                    "Members": {"team", "entity_id", "name"}}
        for slug in self._order()[1:]:
            panel = self.panels[slug]
            search = self._search_of(panel)
            assert search["node"]["search_type"] == "gryphon"
            query = " ".join(search["node"]["definition"]["query"])
            assert set(re.findall(r" AS (\w+)", query)) == returned[panel["node"]["name"]]
            assert {c["field"] for c in panel["node"]["config"]["columns"]} <= returned[panel["node"]["name"]]
        queries = [" ".join(self._search_of(self.panels[s])["node"]["definition"]["query"]) for s in self._order()[1:]]
        assert "identity_core__team)" in queries[0] and "BELONGS_TO_TEAM" not in queries[0]
        assert "LEADS_TEAM__identity_core" in queries[1]
        assert "BELONGS_TO_TEAM__identity_core" in queries[2]

    def test_tables_are_striped_titled_in_title_case_and_link_the_name_to_the_entity(self) -> None:
        for slug in self._order()[1:]:
            config = self.panels[slug]["node"]["config"]
            assert config["striped"] is True and config["quick_filter"] is True
            for column in config["columns"]:
                assert column["title"] == column["title"].title(), column["title"]
                assert "align" not in column
            link = next(c for c in config["columns"] if c["field"] == "name")
            kind = "identity_core__team" if slug == "playground-teams-teams" else "identity_core__human"
            assert link["formatter"] == "link"
            assert link["formatter_params"]["href_template"] == f"/object/{kind}/entity--{{entity_id}}/"

    def test_the_page_carries_a_title_and_tables_only(self) -> None:
        """`page-teams-4`."""
        title = self.panels[self._order()[0]]
        assert title["node"]["config"] == {"text": "", "hide_header": False}
        for slug in self._order()[1:]:
            assert "text" not in self.panels[slug]["node"]["config"]
