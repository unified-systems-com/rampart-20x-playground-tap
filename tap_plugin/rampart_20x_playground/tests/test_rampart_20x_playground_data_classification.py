"""The data classification page, read from the bundle as written (`req-rampart-20x-playground-page-data-classification-*`).

These tests read the JSON file only. What the Searches return, and how the page looks, is checked against a booted
stack in a browser. No test names a classification value: the values come from the dimension dictionary, so a value
added later must render without a change here."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
FILE = "data-classification-page.grift.json"
SLUG = "/playground/data-classification"
TEXT = "tap_web/panels/text_panel.html"
CARD = "tap_web/panels/stat_card_panel.html"
RUNNER = "tap_plugin.compliance_core.searches.dimension_coverage:dimension-coverage"
# The fields the runner returns that a card may name (compliance_core req-compliance-core-dimension-coverage).
RUNNER_FIELDS = {"key", "description", "total", "values", "values_text", "breakdown_text"}
KEYS = {"dataclass.customer", "dataclass.infra"}


def _batch() -> dict:
    return json.loads((GRIFT / FILE).read_text(encoding="utf-8"))["batches"][0]


class TestDataClassificationPage:
    def setup_method(self) -> None:
        self.batch = _batch()
        self.nodes = self.batch["nodes"]
        self.edges = self.batch["edges"]
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}
        self.page = next(n for n in self.nodes if n["entity"]["entity_type"] == "page")
        self.panels = {n["node"]["slug"]: n for n in self.nodes if n["entity"]["entity_type"] == "panel"}
        self.cards = [p for p in self.panels.values() if p["node"]["view"] == CARD]

    def _search_of(self, panel: dict) -> dict:
        links = [
            e for e in self.edges
            if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]
        ]
        assert len(links) == 1
        return self.by_id[links[0]["edge"]["to_entity_id"]]

    def test_the_page_is_routable_and_in_navigation(self) -> None:
        assert self.page["node"]["slug"] == SLUG
        assert "discoverable" not in self.page["node"]

    def test_slots_and_edges_match_exactly(self) -> None:
        slots = {
            row["panel-id"]
            for column in self.page["node"]["layout"]["columns"].values()
            for row in column["rows"].values()
        }
        wired = {
            e["edge"]["properties"]["hotlink"]["value"]: e["edge"]["to_entity_id"]
            for e in self.edges if e["edge"]["edge_type"] == "USES_PANEL"
        }
        assert slots == set(wired)
        assert {self.by_id[i]["node"]["slug"] for i in wired.values()} == slots

    def test_an_introduction_then_two_equal_columns_with_one_card_each_and_no_table(self) -> None:
        columns = self.page["node"]["layout"]["columns"]
        bands: dict[int, list[dict]] = {}
        for column in columns.values():
            bands.setdefault(column["band"], []).append(column)
        assert sorted(bands) == [1, 2]
        assert len(bands[2]) == 2 and {c["width"] for c in bands[2]} == {"6fr"}
        assert len(self.cards) == 2
        assert all(p["node"]["view"] in (TEXT, CARD) for p in self.panels.values())
        intro = self.panels[next(iter(r["panel-id"] for r in bands[1][0]["rows"].values()))]
        assert intro["node"]["view"] == TEXT

    def test_each_card_reads_a_module_search_for_one_key_and_names_the_gryphon_gap(self) -> None:
        keys = set()
        for card in self.cards:
            search = self._search_of(card)["node"]
            assert search["search_type"] == "module" and search["definition"] == {"runner_key": RUNNER}
            keys.add(search["input_schema"]["properties"]["dimension_key"]["default"])
            assert "Gryphon cannot write this" in search["description"]
            assert "entity type" in search["description"]
        assert keys == KEYS

    def test_card_fields_are_row_fields_of_the_runner(self) -> None:
        for card in self.cards:
            config = card["node"]["config"]
            named = {config["title_field"], config["value_field"], *(line["field"] for line in config["lines"])}
            assert named <= RUNNER_FIELDS, named - RUNNER_FIELDS

    def test_no_value_is_named_and_nothing_says_mock(self) -> None:
        text = json.dumps(self.nodes).lower()
        assert "mock" not in text
        assert not re.search(r"dataclass\.(customer|infra)\.", text)  # only the keys, never a key.value

    def test_ids_are_unique_version_7_uuids(self) -> None:
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
