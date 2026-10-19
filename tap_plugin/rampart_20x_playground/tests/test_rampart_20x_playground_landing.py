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
    """`req-rampart-20x-playground-govcloud-layout-8`: C3 (one titled row)."""

    def test_the_deploy_types_are_the_delivery_path(self) -> None:
        assert sorted(_list("DEPLOY_TYPES")) == ["bucket", "codebuild", "ecr", "lambda", "pipeline"]

    def test_a_secret_is_in_the_column_only_when_a_deploy_lambda_retrieves_it(self) -> None:
        """The data difference: the GitHub App token has a RETRIEVES_SECRET_FROM edge from the Lambda; the runtime
        secret has none (it has ENCRYPTED_WITH_KEY). The layout selects by that edge, never by name."""
        assert _list("DEPLOY_SECRET_READERS") == ["lambda"]
        assert "E.retrievesSecret" in _js()
        edges = [e["edge"] for b in json.loads(MOCK.read_text(encoding="utf-8"))["batches"] for e in b["edges"]]
        types = {n["entity"]["entity_id"]: n["entity"]["entity_type"] for n in _nodes()}
        retrieved = {e["to_entity_id"] for e in edges if e["edge_type"] == "RETRIEVES_SECRET_FROM__aws_core"
                     and types[e["from_entity_id"]] == "aws_core__aws_lambda"}
        shown_secrets = {n["entity"]["entity_id"] for n in _by_type("aws_core__aws_secrets_manager_secret")
                         if n["entity"]["dimensions"].get("overview") == "shown"}
        assert shown_secrets and shown_secrets <= retrieved, "every secret still drawn is in the row"

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

    def test_the_members_are_laid_out_by_align_distribute_with_a_label(self) -> None:
        source = _js()
        assert "alignDistributeHorizontal(cy, {...row, label: DEPLOY_LABEL" in source
        assert re.search(r'const DEPLOY_LABEL = "Continuous Delivery";', source)
        assert "anchorMode: \"center\"" in source and "x: account.position(\"x\")" in source
        assert "sort: false" in source and "gap: DEPLOY_GAP" in source

    def test_one_small_named_gap(self) -> None:
        source = _js()
        assert len(re.findall(r"const DEPLOY_GAP = \d+;", source)) == 1
        assert 20 <= int(re.search(r"const DEPLOY_GAP = (\d+);", source).group(1)) <= 40

    def test_the_old_pile_code_is_gone(self) -> None:
        assert "PILE_STEP" not in _js() and "_placeDeployPile" not in _js()

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
                "customer a", "customer a computer", "Authorization Boundary", "github.com",
                "developer a laptop", "developer a",
            }:
                columns[entity["name"]] = int(raw)
        order = ["customer a", "customer a computer", "Authorization Boundary", "github.com",
                 "developer a laptop", "developer a"]
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
        searches = {n["entity"]["name"]: " ".join(n["node"]["definition"]["query"])
                    for n in pages["nodes"] if n["entity"]["entity_type"] == "search"}
        scoped = [q for q in searches.values() if "SCOPED_TO_COMPLIANCE_BOUNDARY" in q]
        assert len(scoped) == 1 and 'b.dimensions["overview"] = "shown"' in scoped[0]
        assert "playground \u2014 landing scoped" in searches
        (panel,) = [n for n in pages["nodes"] if n["entity"]["entity_type"] == "panel"]
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
                    "govcloud-layout-14", "govcloud-layout-15", "govcloud-layout-16", "govcloud-layout-17"):
            assert f"req-rampart-20x-playground-{rid}" in text


APPLICATION_FLOW = PACKAGE_ROOT / "grift" / "application-flow.grift.json"
ENTITIES = PACKAGE_ROOT / "grift" / "inventory-entities.grift.json"
PAGES = PACKAGE_ROOT / "grift" / "pages.grift.json"


def _batch_nodes(path: Path) -> list[dict]:
    return [n for b in json.loads(path.read_text(encoding="utf-8"))["batches"] for n in b["nodes"]]


def _batch_edges(path: Path) -> list[dict]:
    return [e["edge"] for b in json.loads(path.read_text(encoding="utf-8"))["batches"] for e in b["edges"]]


def _name(entity_id: str) -> str:
    for path in (MOCK, ENTITIES, APPLICATION_FLOW):
        for node in _batch_nodes(path):
            if node["entity"]["entity_id"] == entity_id:
                return node["entity"]["name"]
    return entity_id


class TestRunningParts:
    """`req-rampart-20x-playground-govcloud-layout-13`: the containers and programs of the two web tasks (Overview Wave 3)."""

    def test_one_container_per_task_with_a_real_shaped_arn_image_and_digest(self) -> None:
        containers = [n for n in _batch_nodes(APPLICATION_FLOW) if n["entity"]["entity_type"] == "aws_core__aws_ecs_container"]
        assert sorted(n["entity"]["name"] for n in containers) == ["web task a container", "web task b container"]
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
            ("web task a", "web task a container"), ("web task b", "web task b container")]
        assert sorted(by_type["RUNS_PROGRAM__computing_core"]) == [
            ("gunicorn (web task a)", "tap-web (web task a)"), ("gunicorn (web task b)", "tap-web (web task b)"),
            ("web task a container", "gunicorn (web task a)"), ("web task b container", "gunicorn (web task b)")]
        assert sorted(by_type["RUNS_IMAGE__computing_core"]) == [
            ("web task a container", "git-serious web image"), ("web task b container", "git-serious web image")]

    def test_the_programs_are_one_set_per_container_and_postgres_stays(self) -> None:
        programs = {n["entity"]["name"]: n for n in _batch_nodes(ENTITIES) if n["entity"]["entity_type"] == "computing_core__program"}
        assert sorted(programs) == [
            "PostgreSQL database instance", "gunicorn (web task a)", "gunicorn (web task b)",
            "tap-web (web task a)", "tap-web (web task b)"]
        assert programs["tap-web (web task a)"]["node"]["program_name"] == programs["tap-web (web task b)"]["node"]["program_name"] == "tap-web"
        for node in programs.values():
            assert node["entity"]["dimensions"]["inventory"] == "applications"

    def test_only_web_task_a_s_interior_and_the_flow_are_on_the_overview(self) -> None:
        shown = {n["entity"]["name"] for n in _batch_nodes(APPLICATION_FLOW) + _batch_nodes(ENTITIES)
                 if n["entity"]["dimensions"].get("overview") == "shown"}
        assert shown == {"web task a container", "customer traffic", "gunicorn (web task a)", "tap-web (web task a)"}

    def test_the_nesting_is_three_configured_relationships_not_type_tests(self) -> None:
        source = _js()
        for name in ("task-holds-container", "container-holds-program", "program-holds-program"):
            assert f'name: "{name}"' in source
        assert "(parent:${T.task})-[:${E.runsContainer}]->(child:${T.ecsContainer})" in source
        assert "(parent:${T.program})-[:${E.runsProgram}]->(child:${T.program})" in source
        assert {"task", "ecsContainer"} <= set(_list("CONTAINERS"))

    def test_searches_bring_the_containment_edges_and_the_flow_edges(self) -> None:
        pages = json.loads(PAGES.read_text(encoding="utf-8"))["batches"][0]
        searches = {n["entity"]["name"]: " ".join(n["node"]["definition"]["query"])
                    for n in pages["nodes"] if n["entity"]["entity_type"] == "search"}
        for slug, edge in (("runs-container", "RUNS_CONTAINER__aws_core"), ("runs-program", "RUNS_PROGRAM__computing_core"),
                           ("flow-source", "APPLICATION_FLOW_SOURCE__computing_core"),
                           ("flow-destination", "APPLICATION_FLOW_DESTINATION__computing_core")):
            query = searches[f"playground \u2014 landing {slug}"]
            assert edge in query and 'a.dimensions["overview"] = "shown" AND b.dimensions["overview"] = "shown"' in query
        (panel,) = [n for n in pages["nodes"] if n["entity"]["entity_type"] == "panel"]
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
        (flow,) = [n for n in _batch_nodes(APPLICATION_FLOW) if n["entity"]["entity_type"] == "computing_core__application_flow"]
        return flow

    def test_one_flow_with_a_name_a_description_and_one_data_class(self) -> None:
        flow = self._flow()
        assert flow["node"]["name"] == flow["entity"]["name"] and flow["node"]["description"]
        assert set(flow["node"]) == {"name", "description"}
        dims = flow["entity"]["dimensions"]
        assert dims["dataclass.customer"] == "data" and dims["dcom"] == "design" and dims["overview"] == "shown"
        assert [k for k in dims if k.startswith("dataclass.")] == ["dataclass.customer"]
        assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", flow["entity"]["entity_id"])

    def test_the_flow_runs_from_the_customer_s_computer_to_the_tap_web_program_of_task_a(self) -> None:
        flow_id = self._flow()["entity"]["entity_id"]
        edges = [e for e in _batch_edges(APPLICATION_FLOW) if flow_id in (e["from_entity_id"], e["to_entity_id"])]
        assert sorted((e["edge_type"], _name(e["from_entity_id"]), _name(e["to_entity_id"])) for e in edges) == [
            ("APPLICATION_FLOW_DESTINATION__computing_core", "customer traffic", "tap-web (web task a)"),
            ("APPLICATION_FLOW_SOURCE__computing_core", "customer a computer", "customer traffic"),
        ]

    def test_the_flow_is_a_half_size_dark_blue_circle_centred_in_the_gap_on_the_line_of_sight(self) -> None:
        source = _js()
        assert "applyIconNodes(cy, {members: shown([T.flow])" in source and "solo: true" in source
        assert "const FLOW_SCALE = 0.5;" in source and 'const FLOW_BLUE = "#0B3D91";' in source
        assert 'n.data("_stage") < flow.data("_stage")' in source, "centred between what is left of it and the product box"
        assert "_centreFlow(cy, roots, productRoot, shown([T.flow]));" in source
        assert '"target-arrow-shape": type === E.flowSource ? "none" : "triangle"' in source


class TestEdgeLiftAndLayers:
    """`req-rampart-20x-playground-govcloud-layout-16`: the flow's edge ends on the task at the account elevation and
    is drawn above the container fills and below the leaf nodes."""

    def test_the_edge_lift_is_data_relationships_and_the_interior_is_hidden_at_the_account_elevation(self) -> None:
        source = _js()
        assert "const LIFT_EDGE = [" in source and "liftEdge(cy, {relationships: LIFT_EDGE})" in source
        assert "next.contained.addClass(ELEVATION_HIDDEN_CLASS);" in source
        assert "const REVEAL_ON_ZOOM = false;" in source, "stays off until the scope-box recursion is fixed in tap_viz"

    def test_edges_sit_between_the_container_fills_and_the_leaf_nodes(self) -> None:
        source = _js()
        body = source.split("function _layerEdges")[1].split("\n}\n")[0]
        assert '"z-compound-depth": "auto"' in body, "not `top`, which draws over every node"
        assert '"z-index-compare": "manual"' in body, "`auto` draws every node after every edge"
        assert "edgeZ + 1" in body and "isParent(n) || isOwnLayer(n)" in body
        assert "_layerEdges(cy);" in source
        assert "Playground exception 13 (should become an `edge_layer` option of applyStandardChrome" in source


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
        body = source.split("function _bindFlowWindow")[1]
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
