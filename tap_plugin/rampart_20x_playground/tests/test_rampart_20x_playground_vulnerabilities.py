"""The vulnerabilities pages, read from the bundle as written (`req-rampart-20x-playground-page-vulnerabilities-*`).

These tests read the JSON file only, so they hold what the bundle declares, not what a grid returns. What the
Searches return, and how the pages look, is checked against a booted stack in a browser."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
FILE = "vulnerabilities-page.grift.json"
OVERVIEW = "/playground/vulnerabilities"
VULNERABILITY = "/playground/vulnerabilities/vulnerability"
COMPONENT = "/playground/vulnerabilities/component"
CVE = "/playground/vulnerabilities/cve"
MOSAIC = "vuln_mosaic/panels/cve.html"
CARD = "tap_web/panels/stat_card_panel.html"
CHART = "tap_web/panels/chart.html"
TABLE = "tap_web/panels/table_panel.html"
# Plugins whose node types the Searches may name; no Search names a scanner, a tool or a node id.
VOCABULARY = ("compliance_core__", "computing_core__", "github_core__")
SCANNERS = ("Trivy", "Grype", "SonarCloud", "CodeQL", "Dependabot")
# The two tables are `module` Searches (compliance_core v0.8.0 runners): Gryphon has no group-concat and no
# conditional counts. The fields below are the rows those runners return (req-compliance-core-searches).
RUNNER_PREFIX = "tap_plugin.compliance_core.searches.cross_tabs:"
RUNNER_ROWS = {
    "vulnerability-components": {"id", "title", "cvss", "kev", "published", "components", "component_names", "component_items"},
    "component-severity": {"cid", "component", "type", "high", "medium", "low", "unscored", "kev", "total"},
}


def _bundle() -> dict:
    return json.loads((GRIFT / FILE).read_text(encoding="utf-8"))


class TestVulnerabilityPages:
    def setup_method(self) -> None:
        batch = _bundle()["batches"][0]
        self.batch = batch
        self.nodes = batch["nodes"]
        self.edges = batch["edges"]
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}
        self.pages = {n["node"]["slug"]: n for n in self.nodes if n["entity"]["entity_type"] == "page"}
        every = [n for n in self.nodes if n["entity"]["entity_type"] == "panel"]
        # the CVE record panel belongs to vuln-mosaic and reads no Search; every other panel reads exactly one
        self.mosaic = [p for p in every if p["node"]["view"] == MOSAIC]
        self.panels = [p for p in every if p["node"]["view"] != MOSAIC]
        self.by_slug = {p["node"]["slug"]: p for p in every}

    def _search_of(self, panel: dict) -> dict:
        links = [
            e for e in self.edges
            if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]
        ]
        assert len(links) == 1, panel["entity"]["name"]
        return self.by_id[links[0]["edge"]["to_entity_id"]]

    def _is_module(self, panel: dict) -> bool:
        return self._search_of(panel)["node"]["search_type"] == "module"

    def _query(self, panel: dict) -> str:
        definition = self._search_of(panel)["node"]["definition"]
        return definition["runner_key"] if "runner_key" in definition else " ".join(definition["query"])

    def _returned(self, panel: dict) -> set[str]:
        if self._is_module(panel):
            return RUNNER_ROWS[self._query(panel).removeprefix(RUNNER_PREFIX)]
        return set(re.findall(r" AS (\w+)", self._query(panel)))

    def _bands(self, slug: str) -> dict[int, list[dict]]:
        bands: dict[int, list[dict]] = {}
        columns = self.pages[slug]["node"]["layout"]["columns"]
        for key in sorted(columns, key=lambda k: int(k.split("-")[1])):
            bands.setdefault(columns[key]["band"], []).append(columns[key])
        return bands

    def _slots(self, slug: str) -> list[str]:
        return [row["panel-id"] for col in self.pages[slug]["node"]["layout"]["columns"].values() for row in col["rows"].values()]

    def _of(self, band: list[dict]) -> list[list[dict]]:
        return [[self.by_slug[row["panel-id"]] for row in col["rows"].values()] for col in band]

    # -- every page ------------------------------------------------------------------------------------------

    def test_the_overview_and_its_two_drill_in_pages_exist(self) -> None:
        assert set(self.pages) == {OVERVIEW, VULNERABILITY, COMPONENT, CVE}

    def test_each_slot_is_wired_to_exactly_one_panel_and_each_panel_to_one_slot(self) -> None:
        for slug, page in self.pages.items():
            slots = self._slots(slug)
            assert len(slots) == len(set(slots)), slug
            hotlinks = [
                e["edge"]["properties"]["hotlink"]["value"] for e in self.edges
                if e["edge"]["edge_type"] == "USES_PANEL" and e["edge"]["from_entity_id"] == page["entity"]["entity_id"]
            ]
            assert sorted(hotlinks) == sorted(slots), slug
            assert all(s in self.by_slug for s in slots), slug
        every = [s for slug in self.pages for s in self._slots(slug)]
        assert sorted(every) == sorted(self.by_slug)

    def test_bands_are_numbered_from_one_without_gaps(self) -> None:
        for slug in self.pages:
            assert sorted(self._bands(slug)) == list(range(1, len(self._bands(slug)) + 1)), slug

    def test_every_panel_reads_one_search(self) -> None:
        for panel in self.panels:
            self._search_of(panel)

    def test_no_search_names_a_scanner_a_vulnerability_or_a_node_id(self) -> None:
        """Tools and vulnerabilities are nodes: the Searches reach them by edge or by a parameter, never by value."""
        for panel in self.panels:
            text = self._query(panel)
            for tool in SCANNERS:
                assert tool not in text, (panel["entity"]["name"], tool)
            assert not re.search(r"CVE-\d", text), panel["entity"]["name"]
            assert not re.search(r"entity_id\s*=\s*\"", text), panel["entity"]["name"]

    def test_searches_use_the_standard_vocabulary_only(self) -> None:
        for panel in self.panels:
            if self._is_module(panel):
                continue
            types = set(re.findall(r"[:\[]([a-z_]+__[A-Za-z_]+)", self._query(panel)))
            assert types and all(t.startswith(VOCABULARY) for t in types), (panel["entity"]["name"], types)

    def test_a_search_that_takes_a_parameter_declares_it(self) -> None:
        for panel in self.panels:
            if self._is_module(panel):
                continue  # a runner reads its inputs in code; its schema is checked in the module-search test
            search = self._search_of(panel)["node"]
            used = set(re.findall(r"\$(\w+)", self._query(panel)))
            declared = set(search.get("input_schema", {}).get("properties", {}))
            assert used == declared, (panel["entity"]["name"], used, declared)
            if used:
                assert set(search["input_schema"]["required"]) == used, panel["entity"]["name"]

    def test_table_columns_and_row_links_name_aliases_the_search_returns(self) -> None:
        for panel in self.panels:
            if panel["node"]["view"] != TABLE:
                continue
            config, returned = panel["node"]["config"], self._returned(panel)
            assert {c["field"] for c in config["columns"]} <= returned, panel["entity"]["name"]
            if "row_url_template" in config:
                assert set(re.findall(r"\{(\w+)\}", config["row_url_template"])) <= returned, panel["entity"]["name"]
            for column in config["columns"]:
                if column.get("formatter") == "linkList":
                    continue  # its placeholders are the keys of each list item, checked in the linkList test
                template = column.get("formatter_params", {}).get("href_template", "")
                assert set(re.findall(r"\{(\w+)\}", template)) <= returned, (panel["entity"]["name"], column["field"])

    def test_every_column_explains_itself_or_says_what_it_is_by_its_title(self) -> None:
        for panel in self.panels:
            if panel["node"]["view"] != TABLE:
                continue
            for column in panel["node"]["config"]["columns"]:
                assert column["title"].strip(), (panel["entity"]["name"], column["field"])

    def test_row_links_land_on_the_drill_in_pages(self) -> None:
        links = {
            panel["node"]["slug"]: panel["node"]["config"]["row_url_template"]
            for panel in self.panels if "row_url_template" in panel["node"].get("config", {})
        }
        assert links
        for slug, link in links.items():
            assert link.startswith((VULNERABILITY + "?vuln_id=", COMPONENT + "?component_id=")), slug

    def test_the_drill_in_pages_are_hidden_from_navigation_and_the_overview_is_not(self) -> None:
        for slug in (VULNERABILITY, COMPONENT, CVE):
            assert self.pages[slug]["node"]["discoverable"] is False, slug
        assert "discoverable" not in self.pages[OVERVIEW]["node"]

    # -- the overview ----------------------------------------------------------------------------------------

    def test_the_overview_has_a_band_of_three_columns_then_one_band_of_tables(self) -> None:
        bands = self._bands(OVERVIEW)
        assert sorted(bands) == [1, 2]
        assert [c["width"] for c in bands[1]] == ["4fr", "4fr", "4fr"]
        assert len(bands[2]) == 1 and bands[2][0]["width"] == "12fr"
        assert all(p["node"]["view"] == TABLE for p in self._of(bands[2])[0])

    def test_each_column_is_a_card_over_a_chart_so_the_card_is_as_wide_as_the_column(self) -> None:
        for column in self._of(self._bands(OVERVIEW)[1]):
            assert [p["node"]["view"] for p in column] == [CARD, CHART]

    def test_the_cards_run_kev_then_open_then_closed(self) -> None:
        first_row = [col["rows"]["row-1"]["panel-id"] for col in self._bands(OVERVIEW)[1]]
        assert first_row == [f"playground-vulnerabilities-{s}" for s in ("kev", "open", "closed")]

    def test_the_cards_draw_their_text_in_the_tone_and_kev_greys_out_at_zero(self) -> None:
        tones = {"kev": "bad", "open": "warn", "closed": "good"}
        for slot, tone in tones.items():
            config = self.by_slug[f"playground-vulnerabilities-{slot}"]["node"]["config"]
            assert config["tone"] == tone and config["tone_text"] is True, slot
        assert self.by_slug["playground-vulnerabilities-kev"]["node"]["config"]["zero_tone"] == "muted"

    def test_the_cards_say_a_number_and_nothing_else(self) -> None:
        """No unit, no secondary lines, no tone words and no header or description: the figure and the tone's left edge."""
        cards = [p for p in self.panels if p["node"]["view"] == CARD]
        assert len(cards) == 3
        for card in cards:
            config = card["node"]["config"]
            assert config["hide_header"] is True and config["title"], card["entity"]["name"]
            assert "unit" not in config and "lines" not in config, card["entity"]["name"]
            assert set(config["tone_labels"].values()) == {""}, card["entity"]["name"]

    def test_the_three_charts_share_one_height_and_the_score_chart_prints_its_numbers(self) -> None:
        charts = [p for p in self.panels if p["node"]["view"] == CHART]
        assert len(charts) == 3
        assert len({c["node"]["config"]["height"] for c in charts}) == 1
        score = self.by_slug["playground-vulnerabilities-cvss"]["node"]["config"]["option"]["series"][0]
        assert score["label"]["show"] is True

    def test_every_chart_describes_itself_and_says_what_an_empty_result_means(self) -> None:
        for panel in self.panels:
            if panel["node"]["view"] == CHART:
                config = panel["node"]["config"]
                assert config.get("aria_label") and config.get("empty_text"), panel["entity"]["name"]

    def test_chart_fields_are_row_aliases_the_search_returns(self) -> None:
        for panel in self.panels:
            if panel["node"]["view"] != CHART:
                continue
            series = panel["node"]["config"]["option"]["series"][0]
            used = {v for v in series.get("encode", {}).values() if isinstance(v, str)}
            for v in series.get("encode", {}).values():
                if isinstance(v, list):
                    used |= set(v)
            assert used <= self._returned(panel), panel["entity"]["name"]

    def test_the_component_and_severity_charts_click_through_to_their_drill_in_pages(self) -> None:
        expect = {
            "playground-vulnerabilities-top-components": COMPONENT + "?component_id={cid}",
            "playground-vulnerabilities-severity-age": VULNERABILITY + "?vuln_id={id}",
        }
        for slug, template in expect.items():
            panel = self.by_slug[slug]
            assert panel["node"]["config"]["click"] == {"row_url_template": template}, slug
            assert set(re.findall(r"\{(\w+)\}", template)) <= self._returned(panel), slug
        others = [p for p in self.panels if p["node"]["view"] == CHART and p["node"]["slug"] not in expect]
        assert all("click" not in p["node"]["config"] for p in others)

    def test_the_two_overview_tables_search_and_page(self) -> None:
        (column,) = self._of(self._bands(OVERVIEW)[2])
        assert len(column) == 2
        for table in column:
            config = table["node"]["config"]
            assert config["quick_filter"] is True and config["default_page_size"] >= 10, table["entity"]["name"]
            assert config["row_url_template"], table["entity"]["name"]

    def test_the_component_table_says_what_kind_of_thing_each_row_is_and_counts_by_band(self) -> None:
        table = self.by_slug["playground-vulnerabilities-open-components"]
        fields = {c["field"] for c in table["node"]["config"]["columns"]}
        assert {"type", "high", "medium", "low", "kev"} <= fields
        assert self._query(table) == RUNNER_PREFIX + "component-severity"

    def test_the_vulnerability_table_lists_its_components_as_links(self) -> None:
        table = self.by_slug["playground-vulnerabilities-open-vulnerabilities"]
        (column,) = [c for c in table["node"]["config"]["columns"] if c["field"] == "component_items"]
        assert column["formatter"] == "linkList"
        params = column["formatter_params"]
        assert params["href_template"] == COMPONENT + "?component_id={id}"
        assert params["label_field"] == "name" and params["external"] is False
        assert set(re.findall(r"\{(\w+)\}", params["href_template"])) | {params["label_field"]} <= {"id", "name", "type"}
        assert self._query(table) == RUNNER_PREFIX + "vulnerability-components"

    def test_a_module_search_records_the_gryphon_capability_it_lacks_and_leaves_out_systems(self) -> None:
        """`req-grid-search-canonical-read-3`: the reason sits in the description; the repository is excluded by an input."""
        modules = [p for p in self.panels if self._is_module(p)]
        assert len(modules) == 2
        for panel in modules:
            search = self._search_of(panel)["node"]
            assert "Gryphon has no" in search["description"] and "missing capability" in search["description"]
            default = search["input_schema"]["properties"]["exclude_types"]["default"]
            assert default == ["github_core__github_repository"]

    def test_the_removed_overview_panels_are_gone(self) -> None:
        for gone in ("exploitation", "tree", "remediation", "found-by", "l1-lede", "l2-lede", "l3-lede"):
            assert f"playground-vulnerabilities-{gone}" not in self.by_slug, gone

    # -- the drill-ins ---------------------------------------------------------------------------------------

    def test_the_vulnerability_page_shows_its_context_its_components_and_its_systems(self) -> None:
        slots = set(self._slots(VULNERABILITY))
        for need in ("vuln-identity", "vuln-description", "vuln-components", "vuln-systems"):
            assert f"playground-vulnerabilities-{need}" in slots, need
        systems = self.by_slug["playground-vulnerabilities-vuln-systems"]
        assert "computing_core__host" in self._query(systems)
        assert "$vuln_id" in self._query(systems)

    def test_the_component_page_lists_the_vulnerabilities_of_one_component(self) -> None:
        slots = set(self._slots(COMPONENT))
        for need in ("component-identity", "component-vulnerabilities", "component-systems"):
            assert f"playground-vulnerabilities-{need}" in slots, need
        assert "$component_id" in self._query(self.by_slug["playground-vulnerabilities-component-vulnerabilities"])

    def test_the_cve_page_is_one_vuln_mosaic_panel_that_writes_nothing(self) -> None:
        (panel,) = self.mosaic
        assert self._slots(CVE) == [panel["node"]["slug"]]
        assert panel["node"]["config"] == {
            "vuln_id_var": "vuln_id", "hide_header": True, "queue_misses": False, "max_references_per_tag": 8,
        }
        assert not [e for e in self.edges if e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]]

    def test_the_vulnerability_page_opens_the_cve_page_by_the_id_it_carries(self) -> None:
        identity = self.by_slug["playground-vulnerabilities-vuln-identity"]
        (column,) = [c for c in identity["node"]["config"]["columns"] if c["field"] == "id"]
        assert column["formatter_params"]["href_template"] == CVE + "?vuln_id={id}"

    def test_vuln_mosaic_is_not_a_dependency_of_the_plugin(self) -> None:
        """vuln-mosaic is a local dev plugin for the demo: no manifest dependency and no pin in a shipped boot record."""
        for path in (PACKAGE_ROOT / "tap-plugin.toml", *(PACKAGE_ROOT / "boot").glob("*.json")):
            assert "vuln_mosaic" not in path.read_text(encoding="utf-8").replace("-", "_"), path.name

    # -- the data is observed --------------------------------------------------------------------------------

    def test_names_follow_the_playground_pattern(self) -> None:
        for panel in self.panels:
            slug = panel["node"]["slug"]
            assert slug.startswith("playground-vulnerabilities-"), slug
            assert self._search_of(panel)["entity"]["name"].startswith("playground — vulnerabilities "), slug

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
