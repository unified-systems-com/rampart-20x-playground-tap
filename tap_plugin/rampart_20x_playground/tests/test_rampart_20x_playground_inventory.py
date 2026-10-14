"""The inventory build, read from the bundles as written (`req-rampart-20x-playground-inventory-*`).

These tests read the JSON files only, so they hold what the bundles declare, not what a grid returns:
that the seven tables exist and are wired, that every entity carries one valid `inventory` value, that no
secret material is recorded. What a table shows once imported is checked in the browser."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"

CATEGORIES = ("applications", "libraries", "os", "containers", "secrets", "cloud", "saas")
# The panel slot (page `panel-id`) of each table, in page order.
SLOTS = {
    "applications": "applications",
    "libraries": "libraries",
    "os": "operating-systems",
    "containers": "containers",
    "secrets": "secrets",
    "cloud": "cloud-services",
    "saas": "saas",
}
# Conceptual containers and instances: no row anywhere (`-tables`, `-cloud`, `-rows`).
UNLISTED_TYPES = (
    "aws_core__aws_vpc",
    "aws_core__aws_subnet",
    "aws_core__aws_account",
    "aws_core__aws_ecs_task",
)


def _load(name: str) -> dict:
    return json.loads((GRIFT / name).read_text(encoding="utf-8"))


def _nodes(name: str) -> list[dict]:
    return [node for batch in _load(name)["batches"] for node in batch["nodes"]]


def _edges(name: str) -> list[dict]:
    return [edge for batch in _load(name)["batches"] for edge in batch["edges"]]


def _stamped() -> list[dict]:
    return [n for f in ("mock-inventory.grift.json", "inventory-entities.grift.json") for n in _nodes(f)]


class TestDimensionSplit:
    """`req-rampart-20x-playground-inventory-dimension`."""

    def test_inventory_categories_are_the_seven(self) -> None:
        names = {n["entity"]["name"] for n in _nodes("dimensions.grift.json")}
        assert {n for n in names if n.startswith("inventory.")} == {f"inventory.{c}" for c in CATEGORIES}

    def test_os_is_operating_systems_only(self) -> None:
        by_name = {n["entity"]["name"]: n["node"] for n in _nodes("dimensions.grift.json")}
        assert "container" not in by_name["inventory.os"]["description"]
        assert "container" in by_name["inventory.containers"]["description"]


class TestStamps:
    """`req-rampart-20x-playground-mock-inventory-4`: one category or none, and always on the design position."""

    def test_every_inventory_value_is_a_category(self) -> None:
        stamped = [n for n in _stamped() if "inventory" in n["entity"]["dimensions"]]
        assert stamped
        for node in stamped:
            assert node["entity"]["dimensions"]["inventory"] in CATEGORIES, node["entity"]["name"]

    def test_stamped_entities_are_on_the_design_position(self) -> None:
        for node in _stamped():
            if "inventory" in node["entity"]["dimensions"]:
                assert node["entity"]["dimensions"]["dcom"] == "design", node["entity"]["name"]

    def test_conceptual_containers_and_instances_have_no_row(self) -> None:
        for node in _stamped():
            if node["entity"]["entity_type"] in UNLISTED_TYPES:
                assert "inventory" not in node["entity"]["dimensions"], node["entity"]["name"]

    def test_the_container_table_holds_the_image_not_the_tasks(self) -> None:
        containers = [n for n in _stamped() if n["entity"]["dimensions"].get("inventory") == "containers"]
        assert [n["entity"]["entity_type"] for n in containers] == ["github_core__github_package_version"]

    def test_operating_systems_are_not_stamped_on_a_container(self) -> None:
        # The OS table has no node type behind it yet; nothing is stamped `os` by guesswork.
        assert not [n for n in _stamped() if n["entity"]["dimensions"].get("inventory") == "os"]


class TestInventoryEntities:
    """`grift/inventory-entities.grift.json`: existing computing_core types only, no edges, no secret values."""

    def test_existing_types_only(self) -> None:
        allowed = {
            "computing_core__program",
            "computing_core__file",
            "computing_core__public_key",
            "computing_core__private_key",
        }
        assert {n["entity"]["entity_type"] for n in _nodes("inventory-entities.grift.json")} <= allowed

    def test_no_edges_are_invented(self) -> None:
        assert _edges("inventory-entities.grift.json") == []

    def test_no_secret_value_or_fingerprint_is_recorded(self) -> None:
        for node in _nodes("inventory-entities.grift.json"):
            assert not node["node"].get("fingerprint"), node["entity"]["name"]
            assert "content" not in node["node"] and "value" not in node["node"], node["entity"]["name"]

    def test_certificate_halves_are_identified(self) -> None:
        by_type = {n["entity"]["entity_type"]: n["node"] for n in _nodes("inventory-entities.grift.json")}
        assert by_type["computing_core__public_key"]["algorithm"] == by_type["computing_core__private_key"]["algorithm"]


class TestInventoryPage:
    """`req-rampart-20x-playground-inventory-tables` and `-page-inventory`."""

    def setup_method(self) -> None:
        self.nodes = _nodes("inventory-page.grift.json")
        self.edges = _edges("inventory-page.grift.json")
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}

    def _of(self, entity_type: str) -> list[dict]:
        return [n for n in self.nodes if n["entity"]["entity_type"] == entity_type]

    def test_route(self) -> None:
        (page,) = self._of("page")
        assert page["node"]["slug"] == "/playground/inventory"

    def test_seven_tables_each_over_its_category(self) -> None:
        searches = self._of("search")
        assert len(searches) == len(self._of("panel")) == 7
        queried = set()
        for search in searches:
            where = [line for line in search["node"]["definition"]["query"] if line.startswith("WHERE")]
            assert len(where) == 1 and where[0].startswith('WHERE n.dimensions["inventory"] = "'), where
            queried.add(where[0].split('"')[3])
        assert queried == set(CATEGORIES)

    def test_each_panel_is_a_table_bound_to_exactly_one_search(self) -> None:
        for panel in self._of("panel"):
            assert panel["node"]["view"] == "tap_web/panels/table_panel.html"
            links = [
                e
                for e in self.edges
                if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]
            ]
            assert len(links) == 1, panel["entity"]["name"]
            assert self.by_id[links[0]["edge"]["to_entity_id"]]["entity"]["entity_type"] == "search"

    def test_page_slots_match_the_uses_panel_edges(self) -> None:
        (page,) = self._of("page")
        slots = [
            row["panel-id"]
            for col in page["node"]["layout"]["columns"].values()
            for row in col["rows"].values()
        ]
        hotlinks = [
            e["edge"]["properties"]["hotlink"]["value"] for e in self.edges if e["edge"]["edge_type"] == "USES_PANEL"
        ]
        assert sorted(slots) == sorted(hotlinks) == sorted(SLOTS.values())

    def test_each_slot_mounts_the_panel_of_its_category(self) -> None:
        for category, slot in SLOTS.items():
            edge = next(
                e
                for e in self.edges
                if e["edge"]["edge_type"] == "USES_PANEL" and e["edge"]["properties"]["hotlink"]["value"] == slot
            )
            panel = self.by_id[edge["edge"]["to_entity_id"]]
            assert panel["node"]["slug"] == f"playground-inventory-{slot}"
            search_edge = next(
                e
                for e in self.edges
                if e["edge"]["edge_type"] == "USES_SEARCH"
                and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]
            )
            query = self.by_id[search_edge["edge"]["to_entity_id"]]["node"]["definition"]["query"]
            assert f'WHERE n.dimensions["inventory"] = "{category}"' in query

    def test_common_columns_on_every_table(self) -> None:
        for panel in self._of("panel"):
            fields = [c["field"] for c in panel["node"]["config"]["columns"]]
            assert fields[:2] == ["entity_id", "name"], panel["entity"]["name"]
            assert "data.description" in fields, panel["entity"]["name"]

    def test_no_free_text_comments_column_and_no_secret_columns(self) -> None:
        for panel in self._of("panel"):
            for column in panel["node"]["config"]["columns"]:
                assert "comment" not in column["field"].lower() and "comment" not in column["title"].lower()
                assert "fingerprint" not in column["field"].lower()

    def test_app_entities_carry_no_dcom_value(self) -> None:
        """`req-rampart-20x-playground-nongoals-4`: the page, panels, Searches and edges are the app, not the system."""
        for node in self.nodes:
            assert "dcom" not in node["entity"]["dimensions"], node["entity"]["name"]


class TestNewIds:
    def test_new_ids_are_unique_version_7_uuids(self) -> None:
        ids: list[str] = []
        for name in ("inventory-entities.grift.json", "inventory-page.grift.json"):
            for batch in _load(name)["batches"]:
                ids.append(batch["batch_entity"]["entity_id"])
                ids += [n["entity"]["entity_id"] for n in batch["nodes"]]
                ids += [e["entity"]["entity_id"] for e in batch["edges"]]
        assert len(ids) == len(set(ids))
        assert all(uuid.UUID(i).version == 7 for i in ids)
        existing = {
            n["entity"]["entity_id"] for f in ("mock-inventory.grift.json", "pages.grift.json") for n in _nodes(f)
        }
        assert not existing & set(ids)
