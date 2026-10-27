"""The Coverage report panel of the Overview, read from the bundle as written (`req-rampart-20x-playground-coverage-panel-*`).

These tests read JSON and TOML only. What the Searches return is checked against a booted stack."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
SLUG = "playground-overview-coverage"
OVERVIEW = "01a13b2c-82d6-73d2-baa8-17415ac66a72"
SEARCHES = {
    "01a16098-57bd-7444-a312-2ffdd24c4174",  # responsibility totals
    "01a16098-57be-71da-9424-40b57d974dd7",  # classification totals
    "01a16098-57bd-7444-a312-2ffbc5719ad7",  # responsibility history
    "01a16098-57bd-7444-a312-2ffc2d3549d0",  # classification history
}


def _batch() -> dict:
    return json.loads((GRIFT / "coverage-panel.grift.json").read_text(encoding="utf-8"))["batches"][0]


def _panel() -> dict:
    (panel,) = [n for n in _batch()["nodes"] if n["entity"]["entity_type"] == "panel"]
    return panel


def _items() -> list[dict]:
    return [i for s in _panel()["node"]["config"]["sections"] for i in s["items"]]


@pytest.mark.spec("req-rampart-20x-playground-coverage-panel-1")
def test_one_report_panel_with_the_listed_sections_and_items() -> None:
    node = _panel()["node"]
    config = node["config"]
    assert node["view"] == "compliance_core/panels/report.html"
    assert config["title"] == "Coverage" and config["show_as_of"] is True
    assert "cut_line" not in config and "page_break_before" not in config
    shown = {s["heading"]: [i.get("label") for i in s["items"]] for s in config["sections"]}
    assert shown == {
        "Responsibility": ["Overall Coverage", "Entries", "With A Team", "Without A Team"],
        "Data Classification": ["Overall Coverage", "Mapped", "Unmapped", "Incorrect"],
        "Coverage Over Time": ["Overall Coverage"],
    }
    fields = [(i["field"], i["format"]) for s in config["sections"][:2] for i in s["items"]]
    assert fields == [
        ("percent_overall", "percent"), ("denominator", "count"), ("mapped", "count"), ("unmapped", "count"),
        ("percent_overall", "percent"), ("mapped", "count"), ("unmapped", "count"), ("mapped_incorrectly", "count"),
    ]  # fmt: skip
    (trend,) = [i for i in _items() if i["kind"] == "trend"]
    assert [(ln["label"], ln["series"], ln["series_field"], ln["value_field"], ln["x_field"]) for ln in trend["lines"]] == [
        ("Responsibility", "Overall", "series", "value", "observed_at"),
        ("Data Classification", "Overall", "series", "value", "observed_at"),
    ]


@pytest.mark.spec("req-rampart-20x-playground-coverage-panel-2")
def test_linked_to_the_four_searches_and_no_other() -> None:
    panel_id = _panel()["entity"]["entity_id"]
    linked = {e["edge"]["to_entity_id"] for e in _batch()["edges"] if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["from_entity_id"] == panel_id}
    assert linked == SEARCHES
    named = {i["search"] for i in _items() if i["kind"] == "figure"} | {ln["search"] for i in _items() if i["kind"] == "trend" for ln in i["lines"]}
    assert named == SEARCHES


@pytest.mark.spec("req-rampart-20x-playground-coverage-panel-3")
def test_mounted_on_the_landing_page_under_the_graph() -> None:
    panel_id = _panel()["entity"]["entity_id"]
    assert not [e for e in _batch()["edges"] if e["edge"]["edge_type"] == "USES_PANEL"]  # the mount is in pages
    pages_batch = json.loads((GRIFT / "pages.grift.json").read_text(encoding="utf-8"))["batches"][0]
    # The page-panels hotlink needs this edge when the Overview is created, so it lives with the page.
    (mount,) = [e for e in pages_batch["edges"] if e["edge"].get("to_entity_id") == panel_id]
    assert (mount["edge"]["from_entity_id"], mount["edge"]["to_entity_id"]) == (OVERVIEW, panel_id)
    assert mount["edge"]["properties"]["hotlink"]["value"] == SLUG
    pages = pages_batch["nodes"]
    (landing,) = [n for n in pages if n["entity"]["entity_id"] == OVERVIEW]
    columns = landing["node"]["layout"]["columns"]
    band = {r["panel-id"]: c["band"] for c in columns.values() for r in c["rows"].values()}
    assert band[SLUG] > band["landing"]
    assert {"playground-overview-kev", "playground-overview-cwe506", "landing"} <= set(band)  # nothing already there changed


@pytest.mark.spec("req-rampart-20x-playground-coverage-panel-6")
def test_the_panel_does_no_arithmetic() -> None:
    assert not [n for n in _batch()["nodes"] if n["entity"]["entity_type"] == "search"]
    assert {i["kind"] for i in _items()} == {"figure", "trend"}
    assert not [i for i in _items() if "of" in i or "where" in i or "row" in i]


@pytest.mark.spec("req-rampart-20x-playground-coverage-panel-8")
def test_no_prose() -> None:
    node = _panel()["node"]
    assert set(node["config"]) == {"title", "show_as_of", "sections"}
    text = json.dumps(node["config"])
    assert "." not in text.replace("0.", "")  # no sentence anywhere in the config


@pytest.mark.spec("req-rampart-20x-playground-coverage-panel-9")
def test_floor_and_pins_name_the_release_with_the_report_panel() -> None:
    manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
    floors = {d["slug"]: d.get("min_version") for d in manifest["depends_on"]}
    assert floors["compliance_core"] == "0.8.10"
    assert manifest["grift"]["coverage_panel"] == "grift/coverage-panel.grift.json"
    for name in ("ci", "demo"):
        record = json.loads((PACKAGE_ROOT / "boot" / f"{name}.boot.json").read_text(encoding="utf-8"))
        entry = next(e for e in record["install"]["plugins"] if e["slug"] == "compliance_core")
        assert entry["source"]["rev"] == "v0.8.10"
