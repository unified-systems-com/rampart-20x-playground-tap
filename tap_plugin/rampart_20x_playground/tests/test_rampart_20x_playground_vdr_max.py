"""The VDR max page, read from the bundle as written (`req-rampart-20x-playground-page-vdr-max-*`).

These tests read JSON and TOML only. What the Searches return is checked against a booted stack."""

from __future__ import annotations

import json
import tomllib
from collections import Counter
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
SLUG = "/playground/vdr-max"
RUNNER = "tap_plugin.fedramp_20x_vdr.searches.clocks:"


def _batch() -> dict:
    return json.loads((GRIFT / "vdr-max-page.grift.json").read_text(encoding="utf-8"))["batches"][0]


def _of(entity_type: str) -> list[dict]:
    return [n for n in _batch()["nodes"] if n["entity"]["entity_type"] == entity_type]


@pytest.mark.spec("req-rampart-20x-playground-page-vdr-max-1")
def test_page_and_panels() -> None:
    (page,) = _of("page")
    assert page["node"]["slug"] == SLUG
    in_layout = {r["panel-id"] for c in page["node"]["layout"]["columns"].values() for r in c["rows"].values()}
    slugs = {n["node"]["slug"] for n in _of("panel")}
    assert in_layout == slugs and len(slugs) == 10
    used = {e["edge"]["properties"]["hotlink"]["value"] for e in _batch()["edges"] if e["edge"]["edge_type"] == "USES_PANEL"}
    assert used == slugs


@pytest.mark.spec("req-rampart-20x-playground-page-vdr-max-2")
def test_each_data_panel_reads_one_search_and_no_panel_computes() -> None:
    panels = {n["entity"]["entity_id"]: n for n in _of("panel")}
    searches = [n["node"] for n in _of("search")]
    bound = Counter(e["edge"]["from_entity_id"] for e in _batch()["edges"] if e["edge"]["edge_type"] == "USES_SEARCH")
    data = [p for p in panels.values() if "text_panel" not in p["node"]["view"]]
    assert len(data) == 7 and all(bound[p["entity"]["entity_id"]] == 1 for p in data)
    for s in searches:
        runner = s["definition"].get("runner_key")
        assert (runner is None and s["search_type"] == "gryphon") or runner.startswith(RUNNER)


@pytest.mark.spec("req-rampart-20x-playground-page-vdr-max-3")
def test_the_picker_reloads_the_page_and_the_followers_declare_entity_id() -> None:
    (picker,) = [n for n in _of("panel") if n["node"]["slug"].endswith("-picker")]
    assert picker["node"]["config"]["row_url_template"] == SLUG + "?entity_id={finding_id}"
    by_name = {n["node"]["name"]: n["node"] for n in _of("search")}
    defaults = set()
    for key in ("clock", "evaluation", "incident"):
        prop = by_name[f"playground — vdr max {key}"]["input_schema"]["properties"]["entity_id"]
        defaults.add(prop["default"])
    assert len(defaults) == 1  # one listed finding drives all three
    assert "entity_id" not in by_name["playground — vdr max open evaluations"]["input_schema"]["properties"]


@pytest.mark.spec("req-rampart-20x-playground-page-vdr-max-4")
def test_only_three_panels_carry_prose() -> None:
    text = [n["node"]["slug"] for n in _of("panel") if "text_panel" in n["node"]["view"]]
    assert sorted(text) == ["playground-vdr-max-intro", "playground-vdr-max-rules", "playground-vdr-max-steps"]


@pytest.mark.spec("req-rampart-20x-playground-page-vdr-max-5")
def test_needs_the_release_with_the_summary_and_the_demo_fires_the_collector_once() -> None:
    manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
    dep = next(d for d in manifest["depends_on"] if d["slug"] == "fedramp_20x_vdr")
    assert dep["min_version"] == "0.1.5" and "vdr_max_page" in manifest["grift"]
    for record in ("ci", "demo"):
        data = json.loads((PACKAGE_ROOT / "boot" / f"{record}.boot.json").read_text(encoding="utf-8"))
        rev = next(p for p in data["install"]["plugins"] if p["slug"] == "fedramp_20x_vdr")["source"]["rev"]
        assert tuple(int(x) for x in rev[1:].split(".")) >= (0, 1, 5), record
    demo = json.loads((PACKAGE_ROOT / "boot" / "demo.boot.json").read_text(encoding="utf-8"))
    fires = [s for s in demo["population"]["steps"] if s["type"] == "fire-collector"]
    assert [s["key"] for s in fires] == ["fedramp_20x_vdr:vdr_max"]
    ci = json.loads((PACKAGE_ROOT / "boot" / "ci.boot.json").read_text(encoding="utf-8"))
    assert "vdr_max_page" in {s.get("bundle") for s in ci["population"]["steps"]}


@pytest.mark.spec("req-rampart-20x-playground-page-vdr-max-6")
def test_an_unset_factor_is_shown_as_the_worst_case() -> None:
    (panel,) = [n for n in _of("panel") if n["node"]["slug"].endswith("-evaluation")]
    columns = {c["field"]: c for c in panel["node"]["config"]["columns"]}
    for field in ("likely_exploitable", "internet_reachable", "pain"):
        assert columns[field]["empty_text"].startswith("unset (worst case")


@pytest.mark.spec("req-rampart-20x-playground-page-vdr-max-7")
def test_the_page_is_named_vdr_max_nests_under_the_section_and_a_schedule_runs_the_collector_hourly() -> None:
    (page,) = _of("page")
    assert page["node"]["name"] == "VDR MAX" and page["node"]["nav_weight"] == 10
    nav = json.loads((GRIFT / "vdr-max-nav.grift.json").read_text(encoding="utf-8"))["batches"][0]
    (edge,) = nav["edges"]
    assert edge["edge"]["edge_type"] == "NESTS_UNDER" and edge["edge"]["from_entity_id"] == page["entity"]["entity_id"]
    section = json.loads((GRIFT / "vdr-implementations.grift.json").read_text(encoding="utf-8"))["batches"][0]
    (section_page,) = [n for n in section["nodes"] if n["entity"]["entity_type"] == "page"]
    assert edge["edge"]["to_entity_id"] == section_page["entity"]["entity_id"] and section_page["node"]["nav_weight"] == 10
    (schedule,) = _of("schedule")
    assert schedule["node"]["cron_expression"] == "0 * * * *" and schedule["node"]["enabled"] is True
    targets = [e["edge"] for e in _batch()["edges"] if e["edge"]["edge_type"] == "SCHEDULED_TARGET"]
    assert [t["from_entity_id"] for t in targets] == [schedule["entity"]["entity_id"]]
    assert targets[0]["to_entity_id"] == "ef175d1e-f754-5818-8e0a-22c69cfe81b9"
    manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
    order = list(manifest["grift"])
    assert order.index("vdr_max_nav") > max(order.index("vdr_implementations"), order.index("vdr_max_page"))


def _layout_bands() -> list[list[str]]:
    (page,) = _of("page")
    cols = sorted(page["node"]["layout"]["columns"].values(), key=lambda c: c["band"])
    bands: list[tuple[int, list[str]]] = []
    for c in cols:
        if not bands or bands[-1][0] != c["band"]:
            bands.append((c["band"], []))
        bands[-1][1].extend(r["panel-id"] for r in c["rows"].values())
    return [b[1] for b in bands]


@pytest.mark.spec("req-rampart-20x-playground-page-vdr-max-8")
def test_the_rules_and_steps_text_is_the_last_band() -> None:
    bands = _layout_bands()
    assert bands[0] == ["playground-vdr-max-intro"] and bands[-1] == ["playground-vdr-max-rules", "playground-vdr-max-steps"]


@pytest.mark.spec("req-rampart-20x-playground-page-vdr-max-9")
def test_the_count_card_has_a_title_and_shows_the_figure_once() -> None:
    (card,) = [n for n in _of("panel") if n["node"]["slug"] == "playground-vdr-max-cards"]
    config = card["node"]["config"]
    assert config["title"] == "Open Evaluations" and "title_field" not in config and "unit" not in config
    assert config["layout"] == "figure_right" and config["value_field"] == "evaluations"


@pytest.mark.spec("req-rampart-20x-playground-page-vdr-max-10")
def test_the_tables_fit_and_the_page_size_is_one_the_row_selector_offers() -> None:
    panels = {n["node"]["slug"]: n["node"]["config"] for n in _of("panel")}
    for slug in ("picker", "timeframes"):
        assert panels[f"playground-vdr-max-{slug}"]["default_page_size"] == 25  # the selector offers 25, 50 and All
    # Evaluation and Reportable Incident each have a band to themselves (full width), so the unset text and headers fit.
    bands = _layout_bands()
    assert ["playground-vdr-max-evaluation"] in bands and ["playground-vdr-max-incident"] in bands
    for slug in ("picker", "clock", "evaluation", "incident"):
        columns = panels[f"playground-vdr-max-{slug}"]["columns"]
        assert all("width" in c or "widthGrow" in c for c in columns), slug
        assert sum(c.get("width", c.get("minWidth", 0)) for c in columns) <= 1216, slug  # widths and minimums fit a 1280 px window
    evaluation = {c["field"]: c for c in panels["playground-vdr-max-evaluation"]["columns"]}
    assert evaluation["likely_exploitable"]["minWidth"] >= 200 and evaluation["internet_reachable"]["minWidth"] >= 200
