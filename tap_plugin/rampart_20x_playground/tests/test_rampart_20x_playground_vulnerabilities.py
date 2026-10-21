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
SPECS = PACKAGE_ROOT.parents[1] / "specs"
FILE = "vulnerabilities-page.grift.json"
OVERVIEW = "/playground/vulnerabilities"
VULNERABILITY = "/playground/vulnerabilities/vulnerability"
COMPONENT = "/playground/vulnerabilities/component"
CVE = "/playground/vulnerabilities/cve"
MOSAIC = "vuln_mosaic/panels/cve.html"
TEXT = "tap_web/panels/text_panel.html"
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
        # the CVE dashboard panel belongs to vuln-mosaic and the CVE page's section headings are text panels; neither
        # reads a Search, and every other panel reads exactly one
        self.mosaic = [p for p in every if p["node"]["view"] == MOSAIC]
        self.headings = [p for p in every if p["node"]["view"] == TEXT]
        self.panels = [p for p in every if p["node"]["view"] not in (MOSAIC, TEXT)]
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
            assert link.startswith((CVE + "?vuln_id=", COMPONENT + "?component_id=")), slug

    def test_nothing_opens_the_older_vulnerability_page(self) -> None:
        """The CVE page replaces the vulnerability links on the overview and on the component page; the older
        drill-in is reachable by its address only."""
        for slug in self._slots(OVERVIEW) + self._slots(COMPONENT) + self._slots(CVE):
            assert VULNERABILITY not in json.dumps(self.by_slug[slug]["node"]["config"]), slug

    def test_the_drill_in_pages_are_hidden_from_navigation_and_the_overview_is_not(self) -> None:
        for slug in (VULNERABILITY, COMPONENT, CVE):
            assert self.pages[slug]["node"]["discoverable"] is False, slug
        assert "discoverable" not in self.pages[OVERVIEW]["node"]

    # -- the overview ----------------------------------------------------------------------------------------

    def test_the_overview_has_a_row_of_cards_a_row_of_charts_then_one_band_of_tables(self) -> None:
        """req-rampart-20x-playground-page-vulnerabilities-2"""
        bands = self._bands(OVERVIEW)
        assert sorted(bands) == [1, 2, 3]
        assert [c["width"] for c in bands[1]] == ["3fr"] * 4
        assert [c["width"] for c in bands[2]] == ["4fr"] * 3
        assert len(bands[3]) == 1 and bands[3][0]["width"] == "12fr"
        assert all(p["node"]["view"] == TABLE for p in self._of(bands[3])[0])

    def test_each_first_band_column_is_one_card_and_each_second_band_column_one_chart(self) -> None:
        assert [[p["node"]["view"] for p in col] for col in self._of(self._bands(OVERVIEW)[1])] == [[CARD]] * 4
        assert [[p["node"]["view"] for p in col] for col in self._of(self._bands(OVERVIEW)[2])] == [[CHART]] * 3

    def test_the_cards_run_kev_then_open_then_closed_then_cwe506(self) -> None:
        first_row = [col["rows"]["row-1"]["panel-id"] for col in self._bands(OVERVIEW)[1]]
        assert first_row == [f"playground-vulnerabilities-{s}" for s in ("kev", "open", "closed", "cwe506")]

    def test_the_cards_draw_their_text_in_the_tone_and_kev_greys_out_at_zero(self) -> None:
        tones = {"kev": "bad", "open": "warn", "closed": "good", "cwe506": "bad"}
        for slot, tone in tones.items():
            config = self.by_slug[f"playground-vulnerabilities-{slot}"]["node"]["config"]
            assert config["tone"] == tone and config["tone_text"] is True, slot
        assert self.by_slug["playground-vulnerabilities-kev"]["node"]["config"]["zero_tone"] == "muted"
        assert self.by_slug["playground-vulnerabilities-cwe506"]["node"]["config"]["zero_tone"] == "good"

    def test_the_cards_say_a_number_and_nothing_else(self) -> None:
        """No unit, no secondary lines, no tone words and no header or description: the figure and the tone's left edge."""
        cards = [self.by_slug[s] for s in self._slots(OVERVIEW) if self.by_slug[s]["node"]["view"] == CARD]
        assert len(cards) == 4
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
            used: set[str] = set()
            for series in panel["node"]["config"]["option"]["series"]:
                used |= {v for v in series.get("encode", {}).values() if isinstance(v, str)}
                for v in series.get("encode", {}).values():
                    if isinstance(v, list):
                        used |= set(v)
            assert used <= self._returned(panel), panel["entity"]["name"]

    def test_the_component_and_severity_charts_click_through_to_their_drill_in_pages(self) -> None:
        expect = {
            "playground-vulnerabilities-top-components": COMPONENT + "?component_id={cid}",
            "playground-vulnerabilities-severity-age": CVE + "?vuln_id={id}",
        }
        for slug, template in expect.items():
            panel = self.by_slug[slug]
            assert panel["node"]["config"]["click"] == {"row_url_template": template}, slug
            assert set(re.findall(r"\{(\w+)\}", template)) <= self._returned(panel), slug
        others = [p for p in self.panels if p["node"]["view"] == CHART and p["node"]["slug"] not in expect]
        assert all("click" not in p["node"]["config"] for p in others)

    def test_the_most_open_findings_chart_is_stacked_by_cvss_band(self) -> None:
        """req-rampart-20x-playground-page-vulnerabilities-20"""
        panel = self.by_slug["playground-vulnerabilities-top-components"]
        config = panel["node"]["config"]
        series = config["option"]["series"]
        assert [(s["name"], s["encode"]["x"], s["itemStyle"]["color"]) for s in series] == [
            ("High", "high", "#c0392b"), ("Medium", "medium", "#d9a400"), ("Low", "low", "#2f9e6b"),
        ]
        assert {s["stack"] for s in series} == {"findings"} and all(s["type"] == "bar" for s in series)
        assert config["option"]["legend"]["data"] == ["High", "Medium", "Low"]
        assert config["sort"] == {"field": "total", "order": "desc"} and config["limit"] == 10
        assert self._query(panel) == RUNNER_PREFIX + "component-severity"
        assert self.by_slug["playground-vulnerabilities-cvss"]["node"]["config"]["option"]["visualMap"]["pieces"][0]["color"] == "#2f9e6b"

    def test_the_cwe506_card_and_table_read_the_cwe_list(self) -> None:
        """req-rampart-20x-playground-page-vulnerabilities-22"""
        card = self.by_slug["playground-vulnerabilities-cwe506"]
        assert card["node"]["config"]["title"] == "Embedded Malicious Code (CWE-506)"
        assert self._query(card).endswith("RETURN COUNT(v) AS malicious")
        assert 'v.data.cwes CONTAINS "CWE-506"' in self._query(card)
        table = self.by_slug["playground-vulnerabilities-cwe506-components"]
        assert table["node"]["name"] == "Components With Embedded Malicious Code"
        assert table["node"]["config"]["empty_text"] == "No component carries a CWE-506 vulnerability."
        assert 'v.data.cwes CONTAINS "CWE-506"' in self._query(table)
        assert self._search_of(table)["node"]["search_type"] == "gryphon"
        assert self._slots(OVERVIEW)[-1] == "playground-vulnerabilities-cwe506-components"
        assert self.batch["batch_entity"]["name"].endswith("v0.8.0")

    def test_the_bubble_counts_are_white_with_no_outline(self) -> None:
        """req-rampart-20x-playground-page-vulnerabilities-19"""
        label = self.by_slug["playground-vulnerabilities-severity-age"]["node"]["config"]["option"]["series"][0]["label"]
        assert label["color"] == "#ffffff" and label["fontWeight"] == "bold"
        assert label["textBorderWidth"] == 0 and "textBorderColor" not in label

    def test_the_overview_tables_are_striped_with_plain_links(self) -> None:
        """req-rampart-20x-playground-page-vulnerabilities-18"""
        for slug in ("open-vulnerabilities", "open-components", "cwe506-components"):
            config = self.by_slug[f"playground-vulnerabilities-{slug}"]["node"]["config"]
            assert config["striped"] is True, slug
            links = [c for c in config["columns"] if c.get("formatter") in ("link", "linkList")]
            assert links and all(c["formatter_params"]["style"] == "plain" for c in links), slug

    def test_every_name_and_title_is_in_title_case(self) -> None:
        """req-rampart-20x-playground-page-vulnerabilities-17"""
        def title_case(text: str) -> bool:
            words = [w for w in re.split(r"[ -]", text) if w[:1].isalpha()]
            return all(w[0].isupper() for w in words)

        for node in self.nodes:
            if node["entity"]["entity_type"] not in ("panel", "page"):
                continue
            config = node["node"].get("config") or {}
            texts = [node["node"]["name"], config.get("title", "")]
            texts += [c["title"] for c in config.get("columns", [])]
            option = config.get("option", {})
            texts += [option[a]["name"] for a in ("xAxis", "yAxis") if isinstance(option.get(a), dict) and "name" in option[a]]
            for text in texts:
                assert title_case(text), (node["node"]["name"], text)
        names = {p["node"]["name"] for p in self.panels}
        assert {"CVSS Score", "Most Open Findings", "Severity By Age"} <= names

    def test_the_three_overview_tables_search_and_page(self) -> None:
        (column,) = self._of(self._bands(OVERVIEW)[3])
        assert len(column) == 3
        for table in column:
            config = table["node"]["config"]
            assert config["quick_filter"] is True and config["default_page_size"] >= 10, table["entity"]["name"]
            assert config["row_url_template"], table["entity"]["name"]

    def test_the_open_vulnerability_table_opens_the_cve_dashboard_by_row_and_by_id_link(self) -> None:
        config = self.by_slug["playground-vulnerabilities-open-vulnerabilities"]["node"]["config"]
        assert config["row_url_template"] == CVE + "?vuln_id={id}"
        (column,) = [c for c in config["columns"] if c["field"] == "id"]
        assert column["formatter"] == "link"
        assert column["formatter_params"] == {"href_template": CVE + "?vuln_id={id}", "external": False, "style": "plain"}

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
        assert len(modules) == 3
        for panel in modules:
            search = self._search_of(panel)["node"]
            assert "Gryphon has no" in search["description"] and "missing capability" in search["description"]
            default = search["input_schema"]["properties"]["exclude_types"]["default"]
            assert default == ["github_core__github_repository"]

    def test_the_removed_overview_panels_are_gone(self) -> None:
        for gone in ("exploitation", "tree", "remediation", "found-by", "l1-lede", "l2-lede", "l3-lede"):
            assert f"playground-vulnerabilities-{gone}" not in self.by_slug, gone

    # -- the drill-ins ---------------------------------------------------------------------------------------

    def test_the_older_vulnerability_page_keeps_its_two_tables_and_gives_up_the_components_and_systems(self) -> None:
        assert self._slots(VULNERABILITY) == [
            "playground-vulnerabilities-vuln-identity", "playground-vulnerabilities-vuln-description",
        ]
        description = self.pages[VULNERABILITY]["node"]["description"]
        assert "components" not in description.replace("components and systems too", "")
        assert "nothing links here" in description

    def test_the_component_page_lists_the_vulnerabilities_of_one_component(self) -> None:
        slots = set(self._slots(COMPONENT))
        for need in ("component-identity", "component-vulnerabilities", "component-systems"):
            assert f"playground-vulnerabilities-{need}" in slots, need
        assert "$component_id" in self._query(self.by_slug["playground-vulnerabilities-component-vulnerabilities"])

    def test_the_component_page_is_a_hero_over_two_full_width_striped_tables(self) -> None:
        """`req-rampart-20x-playground-page-vulnerabilities-21`."""
        layout = self.pages[COMPONENT]["node"]["layout"]["columns"]
        assert list(layout) == ["col-1"] and layout["col-1"]["width"] == "12fr"
        assert [r["panel-id"] for r in layout["col-1"]["rows"].values()] == [
            "playground-vulnerabilities-component-identity", "playground-vulnerabilities-component-systems",
            "playground-vulnerabilities-component-vulnerabilities"]
        hero = self.by_slug["playground-vulnerabilities-component-identity"]["node"]
        assert hero["view"] == "tap_web/panels/stat_card_panel.html"
        config = hero["config"]
        assert config["layout"] == "figure_right" and config["value_field"] == "vulnerabilities" and config["unit"] == "open findings"
        assert config["title_field"] == "component"
        assert [(line["field"], line.get("placement")) for line in config["lines"]] == [("type", "header"), ("worst", None)]
        for slug in ("component-systems", "component-vulnerabilities"):
            assert self.by_slug[f"playground-vulnerabilities-{slug}"]["node"]["config"]["striped"] is True
        (link,) = [c for c in self.by_slug["playground-vulnerabilities-component-vulnerabilities"]["node"]["config"]["columns"] if c["field"] == "id"]
        assert link["formatter_params"]["style"] == "plain"
        text = (SPECS / "spec-rampart_20x_playground-v0.md").read_text(encoding="utf-8")
        assert "req-rampart-20x-playground-page-vulnerabilities-21" in text and "Backlog, not built" in text

    def test_the_component_page_opens_the_cve_page_by_row_and_by_id_link(self) -> None:
        config = self.by_slug["playground-vulnerabilities-component-vulnerabilities"]["node"]["config"]
        assert config["row_url_template"] == CVE + "?vuln_id={id}"
        (column,) = [c for c in config["columns"] if c["field"] == "id"]
        assert column["formatter_params"] == {"href_template": CVE + "?vuln_id={id}", "external": False, "style": "plain"}

    # -- the CVE page: answer first, then how bad, what it is, where it affects us, details and sources ---------

    def _cve_rows(self) -> list[tuple[int, str, list[str]]]:
        """(band, width, [panel slugs]) per column, in reading order."""
        columns = self.pages[CVE]["node"]["layout"]["columns"]
        ordered = sorted(columns, key=lambda k: int(k.split("-")[1]))
        return [
            (columns[k]["band"], columns[k]["width"], [r["panel-id"] for r in columns[k]["rows"].values()])
            for k in ordered
        ]

    def _stat_fields(self, panel: dict) -> set[str]:
        """Every row field a stat card's config names: figure, title, lines and the field its tone follows."""
        config = panel["node"]["config"]
        fields = {config["value_field"]}
        fields |= {config[k] for k in ("title_field",) if k in config}
        fields |= {line["field"] for line in config.get("lines", [])}
        if isinstance(config.get("tone"), dict):
            fields.add(config["tone"]["field"])
        return fields

    def test_the_cve_page_reads_top_to_bottom_in_nine_bands(self) -> None:
        slug = lambda s: f"playground-vulnerabilities-{s}"  # noqa: E731
        assert self._cve_rows() == [
            (1, "12fr", [slug("cve-headline")]),
            (2, "12fr", [slug("cve-h-urgency")]),
            (3, "6fr", [slug("cve-cvss")]), (3, "5fr", [slug("cve-exploited")]),
            (3, "5fr", [slug("cve-likelihood")]), (3, "5fr", [slug("cve-exposure")]),
            (4, "12fr", [slug("cve-h-what")]),
            (5, "8fr", [slug("cve-description")]), (5, "4fr", [slug("cve-weakness")]),
            (6, "12fr", [slug("cve-h-where")]),
            (7, "7fr", [slug("vuln-components")]), (7, "5fr", [slug("vuln-systems")]),
            (8, "12fr", [slug("cve-h-details")]),
            (9, "12fr", [slug("cve")]),
        ]

    def test_the_cve_page_is_named_cve_and_has_the_vuln_mosaic_panel_last_and_unchanged(self) -> None:
        page = self.pages[CVE]["node"]
        assert page["name"] == "CVE" == self.pages[CVE]["entity"]["name"]
        (panel,) = self.mosaic
        assert self._slots(CVE)[-1] == panel["node"]["slug"]
        # the panel keeps its current config until vuln-mosaic ships a `sections` key (see the spec)
        assert panel["node"]["config"] == {
            "vuln_id_var": "vuln_id", "hide_header": True, "queue_misses": False, "max_references_per_tag": 8,
        }
        assert not [e for e in self.edges if e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]]

    def test_the_cve_page_description_says_what_it_explains_and_where_it_is_opened_from(self) -> None:
        description = self.pages[CVE]["node"]["description"]
        for phrase in ("how bad it scores", "exploited", "what it is", "components and systems", "details and sources",
                       "Vulnerabilities or Component page"):
            assert phrase in description, phrase

    def test_the_section_headings_name_the_bands_they_head_and_say_how_to_read_them(self) -> None:
        names = [h["node"]["name"] for h in self.headings]
        assert sorted(names) == sorted(
            ["How Bad And How Urgent", "What It Is", "Where It Affects Us", "Details And Sources"]
        )
        for heading in self.headings:
            config = heading["node"]["config"]
            assert config["hide_header"] is False
            assert config["text"].endswith(".") and len(config["text"]) > 40, heading["node"]["name"]
            assert not [e for e in self.edges if e["edge"]["from_entity_id"] == heading["entity"]["entity_id"]]
        by_band = {band: slugs for band, _, slugs in self._cve_rows()}
        assert [by_band[b][0] for b in (2, 4, 6, 8)] == [
            h["node"]["slug"] for n in ("How Bad And How Urgent", "What It Is", "Where It Affects Us", "Details And Sources")
            for h in self.headings if h["node"]["name"] == n
        ]

    def test_the_headline_card_puts_the_id_and_the_title_first_with_severity_and_kev_state(self) -> None:
        panel = self.by_slug["playground-vulnerabilities-cve-headline"]
        config = panel["node"]["config"]
        assert panel["node"]["view"] == CARD
        assert config["value_field"] == "id" and config["title_field"] == "title"
        assert {line["field"] for line in config["lines"]} == {"cvss", "version", "scored_by", "published"}
        assert config["tone"]["field"] == "kev" and config["tone_text"] is True
        assert config["tone"]["map"] == {"True": "bad", "true": "bad", "False": "good", "false": "good"}
        assert config["tone_labels"]["bad"].startswith("Actively exploited")
        assert config["tone_labels"]["good"].startswith("Not on the CISA exploited list")
        assert config["tone_labels"]["neutral"]
        assert self._stat_fields(panel) <= self._returned(panel)

    def test_the_four_answer_cards_run_cvss_exploited_likelihood_exposure_with_cvss_the_widest(self) -> None:
        band = [(w, slugs[0]) for b, w, slugs in self._cve_rows() if b == 3]
        assert [s for _, s in band] == [f"playground-vulnerabilities-cve-{s}" for s in ("cvss", "exploited", "likelihood", "exposure")]
        widths = [int(w.removesuffix("fr")) for w, _ in band]
        assert widths[0] > max(widths[1:]) and len(set(widths[1:])) == 1
        for _, slug in band:
            panel = self.by_slug[slug]
            config = panel["node"]["config"]
            assert panel["node"]["view"] == CARD and config["hide_header"] is True and config["tone_text"] is True, slug
            assert config["title"] and config["empty_text"] and config["null_text"] == "not recorded", slug

    def test_every_stat_card_on_the_cve_page_names_only_fields_its_search_returns(self) -> None:
        cards = [self.by_slug[s] for s in self._slots(CVE) if self.by_slug[s]["node"]["view"] == CARD]
        assert len(cards) == 6
        for card in cards:
            assert self._stat_fields(card) <= self._returned(card), card["entity"]["name"]
            assert "$vuln_id" in self._query(card), card["entity"]["name"]

    def test_the_cvss_card_words_and_colours_every_score_by_its_band(self) -> None:
        config = self.by_slug["playground-vulnerabilities-cve-cvss"]["node"]["config"]
        assert config["value_field"] == "cvss" and config["unit"] == "out of 10"
        assert config["tone_labels"] == {"good": "Low", "warn": "Medium", "bad": "High or critical", "neutral": ""}
        tones = config["tone"]["map"]
        for tenth in range(0, 101):
            score = tenth / 10
            expect = "neutral" if tenth == 0 else "good" if tenth < 40 else "warn" if tenth < 70 else "bad"
            assert tones[f"{score:.1f}"] == expect, score
            if tenth % 10 == 0:
                assert tones[str(tenth // 10)] == expect, score
        assert len(tones) == 101 + 11
        assert {"vector", "version", "scored_by"} == {line["field"] for line in config["lines"]}

    def test_the_exploited_card_answers_in_words_and_carries_the_kev_facts(self) -> None:
        config = self.by_slug["playground-vulnerabilities-cve-exploited"]["node"]["config"]
        assert config["tone"]["field"] == "kev"
        assert config["tone_labels"]["bad"].startswith("Yes") and config["tone_labels"]["good"].startswith("No")
        assert config["value_field"] == "due" and config["unit"] == "CISA fix-by date"
        assert [line["field"] for line in config["lines"]] == ["added", "ransomware", "action"]

    def test_the_likelihood_card_shows_epss_and_spells_out_the_ssvc_assessment(self) -> None:
        config = self.by_slug["playground-vulnerabilities-cve-likelihood"]["node"]["config"]
        assert config["value_field"] == "epss" and config["value_formatter"] == "number"
        assert config["tone"]["map"] == {"none": "good", "poc": "warn", "active": "bad"}
        assert all(label.startswith("CISA SSVC") for k, label in config["tone_labels"].items() if label)
        fields = [line["field"] for line in config["lines"]]
        assert fields == ["percentile", "as_of", "exploitation", "automatable", "impact"]
        percentile = config["lines"][0]["label"]
        assert "0.31" in percentile and "higher than 31% of vulnerabilities" in percentile

    def test_the_exposure_card_counts_open_findings_on_components_and_goes_green_at_zero(self) -> None:
        panel = self.by_slug["playground-vulnerabilities-cve-exposure"]
        config = panel["node"]["config"]
        assert (config["tone"], config["zero_tone"]) == ("warn", "good")
        assert config["value_formatter"] == "integer" and config["unit"] == "open findings"
        query = self._query(panel)
        assert 'f.data.status = "open"' in query and "COUNT(f) AS findings" in query
        assert 'c.entity_type != "github_core__github_repository"' in query

    def test_the_description_is_whole_in_a_card_line_not_a_clipped_table_cell(self) -> None:
        panel = self.by_slug["playground-vulnerabilities-cve-description"]
        assert panel["node"]["view"] == CARD
        assert {"label": "Description", "field": "description"} in panel["node"]["config"]["lines"]
        assert "description" in self._returned(panel)
        assert "SUBSTRING" not in self._query(panel).upper() and "LEFT(" not in self._query(panel).upper()
        assert panel["node"]["config"]["value_field"] == "published"
        assert panel["node"]["config"]["value_formatter"] == "age"

    def test_the_weakness_types_are_a_one_row_list_cell(self) -> None:
        panel = self.by_slug["playground-vulnerabilities-cve-weakness"]
        config = panel["node"]["config"]
        assert panel["node"]["view"] == TABLE and config["chrome"] == "minimal"
        (column,) = config["columns"]
        assert column["field"] == "cwes" and column["formatter"] == "linkList"
        assert "cwes" in self._returned(panel)

    def test_the_components_and_systems_tables_moved_to_the_cve_page_with_their_searches_unchanged(self) -> None:
        slots = set(self._slots(CVE))
        assert {"playground-vulnerabilities-vuln-components", "playground-vulnerabilities-vuln-systems"} <= slots
        components = self.by_slug["playground-vulnerabilities-vuln-components"]
        systems = self.by_slug["playground-vulnerabilities-vuln-systems"]
        assert "$vuln_id" in self._query(components) and "$vuln_id" in self._query(systems)
        assert "computing_core__host" in self._query(systems)
        assert components["node"]["config"]["row_url_template"] == COMPONENT + "?component_id={cid}"
        assert {c["field"] for c in components["node"]["config"]["columns"]} == {"component", "type", "status", "findings"}
        assert {c["field"] for c in systems["node"]["config"]["columns"]} == {"system", "packages"}

    def test_the_vulnerability_page_opens_the_cve_page_by_the_id_it_carries(self) -> None:
        identity = self.by_slug["playground-vulnerabilities-vuln-identity"]
        (column,) = [c for c in identity["node"]["config"]["columns"] if c["field"] == "id"]
        assert column["formatter_params"]["href_template"] == CVE + "?vuln_id={id}"

    def test_vuln_mosaic_is_in_the_demo_record_and_not_a_dependency_of_the_plugin(self) -> None:
        """`req-rampart-20x-playground-boot-6`: the demo installs vuln_mosaic and seeds its schedule before this plugin; the manifest and the ci record do not name it."""
        manifest = (PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8").replace("-", "_")
        assert 'slug = "vuln_mosaic"' not in manifest
        assert "vuln_mosaic" not in (PACKAGE_ROOT / "boot" / "ci.boot.json").read_text(encoding="utf-8").replace("-", "_")
        demo = json.loads((PACKAGE_ROOT / "boot" / "demo.boot.json").read_text(encoding="utf-8"))
        (entry,) = [p for p in demo["install"]["plugins"] if p["slug"] == "vuln_mosaic"]
        assert entry["source"]["rev"] == "v0.6.0"
        assert entry["source"]["commit"] == "b0ae7728c41004aa885aac974654a16e8a13fb6a"
        steps = [(s["plugin"], s.get("bundle")) for s in demo["population"]["steps"]]
        assert ("vuln_mosaic", None) in steps
        assert steps.index(("vuln_mosaic", None)) < steps.index(("rampart_20x_playground", None))

    def test_the_demo_runs_the_ksi_catalog_hourly_and_its_description_says_what_runs(self) -> None:
        """`req-rampart-20x-playground-boot-7`: fedramp_20x_ksi v0.4.2 with its schedule bundle seeded; the description no longer claims that no collector runs."""
        demo = json.loads((PACKAGE_ROOT / "boot" / "demo.boot.json").read_text(encoding="utf-8"))
        (ksi,) = [p for p in demo["install"]["plugins"] if p["slug"] == "fedramp_20x_ksi"]
        assert (ksi["source"]["rev"], ksi["source"]["commit"]) == ("v0.4.2", "5069b9d53b002a7f0626fad377f3abea0b193df6")
        steps = [(s["plugin"], s.get("bundle")) for s in demo["population"]["steps"]]
        assert steps.index(("fedramp_20x_ksi", "ksi_schedule")) < steps.index(("rampart_20x_playground", None))
        assert "No collector runs" not in demo["description"]
        for host in ("raw.githubusercontent.com", "www.cisa.gov", "epss.empiricalsecurity.com"):
            assert host in demo["description"]

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


class TestStatCardTextLimits:
    """The core stat-card schema caps `unit` and each `tone_labels` entry at 40 characters, `null_text` and the like at 80,
    `empty_text` at 200; a longer string makes the whole card show 'Invalid stat-card config' (seen live on the CVE page)."""

    def test_no_stat_card_string_exceeds_the_core_limits(self) -> None:
        import json

        batch = json.loads(
            (PACKAGE_ROOT / "grift" / "vulnerabilities-page.grift.json").read_text(encoding="utf-8")
        )["batches"][0]
        too_long: list[str] = []
        for node in batch["nodes"]:
            config = node["node"].get("config") or {}
            if not isinstance(config, dict):
                continue
            slug = node["node"].get("slug")
            if len(config.get("unit", "")) > 40:
                too_long.append(f"{slug}: unit")
            for tone, text in (config.get("tone_labels") or {}).items():
                if len(text) > 40:
                    too_long.append(f"{slug}: tone_labels.{tone}")
            for key, limit in (("null_text", 80), ("missing_text", 80), ("blank_text", 80), ("empty_text", 200)):
                if len(config.get(key, "")) > limit:
                    too_long.append(f"{slug}: {key}")
        assert not too_long, too_long
