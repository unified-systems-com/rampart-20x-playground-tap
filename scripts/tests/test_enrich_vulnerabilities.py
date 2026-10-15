"""Tests for scripts/enrich_vulnerabilities.py. The fixtures are real alert fields and real CVE records
(req-rampart-20x-playground-vulnenrich-script). Run in a throwaway container:

    python3 -I -m unittest discover -s scripts/tests -v
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
REPO = HERE.parent.parent
GRIFT = REPO / "tap_plugin" / "rampart_20x_playground" / "grift"

_spec = importlib.util.spec_from_file_location("enrich", HERE.parent / "enrich_vulnerabilities.py")
enrich = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(enrich)

ALERTS = json.loads((FIXTURES / "alerts.json").read_text(encoding="utf-8"))


def record(cve: str) -> dict:
    return json.loads((FIXTURES / f"{cve}.json").read_text(encoding="utf-8"))


class ParserTests(unittest.TestCase):
    def test_trivy_language_package(self):
        p = enrich.parse_trivy(ALERTS["trivy_language"])
        self.assertEqual(p["vuln"], "CVE-2026-49265")
        self.assertEqual(p["component"], ("pypi", "oauthlib", "3.3.1"))
        self.assertEqual(p["fixed"], ["4.0.0"])

    def test_trivy_os_package_is_apk(self):
        p = enrich.parse_trivy(ALERTS["trivy_os"])
        self.assertEqual(p["component"][0], "apk")
        self.assertEqual(p["fixed"], ["3.14.8_git20261008-r0"])

    def test_trivy_message_without_a_package_fails_loudly(self):
        bad = {**ALERTS["trivy_language"], "message": "something else entirely"}
        with self.assertRaises(enrich.ParseFailure):
            enrich.parse_trivy(bad)

    def test_grype_splits_the_cve_from_the_package_suffix(self):
        p = enrich.parse_grype(ALERTS["grype"])
        self.assertEqual(p["vuln"], "CVE-2026-77696")
        self.assertEqual(p["component"], ("generic", "openssl-fips-provider", "3.5.8"))

    def test_grype_fix_versions_are_a_list_one_per_release_branch(self):
        p = enrich.parse_grype(ALERTS["grype"])
        self.assertEqual(p["fixed"], ["1.1.1zj", "3.0.23", "3.4.8", "3.5.9", "3.6.5", "4.0.3"])

    def test_grype_suffix_must_equal_the_message_package(self):
        bad = {**ALERTS["grype"], "rule_id": "CVE-2026-77696-some-other-package"}
        with self.assertRaises(enrich.ParseFailure):
            enrich.parse_grype(bad)

    def test_grype_unmapped_package_type_is_not_guessed(self):
        bad = {**ALERTS["grype"], "message": ALERTS["grype"]["message"].replace("UnknownPackage", "RpmPkg")}
        with self.assertRaises(enrich.ParseFailure):
            enrich.parse_grype(bad)

    def test_dependabot_keeps_the_ghsa_as_an_alias(self):
        p = enrich.parse_dependabot(ALERTS["dependabot"])
        self.assertEqual(p["vuln"], "CVE-2026-102275")
        self.assertEqual(p["aliases"], ["GHSA-x33g-cr3x-6449"])
        self.assertEqual(p["package"], ("pypi", "PyJWT"))
        self.assertIsNone(p["component"])

    def test_dependabot_without_a_cve_is_keyed_by_the_ghsa(self):
        p = enrich.parse_dependabot({**ALERTS["dependabot"], "cve_id": None})
        self.assertEqual(p["vuln"], "GHSA-x33g-cr3x-6449")
        self.assertEqual(p["aliases"], [])


class RangeTests(unittest.TestCase):
    def test_inside_and_outside(self):
        self.assertTrue(enrich.in_range("2.13.0", ">= 2.1.0, <= 2.14.0"))
        self.assertFalse(enrich.in_range("2.15.0", ">= 2.1.0, <= 2.14.0"))
        self.assertFalse(enrich.in_range("2.0.9", ">= 2.1.0, <= 2.14.0"))

    def test_open_ended_and_exclusive(self):
        self.assertTrue(enrich.in_range("0.5.4", "< 0.5.5"))
        self.assertFalse(enrich.in_range("0.5.5", "< 0.5.5"))
        self.assertTrue(enrich.in_range("6.0.5", ">= 6.0, < 6.0.6"))

    def test_unorderable_versions_are_false_not_a_guess(self):
        self.assertFalse(enrich.in_range("2.0.0rc1", ">= 2.0.0, < 3"))
        self.assertFalse(enrich.in_range("2.1.0", ">= 2.0.0a1, < 3"))
        self.assertFalse(enrich.in_range("2.1.0", ""))


class RecordTests(unittest.TestCase):
    def test_url_uses_the_thousands_bucket(self):
        self.assertTrue(enrich.cve_url("CVE-2026-49265").endswith("/cves/2026/49xxx/CVE-2026-49265.json"))
        self.assertTrue(enrich.cve_url("CVE-2026-102275").endswith("/cves/2026/102xxx/CVE-2026-102275.json"))

    def test_cna_cvss_and_cisa_ssvc(self):
        r = enrich.extract_record(record("CVE-2026-49265"))
        self.assertEqual(r["cvss"]["cvss_source"], "GitHub_M")
        self.assertEqual(r["cvss"]["cvss_score"], 6.8)
        self.assertEqual(r["cwes"], ["CWE-208"])
        self.assertEqual(r["ssvc"]["exploitation"], "none")
        self.assertEqual(r["ssvc"]["technical_impact"], "total")

    def test_cisa_cvss_is_used_when_the_cna_gives_none(self):
        r = enrich.extract_record(record("CVE-2026-77696"))
        self.assertEqual(r["cvss"]["cvss_source"], "CISA-ADP")
        self.assertEqual(r["cvss"]["cvss_score"], 3.7)

    def test_poc_exploitation_is_read(self):
        self.assertEqual(enrich.extract_record(record("CVE-2026-102275"))["ssvc"]["exploitation"], "poc")


class BuildTests(unittest.TestCase):
    """The pieces together, over a two-alert bundle."""

    def setUp(self):
        def alert(entity_id, kind, body):
            return {"entity": {"entity_id": entity_id, "entity_type": f"github_core__{kind}"}, "node": body}

        self.alerts = {
            "nodes": [
                alert("a1", "code_scanning_alert", {**ALERTS["trivy_language"], "location": {}}),
                alert("a2", "code_scanning_alert", {**ALERTS["sonar"], "location": {}}),
                alert("a3", "dependabot_alert", ALERTS["dependabot"]),
                {"entity": {"entity_id": "f1", "entity_type": "compliance_core__compliance_finding"}, "node": {}},
                {"entity": {"entity_id": "f2", "entity_type": "compliance_core__compliance_finding"}, "node": {}},
                {"entity": {"entity_id": "f3", "entity_type": "compliance_core__compliance_finding"}, "node": {}},
            ],
            "edges": [
                {"edge": {"edge_type": "DETAILS_FINDING__github_core", "from_entity_id": a, "to_entity_id": f}}
                for a, f in (("a1", "f1"), ("a2", "f2"), ("a3", "f3"))
            ],
        }
        self.inventory = {"nodes": [
            {"entity": {"entity_id": "inv-pyjwt", "entity_type": "computing_core__package"},
             "node": {"ecosystem": "pypi", "name": "PyJWT", "version": "2.13.0"}},
        ]}
        self.cache = {cve: {**enrich.extract_record(record(cve)), "url": enrich.cve_url(cve), "fetched_at": "t"}
                      for cve in ("CVE-2026-49265", "CVE-2026-102275")}
        self.kev = {"catalog_version": "t", "entries": {}}
        self.batch, self.report = enrich.build(self.alerts, self.inventory, self.cache, self.kev)

    def types(self):
        return [n["entity"]["entity_type"] for n in self.batch["nodes"]]

    def test_one_scanner_per_tool_and_every_finding_has_exactly_one(self):
        self.assertEqual(self.types().count("compliance_core__compliance_scanner"), 3)  # Trivy, SonarCloud, Dependabot
        inbound = [e["edge"]["to_entity_id"] for e in self.batch["edges"] if e["edge"]["edge_type"].startswith("DETECTS")]
        self.assertEqual(sorted(inbound), ["f1", "f2", "f3"])

    def test_a_code_rule_has_a_scanner_but_no_vulnerability(self):
        concerns = [e["edge"]["from_entity_id"] for e in self.batch["edges"] if e["edge"]["edge_type"].startswith("CONCERNS")]
        self.assertEqual(sorted(concerns), ["f1", "f3"])

    def test_the_inventory_node_is_reused_for_the_dependabot_range(self):
        carries = {(e["edge"]["from_entity_id"], e["edge"]["to_entity_id"]) for e in self.batch["edges"]
                   if e["edge"]["edge_type"].startswith("CARRIES")}
        self.assertIn(("inv-pyjwt", "f3"), carries)
        self.assertNotIn("inv-pyjwt", [n["entity"]["entity_id"] for n in self.batch["nodes"]])

    def test_a_component_the_inventory_lacks_is_minted_without_inventory_dimensions(self):
        minted = [n for n in self.batch["nodes"] if n["entity"]["entity_type"] == "computing_core__package"]
        self.assertEqual([n["node"]["name"] for n in minted], ["oauthlib"])
        self.assertNotIn("inventory", minted[0]["entity"]["dimensions"])
        self.assertNotIn("dcom", minted[0]["entity"]["dimensions"])

    def test_fixed_versions_ride_on_the_edge(self):
        edge = next(e for e in self.batch["edges"]
                    if e["edge"]["edge_type"].startswith("CONCERNS") and e["edge"]["from_entity_id"] == "f1")
        self.assertEqual(edge["edge"]["properties"], {"fixed_versions": ["4.0.0"]})

    def test_unfetched_vulnerability_keeps_nulls_not_blanks(self):
        batch, _ = enrich.build(self.alerts, self.inventory, {}, None)
        v = next(n["node"] for n in batch["nodes"] if n["node"].get("vuln_id") == "CVE-2026-49265")
        self.assertIsNone(v["cvss_score"])
        self.assertIsNone(v["ssvc_exploitation"])
        self.assertIsNone(v["kev"])

    def test_kev_false_only_when_the_catalog_was_read(self):
        v = next(n["node"] for n in self.batch["nodes"] if n["node"].get("vuln_id") == "CVE-2026-49265")
        self.assertIs(v["kev"], False)
        self.assertEqual(v["kev_catalog_version"], "t")

    def test_output_is_deterministic(self):
        again, _ = enrich.build(self.alerts, self.inventory, self.cache, self.kev)
        self.assertEqual(json.dumps(self.batch, sort_keys=True), json.dumps(again, sort_keys=True))


@unittest.skipUnless((GRIFT / "inventory-software.grift.json").exists(), "inventory bundle not on this branch")
class BundleTests(unittest.TestCase):
    """The generated bundle against the real inputs."""

    def test_every_edge_endpoint_exists_and_no_alert_is_unparsed(self):
        alerts = enrich.load_batch(GRIFT / "security-alerts.grift.json")
        inventory = enrich.load_batch(GRIFT / "inventory-software.grift.json")
        batch, report = enrich.build(alerts, inventory, enrich.load_cache(), enrich.load_kev())
        known = {n["entity"]["entity_id"] for b in (alerts, inventory, batch) for n in b["nodes"]}
        for e in batch["edges"]:
            self.assertIn(e["edge"]["from_entity_id"], known)
            self.assertIn(e["edge"]["to_entity_id"], known)
        self.assertEqual(report["failures"], [])


if __name__ == "__main__":
    unittest.main()
