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
GRAPH = "tap_viz/panels/graph_panel.html"
MODULE = PACKAGE_ROOT / "static" / "rampart_20x_playground" / "js" / "projections" / "teams.js"
SPEC = PACKAGE_ROOT.parents[1] / "specs" / "spec-rampart_20x_playground-v0.md"
KEY = "team.responsible"
BELONGS = "BELONGS_TO_TEAM__identity_core"
LEADS = "LEADS_TEAM__identity_core"
ANSWERS = "ANSWERS_FOR_DIMENSION__identity_core"
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
    # The coverage seed (`coverage-seed-2`): the public key stays unowned.
    ("github_core__github_platform", "github.com"): "devops",
    ("computing_core__file", "container tls certificate"): "infra",
    ("computing_core__private_key", "container tls private key"): "infra",
}
UNSTAMPED_TYPES = {
    "identity_core__human", "computing_core__os_user", "computing_core__public_key", "compliance_core__compliance_finding",
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

    def test_each_team_answers_for_the_team_responsible_dimension_node(self) -> None:
        """`teams-9`: one ANSWERS_FOR_DIMENSION edge per team, each to the `team.responsible` dimension node."""
        key_id = next(n["entity"]["entity_id"] for n in self.nodes if n["entity"]["name"] == KEY)
        team_ids = {n["entity"]["entity_id"]: h for h, n in self.teams.items()}
        answers = self._edges(ANSWERS)
        assert sorted(team_ids[e["from_entity_id"]] for e in answers) == sorted(HANDLES)
        assert {e["to_entity_id"] for e in answers} == {key_id}
        assert all(e["properties"] == {} for e in answers)

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
        assert stamped == Counter({"git-serious": 1, "devops": 15, "engineering": 315, "infra": 36})

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
        assert identity["min_version"] == "0.1.6"
        assert manifest["grift"]["teams"] == "grift/teams.grift.json"
        for name in ("ci", "demo"):
            record = json.loads((PACKAGE_ROOT / "boot" / f"{name}.boot.json").read_text(encoding="utf-8"))
            entry = next(p for p in record["install"]["plugins"] if p["slug"] == "identity_core")
            assert entry["source"]["rev"] == "v0.1.6"
            assert entry["source"]["commit"] == "11f087954ff5d06792abc4a3994d7eae77bbcb5b"


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

    def test_a_title_then_the_graph_then_the_teams_leaders_and_members_tables(self) -> None:
        """`page-teams-2`."""
        order = self._order()
        assert [self.panels[p]["node"]["view"] for p in order] == [TEXT, GRAPH, TABLE, TABLE, TABLE]
        assert [self.panels[p]["node"]["name"] for p in order] == ["Teams", "Teams Graph", "Teams", "Leaders", "Members"]

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
        for slug in self._order()[2:]:
            panel = self.panels[slug]
            search = self._search_of(panel)
            assert search["node"]["search_type"] == "gryphon"
            query = " ".join(search["node"]["definition"]["query"])
            assert set(re.findall(r" AS (\w+)", query)) == returned[panel["node"]["name"]]
            assert {c["field"] for c in panel["node"]["config"]["columns"]} <= returned[panel["node"]["name"]]
        queries = [" ".join(self._search_of(self.panels[s])["node"]["definition"]["query"]) for s in self._order()[2:]]
        assert "identity_core__team)" in queries[0] and "BELONGS_TO_TEAM" not in queries[0]
        assert "LEADS_TEAM__identity_core" in queries[1]
        assert "BELONGS_TO_TEAM__identity_core" in queries[2]

    def test_tables_are_striped_titled_in_title_case_and_link_the_name_to_the_entity(self) -> None:
        for slug in self._order()[2:]:
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
        for slug in self._order()[2:]:
            assert "text" not in self.panels[slug]["node"]["config"]


class TestTeamsGraph:
    """`teams-viz`: the graph panel, its projection chain and its layout module, read as written.

    What the module draws (four teams, three inside git-serious, thirteen people, four leaders) is counted in a browser."""

    def setup_method(self) -> None:
        self.batch = _batch()
        self.nodes = self.batch["nodes"]
        self.edges = [e["edge"] for e in self.batch["edges"]]
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}
        self.panel = next(n for n in self.nodes if n["node"].get("slug") == "playground-teams-graph")
        self.source = MODULE.read_text(encoding="utf-8")

    def _out(self, from_node: dict, edge_type: str) -> list[dict]:
        return [self.by_id[e["to_entity_id"]] for e in self.edges
                if e["edge_type"] == edge_type and e["from_entity_id"] == from_node["entity"]["entity_id"]]

    def test_the_graph_is_the_second_slot_full_width_with_no_header(self) -> None:
        """`teams-viz-1`, `teams-viz-6`."""
        page = next(n for n in self.nodes if n["entity"]["entity_type"] == "page")
        columns = page["node"]["layout"]["columns"]
        ordered = [columns[c] for c in sorted(columns, key=lambda k: columns[k]["band"])]
        assert [list(c["rows"].values())[0]["panel-id"] for c in ordered][:3] == [
            "playground-teams-title", "playground-teams-graph", "playground-teams-teams"]
        assert all(c["width"] == "12fr" for c in ordered)
        assert self.panel["node"]["view"] == GRAPH
        assert self.panel["node"]["config"]["hide_header"] is True
        assert "text" not in self.panel["node"]["config"]

    def test_projection_elevation_and_layout_are_data_joined_by_hotlinks(self) -> None:
        """`teams-viz-4`."""
        (projection,) = self._out(self.panel, "USES_PROJECTION")
        (elevation,) = self._out(projection, "USES_ELEVATION")
        (default,) = self._out(projection, "USES_DEFAULT_ELEVATION")
        (layout,) = self._out(elevation, "USES_LAYOUT")
        assert default is elevation
        assert projection["node"]["definition"]["node_style"] == {"mode": "icon-badge"}
        assert projection["node"]["definition"]["elevations"] == [elevation["entity"]["entity_id"]]
        assert elevation["node"]["definition"]["layouts"] == [layout["entity"]["entity_id"]]
        js_file = layout["node"]["definition"]["js_file"]
        assert js_file == "tap_plugin/rampart_20x_playground/static/rampart_20x_playground/js/projections/teams.js"
        assert (PACKAGE_ROOT.parents[1] / js_file).is_file()

    def test_three_gryphon_searches_bring_the_two_nesting_edges_and_the_leaders(self) -> None:
        """`teams-viz-4`: one MATCH each, returning the nodes at both ends of one edge type."""
        searches = self._out(self.panel, "USES_SEARCH")
        queries = sorted(" ".join(s["node"]["definition"]["query"]) for s in searches)
        assert all(s["node"]["search_type"] == "gryphon" for s in searches)
        assert queries == sorted([
            "MATCH (h:identity_core__human)-[:BELONGS_TO_TEAM__identity_core]->(t:identity_core__team) RETURN h, t",
            "MATCH (c:identity_core__team)-[:BELONGS_TO_TEAM__identity_core]->(p:identity_core__team) RETURN c, p",
            "MATCH (h:identity_core__human)-[:LEADS_TEAM__identity_core]->(t:identity_core__team) RETURN h, t",
        ])

    def test_nesting_is_two_single_hop_relationships_over_belongs_to_team(self) -> None:
        """`teams-viz-2`."""
        assert "projectNested(cy, {" in self.source
        assert "(parent:${T.team})<-[:${BELONGS}]-(child:${T.human})" in self.source
        assert "(parent:${T.team})<-[:${BELONGS}]-(child:${T.team})" in self.source
        assert 'const BELONGS = "BELONGS_TO_TEAM__identity_core";' in self.source
        for token in ("baseSizes", "padding", "innerLayout", "applyStandardChrome", "placeParentLabels", 'cy.fit('):
            assert token in self.source, token
        assert 'trigger_reason === "initial_load"' in self.source

    def test_every_child_of_a_team_is_its_own_stage_in_one_row_leader_first(self) -> None:
        """`teams-viz-7`, `teams-viz-8`: the `ranked` natural layout, ordered by stamped integers and never by a label."""
        assert 'innerLayout: {name: "ranked", sort: "order"' in self.source
        # One row per team: the leader, the other people by typed name, then the child teams by typed name.
        assert "(leaders.contains(a) ? 0 : 1) - (leaders.contains(b) ? 0 : 1) || byName(a, b)" in self.source
        assert "people.toArray().forEach((n, i) => n.data({_stage: i, _order: 0}))" in self.source
        assert "_edgeType(e) === BELONGS" in self.source
        assert '"top-center"' in self.source

    def test_a_team_with_child_teams_stacks_its_people_above_one_row_of_child_teams(self) -> None:
        """`teams-viz-7`, `teams-viz-8`: the decision is the graph fact (a team that is the parent of child teams), set through `_inner_layout`."""
        assert "if (teams.length > 0) {" in self.source
        assert "teams.toArray().forEach((n, i) => n.data({_stage: 1, _order: i}))" in self.source
        assert "n.data({_stage: 0, _order: leaders.contains(n) ? 0 : 1})" in self.source
        assert 'cy.getElementById(parent).data("_inner_layout", {name: "ranked", axis: "rows", sort: "order", columnGap: 56, rowGap: 44})' in self.source
        assert self.source.count("_inner_layout") >= 1 and "git-serious" not in self.source

    def test_the_slot_is_a_thin_banner_at_the_top_of_the_page(self) -> None:
        """`teams-viz-11`: 40vh, ruled by George over 25vh (too small to read) and 33vh."""
        page = next(n for n in self.nodes if n["entity"]["entity_type"] == "page")
        rows = [r for c in page["node"]["layout"]["columns"].values() for r in c["rows"].values()]
        slot = next(r for r in rows if r["panel-id"] == "playground-teams-graph")
        assert slot["height"] == "40vh"
        assert 'cy.fit(cy.nodes(":visible"), 12)' in self.source

    def test_a_leader_is_read_from_the_leads_team_edge_and_set_apart_on_the_label(self) -> None:
        """`teams-viz-3`, `teams-viz-9`."""
        assert 'const LEADS = "LEADS_TEAM__identity_core";' in self.source
        assert "_edgeType(e) === LEADS" in self.source and "leaders.merge(e.source())" in self.source
        assert "e.addClass(ELEVATION_HIDDEN_CLASS)" in self.source
        assert "leaders.style(LEADER_LABEL)" in self.source and "people.style(PERSON_LABEL)" in self.source
        assert re.search(r'const LEADER_LABEL = \{"color": "#0f5c70", "font-weight": 700, "text-background-opacity": 0\};', self.source)
        assert "text-background-color" not in self.source

    def test_every_person_is_a_solo_icon_and_a_team_stays_a_box(self) -> None:
        """`teams-viz-10`: `applyIconNodes` with `solo: true` on the humans only (an icon node is terminal, so a team cannot be one)."""
        assert 'import {applyIconNodes} from "/static/tap_viz/js/runtime/icon-node.js";' in self.source
        assert "applyIconNodes(cy, {members: people," in self.source and "solo: true" in self.source
        assert 'const people = cy.nodes(`[entity_type = "${T.human}"]`);' in self.source
        assert "members: cy.nodes()" not in self.source
        # The projection keeps the type-icon badge for the teams; solo is a layout primitive, not a node_style value.
        (projection,) = self._out(self.panel, "USES_PROJECTION")
        assert projection["node"]["definition"]["node_style"] == {"mode": "icon-badge"}

    def test_the_module_has_no_geometry_and_places_nothing_by_label_or_id(self) -> None:
        """`teams-viz-2`: configuration and data reads only."""
        assert not re.search(r"\.(position|renderedPosition|shift)\(|\.positions\(", self.source)
        assert not re.search(r'data\("label"\)\s*[=!]==|entity_id\s*[=!]==|handle', self.source)
        assert self.source.count("\nexport async function execute(context)") == 1

    def test_the_spec_carries_the_requirement_and_its_ten_criteria(self) -> None:
        text = SPEC.read_text(encoding="utf-8")
        assert "RID: `req-rampart-20x-playground-teams-viz`" in text
        for n in range(1, 12):
            assert f"| req-rampart-20x-playground-teams-viz-{n} |" in text
