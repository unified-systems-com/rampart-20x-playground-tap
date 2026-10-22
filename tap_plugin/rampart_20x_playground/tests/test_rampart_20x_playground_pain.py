"""PAIN on the instance: the program stamps, the two Searches and the page, read from the bundle as written
(`req-rampart-20x-playground-pain-profiles-*`, `req-rampart-20x-playground-page-pain-*`).

These tests read JSON only. What the runners return is checked on a booted stack. The tests that compare against the
`stackarmor_vdr` seed skip when that private plugin is not installed, which is the case in the ci record."""

from __future__ import annotations

import importlib.util
import json
import re
import tomllib
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRIFT = PACKAGE_ROOT / "grift"
BOOT = PACKAGE_ROOT / "boot"
SLUG = "/playground/pain"
TABLE = "tap_web/panels/table_panel.html"
TEXT = "tap_web/panels/text_panel.html"
FINDINGS_KEY = "tap_plugin.stackarmor_vdr.searches.pain:stackarmor-pain"
ASSETS_KEY = "tap_plugin.stackarmor_vdr.searches.pain:stackarmor-assets"
# The inputs `stackarmor_vdr`'s INPUT_SCHEMA declares (searches/pain.py, v0.3.2).
RUNNER_INPUTS = {
    "impact_weights", "requirement_weights", "u1", "u2", "theta3", "epss_irv", "epss_non_irv", "multi_agency",
    "fedramp_class", "scheme", "evaluation_scheme", "entity_id", "max_results",
}
FINDING_FIELDS = {
    "finding_id", "vuln_id", "component", "component_id", "container_id", "container", "owner_kind", "owner_id", "owner",
    "scheme", "profile_source", "impact_source", "c", "i", "a", "subsequent", "cr", "ir", "ar", "u", "s", "word", "m",
    "multi_agency_source", "pain", "lev", "irv", "column", "fedramp_class", "deadline_hours", "cve", "component_type",
    "owner_type", "container_type",
}
ASSET_FIELDS = {"asset_id", "asset", "scheme", "programs", "classified", "cr", "ir", "ar"}
STAMPS = {
    "tap-web": "app_tier", "tap-web (web task b)": "app_tier", "gunicorn": "app_tier",
    "gunicorn (web task b)": "app_tier", "PostgreSQL database instance": "data_sensitive",
    "teleport proxy": "identity_secrets", "teleport auth": "identity_secrets", "teleport ssh": "identity_secrets",
}
FINDING_TITLES = [
    "Vuln ID", "Component", "Owner", "Owner Kind", "PAIN", "Word", "C", "I", "A", "CR", "IR", "AR", "Profile Source",
    "Exposure Column", "Deadline Hours",
]
FINDING_COLUMNS = [
    "cve", "component", "owner", "owner_kind", "pain", "word", "c", "i", "a", "cr", "ir", "ar", "profile_source",
    "column", "deadline_hours",
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["batches"][0]


class TestStamps:
    def setup_method(self) -> None:
        self.batch = _load(GRIFT / "pain.grift.json")
        self.nodes = {n["entity"]["entity_id"]: n for n in self.batch["nodes"]}
        self.edges = [e["edge"] for e in self.batch["edges"]]
        inventory = _load(GRIFT / "inventory-entities.grift.json")
        self.programs = {
            n["entity"]["entity_id"]: n["entity"]["name"]
            for n in inventory["nodes"] if n["entity"]["entity_type"] == "computing_core__program"
        }
        self.stamps = {i: n for i, n in self.nodes.items() if n["entity"]["entity_type"] == "stackarmor_vdr__asset_profile"}

    def test_every_program_has_one_stamp_and_nothing_else_is_stamped(self) -> None:
        """`pain-profiles-1`"""
        assert set(STAMPS) == set(self.programs.values())
        assert len(self.stamps) == len(self.programs)
        profiles = [e for e in self.edges if e["edge_type"] == "PROFILES_PROGRAM__stackarmor_vdr"]
        assert {e["from_entity_id"] for e in profiles} == set(self.stamps)
        assert sorted(self.programs[e["to_entity_id"]] for e in profiles) == sorted(self.programs.values())
        archetype = [e for e in self.edges if e["edge_type"] == "USES_ARCHETYPE__stackarmor_vdr"]
        assert sorted(e["from_entity_id"] for e in archetype) == sorted(self.stamps)

    def test_each_stamp_names_the_archetype_of_the_table(self) -> None:
        """`pain-profiles-1`, `-2`: the edge targets are archetype node ids; the id-to-key map is checked when the plugin is present."""
        wanted = {}
        for e in self.edges:
            if e["edge_type"] == "USES_ARCHETYPE__stackarmor_vdr":
                program = next(
                    self.programs[p["to_entity_id"]] for p in self.edges
                    if p["edge_type"] == "PROFILES_PROGRAM__stackarmor_vdr" and p["from_entity_id"] == e["from_entity_id"]
                )
                wanted[program] = e["to_entity_id"]
        assert len(set(wanted.values())) == 3
        spec = importlib.util.find_spec("tap_plugin.stackarmor_vdr")
        if spec is None or not spec.submodule_search_locations:
            pytest.skip("stackarmor_vdr is not installed")
        seed = _load(Path(next(iter(spec.submodule_search_locations))) / "grift" / "archetypes.grift.json")
        by_id = {n["entity"]["entity_id"]: n["entity"]["name"] for n in seed["nodes"]}
        assert {program: by_id[i] for program, i in wanted.items()} == STAMPS

    def test_a_stamp_carries_no_override_and_no_archetype_field(self) -> None:
        """`pain-profiles-3`"""
        for node in self.stamps.values():
            body = node["node"]
            assert set(body) == {"source", "stamp_key", "scheme", "rationale"}
            assert body["source"] == "playground-seed" and body["scheme"] == "stackarmor" and body["rationale"]

    def test_a_stamp_changes_nothing_that_describes_the_system(self) -> None:
        """`pain-profiles-8`: the bundle holds no node of an inventory type, and a stamp has no team or data class."""
        own = {"stackarmor_vdr__asset_profile", "search", "panel", "page", "edge", "batch"}
        assert {n["entity"]["entity_type"] for n in self.batch["nodes"]} <= own
        for node in self.stamps.values():
            assert node["entity"]["dimensions"] == {}

    def test_no_root_package_edge_is_added_for_postgres(self) -> None:
        """`pain-profiles-4`: only the four edges of the software bundle exist; the PostgreSQL edge would put an apk package on the
        Overview graph, which `govcloud-layout-36` pins to the two Python roots, so it is left out and reported."""
        software = _load(GRIFT / "inventory-software.grift.json")
        runs = [e for e in software["edges"] if e["edge"]["edge_type"] == "RUNS_PACKAGE__computing_core"]
        assert len(runs) == 4
        assert not [e for e in self.edges if e["edge_type"] == "RUNS_PACKAGE__computing_core"]


class TestSearches:
    def setup_method(self) -> None:
        batch = _load(GRIFT / "pain.grift.json")
        self.searches = {n["node"]["name"]: n["node"] for n in batch["nodes"] if n["entity"]["entity_type"] == "search"}

    def test_two_module_searches_with_the_exact_runner_keys(self) -> None:
        """`pain-profiles-5`"""
        assert set(self.searches) == {"PAIN Findings", "PAIN Assets"}
        for name, key in (("PAIN Findings", FINDINGS_KEY), ("PAIN Assets", ASSETS_KEY)):
            search = self.searches[name]
            assert search["search_type"] == "module" and search["definition"] == {"runner_key": key}

    def test_inputs_are_only_ones_the_runner_declares_and_only_the_class_is_set(self) -> None:
        for search in self.searches.values():
            props = search["input_schema"]["properties"]
            assert set(props) <= RUNNER_INPUTS
            assert {k for k, v in props.items() if "default" in v} == {"fedramp_class"}
            assert props["fedramp_class"]["default"] == "d"


class TestTables:
    def setup_method(self) -> None:
        self.batch = _load(GRIFT / "pain.grift.json")
        by_id = {n["entity"]["entity_id"]: n for n in self.batch["nodes"]}
        self.by_id = by_id
        self.panels = {n["node"]["slug"]: n for n in by_id.values() if n["entity"]["entity_type"] == "panel"}
        self.edges = [e["edge"] for e in self.batch["edges"]]

    def _search_of(self, panel: dict) -> dict:
        links = [e for e in self.edges if e["edge_type"] == "USES_SEARCH" and e["from_entity_id"] == panel["entity"]["entity_id"]]
        assert len(links) == 1
        return self.by_id[links[0]["to_entity_id"]]["node"]

    def test_the_bundle_holds_no_page_and_the_tables_are_placed_by_the_stackarmor_page(self) -> None:
        """`page-pain-1`, `-2`: the PAIN page is gone; its two tables sit on `/playground/stackarmor`."""
        assert not [n for n in self.by_id.values() if n["entity"]["entity_type"] == "page"]
        assert not [e for e in self.edges if e["edge_type"] in ("USES_PANEL", "NESTS_UNDER")]
        assert sorted(self.panels) == ["playground-pain-assets", "playground-pain-findings"]
        page = _load(GRIFT / "stackarmor-page.grift.json")
        placed = {e["edge"]["to_entity_id"] for e in page["edges"] if e["edge"]["edge_type"] == "USES_PANEL"}
        assert {p["entity"]["entity_id"] for p in self.panels.values()} <= placed

    def test_each_table_reads_its_search_and_names_only_returned_fields(self) -> None:
        """`page-pain-3`"""
        findings = self.panels["playground-pain-findings"]
        assets = self.panels["playground-pain-assets"]
        assert self._search_of(findings)["name"] == "PAIN Findings"
        assert self._search_of(assets)["name"] == "PAIN Assets"
        assert [c["field"] for c in findings["node"]["config"]["columns"]] == FINDING_COLUMNS
        assert {c["field"] for c in findings["node"]["config"]["columns"]} <= FINDING_FIELDS
        assert [c["field"] for c in assets["node"]["config"]["columns"]] == ["asset", "cr", "ir", "ar", "programs", "classified"]
        assert {c["field"] for c in assets["node"]["config"]["columns"]} <= ASSET_FIELDS

    def test_titles_are_the_spec_titles_in_title_case(self) -> None:
        """`page-pain-7`"""
        findings = self.panels["playground-pain-findings"]["node"]["config"]["columns"]
        assets = self.panels["playground-pain-assets"]["node"]["config"]["columns"]
        assert [c["title"] for c in findings] == FINDING_TITLES
        assert [c["title"] for c in assets] == ["Asset", "CR", "IR", "AR", "Programs", "Classified"]
        for panel in self.panels.values():
            assert re.fullmatch(r"[A-Z][A-Za-z]*", panel["node"]["name"])

    def test_filter_and_paging(self) -> None:
        """`page-pain-5`"""
        for slug in ("playground-pain-findings", "playground-pain-assets"):
            config = self.panels[slug]["node"]["config"]
            assert config["quick_filter"] is True and config["default_page_size"] == 25 and config["show_all_rows"] is False

    def test_an_empty_deadline_shows_a_dash_not_a_blank(self) -> None:
        column = next(c for c in self.panels["playground-pain-findings"]["node"]["config"]["columns"] if c["field"] == "deadline_hours")
        assert column["empty_text"]

    def test_the_vulnerability_component_and_owner_link_by_the_type_the_row_carries(self) -> None:
        """`page-pain-4`: the runner returns the CVE id (`cve`) and the entity type of the component and the owner, so a link
        template fills the type from the row (`{component_type}`, `{owner_type}`) and one column serves every type."""
        columns = {c["field"]: c for c in self.panels["playground-pain-findings"]["node"]["config"]["columns"]}
        expected = {
            "cve": "/playground/vulnerabilities/cve?vuln_id={cve}",
            "component": "/object/{component_type}/entity--{component_id}/",
            "owner": "/object/{owner_type}/entity--{owner_id}/",
        }
        for field, template in expected.items():
            assert columns[field]["formatter"] == "link", field
            assert columns[field]["formatter_params"]["href_template"] == template, field
            assert columns[field]["formatter_params"]["external"] is False, field
        for field in ("vuln_id", "component_id", "owner_id"):
            assert field not in columns, field
        used = {m for c in columns.values() for m in re.findall(r"\{(\w+)\}", c.get("formatter_params", {}).get("href_template", ""))}
        assert used <= FINDING_FIELDS, used - FINDING_FIELDS

    def test_the_assets_table_links_nothing(self) -> None:
        """The assets Search returns no entity type, so its asset names stay plain text."""
        for column in self.panels["playground-pain-assets"]["node"]["config"]["columns"]:
            assert "formatter" not in column, column["field"]

    def test_the_identifying_columns_are_wide_enough_not_to_truncate(self) -> None:
        columns = {c["field"]: c for c in self.panels["playground-pain-findings"]["node"]["config"]["columns"]}
        assert columns["cve"]["width"] >= 170
        assert columns["component"]["minWidth"] >= 165 and columns["owner"]["minWidth"] >= 165


class TestVdrNavigationSection:
    def setup_method(self) -> None:
        self.batch = _load(GRIFT / "vdr-implementations.grift.json")
        self.pages = {n["entity"]["entity_id"]: n for n in self.batch["nodes"] if n["entity"]["entity_type"] == "page"}

    def test_one_titled_page_with_a_title_panel_only(self) -> None:
        (page,) = self.pages.values()
        assert page["node"]["name"] == "VDR Implementations" and page["node"]["slug"] == "/playground/vdr-implementations"
        panels = [r["panel-id"] for c in page["node"]["layout"]["columns"].values() for r in c["rows"].values()]
        assert panels == ["playground-vdr-implementations-title"]
        (panel,) = [n for n in self.batch["nodes"] if n["entity"]["entity_type"] == "panel"]
        assert panel["node"]["config"]["text"] == ""

    def test_only_the_stackarmor_page_nests_under_it_and_keeps_its_route(self) -> None:
        (section,) = self.pages
        nests = [e["edge"] for e in self.batch["edges"] if e["edge"]["edge_type"] == "NESTS_UNDER"]
        assert len(nests) == 1 and nests[0]["to_entity_id"] == section and nests[0]["properties"] == {}
        stack = next(n for n in _load(GRIFT / "stackarmor-page.grift.json")["nodes"] if n["entity"]["entity_type"] == "page")
        assert nests[0]["from_entity_id"] == stack["entity"]["entity_id"] and stack["node"]["slug"] == "/playground/stackarmor"

    def test_it_is_seeded_after_the_page_it_moves(self) -> None:
        manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
        order = list(manifest["grift"])
        assert order.index("vdr_implementations") > order.index("stackarmor_page")

    def test_the_section_pages_order_in_the_navbar(self) -> None:
        """Data Classification, Inventory, Vulnerabilities, VDR Implementations, then Teams (weight 0)."""
        weights = {}
        for name in ("data-classification-page", "inventory-page", "vulnerabilities-page", "vdr-implementations", "teams"):
            for n in _load(GRIFT / f"{name}.grift.json")["nodes"]:
                if n["entity"]["entity_type"] == "page" and n["node"]["slug"].count("/") == 2 and n["node"]["slug"] != "/playground/stackarmor":
                    weights[n["node"]["slug"]] = n["node"].get("nav_weight", 0)
        ranked = sorted(weights, key=lambda s: -weights[s])
        assert ranked == [
            "/playground/data-classification", "/playground/inventory", "/playground/vulnerabilities",
            "/playground/vdr-implementations", "/playground/teams",
        ]


class TestBootRecords:
    @staticmethod
    def _record(name: str) -> dict:
        return json.loads((BOOT / f"{name}.boot.json").read_text(encoding="utf-8"))

    def test_the_demo_installs_the_private_plugin_by_commit_with_a_credential_and_seeds_it_before_the_playground(self) -> None:
        """`pain-profiles-6`"""
        demo = self._record("demo")
        slugs = [p["slug"] for p in demo["install"]["plugins"]]
        assert slugs.index("fedramp_20x_vdr") < slugs.index("stackarmor_vdr")
        entry = next(p for p in demo["install"]["plugins"] if p["slug"] == "stackarmor_vdr")["source"]
        assert entry["type"] == "git" and entry["rev"] == "v0.3.2" and entry["credential"] == "stackarmor_vdr"
        assert re.fullmatch(r"[0-9a-f]{40}", entry["commit"])
        vdr = next(p for p in demo["install"]["plugins"] if p["slug"] == "fedramp_20x_vdr")["source"]["rev"]
        assert tuple(int(x) for x in vdr[1:].split(".")) >= (0, 1, 2)
        steps = [s["plugin"] for s in demo["population"]["steps"]]
        assert steps.index("fedramp_20x_vdr") < steps.index("stackarmor_vdr") < steps.index("rampart_20x_playground")

    def test_the_ci_record_stays_offline_and_seeds_every_bundle_but_the_stackarmor_ones(self) -> None:
        ci = self._record("ci")
        assert "stackarmor_vdr" not in [p["slug"] for p in ci["install"]["plugins"]]
        assert not any("credential" in p["source"] for p in ci["install"]["plugins"])
        bundles = [s["bundle"] for s in ci["population"]["steps"] if s.get("plugin") == "rampart_20x_playground"]
        manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))
        # the bundles that need the private plugin: pain, and the stackarmor examples and page
        assert bundles == [b for b in manifest["grift"] if b not in ("pain", "stackarmor_examples", "stackarmor_page", "vdr_implementations")]
        assert "stackarmor_vdr" not in {d["slug"] for d in manifest["depends_on"]}
