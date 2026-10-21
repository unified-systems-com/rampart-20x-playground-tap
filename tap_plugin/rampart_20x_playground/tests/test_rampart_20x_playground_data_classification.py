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
MAPPING_FILE = "classification-mapping.grift.json"
SLUG = "/playground/data-classification"
TABLE = "tap_web/panels/table_panel.html"
TEXT = "tap_web/panels/text_panel.html"
CARD = "tap_web/panels/stat_card_panel.html"
RUNNER = "tap_plugin.compliance_core.searches.dimension_coverage:dimension-coverage"
# The fields the runner returns that a card may name (compliance_core req-compliance-core-dimension-coverage).
RUNNER_FIELDS = {"key", "description", "total", "values", "values_text", "breakdown_text"}
# The keys of each element of the runner's `values` array that a table column may name.
VALUE_FIELDS = {"value", "description", "declared", "count", "by_type"}
KEYS = {"dataclass.customer", "dataclass.infra", "dataclass.action"}


def _batch() -> dict:
    return json.loads((GRIFT / FILE).read_text(encoding="utf-8"))["batches"][0]


class TestDataClassificationPage:
    def setup_method(self) -> None:
        self.batch = _batch()
        self.nodes = self.batch["nodes"]
        self.edges = self.batch["edges"]
        # The four classification-mapping tables are panels of the mapping bundle, placed on this page by edges held here.
        self.mapping = json.loads((GRIFT / MAPPING_FILE).read_text(encoding="utf-8"))["batches"][0]
        self.coverage = json.loads((GRIFT / "inventory-coverage.grift.json").read_text(encoding="utf-8"))["batches"][0]
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes + self.mapping["nodes"] + self.coverage["nodes"]}
        self.page = next(n for n in self.nodes if n["entity"]["entity_type"] == "page")
        self.panels = {n["node"]["slug"]: n for n in self.by_id.values() if n["entity"]["entity_type"] == "panel"}
        self.cards = [
            p for p in self.panels.values()
            if p["node"]["view"] == CARD and p["node"]["slug"].startswith("playground-data-classification-")
        ]

    def _search_of(self, panel: dict) -> dict:
        links = [
            e for e in self.edges + self.mapping["edges"] + self.coverage["edges"]
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

    def test_a_title_then_coverage_cards_and_chart_then_three_equal_cards_then_the_four_mapping_tables(self) -> None:
        """`page-data-classification-9`, `-13`; `inventory-coverage-5`, `-12`."""
        columns = self.page["node"]["layout"]["columns"]
        bands: dict[int, list[dict]] = {}
        for column in columns.values():
            bands.setdefault(column["band"], []).append(column)
        assert sorted(bands) == [1, 2, 3, 4, 5, 6, 7, 8]
        assert len(bands[2]) == 4 and {c["width"] for c in bands[2]} == {"3fr"}
        assert len(bands[4]) == 3 and {c["width"] for c in bands[4]} == {"4fr"}
        assert all(len(bands[b]) == 1 and bands[b][0]["width"] == "12fr" for b in (1, 3, 5, 6, 7, 8))
        assert len([p for p in self.panels.values() if p['node']['view'] == CARD and 'classification' in p['node']['slug']]) == 7  # three classification, four coverage

        def slot(column: dict) -> str:
            return next(iter(r["panel-id"] for r in column["rows"].values()))

        intro = self.panels[slot(bands[1][0])]
        assert intro["node"]["view"] == TEXT
        assert [slot(c) for c in bands[2]] == [
            "playground-classification-coverage-overall", "playground-classification-coverage-mapped",
            "playground-classification-coverage-unmapped", "playground-classification-coverage-incorrect",
        ]
        assert slot(bands[3][0]) == "playground-classification-coverage-chart"
        assert [slot(c) for c in bands[4]] == [
            "playground-data-classification-customer", "playground-data-classification-infra",
            "playground-data-classification-action",
        ]
        tables = [self.panels[slot(bands[b][0])] for b in (5, 6, 7, 8)]
        assert [t["node"]["view"] for t in tables] == [TABLE] * 4
        assert [t["node"]["name"] for t in tables] == ["Summary", "Mapped Incorrectly", "Unmapped", "Mapped"]
        assert all(t["entity"]["entity_id"] in {e["edge"]["to_entity_id"] for e in self.edges} for t in tables)

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
            for line in config["lines"]:
                columns = {c["field"] for c in line.get("columns", [])}
                assert columns <= VALUE_FIELDS, columns - VALUE_FIELDS

    def test_each_card_is_title_and_figure_then_the_header_description_then_the_inventory_table(self) -> None:
        for card in self.cards:
            config = card["node"]["config"]
            assert config["layout"] == "figure_right" and config["title_style"] == "bold"
            assert config["title_field"] == "key" and config["value_field"] == "total"
            assert config["unit"] == "components"
            description, table = config["lines"]
            # George, Q90: the description stands in the header directly under the title, and "Inventory" is a caption above the table.
            assert description["field"] == "description" and "label" not in description and description["placement"] == "header"
            assert table["field"] == "values" and table["formatter"] == "table"
            assert table["label"] == "Inventory" and table["label_placement"] == "above"
            assert [c["field"] for c in table["columns"]] == ["value", "description", "count"]
            assert table["columns"][2]["formatter"] == "integer"  # a zero count shows 0

    def test_the_page_starts_with_its_title_and_has_no_explanatory_prose(self) -> None:
        assert self.page["node"]["name"] == self.page["entity"]["name"] == "Data Classification"
        first = self.panels[
            next(r["panel-id"] for r in self.page["node"]["layout"]["columns"]["col-1"]["rows"].values())
        ]
        assert first["node"]["view"] == TEXT
        assert first["node"]["name"] == first["entity"]["name"] == "Data Classification"
        assert first["node"]["config"] == {"text": "", "hide_header": False}  # the header IS the title
        shown = json.dumps([p["node"]["config"] for p in self.cards])
        for caption in ("What it classifies", "Components by type", "values_text", "breakdown_text"):
            assert caption not in shown, caption

    def test_no_value_is_named_and_nothing_says_mock(self) -> None:
        text = json.dumps(self.nodes).lower()
        assert "mock" not in text
        assert not re.search(r"dataclass\.(customer|infra|action)\.", text)  # only the keys, never a key.value

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
