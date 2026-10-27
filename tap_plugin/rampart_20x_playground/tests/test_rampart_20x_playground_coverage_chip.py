"""The Overview's coverage widget: one stat-card panel, one Search, a card per dimension (`req-rampart-20x-playground-coverage-chip`)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = "01a13b2c-82d6-73d2-baa8-17415ac66a72"
SLUG = "playground-overview-coverage-chip"
RESPONSIBILITY_SUMMARY = "01a15fdf-61ef-710d-b5d3-e3a7ae238a40"
CLASSIFICATION_SUMMARY = "01a15b2f-df3b-7569-bf22-9ead3f816b84"


def _batch() -> dict:
    return json.loads((PACKAGE_ROOT / "grift" / "pages.grift.json").read_text(encoding="utf-8"))["batches"][0]


def _panel() -> dict:
    (panel,) = [n for n in _batch()["nodes"] if n["entity"]["entity_type"] == "panel" and n["node"]["slug"] == SLUG]
    return panel


@pytest.mark.spec("req-rampart-20x-playground-coverage-chip-1")
def test_one_stat_card_panel_with_one_search() -> None:
    panel = _panel()
    assert panel["node"]["view"] == "tap_web/panels/stat_card_panel.html"
    assert panel["node"]["config"]["layout"] == "figure_right"
    edges = [e for e in _batch()["edges"] if e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]]
    assert [e["edge"]["edge_type"] for e in edges] == ["USES_SEARCH"]


@pytest.mark.spec("req-rampart-20x-playground-coverage-chip-2")
def test_the_search_is_the_set_runner_over_the_two_summaries() -> None:
    panel = _panel()
    (edge,) = [e for e in _batch()["edges"] if e["edge"]["from_entity_id"] == panel["entity"]["entity_id"]]
    (search,) = [n for n in _batch()["nodes"] if n["entity"]["entity_id"] == edge["edge"]["to_entity_id"]]
    assert search["node"]["search_type"] == "module"
    assert search["node"]["definition"]["runner_key"].endswith("dimension_mapping_totals:dimension-mapping-totals-set")
    default = search["node"]["input_schema"]["properties"]["summaries"]["default"]
    assert default == [
        {"key": "responsibility", "label": "Responsibility", "summary_search_id": RESPONSIBILITY_SUMMARY},
        {"key": "classification", "label": "Data Classification", "summary_search_id": CLASSIFICATION_SUMMARY},
    ]
    config = panel["node"]["config"]
    assert (config["title_field"], config["value_field"]) == ("label", "percent_text")
    assert "lines" not in config  # one line a card, the height of the notification cards


@pytest.mark.spec("req-rampart-20x-playground-coverage-chip-3")
def test_the_chip_is_in_the_card_row() -> None:
    (page,) = [n for n in _batch()["nodes"] if n["entity"]["entity_id"] == OVERVIEW]
    columns = page["node"]["layout"]["columns"]
    bands: dict[int, list[str]] = {}
    for column in columns.values():
        bands.setdefault(column["band"], []).extend(row["panel-id"] for row in column["rows"].values())
    assert bands == {1: ["playground-overview-kev", "playground-overview-cwe506", SLUG], 2: ["landing"]}
    widths = {row["panel-id"]: c["width"] for c in columns.values() if c["band"] == 1 for row in c["rows"].values()}
    assert widths[SLUG] != "compact" and widths["playground-overview-kev"] == "compact"  # the widget is wider than the cards
    (mount,) = [e for e in _batch()["edges"] if e["edge"]["to_entity_id"] == _panel()["entity"]["entity_id"] and e["edge"]["edge_type"] == "USES_PANEL"]
    assert mount["edge"]["from_entity_id"] == OVERVIEW and mount["edge"]["properties"]["hotlink"]["value"] == SLUG


@pytest.mark.spec("req-rampart-20x-playground-coverage-chip-5")
def test_the_chip_does_no_arithmetic() -> None:
    config = _panel()["node"]["config"]
    assert config["value_formatter"] == "text"  # shown as returned, never divided or summed here
    assert not [k for k in config if k in ("of", "where", "row", "formula")]


@pytest.mark.spec("req-rampart-20x-playground-coverage-chip-6")
def test_no_prose() -> None:
    config = _panel()["node"]["config"]
    assert "title" not in config and "lines" not in config  # each card is a label and a figure
    assert "." not in json.dumps(config).replace("0.", "")
