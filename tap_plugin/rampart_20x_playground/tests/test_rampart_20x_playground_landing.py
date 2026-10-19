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


class TestDeployPile:
    """`req-rampart-20x-playground-govcloud-layout-8`: C3 (a pile, not a column)."""

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
        assert shown_secrets and shown_secrets <= retrieved, "every secret still drawn is in the pile"

    def test_the_certificate_the_key_and_the_runtime_secret_are_not_on_the_overview(self) -> None:
        """`req-rampart-20x-playground-govcloud-layout-11`: no `overview` value, nodes kept for the grid."""
        hidden = {"tls certificate", "DB Encryption Key", "runtime secrets"}
        found = {n["entity"]["name"]: n["entity"]["dimensions"] for n in _nodes() if n["entity"]["name"] in hidden}
        assert set(found) == hidden
        assert all("overview" not in dims and dims.get("inventory") for dims in found.values())
        source = _js()
        assert "T.cert" not in source and "T.key" not in source

    def test_nothing_in_the_deploy_pile_is_a_line_of_sight_type(self) -> None:
        assert not set(_list("DEPLOY_TYPES")) & {"zone", "alb", "rds", "igw"}

    def test_the_deploy_types_are_not_account_rows_any_more(self) -> None:
        tiers = re.search(r"tiers: \[(.*?)\n\s*\],", _js(), re.S)
        assert tiers
        named = set(re.findall(r"T\.(\w+)", tiers.group(1)))
        assert named == {"zone", "vpc"}

    def test_the_administrator_pair_hangs_under_the_account_centre(self) -> None:
        source = _js()
        assert len(re.findall(r"const BELOW_ACCOUNT_GAP = \d+;", source)) == 1
        assert "const x = account.position(\"x\");" in source.split("function _closePairs")[1]
        assert "computer.position({x, y});" in source and "person.position({x, y: y +" in source

    def test_the_pile_is_a_small_equal_diagonal_offset_centred_on_the_account(self) -> None:
        source = _js()
        step = re.search(r"const PILE_STEP = \{dx: (\d+), dy: (\d+)\}", source)
        assert step
        dx, dy = int(step.group(1)), int(step.group(2))
        assert 0 < dx <= 20 and 0 < dy <= 30, "small enough that each icon overlaps the next"
        assert "const x0 = account.position(\"x\") - ((count - 1) * PILE_STEP.dx) / 2;" in source
        assert "x: x0 + i * PILE_STEP.dx, y: y0 + i * PILE_STEP.dy" in source

    def test_edges_inside_the_pile_are_hidden_and_the_others_stay(self) -> None:
        source = _js()
        assert "deploy.anySame(e.source()) && deploy.anySame(e.target())" in source


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
                "customer a", "customer a computer", "git-serious", "github.com", "developer a laptop", "developer a",
            }:
                columns[entity["name"]] = int(raw)
        order = ["customer a", "customer a computer", "git-serious", "github.com", "developer a laptop", "developer a"]
        assert [columns[n] for n in order] == sorted(columns[n] for n in order)
        assert len(set(columns.values())) == len(order)

    def test_github_carries_its_column_as_a_tag(self) -> None:
        """The platform type has a tagging system; its column is a tag, never a dimension."""
        (github,) = _by_type("github_core__github_platform")
        assert github["node"]["tags"]["layout:column"] == "3"
        assert "column" not in github["entity"].get("dimensions", {})

    def test_no_placement_by_label_or_id(self) -> None:
        source = _js()
        assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", source)
        assert not re.search(r"data\(\"label\"\)\s*===", source)


class TestPersonComputerPairs:
    """`req-rampart-20x-playground-govcloud-layout-10`."""

    def test_one_named_gap_constant_marked_as_an_exception(self) -> None:
        source = _js()
        assert len(re.findall(r"const PAIR_GAP = \d+;", source)) == 1
        gap = int(re.search(r"const PAIR_GAP = (\d+);", source).group(1))
        assert 20 <= gap <= 32
        assert "_closePairs(roots, account);" in source

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
        for rid in ("govcloud-layout-8", "govcloud-layout-9", "govcloud-layout-2"):
            assert f"req-rampart-20x-playground-{rid}" in text
