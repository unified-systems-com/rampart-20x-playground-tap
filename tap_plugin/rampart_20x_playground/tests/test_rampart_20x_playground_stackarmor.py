"""The StackArmor examples bundle and page, read from the bundles as written
(`req-rampart-20x-playground-stackarmor-examples-*`, `req-rampart-20x-playground-page-stackarmor-*`).

These tests read JSON and TOML only. What the Searches return is checked against a booted stack."""

from __future__ import annotations

import json
import tomllib
from collections import Counter
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
SLUG = "/playground/stackarmor"
RUNNER = "tap_plugin.stackarmor_vdr.searches.pain:"
CC = "compliance_core__"


def _nodes(name: str) -> list[dict]:
    return [n for b in json.loads((GRIFT / name).read_text(encoding="utf-8"))["batches"] for n in b["nodes"]]


def _edges(name: str) -> list[dict]:
    return [e for b in json.loads((GRIFT / name).read_text(encoding="utf-8"))["batches"] for e in b["edges"]]


def _of(nodes: list[dict], entity_type: str) -> list[dict]:
    return [n for n in nodes if n["entity"]["entity_type"] == entity_type]


class TestExamples:
    nodes = _nodes("stackarmor-examples.grift.json")

    @pytest.mark.spec("req-rampart-20x-playground-stackarmor-examples-1")
    def test_five_examples(self) -> None:
        counts = Counter(n["entity"]["entity_type"] for n in self.nodes)
        assert counts[CC + "compliance_finding"] == 5 and counts["computing_core__program"] == 5
        assert counts["stackarmor_vdr__asset_profile"] == 5 and counts[CC + "compliance_vulnerability"] == 3
        assert {n["node"]["source"] for n in _of(self.nodes, CC + "compliance_finding")} == {"stackarmor-memo"}

    @pytest.mark.spec("req-rampart-20x-playground-stackarmor-examples-2")
    def test_the_memos_inputs(self) -> None:
        stamps = {n["node"]["stamp_key"]: n["node"] for n in _of(self.nodes, "stackarmor_vdr__asset_profile")}
        got = [(s["cr"], s["ir"], s["ar"], s["multi_agency"]) for _, s in sorted(stamps.items())]
        assert got == [
            ("high", "high", "high", 1),
            ("medium", "medium", "medium", 1),
            ("low", "low", "low", 0),
            ("medium", "medium", "high", 0),
            ("low", "medium", "medium", 0),
        ]
        vectors = {n["node"]["vuln_id"]: n["node"]["cvss_vector"] for n in _of(self.nodes, CC + "compliance_vulnerability")}
        assert vectors["DEMO-2026-0001"].endswith("C:H/I:H/A:H")
        assert vectors["DEMO-2026-0004"].endswith("C:N/I:N/A:H")
        assert vectors["DEMO-2026-0005"].endswith("C:H/I:N/A:N")

    @pytest.mark.spec("req-rampart-20x-playground-stackarmor-examples-4")
    def test_stamped_like_the_inventory(self) -> None:
        for n in _of(self.nodes, "computing_core__program") + _of(self.nodes, "computing_core__package"):
            assert n["entity"]["dimensions"]["team.responsible"] == "01a15c19-6922-734d-9272-201aa27ca26f"
        for n in _of(self.nodes, "computing_core__program"):
            assert n["entity"]["dimensions"]["dataclass.action"] == "process"
        for n in _of(self.nodes, "computing_core__host"):
            assert "team.responsible" not in n["entity"]["dimensions"] and "dataclass.action" not in n["entity"]["dimensions"]
        assert not [n for n in self.nodes if "inventory" in n["entity"]["dimensions"]]

    @pytest.mark.spec("req-rampart-20x-playground-stackarmor-examples-5")
    def test_fictional_is_said(self) -> None:
        for n in _of(self.nodes, "computing_core__program"):
            assert n["entity"]["name"].startswith("Memo Example")
        for n in _of(self.nodes, CC + "compliance_finding"):
            assert "Memo" in n["node"]["description"] and n["node"]["summary"].startswith("Memo says")


class TestPage:
    nodes = _nodes("stackarmor-page.grift.json")
    edges = _edges("stackarmor-page.grift.json")

    @pytest.mark.spec("req-rampart-20x-playground-page-stackarmor-1")
    def test_page_and_panels(self) -> None:
        (page,) = _of(self.nodes, "page")
        assert page["node"]["slug"] == SLUG
        in_layout = {r["panel-id"] for c in page["node"]["layout"]["columns"].values() for r in c["rows"].values()}
        slugs = {n["node"]["slug"] for n in _of(self.nodes, "panel")}
        assert in_layout == slugs and len(slugs) == 11
        used = {e["edge"]["properties"]["hotlink"]["value"] for e in self.edges if e["edge"]["edge_type"] == "USES_PANEL"}
        assert used == slugs

    @pytest.mark.spec("req-rampart-20x-playground-page-stackarmor-2")
    def test_each_data_panel_reads_one_search_and_no_panel_computes(self) -> None:
        panels = {n["entity"]["entity_id"]: n for n in _of(self.nodes, "panel")}
        searches = {n["entity"]["entity_id"]: n["node"] for n in _of(self.nodes, "search")}
        bound = Counter(e["edge"]["from_entity_id"] for e in self.edges if e["edge"]["edge_type"] == "USES_SEARCH")
        data = [p for p in panels.values() if "text_panel" not in p["node"]["view"]]
        assert len(data) == 8 and all(bound[p["entity"]["entity_id"]] == 1 for p in data)
        for s in searches.values():
            runner = s["definition"].get("runner_key")
            assert (runner is None and s["search_type"] == "gryphon") or runner.startswith(RUNNER)

    @pytest.mark.spec("req-rampart-20x-playground-page-stackarmor-3")
    def test_the_picker_reloads_the_page_and_the_followers_declare_the_inputs(self) -> None:
        (picker,) = [n for n in _of(self.nodes, "panel") if n["node"]["slug"].endswith("-picker")]
        assert picker["node"]["config"]["row_url_template"] == SLUG + "?entity_id={finding_id}&vuln_id={vuln_id}"
        examples = {n["entity"]["name"]: n["entity"]["entity_id"] for n in _nodes("stackarmor-examples.grift.json")}
        first = next(i for name, i in examples.items() if name.startswith("Memo example 1"))
        by_name = {n["node"]["name"]: n["node"] for n in _of(self.nodes, "search")}
        for key in ("one finding", "trace"):
            assert by_name[f"playground — stackarmor {key}"]["input_schema"]["properties"]["entity_id"]["default"] == first
        assert "vuln_id" in by_name["playground — stackarmor same cve"]["input_schema"]["properties"]

    @pytest.mark.spec("req-rampart-20x-playground-page-stackarmor-4")
    def test_only_three_panels_carry_prose(self) -> None:
        text = [n["node"]["slug"] for n in _of(self.nodes, "panel") if "text_panel" in n["node"]["view"]]
        assert sorted(text) == ["playground-stackarmor-intro", "playground-stackarmor-method", "playground-stackarmor-steps"]

    @pytest.mark.spec("req-rampart-20x-playground-page-stackarmor-5")
    def test_the_demo_record_installs_and_seeds_the_plugin_and_the_ci_record_does_not(self) -> None:
        """Private repository: the demo record installs it (with its install credential) and seeds it; the offline ci
        record does not, so the manifest cannot list it in depends_on either (the pain bundle is the same case)."""
        manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
        assert "stackarmor_vdr" not in [d["slug"] for d in manifest["depends_on"]]
        demo = json.loads((PACKAGE_ROOT / "boot" / "demo.boot.json").read_text(encoding="utf-8"))
        entry = next(p for p in demo["install"]["plugins"] if p["slug"] == "stackarmor_vdr")
        assert entry["source"]["rev"] == "v0.3.2" and entry["source"]["credential"] == "stackarmor_vdr"
        assert "stackarmor_vdr" in [s.get("plugin") for s in demo["population"]["steps"]]
        ci = json.loads((PACKAGE_ROOT / "boot" / "ci.boot.json").read_text(encoding="utf-8"))
        assert "stackarmor_vdr" not in [p["slug"] for p in ci["install"]["plugins"]]
        bundles = {s.get("bundle") for s in ci["population"]["steps"] if s.get("plugin") == "rampart_20x_playground"}
        assert not {"stackarmor_examples", "stackarmor_page", "pain", "vdr_implementations"} & bundles
