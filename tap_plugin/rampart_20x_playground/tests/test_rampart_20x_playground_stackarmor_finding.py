"""The finding walk-through page, read from the bundle as written (`req-rampart-20x-playground-page-stackarmor-finding-*`).

These tests read JSON and TOML only. What the Search returns and how the page renders are checked against a booted stack."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
RUNNER = "tap_plugin.stackarmor_vdr.searches.finding:stackarmor-finding"


def _batch() -> dict:
    return json.loads((GRIFT / "stackarmor-finding-page.grift.json").read_text(encoding="utf-8"))["batches"][0]


def _of(kind: str) -> list[dict]:
    return [n for n in _batch()["nodes"] if n["entity"]["entity_type"] == kind]


@pytest.mark.spec("req-rampart-20x-playground-page-stackarmor-finding-1")
def test_page_and_two_panels() -> None:
    (page,) = _of("page")
    assert page["node"]["slug"] == "/playground/stackarmor/finding" and page["node"]["discoverable"] is False
    bands = {c["band"]: [r["panel-id"] for r in c["rows"].values()] for c in page["node"]["layout"]["columns"].values()}
    panels = {n["node"]["slug"]: n["node"]["config"]["part"] for n in _of("panel")}
    assert bands == {1: ["playground-stackarmor-finding-breakdown"], 2: ["playground-stackarmor-finding-walk"]}
    assert panels == {"playground-stackarmor-finding-breakdown": "breakdown", "playground-stackarmor-finding-walk": "walkthrough"}
    used = {e["edge"]["properties"]["hotlink"]["value"] for e in _batch()["edges"] if e["edge"]["edge_type"] == "USES_PANEL"}
    assert used == set(panels)


@pytest.mark.spec("req-rampart-20x-playground-page-stackarmor-finding-2")
def test_one_search_linked_by_both_panels() -> None:
    (search,) = _of("search")
    assert search["node"]["definition"]["runner_key"] == RUNNER
    assert set(search["node"]["input_schema"]["properties"]) == {"finding_id", "component_id", "owner_id", "container_id"}
    linked = {e["edge"]["from_entity_id"] for e in _batch()["edges"] if e["edge"]["edge_type"] == "USES_SEARCH" and e["edge"]["to_entity_id"] == search["entity"]["entity_id"]}
    assert linked == {n["entity"]["entity_id"] for n in _of("panel")}
    assert all(n["node"]["view"] == "stackarmor_vdr/panels/finding.html" for n in _of("panel"))


@pytest.mark.spec("req-rampart-20x-playground-page-stackarmor-finding-3")
def test_every_findings_row_opens_it() -> None:
    pain = json.loads((GRIFT / "pain.grift.json").read_text(encoding="utf-8"))["batches"][0]
    (table,) = [n for n in pain["nodes"] if n["node"].get("slug") == "playground-pain-findings"]
    template = table["node"]["config"]["row_url_template"]
    assert template.startswith("/playground/stackarmor/finding?")
    assert set(re.findall(r"\{(\w+)\}", template)) == {"finding_id", "component_id", "owner_id"}


@pytest.mark.spec("req-rampart-20x-playground-page-stackarmor-finding-4")
def test_data_only() -> None:
    assert {n["entity"]["entity_type"] for n in _batch()["nodes"]} == {"page", "panel", "search"}
    assert not [n for n in _of("panel") if "text_panel" in n["node"]["view"]]


@pytest.mark.spec("req-rampart-20x-playground-page-stackarmor-finding-5")
def test_demo_only_and_pinned() -> None:
    manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
    assert manifest["grift"]["stackarmor_finding_page"] == "grift/stackarmor-finding-page.grift.json"
    assert "stackarmor_vdr" not in [d["slug"] for d in manifest["depends_on"]]
    demo = json.loads((PACKAGE_ROOT / "boot" / "demo.boot.json").read_text(encoding="utf-8"))
    entry = next(p for p in demo["install"]["plugins"] if p["slug"] == "stackarmor_vdr")
    assert entry["source"]["rev"] == "v0.5.0" and "credential" not in entry["source"]
    ci = json.loads((PACKAGE_ROOT / "boot" / "ci.boot.json").read_text(encoding="utf-8"))
    assert "stackarmor_finding_page" not in {s.get("bundle") for s in ci["population"]["steps"]}
