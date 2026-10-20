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
    "customer.data", "customer.creds", "customer.logs", "customer.sanitized", "infra.code", "infra.secrets", "infra.logs",
    "infra.admin", "action", "action.store", "action.process", "action.transmit", "action.none",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _import(path: Path) -> None:
    from tap_grid.grift import grift_import

    result = grift_import(_load(path))
    assert result.success, result


class TestDimensions:
    """`req-rampart-20x-playground-dimensions-1`."""

    def test_twenty_six_dimension_nodes(self) -> None:
        from tap_grid.models import Dimension

        _import(DIMENSIONS)
        names = sorted(Dimension.objects.filter(name__regex=r"^(inventory|dataclass)").values_list("name", flat=True))
        expected = ["inventory", *(f"inventory.{v}" for v in INVENTORY), "dataclass", "dataclass.customer",
                    "dataclass.infra", *(f"dataclass.{v}" for v in DATACLASS)]
        assert not {"dataclass.customer.reader", "dataclass.customer.writer", "dataclass.customer.storage"} & set(names)
        assert names == sorted(expected)
        assert len(names) == 26

    def test_dataclass_descriptions_are_plain_words_with_no_backticks(self) -> None:
        """The Data classification cards render a value's description literally, so a backtick would show."""
        nodes = _load(DIMENSIONS)["batches"][0]["nodes"]
        described = [n for n in nodes if n["entity"]["name"].startswith("dataclass")]
        assert len(described) == 16
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


class TestDataclassActionStamping:
    """`req-rampart-20x-playground-dimensions-6` to `-11`: read from the seed files, which is where the stamps live."""

    EXPECTED = {
        "computing_core__application_flow": "transmit",
        "computing_core__program": "process",
        "aws_core__aws_ecs_container": "process",
        "aws_core__aws_rds_instance": "store",
        "aws_core__aws_s3_bucket": "store",
    }

    def _stamped(self) -> list[dict]:
        rows = []
        for path in (PACKAGE_ROOT / "grift").glob("*.grift.json"):
            for batch in _load(path)["batches"]:
                rows += [n["entity"] for n in batch["nodes"] if "entity" in n]
        return rows

    def test_only_the_listed_entities_carry_an_action_and_each_carries_one(self) -> None:
        counts: dict[str, int] = {}
        for entity in self._stamped():
            dims = entity["dimensions"]
            assert not [k for k in dims if k.startswith("dataclass.action.")], entity["name"]
            action = dims.get("dataclass.action")
            if action is None:
                continue
            assert action == self.EXPECTED[entity["entity_type"]], entity["name"]
            counts[action] = counts.get(action, 0) + 1
        # five flows, five programs plus two containers, the RDS instance plus two buckets
        assert counts == {"transmit": 5, "process": 7, "store": 3}

    def test_the_retired_administration_flow_is_unstamped(self) -> None:
        old = [e for e in self._stamped() if e.get("entity_id") == "01a15a28-7763-727d-9425-a57a6568592e"]
        assert len(old) == 1 and not [k for k in old[0]["dimensions"] if k.startswith("dataclass")]

    def test_the_database_flow_is_sanitized_and_the_customer_flow_keeps_data(self) -> None:
        flows = {e["name"]: e["dimensions"] for e in self._stamped()
                 if e["entity_type"] == "computing_core__application_flow" and e["dimensions"].get("overview") == "shown"}
        assert flows["database"]["dataclass.customer"] == "sanitized"
        assert flows["customer data"]["dataclass.customer"] == "data"

    def test_no_seed_entity_carries_a_removed_role_value(self) -> None:
        for entity in self._stamped():
            assert entity["dimensions"].get("dataclass.customer") not in ("reader", "writer", "storage"), entity["name"]

    def test_the_action_values_are_declared_with_plain_descriptions(self) -> None:
        nodes = {n["entity"]["name"]: n["node"]["description"] for n in _load(DIMENSIONS)["batches"][0]["nodes"]}
        assert {n for n in nodes if n.startswith("dataclass.action.")} == {f"dataclass.action.{v}" for v in ("store", "process", "transmit", "none")}
        assert nodes["dataclass.customer.sanitized"] == "Customer data that has been filtered to remove untrusted content."
