"""The Reporting page, read from the bundle as written (`req-rampart-20x-playground-page-reporting-*`).

These tests read JSON and TOML only, plus the report panel's own config schema from compliance_core. What the Searches
return, how the page renders and how it prints are checked against a booted stack in a browser."""

from __future__ import annotations

import json
import tomllib
import uuid
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
FILE = "reporting-page.grift.json"
SLUG = "/playground/reporting"
REPORT_VIEW = "compliance_core/panels/report.html"
SUMMARY = "tap_plugin.fedramp_20x_vdr.searches.clocks:vdr-summary"
DEADLINES_SEARCH = "playground — report deadlines"
RESP_TOTALS = "01a16098-57bd-7444-a312-2ffdd24c4174"
CLASS_TOTALS = "01a16098-57be-71da-9424-40b57d974dd7"
RESP_HISTORY = "01a16098-57bd-7444-a312-2ffbc5719ad7"
CLASS_HISTORY = "01a16098-57bd-7444-a312-2ffc2d3549d0"
DEADLINE_FIELDS = ("evaluation_overdue", "remediation_overdue", "acceptance_reached", "detection_unobserved")


def _batch(name: str = FILE) -> dict:
    return json.loads((GRIFT / name).read_text(encoding="utf-8"))["batches"][0]


def _of(entity_type: str) -> list[dict]:
    return [n for n in _batch()["nodes"] if n["entity"]["entity_type"] == entity_type]


def _panel(slug: str) -> dict:
    (panel,) = [n for n in _of("panel") if n["node"]["slug"] == slug]
    return panel


AGENCY = "playground-reporting-agency"
INTERNAL = "playground-reporting-internal"


def _items(config: dict) -> list[dict]:
    return [item for section in config["sections"] for item in section["items"]]


def _named_searches(config: dict) -> set[str]:
    named: set[str] = set()
    for item in _items(config):
        if item["kind"] in ("figure", "list"):
            named.add(item["search"])
        elif item["kind"] == "trend":
            named |= {line["search"] for line in item["lines"]}
    return named


def _linked(panel: dict) -> set[str]:
    return {
        e["edge"]["to_entity_id"]
        for e in _batch()["edges"]
        if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]
    }


def _floor(text: str) -> tuple[int, ...]:
    return tuple(int(x) for x in text.lstrip("v").split("."))


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-1")
def test_the_page_is_named_reporting_routed_and_in_navigation() -> None:
    (page,) = _of("page")
    assert page["node"]["slug"] == SLUG and page["node"]["name"] == "Reporting"
    assert page["node"].get("discoverable", True) is True  # the nav-discovery surfaces list it
    manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
    order = list(manifest["grift"])
    assert manifest["grift"]["reporting_page"] == "grift/" + FILE
    assert order.index("reporting_page") > order.index("inventory_coverage")  # its Searches exist before it links them
    ci = json.loads((PACKAGE_ROOT / "boot" / "ci.boot.json").read_text(encoding="utf-8"))
    assert "reporting_page" in {s.get("bundle") for s in ci["population"]["steps"]}


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-2")
def test_two_report_panels_in_two_bands_and_nothing_else() -> None:
    (page,) = _of("page")
    columns = sorted(page["node"]["layout"]["columns"].values(), key=lambda c: c["band"])
    assert [[r["panel-id"] for r in c["rows"].values()] for c in columns] == [[AGENCY], [INTERNAL]]
    assert len({c["band"] for c in columns}) == 2
    panels = _of("panel")
    assert [p["node"]["slug"] for p in panels] == [AGENCY, INTERNAL]
    assert [p["node"]["name"] for p in panels] == ["Agency Report", "Internal Report"]
    assert all(p["node"]["view"] == REPORT_VIEW for p in panels)
    used = [e["edge"] for e in _batch()["edges"] if e["edge"]["edge_type"] == "USES_PANEL"]
    assert {u["properties"]["hotlink"]["value"] for u in used} == {AGENCY, INTERNAL}
    assert {u["to_entity_id"] for u in used} == {p["entity"]["entity_id"] for p in panels}


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-3")
def test_the_two_parts_are_separate_panel_nodes() -> None:
    agency, internal = _panel(AGENCY), _panel(INTERNAL)
    assert agency["entity"]["entity_id"] != internal["entity"]["entity_id"]
    assert agency["node"]["config"] is not internal["node"]["config"]


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-4")
def test_the_cut_line_is_on_the_internal_part_only() -> None:
    internal = _panel(INTERNAL)["node"]["config"]
    assert internal["cut_line"] == "Internal" and internal["page_break_before"] is True
    agency = _panel(AGENCY)["node"]["config"]
    assert "cut_line" not in agency and not agency.get("page_break_before", False)
    assert agency["title"] == "Status Report" and agency["show_as_of"] is True


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-5")
def test_each_panel_is_linked_to_exactly_the_searches_its_lines_name() -> None:
    searches = {n["entity"]["entity_id"] for n in _of("search")} | {RESP_TOTALS, CLASS_TOTALS, RESP_HISTORY, CLASS_HISTORY}
    for slug in (AGENCY, INTERNAL):
        panel = _panel(slug)
        named = _named_searches(panel["node"]["config"])
        assert named and named == _linked(panel), slug
        assert named <= searches, slug  # every one is a Search of this plugin's bundles


def test_the_agency_lines_built_so_far() -> None:
    """The agency lines that exist today. Not marked `-6`: the severity figures (no severity field or conditional count;
    George has not ruled) and `Days To December 7` (the report panel carries no script and no Search can compute the
    days; a client-side countdown needs a panel type that ships JS) are not built, so `-6` is not met yet."""
    config = _panel(AGENCY)["node"]["config"]
    assert [s["heading"] for s in config["sections"]] == ["Coverage", "Vulnerabilities"]
    coverage, vulnerabilities = config["sections"]
    figures = [(i["label"], i["search"], i["field"], i["format"], i.get("of")) for i in coverage["items"] if i["kind"] == "figure"]
    assert figures == [
        ("Responsibility Coverage", RESP_TOTALS, "percent_overall", "percent", "denominator"),
        ("Data Classification Coverage", CLASS_TOTALS, "percent_overall", "percent", "denominator"),
    ]
    (trend,) = [i for i in coverage["items"] if i["kind"] == "trend"]
    assert trend["label"] == "Coverage Over Time"
    assert [(line["label"], line["search"]) for line in trend["lines"]] == [
        ("Responsibility", RESP_HISTORY), ("Data Classification", CLASS_HISTORY)]
    assert [i["label"] for i in vulnerabilities["items"]] == ["Open Vulnerabilities", "Known Exploited"]


def test_the_internal_lines_built_so_far() -> None:
    """Not marked `-7`: `Last Vulnerability Data Refresh` is not built (George's answer on it is pending, and no field
    records it)."""
    config = _panel(INTERNAL)["node"]["config"]
    assert [s["heading"] for s in config["sections"]] == ["Deadlines", "Coverage Gaps", "Data Freshness"]
    deadlines, gaps, freshness = config["sections"]
    assert [(i["kind"], i["field"], i["format"]) for i in deadlines["items"]] == [("figure", f, "count") for f in DEADLINE_FIELDS]
    assert [(i["label"], i["search"], i["field"], i["format"]) for i in gaps["items"]] == [
        ("Entries Without A Team", RESP_TOTALS, "unmapped", "count"),
        ("Unmapped Classification Entries", CLASS_TOTALS, "unmapped", "count"),
        ("Incorrect Classification Entries", CLASS_TOTALS, "mapped_incorrectly", "count"),
    ]
    (snapshot,) = freshness["items"]
    assert (snapshot["label"], snapshot["format"]) == ("Last Coverage Snapshot", "datetime")


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-8")
def test_nothing_internal_above_the_line() -> None:
    config = _panel(AGENCY)["node"]["config"]
    text = json.dumps(config)
    deadline_ids = {n["entity"]["entity_id"] for n in _of("search") if n["node"]["definition"].get("runner_key") == SUMMARY}
    assert not deadline_ids & _named_searches(config)
    assert all(i["kind"] in ("figure", "trend") for i in _items(config))  # no list, so no finding detail
    people = [n["node"]["name"] for n in _batch("teams.grift.json")["nodes"]
              if n["entity"]["entity_type"] in ("identity_core__team", "identity_core__human")]
    assert people and not [name for name in people if name in text]
    for word in ("Deadline", "Overdue", "Team", "Internal"):
        assert word not in text, word


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-9")
def test_coverage_figures_read_the_cards_totals_and_the_charts_overall_line() -> None:
    """Structure only: the same totals field the `Overall Coverage` cards read, and the `Overall` series of the same
    history Searches the charts draw. That the figures are equal on a live page is observed in a browser, not here."""
    cards = _batch("inventory-coverage.grift.json")
    overall = {n["entity"]["entity_id"] for n in cards["nodes"]
               if n["entity"]["entity_type"] == "panel" and n["node"]["name"] == "Overall Coverage"}
    card_sources = {e["edge"]["to_entity_id"] for e in cards["edges"]
                    if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] in overall}
    assert card_sources == {RESP_TOTALS, CLASS_TOTALS}
    items = _items(_panel(AGENCY)["node"]["config"])
    figures = [i for i in items if i["kind"] == "figure" and i["search"] in card_sources]
    assert {i["search"] for i in figures} == card_sources and {i["field"] for i in figures} == {"percent_overall"}
    (trend,) = [i for i in items if i["kind"] == "trend"]
    for line in trend["lines"]:
        assert (line["series_field"], line["series"], line["x_field"], line["value_field"]) == ("series", "Overall", "observed_at", "value")
    assert "y_min" not in trend and "y_max" not in trend  # the panel's fixed 0 to 100 range


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-11")
def test_configs_are_valid_report_configs_so_the_panel_owns_not_observed() -> None:
    """Every line is drawn by the report panel, which shows `Not observed` for a failed Search, a missing row and a null
    field (`req-compliance-core-panel-report-6`); a config the schema refused would render an error instead."""
    import jsonschema
    from tap_plugin.compliance_core.panels.report import REPORT_PANEL_CONFIG_SCHEMA

    for slug in (AGENCY, INTERNAL):
        jsonschema.validate(_panel(slug)["node"]["config"], REPORT_PANEL_CONFIG_SCHEMA)


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-12")
def test_no_panel_header_chrome() -> None:
    """The print layout itself (agency part on the first page) is checked in a browser print preview, not here."""
    for slug in (AGENCY, INTERNAL):
        assert _panel(slug)["node"]["config"]["hide_header"] is True, slug


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-13")
def test_titles_headings_and_figures_only_in_title_case() -> None:
    assert not [n for n in _of("panel") if "text_panel" in n["node"]["view"]]
    words: list[str] = [_of("page")[0]["node"]["name"]]
    for slug in (AGENCY, INTERNAL):
        panel = _panel(slug)
        config = panel["node"]["config"]
        words.append(panel["node"]["name"])
        words += [config[k] for k in ("title", "cut_line") if k in config]
        for section in config["sections"]:
            words.append(section["heading"])
            for item in section["items"]:
                words.append(item["label"])
                words += [line["label"] for line in item.get("lines", [])]
    for text in words:
        assert len(text) <= 40, text  # a label, not a sentence
        assert all(w[0].isupper() for w in text.split()), text


@pytest.mark.spec("req-rampart-20x-playground-page-reporting-14")
def test_floors_and_pins_name_the_report_panel_and_deadline_releases() -> None:
    manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
    floors = {d["slug"]: d.get("min_version") for d in manifest["depends_on"]}
    assert floors["compliance_core"] == "0.8.10" and _floor(floors["fedramp_20x_vdr"]) >= (0, 1, 3)
    for record in ("ci", "demo"):
        data = json.loads((PACKAGE_ROOT / "boot" / f"{record}.boot.json").read_text(encoding="utf-8"))
        revs = {p["slug"]: p["source"]["rev"] for p in data["install"]["plugins"]}
        assert _floor(revs["compliance_core"]) >= (0, 8, 10), record
        assert _floor(revs["fedramp_20x_vdr"]) >= (0, 1, 3), record


def test_the_deadlines_read_one_summary_row_and_say_they_are_a_bound() -> None:
    """One `vdr-summary` Search (view `counts`, the same row VDR MAX reads) feeds all four Deadlines figures, so the four
    counts come from one run of the runner and match the lists they summarise (`req-fedramp-20x-vdr-summary-1`). The
    remediation and acceptance labels say they are a bound (`req-fedramp-20x-vdr-deadlines-4`); the Search says so too."""
    summaries = [n for n in _of("search") if n["node"]["definition"].get("runner_key") == SUMMARY]
    (summary,) = summaries
    node = summary["node"]
    assert node["name"] == DEADLINES_SEARCH and node["search_type"] == "module" and node["root"] == "node"
    assert node["input_schema"]["properties"]["view"]["default"] == "counts"
    assert "worst-case bound" in node["description"]
    assert not [n for n in _of("search") if "vdr-deadlines" in json.dumps(n["node"]["definition"])]  # no list-returning runner
    internal = _panel(INTERNAL)
    deadlines = [s for s in internal["node"]["config"]["sections"] if s["heading"] == "Deadlines"]
    (section,) = deadlines
    assert {i["search"] for i in section["items"]} == {summary["entity"]["entity_id"]}
    assert summary["entity"]["entity_id"] in _linked(internal)
    for item in section["items"]:
        if item["field"] != "detection_unobserved":
            assert "Worst-Case Bound" in item["label"], item["label"]
    # the same runner and view as the VDR MAX counts card, so one definition of each count
    vdr_max = [n["node"] for n in _batch("vdr-max-page.grift.json")["nodes"] if n["entity"]["entity_type"] == "search"
               and n["node"]["definition"].get("runner_key") == SUMMARY and n["node"]["input_schema"]["properties"]["view"]["default"] == "counts"]
    assert vdr_max, "VDR MAX reads the same vdr-summary counts row"


def test_report_searches_count_in_the_query_and_the_page_does_no_arithmetic() -> None:
    by_name = {n["node"]["name"]: n["node"] for n in _of("search")}
    open_q = " ".join(by_name["playground — report open vulnerabilities"]["definition"]["query"])
    kev_q = " ".join(by_name["playground — report known exploited"]["definition"]["query"])
    snap_q = " ".join(by_name["playground — report last snapshot"]["definition"]["query"])
    assert 'f.data.status = "open"' in open_q and open_q.endswith("RETURN COUNT(f) AS open_vulnerabilities")
    assert 'f.data.status = "open"' in kev_q and "v.data.kev = true" in kev_q and kev_q.endswith("RETURN COUNT(f) AS known_exploited")
    assert snap_q.endswith("RETURN MAX(s.data.observed_at) AS last_snapshot")
    for slug in (AGENCY, INTERNAL):
        assert "2026-12-07" not in json.dumps(_panel(slug)["node"]["config"])  # a date lives in a Search, never a panel


def test_ids_are_unique_version_7_uuids_new_to_this_plugin() -> None:
    batch = _batch()
    ids = [batch["batch_entity"]["entity_id"]] + [n["entity"]["entity_id"] for n in batch["nodes"]]
    ids += [e["entity"]["entity_id"] for e in batch["edges"]]
    assert len(ids) == len(set(ids)) and all(uuid.UUID(i).version == 7 for i in ids)
    other: set[str] = set()
    for path in GRIFT.glob("*.grift.json"):
        if path.name == FILE:
            continue
        for b in json.loads(path.read_text(encoding="utf-8"))["batches"]:
            other.add(b["batch_entity"]["entity_id"])
            other |= {n["entity"]["entity_id"] for n in b["nodes"] if "entity_id" in n["entity"]}
            other |= {e["entity"]["entity_id"] for e in b["edges"] if "entity_id" in e["entity"]}
    assert not other & set(ids)
