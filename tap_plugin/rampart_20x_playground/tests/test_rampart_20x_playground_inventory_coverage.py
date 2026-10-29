"""The inventory coverage bundle, read from the bundle as written (`req-rampart-20x-playground-inventory-coverage-*`).

These tests read JSON and TOML files only. What the runners return, and how the pages look, is checked against a booted
stack in a browser."""

from __future__ import annotations

import json
import tomllib
import uuid
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
FILE = "inventory-coverage.grift.json"
R = "tap_plugin.compliance_core.searches."
SUMMARY = R + "dimension_mapping:dimension-mapping-summary"
SERIES = R + "snapshot_series:search-snapshot-series"
TOTALS = R + "dimension_mapping_totals:dimension-mapping-totals"
RESPONSIBILITY_ID = "01a15fdf-61ef-710d-b5d3-e3a7ae238a40"
CLASSIFICATION_ID = "01a15b2f-df3b-7569-bf22-9ead3f816b84"
CARD = "tap_web/panels/stat_card_panel.html"
CHART = "tap_web/panels/chart.html"
TOTALS_FIELDS = {"groups", "percent_overall", "denominator", "mapped", "unmapped", "mapped_incorrectly", "no_rule", "percent_pooled"}
# page: (card title, field, unit) in the order of the row.
CARDS = {
    "inventory": [("Overall Coverage", "percent_overall", "%"), ("Entries", "denominator", "entries"),
                  ("With A Team", "mapped", "entries"), ("Without A Team", "unmapped", "entries")],
    "classification": [("Overall Coverage", "percent_overall", "%"), ("Mapped", "mapped", "entries"),
                       ("Unmapped", "unmapped", "entries"), ("Incorrect", "mapped_incorrectly", "entries")],
}


def _batch(name: str = FILE) -> dict:
    return json.loads((GRIFT / name).read_text(encoding="utf-8"))["batches"][0]


class TestInventoryCoverage:
    def setup_method(self) -> None:
        self.batch = _batch()
        self.nodes = self.batch["nodes"]
        self.edges = self.batch["edges"]
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}
        self.searches = {n["entity"]["name"]: n for n in self.nodes if n["entity"]["entity_type"] == "search"}
        self.panels = {n["node"]["slug"]: n for n in self.nodes if n["entity"]["entity_type"] == "panel"}

    def _default(self, search: str, name: str):
        return self.searches[f"playground — {search}"]["node"]["input_schema"]["properties"][name]["default"]

    def _search_of(self, panel: dict) -> dict:
        links = [e["edge"] for e in self.edges
                 if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]]
        assert len(links) == 1
        return self.by_id[links[0]["to_entity_id"]]

    def test_the_bundle_is_listed_before_the_pages_that_mount_its_panels(self) -> None:
        manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
        names = list(manifest["grift"])
        assert manifest["grift"]["inventory_coverage"] == "grift/" + FILE
        assert names.index("inventory_coverage") < names.index("inventory_page") < names.index("data_classification_page")

    def test_six_searches_with_the_runners_and_ids(self) -> None:
        """`inventory-coverage-1`: five here, the sixth is the classification summary of the mapping bundle."""
        assert all(s["node"]["search_type"] == "module" and s["node"]["root"] == "node" for s in self.searches.values())
        runners = {name.split(" — ")[1]: s["node"]["definition"]["runner_key"] for name, s in self.searches.items()}
        assert runners == {
            "responsibility coverage": SUMMARY, "responsibility coverage history": SERIES,
            "classification coverage history": SERIES, "responsibility coverage totals": TOTALS,
            "classification coverage totals": TOTALS,
        }
        assert self.searches["playground — responsibility coverage"]["entity"]["entity_id"] == RESPONSIBILITY_ID
        assert self._default("responsibility coverage history", "search_id") == RESPONSIBILITY_ID
        assert self._default("responsibility coverage totals", "summary_search_id") == RESPONSIBILITY_ID
        assert self._default("classification coverage history", "search_id") == CLASSIFICATION_ID
        assert self._default("classification coverage totals", "summary_search_id") == CLASSIFICATION_ID
        mapping = {n["entity"]["entity_id"]: n for n in _batch("classification-mapping.grift.json")["nodes"]}
        assert mapping[CLASSIFICATION_ID]["node"]["definition"]["runner_key"] == SUMMARY
        assert all(self._default(f"{k} coverage history", "series_field") == "label" for k in ("responsibility", "classification"))
        assert all(self._default(f"{k} coverage history", "value_field") == "percent_mapped" for k in ("responsibility", "classification"))

    def test_responsibility_is_presence_of_team_responsible_and_excludes_nothing(self) -> None:
        """`inventory-coverage-2`."""
        (row,) = self._default("responsibility coverage", "mappings")
        assert row["entity_types"] == ["*"] and row["keys"] == [{"key": "team.responsible"}] and row["match"] == "all"
        assert self._default("responsibility coverage", "group_by") == "inventory"
        assert self._default("responsibility coverage", "exclude_groups") == []

    def test_the_classification_chart_reads_the_one_grouped_rulebook(self) -> None:
        """`inventory-coverage-3`: no second mapping is held here."""
        for name, s in self.searches.items():
            if "classification" in name:
                assert "mappings" not in s["node"]["input_schema"]["properties"]

    def test_the_pages_have_four_live_cards_each_bound_to_the_totals_search(self) -> None:
        """`inventory-coverage-12`, `-13`, `-15`, `-16`."""
        for page, cards in CARDS.items():
            totals = f"playground — {'responsibility' if page == 'inventory' else 'classification'} coverage totals"
            for title, field, unit in cards:
                slug = "playground-" + page + "-coverage-" + {
                    "Overall Coverage": "overall", "Entries": "entries", "With A Team": "with-team",
                    "Without A Team": "without-team", "Mapped": "mapped", "Unmapped": "unmapped", "Incorrect": "incorrect",
                }[title]
                card = self.panels[slug]
                assert card["node"]["view"] == CARD and card["node"]["name"] == title
                config = card["node"]["config"]
                assert config["value_field"] == field and config["unit"] == unit and field in TOTALS_FIELDS
                assert self._search_of(card)["entity"]["name"] == totals
                assert set(config) <= {"title", "title_style", "layout", "value_field", "value_formatter", "unit", "hide_header", "null_text"}

    def test_each_page_has_one_line_chart_on_a_time_axis_with_overall_last(self) -> None:
        """`inventory-coverage-5`, `-6`, `-8`, `-9`."""
        # The order of the Summary table: the sorted values of the inventory dimension.
        cats = ["Applications", "Cloud Services", "Containers", "Crypto", "Libraries", "Operating Systems", "Packages", "Third-Party SaaS", "Secrets"]
        expected = {
            "playground-inventory-coverage-chart": ("Responsibility Coverage", cats, "responsibility coverage history"),
            "playground-classification-coverage-chart": ("Data Classification Coverage", [c for c in cats if c != "Crypto"], "classification coverage history"),
        }
        charts = [p for p in self.panels.values() if p["node"]["view"] == CHART]
        assert len(charts) == 2
        for slug, (name, order, history) in expected.items():
            config = self.panels[slug]["node"]["config"]
            assert self.panels[slug]["node"]["name"] == name
            assert {k: v for k, v in config["series_by"].items() if k != "overrides"} == {"category": "observed_at", "series": "series", "value": "value", "order": [*order, "Overall"]}
            option = config["option"]
            assert option["xAxis"]["type"] == "time" and (option["yAxis"]["min"], option["yAxis"]["max"]) == (0, 100)
            (series,) = option["series"]
            assert series["type"] == "line" and "stack" not in series
            # George, 2026-10-21: no legend; each line's name sits at its end, shifted apart where ends cluster.
            assert "legend" not in option and option["tooltip"]["trigger"] == "axis"
            assert series["endLabel"] == {"show": True, "formatter": "{a}", "color": "inherit", "textBorderWidth": 0, "textBorderColor": "transparent", "textShadowBlur": 0} and series["labelLayout"] == {"moveOverlap": "shiftY"}
            assert set(config["color_map"]["map"]) == {*order, "Overall"}
            # George, 2026-10-22: every category line is one muted colour at 1.5 wide; Overall alone is thick, opaque, on top and coloured.
            assert all(config["color_map"]["map"][c] == "muted" for c in order) and config["color_map"]["map"]["Overall"] == "accent-1"
            assert series["lineStyle"] == {"width": 1.5, "opacity": 0.55}
            assert config["series_by"]["overrides"] == {"Overall": {"lineStyle": {"width": 6, "opacity": 1}, "z": 10}}
            assert config["types"] == {"observed_at": "time", "value": "number"}
            assert config["empty_text"] and config["max_rows"] == 5000
            assert self._search_of(self.panels[slug])["entity"]["name"] == f"playground — {history}"
            snapshots = self._default(history, "max_snapshots")
            assert snapshots * (len(order) + 1) <= config["max_rows"]

    def test_no_panel_carries_prose(self) -> None:
        """`inventory-coverage-10`."""
        for panel in self.panels.values():
            assert "text" not in panel["node"]["config"]

    def test_headings_are_title_case(self) -> None:
        for panel in self.panels.values():
            assert panel["node"]["name"] == panel["node"]["name"].title().replace("Saas", "SaaS").replace("A Team", "A Team")

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


class TestDependencies:
    def test_floors_and_boot_pins_name_the_releases_that_ship_the_runners(self) -> None:
        """`inventory-coverage-11`: compliance_core v0.8.11 and fedramp_20x_vdr v0.1.5 (the release with the summary and the one-finding filter)."""
        manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
        floors = {d["slug"]: d.get("min_version") for d in manifest["depends_on"]}
        assert floors["compliance_core"] == "0.8.11" and floors["fedramp_20x_vdr"] == "0.1.5"
        pins = {
            "compliance_core": ("v0.8.11", "54e450e99c9b483aeb5ad3d7f646205b0843dbe2"),
            "fedramp_20x_vdr": ("v0.1.5", "ff9685fdee0918d1a77592ab71d2e11ed3776cc3"),
        }
        for name in ("ci", "demo"):
            record = json.loads((PACKAGE_ROOT / "boot" / f"{name}.boot.json").read_text(encoding="utf-8"))
            for entry in record["install"]["plugins"]:
                if entry["slug"] in pins:
                    assert (entry["source"]["rev"], entry["source"]["commit"]) == pins[entry["slug"]], (name, entry["slug"])


class TestStampsAndWindow:
    def test_containers_and_buckets_are_cloud_services(self) -> None:
        """`dimensions-12`: counted in the Cloud Services line, listed in its table."""
        seen: dict[str, int] = {}
        for name in ("application-flow.grift.json", "mock-inventory.grift.json"):
            for node in _batch(name)["nodes"]:
                entity = node["entity"]
                if entity["entity_type"] in ("aws_core__aws_ecs_container", "aws_core__aws_s3_bucket"):
                    assert entity["dimensions"]["inventory"] == "cloud", entity["name"]
                    seen[entity["entity_type"]] = seen.get(entity["entity_type"], 0) + 1
        assert seen == {"aws_core__aws_ecs_container": 2, "aws_core__aws_s3_bucket": 2}

    def test_the_classification_history_starts_at_the_first_grouped_snapshot(self) -> None:
        """The card and the chart's last Overall point agree only when the chart holds one mapping."""
        nodes = {n["entity"]["name"]: n for n in _batch()["nodes"] if n["entity"]["entity_type"] == "search"}
        since = nodes["playground — classification coverage history"]["node"]["input_schema"]["properties"]["since"]
        assert since["default"] == "2026-10-17T00:00:00Z"
