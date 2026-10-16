"""The vulnerabilities page, read from the bundle as written (`req-rampart-20x-playground-page-vulnerabilities-*`).

These tests read the JSON file only, so they hold what the bundle declares, not what a grid returns. How many
rows each table shows and whether the tool sections match the tools on the grid is checked in the browser."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
FILE = "vulnerabilities-page.grift.json"
# The panel slot of each table, in page order: the open alerts by source, Dependabot first, then the closed alerts.
OPEN_SLOTS = ["dependabot", "trivy", "grype", "sonarcloud", "codeql"]
CLOSED_SLOTS = ["closed-dependabot", "closed-code-scanning"]
SLOTS = OPEN_SLOTS + CLOSED_SLOTS
TOOLS = {"trivy": "Trivy", "grype": "Grype", "sonarcloud": "SonarCloud", "codeql": "CodeQL"}
# Fields the alert models hold (github_core__dependabot_alert, github_core__code_scanning_alert).
DEPENDABOT_FIELDS = {
    "data.package_name", "data.ecosystem", "data.severity", "data.state", "data.advisory_summary", "data.ghsa_id",
    "data.first_patched_version", "data.manifest_path", "data.created_at", "data.fixed_at", "data.html_url",
    "data.dismissed_reason", "data.dismissed_comment", "data.dismissed_at",
}
CODE_SCANNING_FIELDS = {
    "data.tool_name", "data.rule_id", "data.security_severity_level", "data.state", "data.location.path",
    "data.location.start_line", "data.number", "data.created_at", "data.fixed_at", "data.dismissed_at",
    "data.html_url", "data.dismissed_reason", "data.dismissed_comment",
}


def _bundle() -> dict:
    return json.loads((GRIFT / FILE).read_text(encoding="utf-8"))


class TestVulnerabilitiesPage:
    def setup_method(self) -> None:
        batch = _bundle()["batches"][0]
        self.batch = batch
        self.nodes = batch["nodes"]
        self.edges = batch["edges"]
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}

    def _of(self, entity_type: str) -> list[dict]:
        return [n for n in self.nodes if n["entity"]["entity_type"] == entity_type]

    def _tables(self) -> list[dict]:
        """The seven raw alert tables of the detail page; the story page's cards and charts are not tables."""
        return [p for p in self._of("panel") if p["node"]["view"] == "tap_web/panels/table_panel.html"]

    def _search_of(self, panel: dict) -> dict:
        links = [
            e for e in self.edges
            if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]
        ]
        assert len(links) == 1, panel["entity"]["name"]
        return self.by_id[links[0]["edge"]["to_entity_id"]]

    def _panel_in_slot(self, slot: str) -> dict:
        edge = next(
            e for e in self.edges
            if e["edge"]["edge_type"] == "USES_PANEL" and e["edge"]["properties"]["hotlink"]["value"] == slot
        )
        return self.by_id[edge["edge"]["to_entity_id"]]

    def test_route_and_title(self) -> None:
        pages = {p["node"]["slug"]: p["node"]["name"] for p in self._of("page")}
        assert pages == {
            "/playground/vulnerabilities": "Vulnerabilities",
            "/playground/vulnerabilities/detail": "Vulnerability detail",
        }

    def test_open_sections_by_source_then_the_closed_pair(self) -> None:
        (page,) = [p for p in self._of("page") if p["node"]["slug"].endswith("/detail")]
        rows = page["node"]["layout"]["columns"]["col-1"]["rows"]
        assert [rows[k]["panel-id"] for k in sorted(rows, key=lambda r: int(r.split("-")[1]))] == SLOTS
        hotlinks = [
            e["edge"]["properties"]["hotlink"]["value"]
            for e in self.edges
            if e["edge"]["edge_type"] == "USES_PANEL" and e["edge"]["from_entity_id"] == page["entity"]["entity_id"]
        ]
        assert sorted(hotlinks) == sorted(SLOTS)

    def test_each_panel_is_a_standard_table_with_one_search(self) -> None:
        panels = self._tables()
        assert len(panels) == len(SLOTS)
        for panel in panels:
            assert self._search_of(panel)["entity"]["entity_type"] == "search"

    def test_dependabot_search_reads_the_dependabot_alerts(self) -> None:
        query = self._search_of(self._panel_in_slot("dependabot"))["node"]["definition"]["query"]
        assert query[0] == "MATCH (n:github_core__dependabot_alert)"
        assert [line for line in query if line.startswith("WHERE")] == ['WHERE n.data.state = "open"']

    def test_each_tool_search_selects_its_tool_so_no_alert_is_in_two_sections(self) -> None:
        seen = []
        for slot, tool in TOOLS.items():
            query = self._search_of(self._panel_in_slot(slot))["node"]["definition"]["query"]
            assert query[0] == "MATCH (n:github_core__code_scanning_alert)"
            assert f'WHERE n.data.tool_name = "{tool}" AND n.data.state = "open"' in query
            seen.append(tool)
        assert len(seen) == len(set(seen))

    def test_the_open_searches_select_open_alerts_only(self) -> None:
        for slot in OPEN_SLOTS:
            query = " ".join(self._search_of(self._panel_in_slot(slot))["node"]["definition"]["query"])
            assert 'n.data.state = "open"' in query, slot

    def test_the_closed_searches_select_every_alert_that_is_not_open_and_name_no_tool(self) -> None:
        for slot, model in (("closed-dependabot", "dependabot_alert"), ("closed-code-scanning", "code_scanning_alert")):
            query = self._search_of(self._panel_in_slot(slot))["node"]["definition"]["query"]
            assert query[0] == f"MATCH (n:github_core__{model})"
            assert 'WHERE n.data.state != "open"' in query
            assert "tool_name" not in " ".join(query), slot

    def test_the_closed_tables_show_the_dismissal_reason_and_comment_as_recorded(self) -> None:
        for slot in CLOSED_SLOTS:
            fields = {c["field"] for c in self._panel_in_slot(slot)["node"]["config"]["columns"]}
            assert {"data.dismissed_reason", "data.dismissed_comment"} <= fields, slot

    def test_the_closed_code_scanning_table_shows_the_tool_as_a_column(self) -> None:
        fields = {c["field"] for c in self._panel_in_slot("closed-code-scanning")["node"]["config"]["columns"]}
        assert "data.tool_name" in fields

    def test_every_open_panel_opens_sorted_by_severity_rank(self) -> None:
        for slot in OPEN_SLOTS:
            panel = self._panel_in_slot(slot)
            config = panel["node"]["config"]
            severity = [c for c in config["columns"] if c["title"] == "Severity"]
            assert len(severity) == 1 and severity[0]["sorter"] == "severityRank", panel["entity"]["name"]
            assert config["initial_sort"] == [{"field": severity[0]["field"], "dir": "desc"}], panel["entity"]["name"]

    def test_every_closed_panel_has_a_severity_column_that_sorts_by_rank_and_opens_newest_first(self) -> None:
        for slot in CLOSED_SLOTS:
            config = self._panel_in_slot(slot)["node"]["config"]
            severity = [c for c in config["columns"] if c["title"] == "Severity"]
            assert len(severity) == 1 and severity[0]["sorter"] == "severityRank", slot
            assert config["initial_sort"] == [{"field": "data.created_at", "dir": "desc"}], slot

    def test_every_search_orders_newest_first(self) -> None:
        for panel in self._tables():
            assert self._search_of(panel)["node"]["definition"]["query"][-1] == "ORDER BY n.data.created_at DESC"

    def test_columns_read_fields_the_alert_models_hold(self) -> None:
        for slot in SLOTS:
            fields = {c["field"] for c in self._panel_in_slot(slot)["node"]["config"]["columns"]}
            href = {
                c["formatter_params"]["href_field"]
                for c in self._panel_in_slot(slot)["node"]["config"]["columns"]
                if c.get("formatter") == "link"
            }
            allowed = DEPENDABOT_FIELDS if slot in ("dependabot", "closed-dependabot") else CODE_SCANNING_FIELDS
            assert fields | href <= allowed, (slot, sorted((fields | href) - allowed))

    def test_every_column_explains_itself(self) -> None:
        for panel in self._tables():
            for column in panel["node"]["config"]["columns"]:
                assert column["header_tooltip"], (panel["entity"]["name"], column["field"])

    def test_names_follow_the_playground_pattern(self) -> None:
        for slot in SLOTS:
            panel = self._panel_in_slot(slot)
            assert panel["node"]["slug"] == f"playground-vulnerabilities-{slot}"
            assert self._search_of(panel)["entity"]["name"] == f"playground — vulnerabilities {slot}"

    def test_nothing_is_stamped_mock_or_called_mock(self) -> None:
        """The data is observed: no `dcom` value anywhere and no mock framing in any name or description."""
        for node in self.nodes:
            assert "dcom" not in node["entity"]["dimensions"], node["entity"]["name"]
        assert "mock" not in json.dumps(self.nodes).lower()

    def test_new_ids_are_unique_version_7_uuids(self) -> None:
        ids = [self.batch["batch_entity"]["entity_id"]]
        ids += [n["entity"]["entity_id"] for n in self.nodes]
        ids += [e["entity"]["entity_id"] for e in self.edges]
        assert len(ids) == len(set(ids))
        assert all(uuid.UUID(i).version == 7 for i in ids)
        other = set()
        for path in GRIFT.glob("*.grift.json"):
            if path.name == FILE:
                continue
            for batch in json.loads(path.read_text(encoding="utf-8"))["batches"]:
                other.add(batch["batch_entity"]["entity_id"])
                other |= {n["entity"]["entity_id"] for n in batch["nodes"] if "entity_id" in n["entity"]}
                other |= {e["entity"]["entity_id"] for e in batch["edges"] if "entity_id" in e["entity"]}
        assert not other & set(ids)


STORY_VIEWS = {
    "tap_web/panels/chart.html", "tap_web/panels/stat_card_panel.html", "tap_web/panels/text_panel.html",
}


class TestVulnerabilityStory:
    """The story page: lanes of cards and charts over the compliance_core nodes, and nothing hardcoded."""

    def setup_method(self) -> None:
        batch = _bundle()["batches"][0]
        self.nodes = batch["nodes"]
        self.edges = batch["edges"]
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}
        (self.page,) = [n for n in self.nodes if n["entity"]["entity_type"] == "page"
                        and n["node"]["slug"] == "/playground/vulnerabilities"]
        self.panels = [n for n in self.nodes if n["entity"]["entity_type"] == "panel" and n["node"]["view"] in STORY_VIEWS]

    def _search_of(self, panel: dict) -> dict | None:
        links = [e for e in self.edges if e["edge"]["edge_type"] == "USES_SEARCH"
                 and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]]
        return self.by_id[links[0]["edge"]["to_entity_id"]] if links else None

    def test_three_lanes_each_slot_wired_to_one_panel(self) -> None:
        columns = self.page["node"]["layout"]["columns"]
        assert sorted(columns) == ["col-1", "col-2", "col-3"]
        slots = [row["panel-id"] for col in columns.values() for row in col["rows"].values()]
        assert len(slots) == len(set(slots))
        hotlinks = [e["edge"]["properties"]["hotlink"]["value"] for e in self.edges
                    if e["edge"]["edge_type"] == "USES_PANEL" and e["edge"]["from_entity_id"] == self.page["entity"]["entity_id"]]
        assert sorted(hotlinks) == sorted(slots)
        assert {p["node"]["slug"] for p in self.panels} == set(slots)

    def test_every_lane_opens_with_a_text_panel_then_a_card(self) -> None:
        by_slug = {p["node"]["slug"]: p for p in self.panels}
        for col in self.page["node"]["layout"]["columns"].values():
            first, second = (col["rows"][k]["panel-id"] for k in ("row-1", "row-2"))
            assert by_slug[first]["node"]["view"] == "tap_web/panels/text_panel.html"
            assert by_slug[second]["node"]["view"] == "tap_web/panels/stat_card_panel.html"

    def test_cards_and_charts_read_a_search_and_text_panels_do_not(self) -> None:
        for panel in self.panels:
            search = self._search_of(panel)
            assert (search is None) == (panel["node"]["view"] == "tap_web/panels/text_panel.html"), panel["entity"]["name"]

    def test_no_search_names_a_scanner_or_a_node_id(self) -> None:
        """Tools are nodes: the Searches reach scanners by edge, and the page never says which tool."""
        for panel in self.panels:
            search = self._search_of(panel)
            if search is None:
                continue
            text = " ".join(search["node"]["definition"]["query"])
            for tool in ("Trivy", "Grype", "SonarCloud", "CodeQL", "Dependabot"):
                assert tool not in text, (panel["entity"]["name"], tool)
            assert "entity_id =" not in text, panel["entity"]["name"]

    def test_searches_use_the_standard_vocabulary_only(self) -> None:
        allowed = {"compliance_core__", "computing_core__"}
        for panel in self.panels:
            search = self._search_of(panel)
            if search is None:
                continue
            types = {t for line in search["node"]["definition"]["query"] for t in
                     __import__("re").findall(r"[:\[]([a-z_]+__[A-Za-z_]+)", line)}
            assert types and all(any(t.startswith(a) for a in allowed) for t in types), (panel["entity"]["name"], types)

    def test_config_fields_are_row_aliases_the_search_returns(self) -> None:
        import re

        for panel in self.panels:
            search = self._search_of(panel)
            if search is None:
                continue
            returned = set(re.findall(r" AS (\w+)", " ".join(search["node"]["definition"]["query"])))
            config = panel["node"]["config"]
            used: set[str] = set()
            if panel["node"]["view"].endswith("stat_card_panel.html"):
                used |= {config["value_field"]} | {line["field"] for line in config.get("lines", [])}
            else:
                series = config["option"]["series"][0]
                used |= {v for k, v in series.get("encode", {}).items() if isinstance(v, str)}
                for v in series.get("encode", {}).values():
                    if isinstance(v, list):
                        used |= set(v)
                if "series_by" in config:
                    used |= {config["series_by"][k] for k in ("category", "series", "value")}
                if "hierarchy" in config:
                    used |= set(config["hierarchy"]["path"]) | {config["hierarchy"]["value"]}
            assert used <= returned, (panel["entity"]["name"], sorted(used - returned))

    def test_every_chart_describes_itself_and_says_what_an_empty_result_means(self) -> None:
        for panel in self.panels:
            if panel["node"]["view"] != "tap_web/panels/chart.html":
                continue
            config = panel["node"]["config"]
            assert config.get("aria_label") and config.get("empty_text"), panel["entity"]["name"]

    def test_the_story_is_observed_data_not_framed_as_mock(self) -> None:
        for node in self.nodes:
            assert "dcom" not in node["entity"]["dimensions"], node["entity"]["name"]
