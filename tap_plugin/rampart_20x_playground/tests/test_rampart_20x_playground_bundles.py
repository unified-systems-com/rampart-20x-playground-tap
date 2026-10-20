"""The two seed bundles, proved by importing them into a grid (`req-rampart-20x-playground-dimensions`,
`-keystone`, `-nongoals-4`). Assertions are made against what comes back out of the grid, not the JSON."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = PACKAGE_ROOT / "grift" / "dimensions.grift.json"
KEYSTONE = PACKAGE_ROOT / "grift" / "keystone.grift.json"

pytestmark = pytest.mark.django_db(databases=["default", "search_readonly"])

INVENTORY = ("applications", "libraries", "packages", "os", "containers", "crypto", "secrets", "cloud", "saas")
DATACLASS = (
    "customer.data", "customer.creds", "customer.logs", "infra.code", "infra.secrets", "infra.logs", "infra.admin",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _import(path: Path) -> None:
    from tap_grid.grift import grift_import

    result = grift_import(_load(path))
    assert result.success, result


class TestDimensions:
    """`req-rampart-20x-playground-dimensions-1`."""

    def test_twenty_dimension_nodes(self) -> None:
        from tap_grid.models import Dimension

        _import(DIMENSIONS)
        names = sorted(Dimension.objects.filter(name__regex=r"^(inventory|dataclass)").values_list("name", flat=True))
        expected = ["inventory", *(f"inventory.{v}" for v in INVENTORY), "dataclass", "dataclass.customer",
                    "dataclass.infra", *(f"dataclass.{v}" for v in DATACLASS)]
        assert names == sorted(expected)
        assert len(names) == 20

    def test_dataclass_descriptions_are_plain_words_with_no_backticks(self) -> None:
        """The Data classification cards render a value's description literally, so a backtick would show."""
        nodes = _load(DIMENSIONS)["batches"][0]["nodes"]
        described = [n for n in nodes if n["entity"]["name"].startswith("dataclass")]
        assert len(described) == 10
        for node in described:
            assert "`" not in node["node"]["description"], node["entity"]["name"]

    def test_dictionary_nodes_carry_no_dcom_value(self) -> None:
        """Dictionary entries are not entries (`req-dcom-stamping`)."""
        for node in _load(DIMENSIONS)["batches"][0]["nodes"]:
            assert "dcom" not in node["entity"]["dimensions"], node["entity"]["name"]


class TestKeystone:
    """`req-rampart-20x-playground-keystone-1` and `-nongoals-3`, `-nongoals-4`."""

    def test_one_keystone_that_says_the_data_is_mock(self) -> None:
        from tap_grid.models import Keystone

        _import(KEYSTONE)
        rows = list(Keystone.objects.filter(name="rampart-20x-playground"))
        assert len(rows) == 1
        text = rows[0].description
        assert "MOCK DATA" in text and "no FedRAMP authorization has been granted" in text
        assert "draws one authorization boundary, around the git-serious account" in text

    def test_the_keystone_says_the_design_draws_a_boundary(self) -> None:
        """`req-rampart-20x-playground-nongoals-3`: the flag that said `false` now says `true`, and its schema says why."""
        (node,) = _load(KEYSTONE)["batches"][0]["nodes"]
        assert node["node"]["context_json"]["authorization_boundary"] is True
        flag = node["node"]["context_schema_json"]["properties"]["authorization_boundary"]
        assert "Always false" not in flag["description"]

    def test_keystone_carries_no_dcom_value(self) -> None:
        for node in _load(KEYSTONE)["batches"][0]["nodes"]:
            assert "dcom" not in node["entity"]["dimensions"]


class TestOverviewMembership:
    """`req-rampart-20x-playground-govcloud-actors-8`: what the Overview shows is data on the entities."""

    def test_the_overview_dimension_exists(self) -> None:
        names = {n["entity"]["name"] for n in _load(DIMENSIONS)["batches"][0]["nodes"]}
        assert {"overview", "overview.shown"} <= names

    def test_the_overview_searches_hand_list_no_entity_types(self) -> None:
        pages = _load(PACKAGE_ROOT / "grift" / "pages.grift.json")["batches"][0]["nodes"]
        for node in pages:
            if node["entity"]["entity_type"] != "search":
                continue
            definition = node["node"]["definition"]
            if node["node"]["search_type"] == "module":
                # A module Search has no query text to hand-list types in: it names a runner and defaults its inputs.
                assert "query" not in definition and definition["runner_key"], node["entity"]["name"]
                assert "entity_type IN" not in json.dumps(node["node"].get("input_schema", {})), node["entity"]["name"]
                continue
            query = " ".join(definition["query"])
            assert "entity_type IN" not in query, node["entity"]["name"]

    def test_shown_entities_are_stamped_and_the_organization_and_other_accounts_are_not(self) -> None:
        nodes = _load(PACKAGE_ROOT / "grift" / "mock-inventory.grift.json")["batches"][0]["nodes"]
        by_name = {n["entity"]["name"]: n["entity"] for n in nodes}
        assert by_name["organization"]["dimensions"].get("overview") is None
        assert by_name["git-serious"]["dimensions"].get("overview") == "shown"
        for node in nodes:
            if node["entity"]["entity_type"] == "aws_core__aws_account" and node["entity"]["name"] != "git-serious":
                assert node["entity"]["dimensions"].get("overview") is None, node["entity"]["name"]
