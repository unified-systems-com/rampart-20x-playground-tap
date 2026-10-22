"""Structural, strict and loads validation for rampart_20x_playground, plus the identity chain and the
surfaces it deliberately does not have (`req-rampart-20x-playground-nongoals`, `-boot`)."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
from tap.plugin_testing import find_plugin_source_root
from tap_plugins.manifest import load_manifest
from tap_plugins.validate.service import validate_plugin

SLUG = "rampart_20x_playground"
PLUGIN_ROOT = find_plugin_source_root(__file__)
PACKAGE_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    PLUGIN_ROOT is None,
    reason="source-layout validation needs the plugin source tree; installed as a wheel here "
    "(delegated to the plugin repo's own build).",
)


def _raw_manifest() -> dict:
    with (PACKAGE_ROOT / "tap-plugin.toml").open("rb") as fh:
        return tomllib.load(fh)


def _record(name: str) -> dict:
    return json.loads((PACKAGE_ROOT / "boot" / f"{name}.boot.json").read_text(encoding="utf-8"))


class TestValidation:
    """The validator is the authority on structure; do not re-implement its checks here."""

    def test_structure_passes(self) -> None:
        result = validate_plugin(PLUGIN_ROOT, level="structure")
        assert result.ok, result.to_human()

    def test_strict_passes(self) -> None:
        result = validate_plugin(PLUGIN_ROOT, level="structure", strict=True)
        assert result.ok, result.to_human()

    def test_loads_passes(self) -> None:
        result = validate_plugin(PLUGIN_ROOT, level="loads", strict=True)
        assert result.ok, result.to_human()


class TestIdentityChain:
    """`req-tap-plugin-arch-identity`: the validator checks the chain agrees; these assert the VALUES."""

    @staticmethod
    def _pyproject() -> dict:
        assert PLUGIN_ROOT is not None
        with (PLUGIN_ROOT / "pyproject.toml").open("rb") as fh:
            return tomllib.load(fh)

    def test_dist_name(self) -> None:
        from tap.plugin_identity import dist_name_for_slug

        assert self._pyproject()["project"]["name"] == dist_name_for_slug(SLUG) == "rampart-20x-playground-tap"

    def test_entry_point(self) -> None:
        entry_points = self._pyproject()["project"]["entry-points"]["tap.plugins"]
        assert entry_points == {SLUG: "tap_plugin.rampart_20x_playground.apps:Rampart20xPlaygroundConfig"}

    def test_namespace_has_no_init(self) -> None:
        assert PLUGIN_ROOT is not None
        assert not (PLUGIN_ROOT / "tap_plugin" / "__init__.py").exists()

    def test_manifest_slug(self) -> None:
        assert load_manifest(PACKAGE_ROOT).slug == SLUG


class TestSurfaces:
    """What the plugin deliberately does NOT ship (`req-rampart-20x-playground-nongoals-1`)."""

    def test_no_models_no_edges(self) -> None:
        manifest = load_manifest(PACKAGE_ROOT)
        assert manifest.models == []
        assert manifest.edges == []

    def test_grift_bundles(self) -> None:
        grift = load_manifest(PACKAGE_ROOT).grift
        assert sorted(entry.path for entry in grift) == [
            "grift/application-flow.grift.json",
            "grift/classification-mapping.grift.json",
            "grift/coverage-seed.grift.json",
            "grift/data-classification-page.grift.json",
            "grift/dimensions-actors.grift.json",
            "grift/dimensions.grift.json",
            "grift/inventory-coverage.grift.json",
            "grift/inventory-entities.grift.json",
            "grift/inventory-page.grift.json",
            "grift/inventory-software.grift.json",
            "grift/keystone.grift.json",
            "grift/mock-inventory.grift.json",
            "grift/pages.grift.json",
            "grift/pain.grift.json",
            "grift/security-alerts.grift.json",
            "grift/teams.grift.json",
            "grift/vulnerabilities-page.grift.json",
            "grift/vulnerability-enrichment.grift.json",
        ]

    def test_fips_posture_declared(self) -> None:
        assert _raw_manifest()["fips"]["status"] == "compatible"


class TestBootRecords:
    """`req-rampart-20x-playground-boot`. The validator checks digests, closure and credential-freedom."""

    def test_both_records_declared(self) -> None:
        names = {entry["name"] for entry in _raw_manifest()["boot"]["records"]}
        assert names == {"ci", "demo"}

    def test_ci_installs_the_dependency_closure_and_itself(self) -> None:
        installed = [entry["slug"] for entry in _record("ci")["install"]["plugins"]]
        assert installed == ["identity_core", "dcom", "aws_core", "computing_core", "git_core", "compliance_core", "github_core", "fedramp_20x_vdr", SLUG]

    def test_demo_pins_every_released_plugin_by_commit(self) -> None:
        """`req-rampart-20x-playground-boot-2`. Self is unpinned in the first scaffold PR (a record cannot
        carry the commit that introduces it); every other entry must carry a 40-hex commit."""
        for entry in _record("demo")["install"]["plugins"]:
            if entry["slug"] == SLUG:
                continue
            commit = entry["source"].get("commit", "")
            assert len(commit) == 40 and all(c in "0123456789abcdef" for c in commit), entry["slug"]

    def test_demo_installs_siblings_in_dependency_order(self) -> None:
        """`req-rampart-20x-playground-boot-5`. Each entry is installed on its own, so a sibling distribution
        it requires must come earlier in the list. Known constraints from the pinned releases' pyprojects;
        rampart_20x's own dependencies are unread (private repo), so it stays last before this plugin."""
        order = [entry["slug"] for entry in _record("demo")["install"]["plugins"]]
        needs = {
            "github_core": ("git_core", "compliance_core", "identity_core"),
            "fedramp_20x_ksi": ("compliance_core",),
            "fedramp_20x_vdr": ("compliance_core",),
        }
        for slug, deps in needs.items():
            for dep in deps:
                assert order.index(dep) < order.index(slug), f"{dep} must be installed before {slug}"
        assert order[-2:] == ["rampart_20x", SLUG]

    def test_demo_lands_on_the_playground_page(self) -> None:
        """The demo record pins the site root to `/playground` (`req-web-page-landing`): the entity id must
        name the page this plugin seeds, and the slug must be that page's slug."""
        web = _record("demo")["web"]
        bundle = json.loads((PACKAGE_ROOT / "grift" / "pages.grift.json").read_text(encoding="utf-8"))
        pages = {
            node["entity"]["entity_id"]: node["node"]["slug"]
            for batch in bundle["batches"]
            for node in batch["nodes"]
            if node["entity"]["entity_type"] == "page"
        }
        assert pages[web["landing_entity_id"]] == web["landing_slug"] == "/playground"

    def test_excluded_plugins_absent(self) -> None:
        """`req-rampart-20x-playground-boot-4`."""
        for name in ("ci", "demo"):
            slugs = {entry["slug"] for entry in _record(name)["install"]["plugins"]}
            assert not slugs & {"okta", "duo", "teleport", "highbar"}, name
