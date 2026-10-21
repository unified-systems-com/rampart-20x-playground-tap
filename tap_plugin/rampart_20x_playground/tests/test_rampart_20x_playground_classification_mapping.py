"""The classification mapping bundle, read from the bundle as written (`req-rampart-20x-playground-classification-mapping-*`).
The four tables sit on the Data Classification page; its test file pins their placement.

These tests read JSON files only. What the runners return, and how the page looks, is checked against a booted stack."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
FILE = "classification-mapping.grift.json"
TABLE = "tap_web/panels/table_panel.html"
RUNNER = "tap_plugin.compliance_core.searches.dimension_mapping:"
# The id fedramp_20x_vdr's coverage_snapshot collector hard-codes (COVERAGE_SUMMARY_SEARCH_ID). It must never differ.
SUMMARY_SEARCH_ID = "01a15b2f-df3b-7569-bf22-9ead3f816b84"
# uuid5(NAMESPACE_COLLECTOR, "fedramp_20x_vdr:coverage_snapshot")
COLLECTOR_ID = "41611294-9c37-5013-8175-3b1c2c4a3908"
SUMMARY_FIELDS = {"label", "keys_text", "denominator", "mapped", "unmapped", "mapped_incorrectly", "percent_mapped"}
ENTITY_FIELDS = {"label", "name", "found_text", "allowed_text"}


UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _batch() -> dict:
    return json.loads((GRIFT / FILE).read_text(encoding="utf-8"))["batches"][0]


class TestClassificationMapping:
    def setup_method(self) -> None:
        self.batch = _batch()
        self.nodes = self.batch["nodes"]
        self.edges = self.batch["edges"]
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}
        self.searches = [n for n in self.nodes if n["entity"]["entity_type"] == "search"]
        self.panels = {n["node"]["slug"]: n for n in self.nodes if n["entity"]["entity_type"] == "panel"}

    def _search_of(self, panel: dict) -> dict:
        links = [
            e for e in self.edges
            if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]
        ]
        assert len(links) == 1
        return self.by_id[links[0]["edge"]["to_entity_id"]]

    def test_the_summary_search_has_the_fixed_entity_id_the_collector_hard_codes(self) -> None:
        """`classification-mapping-10`."""
        summary = [s for s in self.searches if s["node"]["definition"]["runner_key"] == RUNNER + "dimension-mapping-summary"]
        assert [s["entity"]["entity_id"] for s in summary] == [SUMMARY_SEARCH_ID] == ["01a15b2f-df3b-7569-bf22-9ead3f816b84"]

    def test_four_module_searches_with_the_runners_and_status_defaults(self) -> None:
        assert len(self.searches) == 4
        assert all(s["node"]["search_type"] == "module" and s["node"]["root"] == "node" for s in self.searches)
        statuses = {}
        for s in self.searches:
            key = s["node"]["definition"]["runner_key"]
            status = s["node"]["input_schema"]["properties"].get("status", {}).get("default")
            statuses[s["entity"]["entity_id"]] = (key, status)
        assert statuses.pop(SUMMARY_SEARCH_ID) == (RUNNER + "dimension-mapping-summary", None)
        assert sorted(statuses.values()) == sorted(
            (RUNNER + "dimension-mapping-entities", st) for st in ("mapped_incorrectly", "unmapped", "mapped")
        )

    def test_the_mappings_default_is_identical_in_all_four_searches(self) -> None:
        """`classification-mapping-2`."""
        mappings = [json.dumps(s["node"]["input_schema"]["properties"]["mappings"]["default"], sort_keys=True) for s in self.searches]
        assert len(set(mappings)) == 1
        assert json.loads(mappings[0])

    def test_the_mapping_covers_the_expected_types_and_stamps_only_what_is_approved(self) -> None:
        rows = self.searches[0]["node"]["input_schema"]["properties"]["mappings"]["default"]
        by_type: dict[str, list[tuple[str, tuple[str, ...]]]] = {}
        for row in rows:
            assert row["match"] in ("all", "any")
            by_type.setdefault(row["entity_type"], []).extend((k["key"], tuple(k["allowed"])) for k in row["keys"])
        assert set(by_type) == {
            "computing_core__application_flow", "computing_core__program", "aws_core__aws_ecs_container",
            "aws_core__aws_rds_instance", "aws_core__aws_s3_bucket", "computing_core__library",
            "computing_core__package",
        }
        assert "computing_core__crypto_provider" not in by_type  # a provider is classified through its carrier (`classification-mapping`)
        assert ("dataclass.action", ("transmit",)) in by_type["computing_core__application_flow"]
        assert by_type["computing_core__program"] == [("dataclass.action", ("process",))]
        assert by_type["aws_core__aws_ecs_container"] == [("dataclass.action", ("process",))]
        assert by_type["aws_core__aws_rds_instance"] == [("dataclass.action", ("store",))]
        assert by_type["aws_core__aws_s3_bucket"] == [("dataclass.action", ("store",))]

    def test_no_entity_id_is_named_in_a_search_other_than_its_own(self) -> None:
        """`classification-mapping-4`: the mapping names types, keys and values, never an entity id."""
        for s in self.searches:
            assert not UUID_RE.search(json.dumps(s["node"]["input_schema"]["properties"]["mappings"]["default"]))
            assert s["node"]["definition"].keys() == {"runner_key"}

    def test_one_hourly_schedule_targets_the_snapshot_collector(self) -> None:
        """`classification-mapping-5`."""
        schedules = [n for n in self.nodes if n["entity"]["entity_type"] == "schedule"]
        assert len(schedules) == 1
        node = schedules[0]["node"]
        assert node["enabled"] is True and node["cron_expression"] == "0 * * * *" and node["max_active_runs"] == 1
        targets = [e["edge"] for e in self.edges if e["edge"]["edge_type"] == "SCHEDULED_TARGET"]
        assert len(targets) == 1
        assert targets[0]["from_entity_id"] == schedules[0]["entity"]["entity_id"]
        assert targets[0]["to_entity_id"] == COLLECTOR_ID

    def test_the_summary_headings_and_its_numbers_centred(self) -> None:
        """`page-data-classification-11`."""
        columns = self.panels["playground-classification-mapping-summary"]["node"]["config"]["columns"]
        assert [c["title"] for c in columns] == [
            "Entity Type", "Classification", "Total", "Mapped", "Unmapped", "Incorrect", "%",
        ]
        numeric = [c for c in columns if c["field"] in {"denominator", "mapped", "unmapped", "mapped_incorrectly", "percent_mapped"}]
        assert len(numeric) == 5 and all(c["align"] == "center" for c in numeric)

    def test_the_collector_id_is_derived_from_its_scope_and_key(self) -> None:
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "tap_cares.collector")
        assert str(uuid.uuid5(namespace, "fedramp_20x_vdr:coverage_snapshot")) == COLLECTOR_ID

    def test_the_bundle_holds_no_page_and_four_table_panels(self) -> None:
        assert not [n for n in self.nodes if n["entity"]["entity_type"] == "page"]
        assert not [e for e in self.edges if e["edge"]["edge_type"] == "USES_PANEL"]
        assert [p["node"]["name"] for p in self.panels.values()] == ["Summary", "Mapped Incorrectly", "Unmapped", "Mapped"]
        assert all(p["node"]["view"] == TABLE for p in self.panels.values())

    def test_each_table_reads_its_own_search_and_names_only_returned_fields(self) -> None:
        """`page-data-classification-10`."""
        expected = {
            "Summary": ("dimension-mapping-summary", SUMMARY_FIELDS, None),
            "Mapped Incorrectly": ("dimension-mapping-entities", ENTITY_FIELDS | {"entity_type"}, "mapped_incorrectly"),
            "Unmapped": ("dimension-mapping-entities", ENTITY_FIELDS | {"entity_type"}, "unmapped"),
            "Mapped": ("dimension-mapping-entities", ENTITY_FIELDS | {"entity_type"}, "mapped"),
        }
        seen_searches = set()
        for panel in self.panels.values():
            if panel["node"]["view"] != TABLE:
                continue
            runner, fields, status = expected[panel["node"]["name"]]
            search = self._search_of(panel)
            seen_searches.add(search["entity"]["entity_id"])
            assert search["node"]["definition"]["runner_key"] == RUNNER + runner
            assert search["node"]["input_schema"]["properties"].get("status", {}).get("default") == status
            named = {c["field"] for c in panel["node"]["config"]["columns"]}
            assert named <= fields, named - fields
        assert seen_searches == {s["entity"]["entity_id"] for s in self.searches}

    def test_tables_are_striped_with_title_case_headings_and_the_entity_tables_link_filter_and_page(self) -> None:
        """`page-data-classification-10`."""
        for panel in self.panels.values():
            if panel["node"]["view"] != TABLE:
                continue
            config = panel["node"]["config"]
            assert config["striped"] is True
            for column in config["columns"]:
                assert column["title"] == column["title"].title(), column["title"]
                assert "align" not in column or column["align"] == "center"  # the default is left; numbers sit centred
            if panel["node"]["name"] == "Summary":
                continue
            assert config["quick_filter"] is True and config["default_page_size"] >= 1
            assert config["row_url_template"].startswith("/object/{entity_type}/")
            link = next(c for c in config["columns"] if c["field"] == "name")
            assert link["formatter"] == "link" and link["formatter_params"]["href_template"] == config["row_url_template"]

    def test_no_panel_carries_prose(self) -> None:
        """`page-data-classification-10`."""
        for panel in self.panels.values():
            assert "text" not in panel["node"]["config"] or panel["node"]["config"]["text"] == ""

    def test_ids_are_unique_version_7_uuids_except_the_fixed_summary_id(self) -> None:
        ids = [self.batch["batch_entity"]["entity_id"]]
        ids += [n["entity"]["entity_id"] for n in self.nodes] + [e["entity"]["entity_id"] for e in self.edges]
        assert len(ids) == len(set(ids))
        # The summary Search's id is the one collector-named id; it is version 7 too.
        assert all(uuid.UUID(i).version == 7 for i in ids)
        other: set[str] = set()
        for path in GRIFT.glob("*.grift.json"):
            if path.name == FILE:
                continue
            for batch in json.loads(path.read_text(encoding="utf-8"))["batches"]:
                other.add(batch["batch_entity"]["entity_id"])
                other |= {n["entity"]["entity_id"] for n in batch["nodes"] if "entity_id" in n["entity"]}
                other |= {e["entity"]["entity_id"] for e in batch["edges"] if "entity_id" in e["entity"]}
        assert not other & set(ids)
