"""The Overview's look, pinned from its sources (`req-rampart-20x-playground-govcloud-layout-2`, `-layout-8`,
`-layout-9`, `-actors-3`, `-actors-6`, `-nongoals-5`). Read-only checks of the layout module and the mock inventory:
no Django, no grid, no browser. What actually rendered is counted in a browser and stated in the pull request."""

from __future__ import annotations

import json
import re
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
LANDING = PACKAGE_ROOT / "static" / "rampart_20x_playground" / "js" / "projections" / "landing.js"
MOCK = PACKAGE_ROOT / "grift" / "mock-inventory.grift.json"
SPECS = PACKAGE_ROOT.parents[1] / "specs"
GRIFT = PACKAGE_ROOT / "grift"


def _js() -> str:
    return LANDING.read_text(encoding="utf-8")


def _list(name: str) -> list[str]:
    """The `T.<key>` members of `const <name> = [...]`, as the type constants' keys."""
    match = re.search(rf"const {name} = \[([^\]]*)\]", _js())
    assert match, name
    return re.findall(r"T\.(\w+)", match.group(1))


def _nodes() -> list[dict]:
    return [n for b in json.loads(MOCK.read_text(encoding="utf-8"))["batches"] for n in b["nodes"]]


def _by_type(entity_type: str) -> list[dict]:
    return [n for n in _nodes() if n["entity"]["entity_type"] == entity_type]


class TestSoloIcons:
    """`req-rampart-20x-playground-govcloud-actors-6`: C2."""

    def test_people_and_computers_are_solo_at_the_icon_size(self) -> None:
        assert sorted(_list("SOLO_ICON_TYPES")) == ["host", "human"]
        assert re.search(r"members: shown\(SOLO_ICON_TYPES\), \.\.\.ICON, solo: true", _js())

    def test_route_53_and_ecr_are_solo(self) -> None:
        assert {"zone", "ecr"} <= set(_list("SOLO_TYPES"))

    def test_github_alone_keeps_its_card(self) -> None:
        assert _list("ICON_TYPES") == ["platform"]
        assert "platform" not in _list("SOLO_TYPES") + _list("SOLO_ICON_TYPES")


class TestDeployRow:
    """`req-rampart-20x-playground-govcloud-layout-8`: C3 (one titled collection; a half-size card pile since Overview Wave 10)."""

    def test_the_deploy_types_are_the_delivery_path(self) -> None:
        assert sorted(_list("DEPLOY_TYPES")) == ["bucket", "codebuild", "ecr", "lambda", "pipeline"]

    def test_a_secret_is_in_the_column_only_when_a_deploy_lambda_retrieves_it(self) -> None:
        """The data difference: the GitHub App token has a RETRIEVES_SECRET_FROM edge from the Lambda; the runtime
        secret has none (it has ENCRYPTED_WITH_KEY). The layout selects by that edge, never by name. The token is
        not drawn on the Overview now (no `overview` value), so the row holds no secret; were one drawn again it
        would have to be retrieved by a deploy Lambda."""
        assert _list("DEPLOY_SECRET_READERS") == ["lambda"]
        assert "E.retrievesSecret" in _js()
        edges = [e["edge"] for b in json.loads(MOCK.read_text(encoding="utf-8"))["batches"] for e in b["edges"]]
        types = {n["entity"]["entity_id"]: n["entity"]["entity_type"] for n in _nodes()}
        retrieved = {e["to_entity_id"] for e in edges if e["edge_type"] == "RETRIEVES_SECRET_FROM__aws_core"
                     and types[e["from_entity_id"]] == "aws_core__aws_lambda"}
        shown_secrets = {n["entity"]["entity_id"] for n in _by_type("aws_core__aws_secrets_manager_secret")
                         if n["entity"]["dimensions"].get("overview") == "shown"}
        assert shown_secrets <= retrieved, "every secret still drawn is in the row"

    def test_the_row_is_the_state_bucket_the_pipeline_and_the_source_puller_in_that_order(self) -> None:
        """Ruled 2026-10-20: the image repository, the GitHub App token, the bundle bucket and the plan and apply
        projects carry no `overview` value (nodes kept for the grid); the three that remain are ordered by the
        `layout:order` tag, which `_placeDeployRow` sorts on before label."""
        deploy_types = {"aws_core__aws_s3_bucket", "aws_core__aws_codepipeline_pipeline", "aws_core__aws_lambda",
                        "aws_core__aws_codebuild_project", "aws_core__aws_ecr_repository",
                        "aws_core__aws_secrets_manager_secret"}
        shown = [n for n in _nodes() if n["entity"]["entity_type"] in deploy_types
                 and n["entity"]["dimensions"].get("overview") == "shown"
                 and n["entity"]["name"].startswith(("terraform", "images", "github app"))]
        by_order = sorted(shown, key=lambda n: int(n["node"]["tags"]["layout:order"]))
        assert [n["entity"]["name"] for n in by_order] == ["terraform state", "terraform pipeline", "terraform source puller"]
        hidden = {"github app token", "images", "terraform plan", "terraform apply", "terraform bundle"}
        found = {n["entity"]["name"]: n["entity"]["dimensions"] for n in _nodes() if n["entity"]["name"] in hidden}
        assert set(found) == hidden and all("overview" not in dims for dims in found.values())

    def test_the_certificate_the_key_and_the_runtime_secret_are_not_on_the_overview(self) -> None:
        """`req-rampart-20x-playground-govcloud-layout-11`: no `overview` value, nodes kept for the grid."""
        hidden = {"tls certificate", "DB Encryption Key", "runtime secrets"}
        found = {n["entity"]["name"]: n["entity"]["dimensions"] for n in _nodes() if n["entity"]["name"] in hidden}
        assert set(found) == hidden
        assert all("overview" not in dims and dims.get("inventory") for dims in found.values())
        source = _js()
        assert "T.cert" not in source and "T.key" not in source

    def test_nothing_in_the_deploy_row_is_a_line_of_sight_type(self) -> None:
        assert not set(_list("DEPLOY_TYPES")) & {"zone", "alb", "rds", "igw"}

    def test_the_deploy_types_are_not_account_rows_any_more(self) -> None:
        tiers = re.search(r"tiers: \[(.*?)\n\s*\],", _js(), re.S)
        assert tiers
        named = set(re.findall(r"T\.(\w+)", tiers.group(1)))
        assert named == {"zone", "vpc"}

    def test_the_administrator_pair_hangs_under_the_account_centre(self) -> None:
        source = _js()
        assert len(re.findall(r"const BELOW_ACCOUNT_GAP = \d+;", source)) == 1
        pair = source.split("function _closePairs")[1]
        assert "const x = account.position(\"x\");" in pair
        assert "productRoot.boundingBox(" in pair, "the pair hangs under the boundary's bottom edge"
        assert "computer.position({x, y});" in source and "person.position({x, y: y +" in source

    def test_the_members_stay_in_a_titled_scope_box(self) -> None:
        source = _js()
        assert "applyScopeBoxes(cy, [{label: DEPLOY_LABEL, filter: (n) => ids.has(n.id())" in source
        assert re.search(r'const DEPLOY_LABEL = "Continuous Delivery";', source)
        assert 'import {applyScopeBoxes} from "/static/tap_viz/js/runtime/layout-scope-boxes.js";' in source

    def test_the_icons_are_half_size_and_stand_as_a_card_pile_at_the_bottom_right(self) -> None:
        """George 2026-10-20: 'shrink the CD icons by half size, keep them in a stacked pile [a card pile] and place the set at the
        bottom-right of the account, keep the Continuous Delivery grouping'. The pile is back to front in `layout:order`."""
        source = _js()
        assert "const DEPLOY_SCALE = 0.5;" in source and "width: SOLO.width * DEPLOY_SCALE" in source
        assert 10 <= int(re.search(r"const PILE_STEP = (\d+);", source).group(1)) <= 40
        body = source.split("function _placeDeployPile")[1].split("\n}\n")[0]
        assert "const left = box.x2 - pad.right - DEPLOY_BOX_PADDING - (w + spread);" in body, "the right edge, inside the account"
        assert "left + w / 2 + PILE_STEP * i" in body and "top + h / 2 + PILE_STEP * i" in body
        assert "baseZ + i" in body, "the last is in front"
        assert 'tagOrder(a)' in body and "layout:order" in body
        assert "lineY: " in body
        assert "const pile = _placeDeployPile(cy, account, deploy, pad, slotSize.height);" in source and "_growAncestors(cy, account, accountBottom);" in source
        assert "Playground exception 28 (should become a `pile` arrangement" in source

    def test_the_old_row_code_is_gone(self) -> None:
        assert "DEPLOY_GAP" not in _js() and "_placeDeployRow" not in _js()

    def test_edges_inside_the_row_are_hidden_and_the_others_stay(self) -> None:
        assert "deploy.anySame(e.source()) && deploy.anySame(e.target())" in _js()


class TestLineOfSight:
    """`req-rampart-20x-playground-govcloud-layout-2`, `-actors-3`: C4."""

    def test_load_balancer_is_the_anchor_and_the_gateway_goes_on_its_line(self) -> None:
        source = _js()
        assert "const anchor = shown([T.alb]).first();" in source
        assert re.search(r"alignDistributeHorizontal\(cy, \{members: gateway, anchorNode: anchor, distribute: false", source)

    def test_github_sits_after_the_account_and_before_the_developer_s_computer(self) -> None:
        """The order is data: columns from the dimensions (people, computers) and the tags (account, GitHub)."""
        columns: dict[str, int] = {}
        for node in _nodes():
            entity = node["entity"]
            dims, tags = entity.get("dimensions", {}), node["node"].get("tags", {})
            raw = dims.get("column", tags.get("layout:column"))
            if raw is not None and entity["name"] in {
                "customer", "customer computer", "Authorization Boundary", "github.com",
                "developer laptop", "developer",
            }:
                columns[entity["name"]] = int(raw)
        order = ["customer", "customer computer", "Authorization Boundary", "github.com",
                 "developer laptop", "developer"]
        assert [columns[n] for n in order] == sorted(columns[n] for n in order)
        assert len(set(columns.values())) == len(order)

    def test_github_carries_its_column_as_a_tag(self) -> None:
        """The platform type has a tagging system; its column is a tag, never a dimension."""
        (github,) = _by_type("github_core__github_platform")
        assert github["node"]["tags"]["layout:column"] == "4"
        assert "column" not in github["entity"].get("dimensions", {})

    def test_no_placement_by_label_or_id(self) -> None:
        source = _js()
        assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", source)
        assert not re.search(r"data\(\"label\"\)\s*===", source)


class TestAuthorizationBoundary:
    """`req-rampart-20x-playground-govcloud-layout-12`, `-nongoals-3`: C5 (Overview Wave 2)."""

    def _boundary(self) -> dict:
        (boundary,) = _by_type("compliance_core__compliance_boundary")
        return boundary

    def test_one_boundary_node_with_the_producers_natural_key(self) -> None:
        boundary = self._boundary()
        assert boundary["node"]["source"] == "rampart_20x_playground"
        assert boundary["node"]["source_key"] == "git-serious"
        assert boundary["node"]["name"] == boundary["entity"]["name"] == "Authorization Boundary"
        assert "mock" not in boundary["node"]["description"].lower()
        dims = boundary["entity"]["dimensions"]
        assert dims["dcom"] == "design" and dims["overview"] == "shown"

    def test_one_scoped_to_edge_from_the_account_only(self) -> None:
        boundary = self._boundary()["entity"]["entity_id"]
        edges = [e["edge"] for b in json.loads(MOCK.read_text(encoding="utf-8"))["batches"] for e in b["edges"]
                 if e["edge"]["edge_type"] == "SCOPED_TO_COMPLIANCE_BOUNDARY__compliance_core"]
        (account,) = [n for n in _by_type("aws_core__aws_account") if n["entity"]["name"] == "git-serious"]
        assert [(e["from_entity_id"], e["to_entity_id"]) for e in edges] == [(account["entity"]["entity_id"], boundary)]

    def test_the_boundary_carries_the_column_and_the_account_does_not(self) -> None:
        """The layout tags move to the boundary: a type with no tagging system carries `column` and `row`."""
        dims = self._boundary()["entity"]["dimensions"]
        assert dims["column"] == "3" and dims["row"] == "0"
        (account,) = [n for n in _by_type("aws_core__aws_account") if n["entity"]["name"] == "git-serious"]
        assert "layout:column" not in account["node"].get("tags", {})
        assert "column" not in account["entity"]["dimensions"]

    def test_the_account_nests_in_the_boundary_by_a_configured_relationship(self) -> None:
        source = _js()
        assert re.search(r"name: \"boundary-holds-account\", gryphon: `\(parent:\$\{T\.boundary\}\)<-\[:\$\{E\.scopedTo\}\]-\(child:\$\{T\.account\}\)`", source)
        assert 'boundary: "compliance_core__compliance_boundary"' in source
        assert 'scopedTo: "SCOPED_TO_COMPLIANCE_BOUNDARY__compliance_core"' in source
        assert "boundary" in _list("CONTAINERS")

    def test_the_product_column_is_found_through_the_nesting_not_a_type(self) -> None:
        source = _js()
        assert "const productRoot = account.nonempty() ? _outermost(cy, account) : account;" in source
        assert 'productRoot.data("_stage")' in source
        assert "account.data(\"_stage\")" not in source

    def test_the_boundary_grows_with_the_account_and_is_marked_an_exception(self) -> None:
        source = _js()
        assert "_growAncestors(cy, account, accountBottom);" in source
        assert "Playground exception (should become the same `reserve` option" in source

    def test_the_boundary_is_transparent_bold_red_with_its_title_above(self) -> None:
        source = _js()
        body = source.split("function _styleBoundary")[1].split("function _whenShown")[0]
        assert '"background-opacity": 0' in body
        assert '"border-opacity": 1' in body, "a true red, not the runtime's 0.6-opacity container border"
        assert '"text-valign": "top"' in body and "-BOUNDARY_LABEL_RISE" in body
        assert "_styleBoundary(cy, shown([T.boundary]));" in source
        assert re.search(r'const BOUNDARY_RED = "#dc2626";', source)
        assert int(re.search(r"const BOUNDARY_LINE_WIDTH = (\d+);", source).group(1)) >= 3
        assert "should become a per-node display override" in source

    def test_a_search_brings_the_scoped_to_edge_and_collides_with_no_other(self) -> None:
        pages = json.loads((PACKAGE_ROOT / "grift" / "pages.grift.json").read_text(encoding="utf-8"))["batches"][0]
        all_searches = [n for n in pages["nodes"] if n["entity"]["entity_type"] == "search"]
        # Module Searches (the badge counts) carry a runner_key, not a query; every other Search is a Gryphon query.
        for n in all_searches:
            if n["node"]["search_type"] == "module":
                assert n["node"]["definition"]["runner_key"] and "query" not in n["node"]["definition"], n["entity"]["name"]
            else:
                assert n["node"]["search_type"] == "gryphon", n["entity"]["name"]
        searches = {n["entity"]["name"]: " ".join(n["node"]["definition"]["query"])
                    for n in all_searches if n["node"]["search_type"] == "gryphon"}
        scoped = [q for q in searches.values() if "SCOPED_TO_COMPLIANCE_BOUNDARY" in q]
        assert len(scoped) == 1 and 'b.dimensions["overview"] = "shown"' in scoped[0]
        assert "playground \u2014 landing scoped" in searches
        # The bundle also holds the notification card of the Overview (`req-rampart-20x-playground-govcloud-layout-37`): the graph is the other panel.
        (panel,) = [n for n in pages["nodes"] if n["entity"]["entity_type"] == "panel" and n["node"]["slug"] == "playground-landing-graph"]
        used = {e["edge"]["to_entity_id"] for e in pages["edges"]
                if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]}
        (search,) = [n for n in pages["nodes"] if n["entity"]["name"] == "playground \u2014 landing scoped"]
        assert search["entity"]["entity_id"] in used

    def test_the_specs_say_the_boundary_is_drawn(self) -> None:
        v0 = (SPECS / "spec-rampart_20x_playground-v0.md").read_text(encoding="utf-8")
        landing = (SPECS / "spec-rampart_20x_playground-govcloud-landing.md").read_text(encoding="utf-8")
        assert "| Mock Is Not A Boundary |" not in v0 and "Mock Data, One Drawn Boundary" in v0
        assert "req-rampart-20x-playground-govcloud-layout-12" in landing


class TestPersonComputerPairs:
    """`req-rampart-20x-playground-govcloud-layout-10`."""

    def test_one_named_gap_constant_marked_as_an_exception(self) -> None:
        source = _js()
        assert len(re.findall(r"const PAIR_GAP = \d+;", source)) == 1
        gap = int(re.search(r"const PAIR_GAP = (\d+);", source).group(1))
        assert 20 <= gap <= 32
        assert "_closePairs(roots, account, productRoot);" in source

    def test_the_pair_is_read_from_the_actor_and_device_dimensions(self) -> None:
        source = _js()
        assert 'dim(n, "actor")' in source and 'dim(n, "device")' in source
        assert 'dim(c, "device") === dim(person, "actor")' in source

    def test_every_person_has_exactly_one_computer_with_the_same_value(self) -> None:
        people = {n["entity"]["dimensions"]["actor"] for n in _by_type("identity_core__human")}
        devices = [n["entity"]["dimensions"]["device"] for n in _by_type("computing_core__host")
                   if "device" in n["entity"]["dimensions"]]
        assert people == {"customer", "developer", "administrator"}
        assert sorted(devices) == sorted(people)


class TestPlaygroundException:
    """`req-rampart-20x-playground-nongoals-5`: the standing exception is marked where it is used and recorded."""

    def test_every_tweak_names_the_runtime_form_it_becomes(self) -> None:
        source = _js()
        marks = re.findall(r"[Pp]layground exception[^\n]*", source)
        assert len(marks) >= 4
        assert "should become" in source
        assert "fold into tap_viz" in source

    def test_the_spec_records_the_exception_and_its_exit(self) -> None:
        text = (SPECS / "spec-rampart_20x_playground-v0.md").read_text(encoding="utf-8")
        assert "req-rampart-20x-playground-nongoals-5" in text
        assert "fold into tap_viz when the concepts settle" in text

    def test_the_landing_spec_carries_the_new_requirements(self) -> None:
        text = (SPECS / "spec-rampart_20x_playground-govcloud-landing.md").read_text(encoding="utf-8")
        for rid in ("govcloud-layout-8", "govcloud-layout-9", "govcloud-layout-2", "govcloud-layout-13",
                    "govcloud-layout-14", "govcloud-layout-15", "govcloud-layout-16", "govcloud-layout-17", "govcloud-layout-18",
                    "govcloud-layout-19", "govcloud-layout-20", "govcloud-layout-21", "govcloud-layout-22", "govcloud-layout-23", "govcloud-layout-25", "govcloud-layout-27", "govcloud-layout-28", "govcloud-layout-29"):
            assert f"req-rampart-20x-playground-{rid}" in text


APPLICATION_FLOW = PACKAGE_ROOT / "grift" / "application-flow.grift.json"
ENTITIES = PACKAGE_ROOT / "grift" / "inventory-entities.grift.json"
SOFTWARE = PACKAGE_ROOT / "grift" / "inventory-software.grift.json"  # holds the container image hosts
PAGES = PACKAGE_ROOT / "grift" / "pages.grift.json"


def _batch_nodes(path: Path) -> list[dict]:
    return [n for b in json.loads(path.read_text(encoding="utf-8"))["batches"] for n in b["nodes"]]


def _batch_edges(path: Path) -> list[dict]:
    return [e["edge"] for b in json.loads(path.read_text(encoding="utf-8"))["batches"] for e in b["edges"]]


def _name(entity_id: str) -> str:
    for path in (MOCK, ENTITIES, APPLICATION_FLOW, SOFTWARE):
        for node in _batch_nodes(path):
            if node["entity"].get("entity_id") == entity_id:
                return node["entity"]["name"]
    return entity_id


class TestRunningParts:
    """`req-rampart-20x-playground-govcloud-layout-13`: the containers and programs of the two web tasks (Overview Wave 3)."""

    def test_one_container_per_task_with_a_real_shaped_arn_image_and_digest(self) -> None:
        containers = [n for n in _batch_nodes(APPLICATION_FLOW) if n["entity"]["entity_type"] == "aws_core__aws_ecs_container"]
        assert sorted(n["entity"]["name"] for n in containers) == ["tap-web", "web task b container"]
        for node in containers:
            fields = node["node"]
            assert fields["container_arn"].startswith("arn:aws-us-gov:ecs:us-gov-west-1:100000000001:container/git-serious/")
            assert fields["image"] and fields["image_digest"].startswith("sha256:")
            assert node["entity"]["dimensions"]["dcom"] == "design"
            assert "mock" not in json.dumps(node).lower()

    def test_the_edges_are_official_and_each_container_has_its_own_gunicorn_and_tap_web(self) -> None:
        edges = _batch_edges(APPLICATION_FLOW)
        by_type: dict[str, list[tuple[str, str]]] = {}
        for edge in edges:
            by_type.setdefault(edge["edge_type"], []).append((_name(edge["from_entity_id"]), _name(edge["to_entity_id"])))
        assert sorted(by_type["RUNS_TASK__aws_core"]) == [
            ("cluster", "web task a"), ("cluster", "web task b"), ("web", "web task a"), ("web", "web task b")]
        assert sorted(by_type["RUNS_CONTAINER__aws_core"]) == [
            ("web task a", "tap-web"), ("web task b", "web task b container")]
        assert sorted(by_type["RUNS_PROGRAM__computing_core"]) == [
            ("RDS A", "PostgreSQL database instance"),
            ("Wolfi", "gunicorn"), ("Wolfi", "tap-web"),
            ("gunicorn", "tap-web"), ("gunicorn (web task b)", "tap-web (web task b)"),
            ("tap-web", "gunicorn"),
            ("teleport", "teleport auth"), ("teleport", "teleport proxy"), ("teleport", "teleport ssh"),
            ("web task b container", "gunicorn (web task b)")]
        assert sorted(by_type["RUNS_IMAGE__computing_core"]) == [
            ("tap-web", "git-serious web image"), ("web task b container", "git-serious web image")]

    def test_the_programs_are_one_set_per_container_and_postgres_stays(self) -> None:
        programs = {n["entity"]["name"]: n for n in _batch_nodes(ENTITIES) if n["entity"]["entity_type"] == "computing_core__program"}
        assert sorted(programs) == [
            "PostgreSQL database instance", "gunicorn", "gunicorn (web task b)",
            "tap-web", "tap-web (web task b)", "teleport auth", "teleport proxy", "teleport ssh"]
        assert programs["tap-web"]["node"]["program_name"] == programs["tap-web (web task b)"]["node"]["program_name"] == "tap-web"
        for node in programs.values():
            assert node["entity"]["dimensions"]["inventory"] == "applications"

    def test_the_three_teleport_programs_run_on_the_teleport_instance_and_are_not_on_the_overview(self) -> None:
        names = ("teleport proxy", "teleport auth", "teleport ssh")
        programs = {n["entity"]["name"]: n for n in _batch_nodes(ENTITIES) if n["entity"]["name"] in names}
        assert sorted(programs) == sorted(names)
        for node in programs.values():
            dims = node["entity"]["dimensions"]
            assert dims["inventory"] == "applications" and dims["dataclass.action"] == "process"
            assert "overview" not in dims
        ends = [(_name(e["from_entity_id"]), _name(e["to_entity_id"])) for e in _batch_edges(APPLICATION_FLOW)
                if e["edge_type"] == "RUNS_PROGRAM__computing_core" and _name(e["from_entity_id"]) == "teleport"]
        assert sorted(ends) == sorted(("teleport", n) for n in names)

    def test_only_web_task_a_s_interior_the_flows_and_the_database_program_are_on_the_overview(self) -> None:
        shown = {n["entity"]["name"] for n in _batch_nodes(APPLICATION_FLOW) + _batch_nodes(ENTITIES)
                 if n["entity"]["dimensions"].get("overview") == "shown"}
        assert shown == {"tap-web", "customer data", "gunicorn", "PostgreSQL database instance",
                         "database", "administration", "code", "source pull",
                         "container tls private key", "container tls public key", "container tls certificate"}

    def test_the_nesting_is_configured_relationships_not_type_tests(self) -> None:
        source = _js()
        # Exception 51: the three piles are held by the operating system box, not the container.
        for name in ("task-holds-container", "container-holds-os", "os-holds-program", "os-holds-library", "os-holds-package",
                     "os-holds-key"):
            assert f'name: "{name}"' in source
        assert "(parent:${T.task})-[:${E.runsContainer}]->(child:${T.ecsContainer})" in source
        assert "(parent:${T.os})-[:${E.runsProgram}]->(child:${T.program})" in source
        assert {"task", "ecsContainer"} <= set(_list("CONTAINERS"))

    def test_searches_bring_the_containment_edges_and_the_flow_edges(self) -> None:
        pages = json.loads(PAGES.read_text(encoding="utf-8"))["batches"][0]
        all_searches = [n for n in pages["nodes"] if n["entity"]["entity_type"] == "search"]
        # Module Searches (the badge counts) carry a runner_key, not a query; every other Search is a Gryphon query.
        for n in all_searches:
            if n["node"]["search_type"] == "module":
                assert n["node"]["definition"]["runner_key"] and "query" not in n["node"]["definition"], n["entity"]["name"]
            else:
                assert n["node"]["search_type"] == "gryphon", n["entity"]["name"]
        searches = {n["entity"]["name"]: " ".join(n["node"]["definition"]["query"])
                    for n in all_searches if n["node"]["search_type"] == "gryphon"}
        for slug, edge in (("runs-container", "RUNS_CONTAINER__aws_core"), ("runs-program", "RUNS_PROGRAM__computing_core"),
                           ("flow-source", "APPLICATION_FLOW_SOURCE__computing_core"),
                           ("flow-destination", "APPLICATION_FLOW_DESTINATION__computing_core")):
            query = searches[f"playground \u2014 landing {slug}"]
            assert edge in query and 'a.dimensions["overview"] = "shown" AND b.dimensions["overview"] = "shown"' in query
        # The bundle also holds the notification card of the Overview (`req-rampart-20x-playground-govcloud-layout-37`): the graph is the other panel.
        (panel,) = [n for n in pages["nodes"] if n["entity"]["entity_type"] == "panel" and n["node"]["slug"] == "playground-landing-graph"]
        used = {e["edge"]["to_entity_id"] for e in pages["edges"]
                if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]}
        search_ids = {n["entity"]["name"]: n["entity"]["entity_id"] for n in pages["nodes"] if n["entity"]["entity_type"] == "search"}
        for slug in ("runs-container", "runs-program", "flow-source", "flow-destination"):
            assert search_ids[f"playground \u2014 landing {slug}"] in used

    def test_entity_ids_are_unique_across_the_bundles(self) -> None:
        seen: dict[str, str] = {}
        for path in (MOCK, ENTITIES, APPLICATION_FLOW, PAGES):
            for batch in json.loads(path.read_text(encoding="utf-8"))["batches"]:
                for item in [*batch["nodes"], *batch["edges"]]:
                    eid = item["entity"]["entity_id"]
                    assert eid not in seen, eid
                    seen[eid] = path.name


class TestApplicationFlow:
    """`req-rampart-20x-playground-govcloud-layout-14`: one flow, keyless, with its two edges and one data class."""

    def _flow(self) -> dict:
        (flow,) = [n for n in _batch_nodes(APPLICATION_FLOW) if n["entity"]["entity_type"] == "computing_core__application_flow"
                   and n["entity"]["name"] == "customer data"]
        return flow

    def test_one_flow_with_a_name_a_description_and_one_data_class(self) -> None:
        flow = self._flow()
        assert flow["node"]["name"] == flow["entity"]["name"] and flow["node"]["description"]
        assert set(flow["node"]) == {"name", "description"}
        dims = flow["entity"]["dimensions"]
        assert dims["dataclass.customer"] == "data" and dims["dcom"] == "design" and dims["overview"] == "shown"
        assert [k for k in dims if k.startswith("dataclass.")] == ["dataclass.customer", "dataclass.action"]
        assert dims["dataclass.action"] == "transmit"
        assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", flow["entity"]["entity_id"])

    def test_the_flow_runs_from_the_customer_s_computer_to_the_tap_web_program_of_task_a(self) -> None:
        flow_id = self._flow()["entity"]["entity_id"]
        edges = [e for e in _batch_edges(APPLICATION_FLOW) if flow_id in (e["from_entity_id"], e["to_entity_id"])]
        assert sorted((e["edge_type"], _name(e["from_entity_id"]), _name(e["to_entity_id"])) for e in edges) == [
            ("APPLICATION_FLOW_DESTINATION__computing_core", "customer data", "gunicorn"),
            ("APPLICATION_FLOW_SOURCE__computing_core", "customer computer", "customer data"),
        ]

    def test_the_flow_is_a_half_size_dark_blue_circle_centred_in_the_gap_on_the_line_of_sight(self) -> None:
        source = _js()
        assert "applyIconNodes(cy, {members: shown([T.flow])" in source and "solo: true" in source
        assert "const FLOW_SCALE = 0.5;" in source and 'const FLOW_BLUE = "#0B3D91";' in source
        assert 'n.data("_stage") < flow.data("_stage")' in source, "centred between what is left of it and the product box"
        assert "_centreFlow(cy, roots, productRoot, shown([T.flow]).not(placed));" in source
        edges = source.split("function _styleFlowEdges")[1].split("\n}\n")[0]
        assert 'const head = type === E.flowDestination;' in edges, "the one arrowhead is on the destination line"
        assert '"target-arrow-shape": head ? "triangle" : "none"' in edges and '"source-arrow-shape": "none"' in edges


class TestEdgeLiftAndLayers:
    """`req-rampart-20x-playground-govcloud-layout-16`: the flow's edge ends on the task at the account elevation and
    is drawn above the container fills and below the leaf nodes."""

    def test_the_edge_lift_is_data_relationships_and_the_interior_is_hidden_at_the_account_elevation(self) -> None:
        source = _js()
        assert "const LIFT_EDGE = [" in source and "liftEdge(cy, {relationships: LIFT_EDGE})" in source
        assert "next.contained.addClass(ELEVATION_HIDDEN_CLASS);" in source
        assert "const REVEAL_ON_ZOOM = true;" in source, "the reveal is on now that tap_viz guards the scope box (tap#1077)"

    def test_edges_sit_between_the_container_fills_and_the_leaf_nodes(self) -> None:
        source = _js()
        body = source.split("function _layerEdges")[1].split("\n}\n")[0]
        assert '"z-compound-depth": "auto"' in body, "not `top`, which draws over every node"
        assert '"z-index-compare": "manual"' in body, "`auto` draws every node after every edge"
        assert "edgeZ + 1" in body and "isParent(n) || isOwnLayer(n)" in body
        assert "_layerEdges(cy);" in source
        assert "Playground exception 13 (should become an `edge_layer` option of applyStandardChrome" in source


class TestZoomPolish:
    """`req-rampart-20x-playground-govcloud-layout-18`: the revealed interior (Overview Wave 9)."""

    def _program(self, name: str) -> dict:
        return next(n for n in _batch_nodes(ENTITIES) if n["entity"]["name"] == name)

    def test_gunicorn_stands_left_of_tap_web_and_the_titles_carry_no_task_suffix(self) -> None:
        gunicorn, tap_web = self._program("gunicorn"), self._program("tap-web")
        assert int(gunicorn["entity"]["dimensions"]["column"]) < int(tap_web["entity"]["dimensions"]["column"])
        assert gunicorn["node"]["name"] == "gunicorn" and tap_web["node"]["name"] == "tap-web"
        assert tap_web["node"]["program_name"] == "tap-web"
        # Identity is the fixed entity id, never the name: the ids did not move.
        assert gunicorn["entity"]["entity_id"] == "01a13be3-0373-79d4-9ae8-be13c2e3bfd5"
        assert tap_web["entity"]["entity_id"] == "01a13be3-0373-7afc-8d07-441072bee2eb"

    def test_the_container_takes_its_type_badge_because_it_is_no_longer_excluded(self) -> None:
        pages = json.loads(PAGES.read_text(encoding="utf-8"))
        projection = next(n for b in pages["batches"] for n in b["nodes"] if n["entity"]["entity_type"] == "projection")
        excluded = projection["node"]["definition"]["node_style"]["exclude_types"]
        assert excluded == ["computing_core__program", "computing_core__library", "computing_core__package",
                            "computing_core__private_key", "computing_core__public_key", "computing_core__file"]
        source = _js()
        assert "applyBadgeNodes(cy, {excludeTypes: exclude})" in source and "_refreshBadges(cy, context, true);" in source and "_refreshBadges(cy, context, false);" in source

    def test_the_container_is_a_darker_orange_than_the_task(self) -> None:
        source = _js()
        assert 'const CONTAINER_FILL = "#F29B38";' in source and 'const CONTAINER_BORDER = "#B45309";' in source
        assert "_styleContainer(cy, cy.nodes(" in source
        assert "Playground exception 18" in source

    def test_the_program_the_flow_ends_on_stands_on_the_line_of_sight(self) -> None:
        source = _js()
        body = source.split("function _alignInteriorToLine")[1].split("\n}\n")[0]
        assert "E.flowDestination" in body and 'anchor.position("y") - target.position("y")' in body
        assert "_alignInteriorToLine(cy, anchor);" in source
        assert "const TASK_TOP_ROOM = " in source and "Playground exception 17" in source

    def test_the_interior_fades_in_and_out_and_the_font_sizes_are_unchanged(self) -> None:
        source = _js()
        assert "const FADE_MS = " in source and "animate({style: {opacity: 1}" in source and "animate({style: {opacity: 0}" in source
        assert "Playground exception 15" in source and "Playground exception 16" in source
        assert "const INTERIOR_SCALE = 1 / ELEVATION_ZOOM_RATIO;" in source


class TestElevationFontScale:
    """`req-rampart-20x-playground-govcloud-layout-17`: the interior is laid out and labelled at one scale, once."""

    def test_the_interior_is_scaled_relative_to_the_account_so_the_task_box_never_resizes(self) -> None:
        source = _js()
        assert "const INTERIOR_SCALE = 1 / ELEVATION_ZOOM_RATIO;" in source
        assert "parentFontSize: chrome.parentFontSize * INTERIOR_SCALE" in source
        assert 'parents.filter(isInterior).style({"font-size"' in source
        assert "const BADGE_SIZE = 24;" in source and "_pinBadgeSize(cy);" in source
        assert "Playground exception 10" in source and "Playground exception 12" in source


class TestFlowWindow:
    """`req-rampart-20x-playground-govcloud-layout-15`: the node-tap window of Overview Wave 7."""

    def test_a_node_tap_handler_bound_once_by_the_layout(self) -> None:
        source = _js()
        assert 'cy.on("tap", "node", handler);' in source and 'cy.off("tap", "node", previous);' in source
        assert "_bindFlowWindow(cy);" in source

    def test_it_reads_the_node_s_own_data_and_makes_no_network_call(self) -> None:
        source = _js()
        body = source.split("function _bindFlowWindow")[1].split("function _placedFlows")[0]
        assert 'node.data("dimensions")' in body and 'node.data("fields")' in body and 'node.data("label")' in body
        assert 'const FLOW_DIMENSION_PREFIX = "dataclass.";' in source
        for call in ("fetch(", "XMLHttpRequest", "sendBeacon", "import("):
            assert call not in body

    def test_it_reuses_the_info_window_classes_and_dismisses_like_it(self) -> None:
        body = _js().split("function _bindFlowWindow")[1]
        for cls in ("tap-info-window__header", "tap-info-window__name", "tap-info-window__close", "tap-info-window__body",
                    "tap-info-window__section", "tap-info-window__table"):
            assert cls in body
        assert 'e.key === "Escape"' in body and "outsideClick" in body and "closeInfoWindow();" in body
        assert 'import {closeInfoWindow} from "/static/tap_viz/js/runtime/info-window.js";' in _js()

    def test_it_is_marked_a_standing_exception_with_its_exit(self) -> None:
        source = _js()
        assert "Playground exception 7 (STANDING EXCEPTION; should become a projection-declared `node_info` window of tap_viz" in source
        v0 = (SPECS / "spec-rampart_20x_playground-v0.md").read_text(encoding="utf-8")
        assert "its click window, a node-tap handler" in v0


class TestTaskBubbleSearches:
    """Overview Wave 6: the open-findings bubble and its window are module Searches that sum two routes."""

    def _searches(self) -> dict[str, dict]:
        pages = json.loads(PAGES.read_text(encoding="utf-8"))["batches"][0]
        return {n["entity"]["name"]: n["node"] for n in pages["nodes"] if n["entity"]["entity_type"] == "search"}

    def test_the_two_searches_are_the_reach_runners_with_both_routes_as_defaults(self) -> None:
        searches = self._searches()
        count = searches["playground — landing task-open-findings"]
        listing = searches["playground — landing task-open-vulnerabilities"]
        assert count["search_type"] == listing["search_type"] == "module"
        assert count["definition"]["runner_key"] == "tap_plugin.compliance_core.searches.reach:findings-reached-count"
        assert listing["definition"]["runner_key"] == "tap_plugin.compliance_core.searches.reach:findings-reached-list"
        for node in (count, listing):
            props = node["input_schema"]["properties"]
            assert props["root_type"]["default"] == "aws_core__aws_ecs_task"
            assert [chain[-1] for chain in props["paths"]["default"]] == [
                "INSTALLS_PACKAGE__computing_core", "LOADS_LIBRARY__computing_core"]
            assert "Gryphon has no multi-path aggregate" in node["description"]

    def test_both_tasks_load_the_two_libraries(self) -> None:
        programs = {n["entity"]["entity_id"]: n["entity"]["name"] for n in _batch_nodes(ENTITIES)}
        libs = {e["to_entity_id"] for e in _batch_edges(APPLICATION_FLOW) if e["edge_type"] == "LOADS_LIBRARY__computing_core"}
        sources = {programs[e["from_entity_id"]] for e in _batch_edges(APPLICATION_FLOW) if e["edge_type"] == "LOADS_LIBRARY__computing_core"}
        assert sources == {"tap-web (web task b)"} and len(libs) == 2  # task a's two are in the software bundle


class TestVulnerabilityWindowColumns:
    """Overview: the vulnerability window is a table (core `info_window.columns`, tap#1076)."""

    def test_the_window_shows_id_cvss_and_title_as_columns_with_the_id_as_the_link(self) -> None:
        pages = json.loads(PAGES.read_text(encoding="utf-8"))["batches"][0]
        windows = [
            badge_set["info_window"]
            for n in pages["nodes"]
            for badge_set in n["node"].get("definition", {}).get("status_badges", {}).get("badge_sets", [])
        ]
        assert len(windows) == 1
        columns = windows[0]["columns"]
        assert [(c["field"], c["label"]) for c in columns] == [("id", "ID"), ("cvss", "CVSS"), ("title", "Title"), ("component", "Component")]
        assert columns[0]["link"] is True
        assert columns[0]["nowrap"] is True, "a CVE id stays on one line"
        assert columns[1]["format"] == "number" and columns[1]["align"] == "right"
        assert windows[0]["row_url_template"].endswith("vuln_id={id}")


class TestMoreApplicationFlows:
    """`req-rampart-20x-playground-govcloud-layout-20`, `-21`: the four flows after the customer's, and the database's two forms."""

    def _flows(self) -> dict[str, dict]:
        return {n["entity"]["name"]: n for n in _batch_nodes(APPLICATION_FLOW)
                if n["entity"]["entity_type"] == "computing_core__application_flow" and n["entity"]["dimensions"].get("overview") == "shown"}

    def test_each_flow_is_keyless_shown_unranked_and_stamped_with_one_data_class(self) -> None:
        flows = self._flows()
        assert sorted(flows) == ["administration", "code", "customer data", "database", "source pull"]
        expected = {"database": ("dataclass.customer", "sanitized"), "administration": ("dataclass.infra", "admin"),
                    "code": ("dataclass.infra", "code"), "source pull": ("dataclass.infra", "code")}
        for name, (key, value) in expected.items():
            dims = flows[name]["entity"]["dimensions"]
            assert dims[key] == value and dims["overview"] == "shown" and "column" not in dims and "row" not in dims, name
            assert [k for k in dims if k.startswith("dataclass.")] == [key, "dataclass.action"]
            assert dims["dataclass.action"] == "transmit"
            assert set(flows[name]["node"]) == {"name", "description"} and flows[name]["node"]["description"]
            assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", flows[name]["entity"]["entity_id"])

    def test_each_flow_runs_between_the_named_ends(self) -> None:
        edges = _batch_edges(APPLICATION_FLOW)
        ends = {}
        for name, node in self._flows().items():
            fid = node["entity"]["entity_id"]
            source = [_name(e["from_entity_id"]) for e in edges
                      if e["to_entity_id"] == fid and e["edge_type"] == "APPLICATION_FLOW_SOURCE__computing_core"]
            dest = [_name(e["to_entity_id"]) for e in edges
                    if e["from_entity_id"] == fid and e["edge_type"] == "APPLICATION_FLOW_DESTINATION__computing_core"]
            ends[name] = (source, dest)
        assert ends["database"] == (["tap-web"], ["PostgreSQL database instance"])
        assert ends["administration"] == (["administrator workstation"], ["teleport"])
        assert ends["code"] == (["developer laptop"], ["github.com"])
        assert ends["source pull"] == (["terraform source puller"], ["github.com"])

    def test_the_database_program_is_joined_to_the_rds_instance_by_runs_program_and_shown(self) -> None:
        (rds,) = [n for n in _by_type("aws_core__aws_rds_instance")]
        (pg,) = [n for n in _batch_nodes(ENTITIES) if n["entity"]["name"] == "PostgreSQL database instance"]
        assert pg["entity"]["dimensions"]["overview"] == "shown"
        wired = [e for e in _batch_edges(APPLICATION_FLOW) if e["edge_type"] == "RUNS_PROGRAM__computing_core"
                 and e["from_entity_id"] == rds["entity"]["entity_id"]]
        assert [e["to_entity_id"] for e in wired] == [pg["entity"]["entity_id"]]

    def test_the_database_nests_and_lifts_by_configured_relationships(self) -> None:
        source = _js()
        assert source.count('name: "database-holds-program"') == 2, "once in the nesting and once in the lift"
        assert "(parent:${T.rds})-[:${E.runsProgram}]->(child:${T.program})" in source
        assert "rds" not in _list("SOLO_TYPES"), "the database is a solo icon only through _formDatabase"

    def test_the_rds_instance_is_named_rds_a_and_its_other_identity_is_unchanged(self) -> None:
        (rds,) = _by_type("aws_core__aws_rds_instance")
        assert rds["entity"]["name"] == rds["node"]["name"] == "RDS A"
        assert rds["node"]["db_instance_id"] == "git-serious" and rds["entity"]["entity_id"] == "01a13b2b-a806-70ab-bec7-d24211bfdd43"

    def test_the_two_forms_and_the_top_right_badge_are_one_marked_exception(self) -> None:
        source = _js()
        assert "_formDatabase(cy, cy.nodes(`[entity_type = \"${T.rds}\"]`), true);" in source
        assert "_formDatabase(cy, cy.nodes(`[entity_type = \"${T.rds}\"]`), false);" in source
        assert "badge.position({x: bb.x2, y: bb.y1});" in source
        assert "Playground exception 26 (should become the `icon-solo` / `standard` forms" in source
        assert "const RDS_BOX = " in source

    def test_a_flow_with_no_column_is_hidden_during_the_nesting_and_placed_between_its_ends(self) -> None:
        source = _js()
        assert "const placed = _placedFlows(shown([T.flow]));" in source
        assert "placed.addClass(ELEVATION_HIDDEN_CLASS);" in source and "placed.removeClass(ELEVATION_HIDDEN_CLASS);" in source
        assert "_placeFlows(cy, placed);" in source
        body = source.split("function _placeFlows")[1].split("\n}\n")[0]
        assert "E.flowSource" in body and "E.flowDestination" in body and "outermost" in body
        assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}", body) and 'data("label")' not in body

    def test_the_gaps_that_hold_a_flow_are_named_constants(self) -> None:
        source = _js()
        assert int(re.search(r"const VPC_COLUMN_GAP = (\d+);", source).group(1)) >= 100
        assert int(re.search(r"const BELOW_ACCOUNT_GAP = (\d+);", source).group(1)) >= 150
        assert "columnGap: VPC_COLUMN_GAP" in source

    def test_the_interior_alignment_moves_only_what_the_same_node_holds(self) -> None:
        body = _js().split("function _alignInteriorToLine")[1].split("\n}\n")[0]
        assert "outermost.get(target.id())" in body and "top !== holder" in body


class TestDeliveryLine:
    """`req-rampart-20x-playground-govcloud-layout-22`: GitHub, the developer's laptop and the developer stand on the delivery line."""

    def test_the_marker_is_data_on_the_three_nodes_and_nowhere_else(self) -> None:
        marked = []
        for node in _nodes():
            dims, tags = node["entity"]["dimensions"], node["node"].get("tags", {})
            if dims.get("line") == "delivery" or tags.get("layout:line") == "delivery":
                marked.append(node["entity"]["name"])
        assert sorted(marked) == ["developer", "developer laptop", "github.com"]
        (github,) = _by_type("github_core__github_platform")
        assert github["node"]["tags"]["layout:line"] == "delivery" and "line" not in github["entity"]["dimensions"]

    def test_the_order_after_the_boundary_is_github_laptop_developer_and_is_unchanged(self) -> None:
        github = _by_type("github_core__github_platform")[0]
        laptop = next(n for n in _by_type("computing_core__host") if n["entity"]["name"] == "developer laptop")
        person = next(n for n in _by_type("identity_core__human") if n["entity"]["name"] == "developer")
        assert int(github["node"]["tags"]["layout:column"]) < int(laptop["entity"]["dimensions"]["column"]) \
            < int(person["entity"]["dimensions"]["column"])
        assert laptop["entity"]["dimensions"]["row"] == person["entity"]["dimensions"]["row"] == "0", "a horizontal pair"

    def test_the_layout_reads_the_marker_not_a_type_or_a_name_and_keeps_them_off_the_line_of_sight(self) -> None:
        source = _js()
        body = source.split("function _onDeliveryLine")[1].split("\n}\n")[0]
        assert "LINE_KEY" in body and "LINE_TAG" in body and "LINE_DELIVERY" in body
        assert 'T.' not in body and 'data("label")' not in body
        assert 'const LINE_TAG = "layout:line";' in source and 'const LINE_KEY = "line";' in source
        assert '!_onDeliveryLine(n)' in source, "off the load balancer's line"
        assert "anchor: {y: pile.lineY}, distribute: false" in source, "onto the pile's line, align-only"
        assert "roots.filter(_onDeliveryLine)" in source

    def test_the_two_flows_to_github_are_drawn_between_their_ends(self) -> None:
        names = {n["entity"]["name"] for n in _batch_nodes(APPLICATION_FLOW)}
        assert {"code", "source pull"} <= names

    def test_the_specs_record_it(self) -> None:
        text = (SPECS / "spec-rampart_20x_playground-govcloud-landing.md").read_text(encoding="utf-8")
        assert "req-rampart-20x-playground-govcloud-layout-22" in text and "card pile" in text


class TestTeleportVpc:
    """`req-rampart-20x-playground-govcloud-layout-23`: teleport is a VPC in the git-serious account, not an account."""

    def _named(self, entity_type: str, name: str) -> dict:
        (node,) = [n for n in _by_type(entity_type) if n["entity"]["name"] == name]
        return node

    def test_the_vpc_the_subnet_and_the_instance_exist_with_their_siblings_dimensions(self) -> None:
        vpc = self._named("aws_core__aws_vpc", "Admin Access")
        subnet = self._named("aws_core__aws_subnet", "public")
        instance = self._named("aws_core__aws_ec2_instance", "teleport")
        production = self._named("aws_core__aws_vpc", "Production")
        for node in (vpc, subnet, instance):
            dims = node["entity"]["dimensions"]
            assert dims["dcom"] == "design" and dims["overview"] == "shown" and dims["tap.cloud"] == "aws"
            assert dims["aws_account"] == production["entity"]["dimensions"]["aws_account"] == "100000000001"
            assert dims["aws_region"] == production["entity"]["dimensions"]["aws_region"]
        assert vpc["entity"]["dimensions"]["place"] == "bottom-center" and "place" not in production["entity"]["dimensions"]
        assert subnet["node"]["tags"] == {"tier": "public", "layout:order": "0"}
        assert instance["entity"]["dimensions"]["inventory"] == "cloud"
        assert vpc["node"]["vpc_id"] != production["node"]["vpc_id"] and instance["node"]["instance_id"]

    def test_only_official_edges_join_them_and_the_account_owns_the_vpc(self) -> None:
        edges = [e["edge"] for b in json.loads(MOCK.read_text(encoding="utf-8"))["batches"] for e in b["edges"]]
        names = {n["entity"]["entity_id"]: n["entity"]["name"] for n in _nodes()}
        types = {n["entity"]["entity_id"]: n["entity"]["entity_type"] for n in _nodes()}
        mine = {n["entity"]["entity_id"] for n in _nodes() if n["entity"]["name"] in {"Admin Access", "teleport", "public"}
                and types[n["entity"]["entity_id"]] in {"aws_core__aws_vpc", "aws_core__aws_ec2_instance"}
                or (n["entity"]["name"] == "public" and types[n["entity"]["entity_id"]] == "aws_core__aws_subnet"
                    and n["node"]["subnet_id"] == "subnet-mockteleportpublic")}
        joined = sorted((e["edge_type"], types[e["from_entity_id"]].split("__")[1], names[e["from_entity_id"]], names[e["to_entity_id"]])
                        for e in edges if e["from_entity_id"] in mine or e["to_entity_id"] in mine)
        assert joined == [
            ("BELONGS_TO_ACCOUNT__aws_core", "aws_vpc", "Admin Access", "git-serious"),
            ("PARTITIONED_INTO_SUBNET__aws_core", "aws_vpc", "Admin Access", "public"),
            ("RESIDES_IN_SUBNET__aws_core", "aws_ec2_instance", "teleport", "public"),
        ]
        assert not any(t.startswith("teleport__") for t in types.values())

    def test_the_remote_access_placeholder_account_is_not_the_teleport(self) -> None:
        (account,) = [n for n in _by_type("aws_core__aws_account") if n["entity"]["name"] == "remote-access"]
        assert "overview" not in account["entity"]["dimensions"]

    def test_the_layout_reads_the_slot_from_data_and_draws_the_chain_by_hand(self) -> None:
        source = _js()
        assert 'const PLACE_KEY = "place";' in source and 'const PLACE_BOTTOM_CENTER = "bottom-center";' in source
        assert "ec2" in _list("SOLO_TYPES"), "the instance is a solo icon"
        body = source.split("function _slottedVpcs")[1].split("\n}\n")[0]
        assert "PLACE_KEY" in body and "E.partitioned" in body and "E.residesInSubnet" in body
        assert 'data("label")' not in body and not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}", body)
        assert "slotted.nodes.addClass(ELEVATION_HIDDEN_CLASS);" in source and "slotted.edges.addClass(HIDDEN_CONTAINMENT_CLASS);" in source
        assert "_placeSlotted(cy, account, slotted, slotSize, pile, pad);" in source
        assert "Playground exception 30 (should become a `slot: bottom-center`" in source

    def test_the_row_is_as_tall_as_the_taller_of_the_pile_and_the_vpc_and_the_vpc_is_centred(self) -> None:
        source = _js()
        assert "Math.max(top + h + spread + DEPLOY_BOX_PADDING + nameRoom, above + 44 + slotHeight) + pad.bottom" in source, "the row is as tall as the taller of the pile (with the room for its front name) and the VPC"
        body = source.split("function _placeSlotted")[1].split("\n}\n")[0]
        assert 'const x = account.position("x");' in body and "pile.rowTop" in body


class TestOverviewZoomPolish:
    """`req-rampart-20x-playground-govcloud-layout-19`: Overview zoom polish."""

    def test_each_new_exception_names_its_runtime_form(self) -> None:
        source = _js()
        for n in range(19, 38):
            start = source.index(f" *  {n}. ")
            end = source.index(f"\n *  {n + 1}. ", start) if n < 37 else source.index("\n * None changes", start)
            assert "should become" in source[start:end], n

    def test_the_text_base_is_doubled_once(self) -> None:
        source = _js()
        assert "const FONT_SCALE = 2;" in source and "const BASE_FONT = 11;" in source
        assert 'n.scratch("landingFontBase")' in source, "the base is kept, so a second layout run never doubles again"
        assert "const FLOW_ARROW_SCALE = 1;" in source, "half the 2 it was"

    def test_the_subnet_labels_are_inside_top_centre(self) -> None:
        source = _js()
        assert 'n.data("label_position", "inside")' in source and 'anchor: "top-center"' in source

    def test_the_task_label_is_centred_at_the_account_elevation(self) -> None:
        source = _js()
        body = source.split("function _placeTaskLabel")[1].split("\n}\n")[0]
        assert "revealed ? upperLeft : {mx: 0, my: 0}" in body
        assert "_placeTaskLabel(cy, now, !first);" in source

    def test_the_badges_follow_the_icon_class(self) -> None:
        source = _js()
        assert '"tapzoomsettled"' in source and "config.classes.icon" in source

    def test_the_isolated_subnets_are_the_database_tier(self) -> None:
        subnets = _by_type("aws_core__aws_subnet")
        tiers = sorted((n["node"]["tags"]["tier"], n["node"]["name"]) for n in subnets)
        assert [t for t, _ in tiers].count("database") == 2 and "isolated" not in {t for t, _ in tiers}
        assert {n for t, n in tiers if t == "database"} == {"database-a", "database-b"}

    def test_the_panel_settles_fonts_and_icons_on_their_own_exponents(self) -> None:
        pages = json.loads(PAGES.read_text(encoding="utf-8"))
        panel = next(n for b in pages["batches"] for n in b["nodes"] if n["entity"]["name"] == "Playground landing graph")
        classes = panel["node"]["config"]["zoom_settle"]["classes"]
        assert classes["font"]["exponent"] == 0.5 and classes["icon"]["exponent"] == 0.75
        assert classes["arrow"]["exponent"] == 1, "the arrowhead follows the zoom, so it is not huge at the fit zoom"


class TestArrowPeoplePolish:
    """Overview polish: the arrow follows the zoom, solo icons carry no border, a horizontal pair's names do not touch."""

    def test_solo_icons_get_an_explicit_zero_border(self) -> None:
        source = _js()
        assert "_noBorder(cy.nodes().filter((n) => n.data(\"_icon_solo\")));" in source
        body = source.split("function _noBorder")[1].split("\n}\n")[0]
        assert '"border-width": 0' in body
        assert "Playground exception 24 (should become: zoom_settle leaves a solo icon's border alone" in source
        # After every pass that makes solo icons, so none is missed.
        assert source.index("iconNodeId: \"landing-solo-flow\"") < source.index("_noBorder(cy.nodes()")

    def test_both_kinds_of_pair_have_smaller_labels(self) -> None:
        source = _js()
        factor = float(re.search(r"const PAIR_FONT_FACTOR = ([0-9.]+);", source).group(1))
        assert 0.5 <= factor < 1
        pair = source.split("function _closePairs")[1].split("\n}\n")[0]
        horizontal = pair.split("} else {")[1]
        assert pair.count("landingFontFactor") == 4 and horizontal.count("landingFontFactor") == 2
        assert 'n.scratch("landingFontFactor") || 1' in source and "base * FONT_SCALE * factor" in source


class TestOverviewTweaksTwo:
    """`req-rampart-20x-playground-govcloud-layout-24`: Overview tweaks, round two (playground exceptions 31 to 37)."""

    def test_the_delivery_line_runs_through_the_front_icon_of_the_pile(self) -> None:
        source = _js()
        assert "lineY: top + h / 2 + spread," in source
        assert "_shiftGithub(roots.filter(_onDeliveryLine));" in source
        assert re.search(r"const GITHUB_SHIFT = [1-9][0-9]*;", source)

    def test_a_name_is_hidden_by_the_label_dimension_and_the_revealed_database_shows_it_again(self) -> None:
        source = _js()
        assert 'const LABEL_KEY = "label";' in source and 'const LABEL_HIDDEN = "hidden";' in source
        assert "_hideLabels(cy);" in source and '"text-opacity": 0' in source
        reveal = source.split("if (revealed) {")[1].split("} else {")[0]
        assert 'n.removeStyle("text-opacity font-weight");' in reveal
        hidden = {n["entity"]["entity_type"].split("__")[1] for n in _nodes()
                  if n["entity"]["dimensions"].get("label") == "hidden"}
        assert hidden == {"aws_route53_zone", "aws_lambda", "aws_ec2_instance"}, "the gateway, the load balancer and the database show their names"
        names = {n["entity"]["entity_type"].split("__")[1]: n["entity"]["name"] for n in _nodes()
                 if n["entity"]["entity_type"].split("__")[1] in ("aws_internet_gateway", "aws_alb", "aws_rds_instance")}
        assert names == {"aws_internet_gateway": "IGW", "aws_alb": "ALB", "aws_rds_instance": "RDS A"}
        assert "const NAMED_ICON_TYPES = [T.igw, T.alb, T.rds];" in source and "Playground exception 47" in source

    def test_the_teleport_instance_has_a_logo_card_by_dimension_and_stays_an_ec2(self) -> None:
        source = _js()
        teleport = [n for n in _by_type("aws_core__aws_ec2_instance") if n["entity"]["name"] == "teleport"]
        assert len(teleport) == 1
        assert teleport[0]["entity"]["dimensions"]["icon"] == "teleport/icons/teleport-cluster.svg"
        assert not [n for n in _nodes() if n["entity"]["entity_type"].startswith("teleport__")]
        assert "const logos = _logoNodes(shown(SOLO_TYPES));" in source
        assert "shown(ICON_TYPES).union(logos)" not in source and "shown(SOLO_TYPES).not(deploy).not(logos)" in source
        assert teleport[0]["entity"]["dimensions"]["label"] == "hidden"
        assert "members: logos, width: SOLO.width * DEPLOY_SCALE, height: SOLO.height * DEPLOY_SCALE" in source, "exception 44: the logo card is a delivery icon's size"
        assert "const ICON_PATH = " in source, "only the grid's icons/<key>.svg convention is accepted"

    def test_the_subnet_names_are_small_and_not_bold(self) -> None:
        source = _js()
        assert 'const SUBNET_LABEL_WEIGHT = "normal";' in source
        factor = float(re.search(r"const SUBNET_LABEL_FACTOR = ([0-9.]+);", source).group(1))
        assert 0.4 <= factor < 1
        assert 'n.scratch("landingFontFactor", SUBNET_LABEL_FACTOR);' in source

    def test_a_flow_name_has_no_fill(self) -> None:
        body = _js().split("function _styleFlow(")[1].split("\n}\n")[0]
        assert '"text-background-opacity": 0' in body and "text-background-color" not in body

    def test_the_scope_title_follows_the_font_class(self) -> None:
        source = _js()
        assert "function _syncScopeTitle" in source and "config.classes.font" in source

    def test_the_database_program_is_moved_to_the_line_of_sight(self) -> None:
        source = _js()
        assert "_alignDatabaseProgram(cy, anchor);" in source
        body = source.split("function _alignDatabaseProgram")[1].split("\n}\n")[0]
        assert "anchor.position(\"y\")" in body

    def test_the_new_requirement_is_in_the_landing_spec(self) -> None:
        text = (SPECS / "spec-rampart_20x_playground-govcloud-landing.md").read_text(encoding="utf-8")
        assert "req-rampart-20x-playground-govcloud-layout-24" in text


class TestOverviewNitsThree:
    """`req-rampart-20x-playground-govcloud-layout-25`: Overview nits, round three (playground exceptions 38 to 43)."""

    def _all_flows(self) -> list[dict]:
        return [n for n in _batch_nodes(APPLICATION_FLOW) if n["entity"]["entity_type"] == "computing_core__application_flow"]

    def test_the_names_lost_their_a_and_the_flows_lost_traffic(self) -> None:
        names = {n["entity"]["name"] for n in _nodes()}
        assert {"customer", "customer computer", "developer", "developer laptop", "administrator", "administrator workstation"} <= names
        assert not {n for n in names if re.fullmatch(r"(customer|developer|administrator) a( .*)?", n)}
        assert not [n for n in self._all_flows() if "traffic" in n["entity"]["name"]]
        for node in _nodes():
            assert node["entity"]["name"] == node["node"].get("name", node["entity"]["name"])

    def test_renamed_people_keep_their_identity_columns(self) -> None:
        people = {n["entity"]["name"]: n for n in _by_type("identity_core__human")}
        assert people["customer"]["node"]["handle"] == "customer-a" and people["developer"]["node"]["handle"] == "developer-a"
        assert people["administrator"]["node"]["handle"] == "admin-a"
        computers = {n["entity"]["name"]: n["node"]["stable_id"] for n in _by_type("computing_core__host")}
        assert computers["customer computer"] == "customer-a-computer" and computers["administrator workstation"] == "admin-a-computer"

    def test_the_old_administration_flow_is_retired_and_a_new_one_ends_on_the_teleport_instance(self) -> None:
        admin = [n for n in self._all_flows() if n["entity"]["name"] == "administration"]
        assert len(admin) == 2
        (old,) = [n for n in admin if "overview" not in n["entity"]["dimensions"]]
        (new,) = [n for n in admin if n["entity"]["dimensions"].get("overview") == "shown"]
        assert old["entity"]["entity_id"] == "01a15a28-7763-727d-9425-a57a6568592e", "the old flow keeps its id and its edges"
        assert new["entity"]["entity_id"] != old["entity"]["entity_id"]
        assert new["entity"]["dimensions"]["dataclass.infra"] == "admin"
        assert not [k for k in old["entity"]["dimensions"] if k.startswith("dataclass.")], "one admin flow counts on the Data Classification page"
        (teleport,) = [n for n in _by_type("aws_core__aws_ec2_instance") if n["entity"]["name"] == "teleport"]
        ends = {e["edge_type"]: e for e in _batch_edges(APPLICATION_FLOW)
                if new["entity"]["entity_id"] in (e["from_entity_id"], e["to_entity_id"])}
        assert ends["APPLICATION_FLOW_DESTINATION__computing_core"]["to_entity_id"] == teleport["entity"]["entity_id"]
        assert _name(ends["APPLICATION_FLOW_SOURCE__computing_core"]["from_entity_id"]) == "administrator workstation"
        old_dest = [e for e in _batch_edges(APPLICATION_FLOW) if e["from_entity_id"] == old["entity"]["entity_id"]
                    and e["edge_type"] == "APPLICATION_FLOW_DESTINATION__computing_core"]
        assert [_name(e["to_entity_id"]) for e in old_dest] == ["Authorization Boundary"], "endpoints are immutable on upsert"

    def test_icon_angle_is_a_dimension_in_degrees_and_replaces_the_reversed_arrow(self) -> None:
        angles = {n["entity"]["name"]: n["entity"]["dimensions"].get("icon_angle") for n in self._all_flows()
                  if n["entity"]["dimensions"].get("overview") == "shown"}
        assert angles == {"customer data": "90", "database": "90", "administration": "0",
                          "code": "270", "source pull": "270"}
        assert not [n for n in self._all_flows() if "arrow" in n["entity"]["dimensions"]]
        source = _js()
        assert 'const ICON_ANGLE_KEY = "icon_angle";' in source and "const FLOW_ICON_ANGLE = 90;" in source
        assert "ARROW_REVERSED" not in source and "function _flowAngle" in source and "function _rotateFlowIcons" in source
        assert "_destinationAhead" not in source and "Playground exception 38" in source
        edges = source.split("function _styleFlowEdges")[1].split("\n}\n")[0]
        assert 'const head = type === E.flowDestination;' in edges and '"source-arrow-shape": "none"' in edges, "the arrowhead is always on the destination end"

    def test_the_convention_is_in_the_spec_and_the_readme(self) -> None:
        for path in (SPECS / "spec-rampart_20x_playground-govcloud-landing.md", PACKAGE_ROOT.parents[1] / "README.md"):
            text = path.read_text(encoding="utf-8")
            assert "icon_angle" in text and "0 = north" in text and "270 = west" in text, path.name

    def test_the_new_exceptions_are_marked_with_their_runtime_form(self) -> None:
        header = _js().split("None changes the Python, the vocabulary or the data rules.")[0]
        for number in range(38, 44):
            entry = header.split(f" *  {number}. ")[1].split("\n *  4")[0].split("\n * None")[0]
            assert "should become" in entry or "same exit" in entry, number
    def test_the_labels_are_smaller_inside_and_centred(self) -> None:
        source = _js()
        assert re.search(r"const FLOW_FONT_FACTOR = 0\.[0-9]+;", source) and re.search(r"const DB_TITLE_FACTOR = 0\.[0-9]+;", source)
        body = source.split("function _labelProgramsInside")[1].split("\n}\n")[0]
        assert '"text-valign": "center"' in body and "n.width() * PROGRAM_LABEL_FIT" in body
        assert 'anchor: "top-center", inset: 16,\n        parentFontSize: chrome.parentFontSize * FONT_SCALE * DB_TITLE_FACTOR' in source
        pair = source.split("function _closePairs")[1].split("\n}\n")[0]
        assert pair.count("PAIR_FONT_FACTOR") == 4, "both pairs' names are the same small size"

    def test_the_gateway_is_the_load_balancers_card_drawn_solo_above_the_flow_line(self) -> None:
        (igw,) = _by_type("aws_core__aws_internet_gateway")
        dims = igw["entity"]["dimensions"]
        assert dims["icon"] == "rampart_20x_playground/icons/internet-gateway-card.svg" and dims["icon_form"] == "solo"
        svg = (PACKAGE_ROOT / "static" / "rampart_20x_playground" / "icons" / "internet-gateway-card.svg").read_text(encoding="utf-8")
        assert 'fill="#7B5EA7"' in svg and 'fill="#FFFFFF"' in svg, "the ALB's purple card and a white glyph"
        source = _js()
        assert "!== ICON_FORM_SOLO" in source and "Playground exception 42" in source
        assert "n.style({\"z-index\": edgeZ + 1" in source, "every leaf node, the gateway included, is above the edge layer"

    def test_the_gateway_card_is_a_circle_only(self) -> None:
        svg = (PACKAGE_ROOT / "static" / "rampart_20x_playground" / "icons" / "internet-gateway-card.svg").read_text(encoding="utf-8")
        assert "<circle" in svg and "<rect" not in svg, "nothing square around the circle"

    def test_overview_nits_four(self) -> None:
        source = _js()
        assert "Playground exception 45" in source
        assert float(re.search(r"const VPC_TITLE_FACTOR = ([0-9.]+);", source).group(1)) > float(re.search(r"const SUBNET_LABEL_FACTOR = ([0-9.]+);", source).group(1))
        assert float(re.search(r"const VPC_TITLE_FACTOR = ([0-9.]+);", source).group(1)) < 1
        assert "_labelHidden(ordered[ordered.length - 1]) ? PILE_NAMELESS_ROOM : PILE_NAME_ROOM" in source
        assert 'el.style.background = "transparent"' in source
        assert '"text-wrap": "none",\n    }));\n    _styleFlowEdges' in source, "a flow's name is one line"

    def test_overview_nits_five(self) -> None:
        source = _js()
        assert "Playground exception 46" in source
        assert 'iconNodeId: "landing-solo-zone"' in source and "members: zones, width: SOLO.width * DEPLOY_SCALE" in source
        assert "BASE_FONT * FONT_SCALE * factor * VPC_TITLE_FACTOR" in source, "the scope title is the VPC title's size"
        assert 'shown([T.boundary]).forEach((n) => n.scratch("landingFontFactor", VPC_TITLE_FACTOR))' in source
        assert "_colourTitles(cy, parents.filter" in source and "TITLE_DARKEN" in source

    def test_the_admin_access_vpc_is_snug(self) -> None:
        source = _js()
        assert re.search(r"const SLOT_PADDING = ([0-9]+);", source) and int(re.search(r"const SLOT_PADDING = ([0-9]+);", source).group(1)) <= 16
        assert "const height = SLOT_TOP + subnetBoxes" in source

    def test_the_admin_access_boxes_shrink_to_the_small_nameless_logo_card(self) -> None:
        source = _js()
        assert "Playground exception 44" in source and "SLOT_SUBNET_WIDTH" in source and "SLOT_NAMELESS_BOTTOM" in source
        assert "held.every(_labelHidden)" in source, "the room for a name is dropped only when every resident's name is hidden"
        assert int(re.search(r"const SLOT_SUBNET_WIDTH = ([0-9]+);", source).group(1)) < 230, "narrower than a standard subnet"


class TestContainerInterior:
    """`req-rampart-20x-playground-govcloud-layout-30`: overview nits, round six (the container's interior)."""

    def test_the_container_is_tap_web_and_the_program_keeps_its_name(self) -> None:
        names = {n["entity"]["entity_id"]: n["entity"]["name"] for n in _batch_nodes(APPLICATION_FLOW)}
        assert names["01a1c4c8-3a0c-7582-b96a-f3a59a68c81a"] == "tap-web"
        (container,) = [n for n in _batch_nodes(APPLICATION_FLOW) if n["entity"]["entity_id"] == "01a1c4c8-3a0c-7582-b96a-f3a59a68c81a"]
        assert container["node"]["name"] == "tap-web"

    def test_what_the_interior_draws_is_shown_and_placed_by_data(self) -> None:
        shown: dict[str, list[dict]] = {}
        for node in _batch_nodes(SOFTWARE):
            if node["entity"]["dimensions"].get("overview") == "shown":
                shown.setdefault(node["entity"]["entity_type"], []).append(node["entity"])
        assert sorted(e["name"] for e in shown["computing_core__library"]) == ["cryptography", "openssl-fips-provider"]
        assert len(shown["computing_core__package"]) == 180
        assert [e["name"] for e in shown["computing_core__operating_system"]] == ["Wolfi"]
        assert [e["name"] for e in shown["computing_core__host"]] == ["git-serious web image"]
        for kind in ("computing_core__library", "computing_core__package", "computing_core__operating_system"):
            assert all("column" in e["dimensions"] and "row" in e["dimensions"] for e in shown[kind])

    def test_four_searches_bring_the_official_edges_and_the_panel_uses_them(self) -> None:
        pages = json.loads(PAGES.read_text(encoding="utf-8"))["batches"][0]
        ids = {n["entity"]["name"]: n["entity"]["entity_id"] for n in pages["nodes"] if n["entity"]["entity_type"] == "search"}
        queries = {n["entity"]["name"]: " ".join(n["node"]["definition"]["query"]) for n in pages["nodes"]
                   if n["entity"]["entity_type"] == "search" and n["node"]["search_type"] == "gryphon"}
        used = {e["edge"]["to_entity_id"] for e in pages["edges"] if e["edge"]["edge_type"] == "USES_SEARCH"}
        for slug, edge in (("image", "RUNS_IMAGE__computing_core"), ("os", "RUNS_OPERATING_SYSTEM__computing_core"),
                           ("packages", "INSTALLS_PACKAGE__computing_core"), ("loads-library", "LOADS_LIBRARY__computing_core")):
            name = f"playground \u2014 landing {slug}"
            assert edge in queries[name] and 'a.dimensions["overview"] = "shown"' in queries[name]
            assert ids[name] in used
        (projection,) = [n for n in pages["nodes"] if n["entity"]["entity_type"] == "projection"]
        excluded = projection["node"]["definition"]["node_style"]["exclude_types"]
        assert {"computing_core__library", "computing_core__package"} <= set(excluded)

    def test_the_os_runs_the_two_programs_by_official_edges(self) -> None:
        os_id = "01a13c38-4f5e-735c-9cf2-1f1434dc5163"
        edges = json.loads(APPLICATION_FLOW.read_text(encoding="utf-8"))["batches"][0]["edges"]
        held = {e["edge"]["to_entity_id"] for e in edges
                if e["edge"]["edge_type"] == "RUNS_PROGRAM__computing_core" and e["edge"]["from_entity_id"] == os_id}
        assert held == {"01a13be3-0373-79d4-9ae8-be13c2e3bfd5", "01a13be3-0373-7afc-8d07-441072bee2eb"}
        source = _js()
        assert "OS_RUNS_PROGRAM" not in source and "osRunsProgram" not in source
        assert "(parent:${T.os})-[:${E.runsProgram}]->(child:${T.program})" in source

    def test_the_interior_is_derived_from_official_edges_and_marked_exceptions(self) -> None:
        source = _js()
        assert "Playground exception 48" in source and "Playground exception 49" in source
        for edge in ("runsImage", "runsOs", "installsPackage", "loadsLibrary"):
            assert re.search(rf"\b{edge}: \"[A-Z_]+__computing_core\"", source)
        assert "applyStack" in source and "INTERIOR_PILES" in source
        text = (SPECS / "spec-rampart_20x_playground-govcloud-landing.md").read_text(encoding="utf-8")
        assert "req-rampart-20x-playground-govcloud-layout-30" in text and "closed by `req-rampart-20x-playground-govcloud-layout-31`" in text


class TestContainerKeyPile:
    """`req-rampart-20x-playground-govcloud-layout-31`: the revealed container holds a pile of keys (USES_KEY)."""

    GUNICORN = "01a13be3-0373-79d4-9ae8-be13c2e3bfd5"
    KEYS = {
        "01a13be3-0373-781b-a533-104d8726769b": "computing_core__private_key",
        "01a13be3-0373-7aa9-bbc4-d43332f2fd5b": "computing_core__public_key",
        "01a13be3-0373-7940-9fa5-a9ce49eccd49": "computing_core__file",
    }

    def test_gunicorn_uses_the_three_keys_by_official_edges_program_to_key(self) -> None:
        edges = [e for e in _batch_edges(APPLICATION_FLOW) if e["edge_type"] == "USES_KEY__computing_core"]
        assert {e["from_entity_id"] for e in edges} == {self.GUNICORN}
        assert {e["to_entity_id"] for e in edges} == set(self.KEYS)
        assert len(edges) == 3

    def test_the_keys_are_shown_and_the_search_brings_the_edges(self) -> None:
        entities = json.loads((PACKAGE_ROOT / "grift" / "inventory-entities.grift.json").read_text(encoding="utf-8"))["batches"][0]["nodes"]
        for node in entities:
            if node["entity"]["entity_id"] in self.KEYS:
                assert node["entity"]["entity_type"] == self.KEYS[node["entity"]["entity_id"]]
                assert node["entity"]["dimensions"]["overview"] == "shown"
        pages = json.loads(PAGES.read_text(encoding="utf-8"))["batches"][0]
        (search,) = [n for n in pages["nodes"] if n["entity"]["name"] == "playground \u2014 landing uses-key"]
        assert "USES_KEY__computing_core" in " ".join(search["node"]["definition"]["query"])
        used = {e["edge"]["to_entity_id"] for e in pages["edges"] if e["edge"]["edge_type"] == "USES_SEARCH"}
        assert search["entity"]["entity_id"] in used

    def test_the_pile_is_marked_exception_fifty_and_derived_not_written(self) -> None:
        source = _js()
        assert "Playground exception 50" in source or " 50. " in source
        assert re.search(r"\busesKey: \"USES_KEY__computing_core\"", source)
        assert '[E.containsKey]: "Keys"' in source
        text = (SPECS / "spec-rampart_20x_playground-govcloud-landing.md").read_text(encoding="utf-8")
        assert "req-rampart-20x-playground-govcloud-layout-31" in text and "exception 50" in text


class TestOsPythonPackagePile:
    """`req-rampart-20x-playground-govcloud-layout-36`: the Wolfi box holds a pile of Python packages (RUNS_PACKAGE, then REQUIRES_PACKAGE)."""

    TAP_WEB = {"01a13be3-0373-7afc-8d07-441072bee2eb", "01a1c453-b1c0-7baf-989a-834ff276c1b9"}
    GUNICORN = {"01a13be3-0373-79d4-9ae8-be13c2e3bfd5", "01a1c4a3-6f98-70b4-a09e-8a22c87e25ca"}

    @staticmethod
    def _ref_name(ref: str) -> tuple[str, str, str]:
        kind, payload = ref.split("\x1f", 1)
        body = json.loads(payload)
        return kind, body["ecosystem"], body["name"]

    def _runs_package(self) -> list[dict]:
        return [e for e in _batch_edges(SOFTWARE) if e["edge_type"] == "RUNS_PACKAGE__computing_core"]

    def test_each_program_runs_its_root_package_by_an_official_edge_to_a_package_not_a_source_package(self) -> None:
        edges = self._runs_package()
        assert len(edges) == 4
        by_program = {e["from_entity_id"]: self._ref_name(e["to_ref"]) for e in edges}
        assert {p for p, t in by_program.items() if t == ("computing_core__package", "pypi", "tap")} == self.TAP_WEB
        assert {p for p, t in by_program.items() if t == ("computing_core__package", "pypi", "gunicorn")} == self.GUNICORN
        assert all("source_package" not in e["to_ref"] for e in edges)

    def test_the_roots_exist_as_seeded_packages_and_no_closure_member_is_written_as_a_root(self) -> None:
        refs = {n["entity"].get("ref") for b in json.loads(SOFTWARE.read_text(encoding="utf-8"))["batches"] for n in b["nodes"]}
        for e in self._runs_package():
            assert e["to_ref"] in refs
        # A root is not a closure (`req-computing-core-program-package-3`): only the two roots are drawn to, the rest is walked.
        assert {self._ref_name(e["to_ref"])[2] for e in self._runs_package()} == {"tap", "gunicorn"}

    def test_the_closure_over_requires_package_is_44_packages_and_all_of_them_are_shown(self) -> None:
        batch = json.loads(SOFTWARE.read_text(encoding="utf-8"))["batches"][0]
        shown = {n["entity"]["ref"] for n in batch["nodes"]
                 if "ref" in n["entity"] and n["entity"].get("dimensions", {}).get("overview") == "shown"}
        requires: dict[str, list[str]] = {}
        for e in batch["edges"]:
            if e["edge"]["edge_type"] == "REQUIRES_PACKAGE__computing_core":
                requires.setdefault(e["edge"]["from_ref"], []).append(e["edge"]["to_ref"])
        roots = {e["to_ref"] for e in self._runs_package()}
        seen = set(roots)
        frontier = set(roots)
        while frontier:
            frontier = {t for f in frontier for t in requires.get(f, [])} - seen
            seen |= frontier
        assert len(seen) == 44
        assert seen <= shown
        assert {self._ref_name(r)[1] for r in seen} == {"pypi"}

    def test_the_searches_bring_both_edges_and_the_panel_uses_them(self) -> None:
        pages = json.loads(PAGES.read_text(encoding="utf-8"))["batches"][0]
        queries = {n["entity"]["entity_id"]: " ".join(n["node"]["definition"]["query"]) for n in pages["nodes"]
                   if n["entity"]["entity_type"] == "search" and "query" in n["node"].get("definition", {})}
        wanted = {name: i for i, q in queries.items() for name in ("RUNS_PACKAGE__computing_core", "REQUIRES_PACKAGE__computing_core") if name in q}
        assert set(wanted) == {"RUNS_PACKAGE__computing_core", "REQUIRES_PACKAGE__computing_core"}
        used = {e["edge"]["to_entity_id"] for e in pages["edges"] if e["edge"]["edge_type"] == "USES_SEARCH"}
        assert set(wanted.values()) <= used

    def test_the_pile_is_marked_exception_55_derived_and_not_double_counted(self) -> None:
        source = _js()
        assert " 55. " in source
        assert re.search(r"\brunsPackage: \"RUNS_PACKAGE__computing_core\"", source)
        assert re.search(r"\brequiresPackage: \"REQUIRES_PACKAGE__computing_core\"", source)
        assert '[E.containsPythonPackage]: "Python Packages"' in source
        assert 'containsPythonPackage: "CONTAINS_PYTHON_PACKAGE__playground"' in source
        # The closure is walked, the OS Packages pile leaves out what the Python Packages pile holds, the requirement edges are not drawn.
        assert "closure(roots, E.requiresPackage)" in source
        assert ".filter((pkg) => !python.has(pkg))" in source
        assert "_edgeType(e) === E.requiresPackage).addClass(HIDDEN_CONTAINMENT_CLASS)" in source
        text = (SPECS / "spec-rampart_20x_playground-govcloud-landing.md").read_text(encoding="utf-8")
        assert "req-rampart-20x-playground-govcloud-layout-36" in text and "exception 55" in text


class TestOverviewNotificationCards:
    """`req-rampart-20x-playground-govcloud-layout-37`: a row of notification cards above the graph; the first is the CISA KEV card."""

    VULNERABILITIES = PACKAGE_ROOT / "grift" / "vulnerabilities-page.grift.json"
    OVERVIEW = "01a13b2c-82d6-73d2-baa8-17415ac66a72"
    KEV_SEARCH = "01a13fc0-0c16-71d6-a543-32e09f5b48b8"

    def _vuln(self) -> dict:
        return json.loads(self.VULNERABILITIES.read_text(encoding="utf-8"))["batches"][0]

    @staticmethod
    def _pages() -> dict:
        return json.loads(PAGES.read_text(encoding="utf-8"))["batches"][0]

    @staticmethod
    def _panel(batch: dict, slug: str) -> dict:
        (panel,) = [n for n in batch["nodes"] if n["entity"]["entity_type"] == "panel" and n["node"]["slug"] == slug]
        return panel

    def test_the_card_is_the_vulnerabilities_kev_card_with_a_new_title_and_the_inline_layout(self) -> None:
        original = self._panel(self._vuln(), "playground-vulnerabilities-kev")["node"]["config"]
        card = self._panel(self._pages(), "playground-overview-kev")["node"]["config"]
        assert card["title"] == "CISA Known Exploited List"
        assert card["layout"] == "figure_right"
        # Everything else is the card of the Vulnerabilities page.
        assert {k: v for k, v in card.items() if k not in ("title", "layout")} == {k: v for k, v in original.items() if k != "title"}

    def test_it_reads_the_same_search_and_the_overview_uses_it(self) -> None:
        pages = self._pages()
        panel_id = self._panel(pages, "playground-overview-kev")["entity"]["entity_id"]
        searches = {e["edge"]["to_entity_id"] for e in pages["edges"]
                    if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel_id}
        assert searches == {self.KEV_SEARCH}
        original = self._panel(self._vuln(), "playground-vulnerabilities-kev")["entity"]["entity_id"]
        assert {e["edge"]["to_entity_id"] for e in self._vuln()["edges"]
                if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == original} == {self.KEV_SEARCH}
        assert any(n["entity"]["entity_id"] == self.KEV_SEARCH for n in self._vuln()["nodes"])
        uses = [e["edge"] for e in pages["edges"] if e["edge"]["edge_type"] == "USES_PANEL" and e["edge"]["to_entity_id"] == panel_id]
        assert [(e["from_entity_id"], e["properties"]["hotlink"]["value"]) for e in uses] == [(self.OVERVIEW, "playground-overview-kev")]

    def test_the_overview_is_two_bands_the_cards_then_the_graph(self) -> None:
        pages = json.loads(PAGES.read_text(encoding="utf-8"))["batches"][0]
        (page,) = [n for n in pages["nodes"] if n["entity"]["entity_id"] == self.OVERVIEW]
        columns = page["node"]["layout"]["columns"]
        bands = {}
        for col in columns.values():
            bands.setdefault(col["band"], []).extend(row["panel-id"] for row in col["rows"].values())
        assert bands == {1: ["playground-overview-kev"], 2: ["landing"]}
        (graph,) = [c for c in columns.values() if c["band"] == 2]
        assert graph["rows"]["row-1"]["height"] == "80vh"

    def test_the_pages_bundle_is_imported_after_the_bundle_that_holds_the_cards_search(self) -> None:
        manifest = (PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8")
        assert manifest.index("vulnerabilities_page = ") < manifest.index("\npages = ")


class TestOverviewNitsSeven:
    """`req-rampart-20x-playground-govcloud-layout-32` to `-35`: overview nits, round seven. Source pins; what rendered is stated in the pull request."""

    def test_the_piles_are_held_by_the_os_and_the_derived_edge_runs_from_it(self) -> None:
        source = _js()
        assert "(parent:${T.os})-[:${E.containsLibrary}]->(child:${T.lib})" in source
        assert "(parent:${T.os})-[:${E.containsPackage}]->(child:${T.pkg})" in source
        assert "(parent:${T.os})-[:${E.containsKey}]->(child)" in source
        assert "(parent:${T.os})-[:${E.containsPythonPackage}]->(child:${T.pkg})" in source
        assert "add(systems[0], lib, E.containsLibrary)" in source and "add(container.id(), lib" not in source
        assert "(parent:${T.ecsContainer})-[:${E.containsLibrary}]" not in source

    def test_the_piles_stand_in_one_row_keys_libraries_packages_python_packages(self) -> None:
        source = _js()
        assert "const PILE_ORDER = [E.containsKey, E.containsPythonPackage, E.containsLibrary, E.containsPackage];" in source
        body = source.split("function _placeInterior")[1].split("\n}\n")[0]
        # One y for the whole row: the row is horizontal.
        assert "const y = " in body and "y});" in body.split("piles.forEach")[1]
        assert "_alignKeyPiles" not in source

    def test_the_application_program_is_a_large_square_named_top_centre_and_found_by_an_edge(self) -> None:
        source = _js()
        assert "const PROGRAM_LARGE = {width: 280, height: 140};" in source
        assert "const PROGRAM_TALL = 1.5;" in source
        body = source.split("function _interiorHand")[1].split("\n}\n")[0]
        # The program another program runs (RUNS_PROGRAM from a program): an edge, never a name or an id.
        assert "E.runsProgram" in body and "T.program" in body and "gunicorn" not in body and "tap-web" not in body
        label = source.split("function _labelProgramsInside")[1].split("\n}\n")[0]
        assert 'n.scratch("landingLarge")' in label and "PROGRAM_TITLE_INSET" in label

    def test_the_os_box_is_sized_by_a_floor_and_the_container_fills_the_task_about_the_line_of_sight(self) -> None:
        source = _js()
        assert "baseSizes[T.os] = {width: osFloor.width, height: osFloor.height};" in source
        assert "const containerPad = " in source and "[T.ecsContainer]: containerPad" in source
        assert "hand.nodes.addClass(ELEVATION_HIDDEN_CLASS);" in source and "_placeInterior(cy, hand.entries, interiorPad);" in source
        # Nothing is left to move: the task's top room is only its label's (exception 17 kept the constant).
        assert "const TASK_TOP_ROOM = 0;" in source

    def test_the_flow_colour_is_from_the_stamp_not_from_the_flow(self) -> None:
        source = _js()
        table = re.search(r"const FLOW_COLOURS = \{(.*?)\n\};", source, re.S).group(1)
        assert '"dataclass.customer"' in table and '"dataclass.infra"' in table
        for value in ("data", "sanitized", "creds", "logs", "admin", "code", "secrets"):
            assert re.search(rf"\b{value}: \"#[0-9A-Fa-f]{{6}}\"", table), value
        colours = re.findall(r"#[0-9A-Fa-f]{6}", table)
        assert len(colours) == len(set(c.lower() for c in colours)), "every class has its own colour"
        assert "#0B3D91" in table, "customer data keeps the current blue"
        flow = source.split("function _flowColour")[1].split("\n}\n")[0]
        assert 'flow.data("dimensions")' in flow and "FLOW_COLOURS" in flow and "label" not in flow and "entity_id" not in flow
        # The line, the arrowhead, the glyph and the name all read it.
        edges = source.split("function _styleFlowEdges")[1].split("\n}\n")[0]
        assert "_flowColour(" in edges and '"line-color": colour' in edges and '"target-arrow-color": colour' in edges
        assert '"color": _flowColour(flow)' in source
        assert "_flowColour(flow)" in source.split("async function _rotateFlowIcons")[1]

    def test_every_flow_class_in_use_has_a_colour(self) -> None:
        stamps = {(k, v) for n in _batch_nodes(APPLICATION_FLOW) if n["entity"]["entity_type"] == "computing_core__application_flow"
                  and n["entity"]["dimensions"].get("overview") == "shown"
                  for k, v in n["entity"]["dimensions"].items() if k in ("dataclass.customer", "dataclass.infra")}
        assert stamps == {("dataclass.customer", "data"), ("dataclass.customer", "sanitized"), ("dataclass.infra", "admin"),
                          ("dataclass.infra", "code")}
        table = re.search(r"const FLOW_COLOURS = \{(.*?)\n\};", _js(), re.S).group(1)
        for _key, value in stamps:
            assert re.search(rf"\b{value}: \"#", table)

    def test_a_tap_on_a_pile_lists_its_members_with_links(self) -> None:
        source = _js()
        assert "_pileOf(cy, node)" in source and "_openPileWindow(cy, node, pile)" in source
        assert 'cy.scratch("landing_piles", piles);' in source
        pile = source.split("function _openPileWindow")[1].split("\n}\n")[0]
        assert "/object/" in pile and "url_id" in pile and "pile.members" in pile and "dataset" not in pile
        of = source.split("function _pileOf")[1].split("\n}\n")[0]
        assert "_stack_front_id" in of and "_stack_id" in of and "INTERIOR_STACK_PREFIX" in of
        # The same window as the flow's: one at a time.
        assert source.count("function _showWindow") == 1 and source.count("_closeFlowWindow();\n    closeInfoWindow();") == 1

    def test_a_pile_window_scrolls_itself_and_a_pile_chip_has_no_hover_number(self) -> None:
        source = _js()
        show = source.split("function _showWindow")[1].split("\n}\n")[0]
        assert "el.style.maxHeight" in show and 'overscrollBehavior = "contain"' in show and ".tap-info-window__body" in show
        assert '["wheel", "touchstart", "touchmove", "touchend"]' in show and "e.stopPropagation()" in show
        assert "capture: true, passive: true" in show and "preventDefault" not in show
        close = source.split("function _closeFlowWindow")[1].split("\n}\n")[0]
        assert "state.unguard()" in close
        hide = source.split("function _hideStackTooltips")[1].split("\n}\n")[0]
        assert ".tap-stack-tooltip { display: none !important; }" in hide
        assert source.index("_hideStackTooltips(cy.container())") < source.index("applyStack(cy, pile);")

    def test_the_hidden_interior_leaves_no_badge_behind(self) -> None:
        source = _js()
        drop = source.split("function _dropHiddenBadges")[1].split("\n}\n")[0]
        assert "ELEVATION_HIDDEN_CLASS" in drop and 'style("display")' in drop and ".remove()" in drop
        refresh = source.split("function _refreshBadges")[1].split("\n}\n")[0]
        assert refresh.index("applyBadgeNodes(") < refresh.index("_dropHiddenBadges(cy);")

    def test_the_new_exceptions_are_numbered_after_fifty_and_name_their_runtime_form(self) -> None:
        source = _js()
        for n in range(51, 55):
            start = source.index(f" *  {n}. ")
            end = source.index(f"\n *  {n + 1}. ", start) if n < 54 else source.index("\n * None changes", start)
            assert "should become" in source[start:end], n
        assert "Playground exception 54" in source and "Playground exception 53" in source and "Playground exception 52" in source

    def test_the_spec_rows_record_the_four_changes_and_the_palette(self) -> None:
        text = (SPECS / "spec-rampart_20x_playground-govcloud-landing.md").read_text(encoding="utf-8")
        for n in (32, 33, 34, 35):
            assert f"| req-rampart-20x-playground-govcloud-layout-{n} |" in text
        for exception in ("exception 51", "exception 52", "exception 53", "exception 54"):
            assert exception in text
        table = re.search(r"const FLOW_COLOURS = \{(.*?)\n\};", _js(), re.S).group(1)
        for colour in re.findall(r"#[0-9A-Fa-f]{6}", table):
            assert colour in text, colour


class TestOverviewVulnerabilityDistribution:
    """Exceptions 56 to 58 (the pile order, the bubbles on what carries the vulnerabilities, their size). These tests pin source strings."""

    def test_the_piles_are_ordered_and_the_os_packages_pile_is_renamed(self) -> None:
        source = _js()
        assert '[E.containsPackage]: "OS Packages"' in source and '"Packages"' not in source.replace('"OS Packages"', "").replace('"Python Packages"', "")
        # The programs' row starts at the box's left inner edge, above the first pile.
        placed = source.split("function _placeInterior")[1].split("\n}\n")[0]
        assert "let x = left;" in placed

    def test_the_findings_come_from_a_search_one_row_per_finding(self) -> None:
        source = _js()
        grift = json.loads((GRIFT / "pages.grift.json").read_text(encoding="utf-8"))
        searches = {n["entity"]["name"]: n for b in grift["batches"] for n in b["nodes"] if n["entity"]["entity_type"] == "search"}
        carrier = searches["playground \u2014 landing carrier-findings"]
        projection = next(n for b in grift["batches"] for n in b["nodes"] if n["entity"]["entity_type"] == "projection")
        badge_set = projection["node"]["definition"]["status_badges"]["badge_sets"][0]
        assert badge_set["population"]["interior_findings_search_id"] == carrier["entity"]["entity_id"]
        assert "interior_findings_search_id" in source and carrier["entity"]["entity_id"] not in source
        query = " ".join(carrier["node"]["definition"]["query"])
        assert "CARRIES_COMPLIANCE_FINDING__compliance_core" in query and 'f.data.status = "open"' in query
        assert "f.entity_id AS finding" in query and "MAX(v.data.cvss_score)" in query and "COUNT(" not in query

    def test_the_task_bubble_gives_way_to_the_interior_bubbles_and_returns(self) -> None:
        source = _js()
        place = source.split("function _placeInteriorBubbles")[1].split("\n}\n")[0]
        assert "pile.members.map((m) => m.id())" in place and "_findingsOf(byCarrier, ids)" in place
        assert "placed === total" in place and 'cy.scratch("landing_task_badges"' in place and ".restore()" in place
        assert "_is_interior_badge" in source.split("function _dropHiddenBadges")[1].split("\n}\n")[0]
        found = source.split("function _findingsOf")[1].split("\n}\n")[0]
        assert "new Map()" in found and "found.size" in found  # distinct findings: a finding of two members counts once

    def test_the_pile_window_has_a_vulnerabilities_column_in_the_component_pages_tones(self) -> None:
        source = _js()
        window = source.split("function _openPileWindow")[1].split("\n}\n")[0]
        assert "Vulnerabilities" in window and "tap-info-window__tone--${tone}" in window and "_findingsOf(byCarrier, [n.id()])" in window
        page = json.loads((GRIFT / "vulnerabilities-page.grift.json").read_text(encoding="utf-8"))
        text = json.dumps(page)
        assert '"steps": [{"min": 7, "tone": "bad"}, {"min": 4, "tone": "warn"}, {"min": 0.1, "tone": "good"}]' in text
        assert "const CVSS_TONE_STEPS = [{min: 7, tone: \"bad\"}, {min: 4, tone: \"warn\"}, {min: 0.1, tone: \"good\"}];" in source

    def test_the_bubbles_are_the_size_of_the_pile_chip(self) -> None:
        source = _js()
        assert "const PILE_CHIP_FONT = 14;" in source and "const PILE_CHIP_HEIGHT = 16;" in source
        sizing = source.split("function _syncBadgeSizes")[1].split("\n}\n")[0]
        assert "PILE_CHIP_HEIGHT" in sizing and "PILE_CHIP_FONT * fontFactor" in sizing and "_is_interior_badge" in sizing

    def test_the_new_exceptions_and_spec_rows_are_recorded(self) -> None:
        source = _js()
        for n in (56, 57, 58):
            start = source.index(f" *  {n}. ")
            end = source.index(f"\n *  {n + 1}. ", start) if n < 58 else source.index("\n * None changes", start)
            assert "should become" in source[start:end], n
        text = (SPECS / "spec-rampart_20x_playground-govcloud-landing.md").read_text(encoding="utf-8")
        for n, exception in ((38, "exception 56"), (39, "exception 57"), (40, "exception 58")):
            assert f"| req-rampart-20x-playground-govcloud-layout-{n} |" in text and exception in text

