#!/usr/bin/env python3
"""Demo post-processing: turn the raw alerts on the grid into vulnerabilities, scanners and components.

This is NOT part of the plugin and not a collector. It stands in for a post-collection action until TAP has an
action subsystem (spec-rampart_20x_playground-vulnerability-enrichment.md); the logic is meant to move into node
and edge definitions and an action, not to grow here. Run it by hand, in a throwaway container, never the host
Python and never the running stack:

    python3 -I scripts/enrich_vulnerabilities.py                  # offline; reads the cache
    python3 -I scripts/enrich_vulnerabilities.py --refresh        # fetch CVE records missing from the cache
    python3 -I scripts/enrich_vulnerabilities.py --refresh-all    # refetch every record

It reads the alert bundle and the inventory bundle, never edits either, and writes one additive grift bundle.
Every id it emits is derived from the natural key, so the same inputs give the same bytes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GRIFT = REPO / "tap_plugin" / "rampart_20x_playground" / "grift"
CACHE = Path(__file__).resolve().parent / "vulnerability_enrichment" / "cve-records.json"
KEV_CACHE = Path(__file__).resolve().parent / "vulnerability_enrichment" / "kev-catalog.json"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

ALERTS = "security-alerts.grift.json"
INVENTORY = "inventory-software.grift.json"
OUTPUT = "vulnerability-enrichment.grift.json"

CVE_URL = "https://raw.githubusercontent.com/CVEProject/cvelistV5/main/cves/{year}/{bucket}xxx/{cve}.json"
NS = uuid.uuid5(uuid.NAMESPACE_URL, "tap:rampart_20x_playground:vulnerability-enrichment")

CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$")
# The Dependabot ecosystem name is not a package-URL type; the computing_core ecosystem field is.
DEPENDABOT_ECOSYSTEM = {"pip": "pypi", "npm": "npm"}
# Trivy's rule_name says which kind of package it found. The image is Wolfi, whose manager is apk.
TRIVY_ECOSYSTEM = {"LanguageSpecificPackageVulnerability": "pypi", "OsPackageVulnerability": "apk"}
# Grype's package type from its message. Anything not listed fails loudly instead of being guessed.
GRYPE_ECOSYSTEM = {"UnknownPackage": "generic", "PythonPkg": "pypi", "ApkPkg": "apk"}

TRIVY_PKG = re.compile(r"Package: (?P<name>\S+)\nInstalled Version: (?P<version>\S+)")
TRIVY_FIX = re.compile(r"Fixed Version: (?P<fix>[^\n]*)")
GRYPE_MSG = re.compile(
    r"A (?P<sev>\w+) vulnerability in (?P<type>\w+) package: (?P<name>\S+), version (?P<version>\S+) was found"
)
GRYPE_RULE = re.compile(r"^(?P<cve>CVE-\d{4}-\d{4,})-(?P<pkg>.+)$")


class ParseFailure(Exception):
    """An alert a parser could not read; reconciliation lists it by number."""


# --- ids ---------------------------------------------------------------------------------------------------


def nid(kind: str, *key: str) -> str:
    return str(uuid.uuid5(NS, "|".join((kind, *key))))


def norm_name(ecosystem: str, name: str) -> str:
    n = name.lower()
    return re.sub(r"[-_.]+", "-", n) if ecosystem == "pypi" else n


# --- reading the bundles -----------------------------------------------------------------------------------


def load_batch(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["batches"][0]


def short(entity_type: str) -> str:
    return entity_type.split("__", 1)[-1]


# --- parsers -----------------------------------------------------------------------------------------------


def parse_trivy(a: dict) -> dict:
    m = TRIVY_PKG.search(a["message"])
    if not m or not CVE_RE.match(a["rule_id"]) or a["rule_name"] not in TRIVY_ECOSYSTEM:
        raise ParseFailure(a["message"].splitlines()[0] if a["message"] else "(empty message)")
    fix = TRIVY_FIX.search(a["message"])
    fixed = [f.strip() for f in fix.group("fix").split(",") if f.strip()] if fix else []
    return {
        "vuln": a["rule_id"],
        "component": (TRIVY_ECOSYSTEM[a["rule_name"]], m.group("name"), m.group("version")),
        "fixed": fixed,
        "aliases": [],
    }


def grype_fix_versions(help_text: str) -> list[str]:
    """The `Fix Version` cell of Grype's help table; a comma list, one entry per release branch."""
    rows = [ln for ln in help_text.splitlines() if ln.startswith("|")]
    if len(rows) < 3:
        return []
    header = [c.strip() for c in rows[0].strip("|").split("|")]
    cells = [c.strip() for c in rows[2].strip("|").split("|")]
    if "Fix Version" not in header or len(cells) != len(header):
        raise ParseFailure("Grype help table has no Fix Version column")
    cell = cells[header.index("Fix Version")]
    return [f.strip() for f in cell.split(",") if f.strip()]


def parse_grype(a: dict) -> dict:
    rule = GRYPE_RULE.match(a["rule_id"])
    msg = GRYPE_MSG.search(a["message"])
    if not rule or not msg:
        raise ParseFailure(a["message"].splitlines()[0] if a["message"] else "(empty message)")
    if rule.group("pkg") != msg.group("name"):
        raise ParseFailure(f"rule_id suffix {rule.group('pkg')!r} is not the message package {msg.group('name')!r}")
    if msg.group("type") not in GRYPE_ECOSYSTEM:
        raise ParseFailure(f"unmapped Grype package type {msg.group('type')!r}")
    return {
        "vuln": rule.group("cve"),
        "component": (GRYPE_ECOSYSTEM[msg.group("type")], msg.group("name"), msg.group("version")),
        "fixed": grype_fix_versions(a["configuration"]["rule"].get("help", "")),
        "aliases": [],
    }


def parse_dependabot(a: dict) -> dict:
    eco = DEPENDABOT_ECOSYSTEM.get(a["ecosystem"])
    if eco is None or not a.get("ghsa_id"):
        raise ParseFailure(f"unmapped Dependabot ecosystem {a['ecosystem']!r} or no GHSA id")
    cve = a.get("cve_id") or ""
    vuln = cve if CVE_RE.match(cve) else a["ghsa_id"]
    fixed = [a["first_patched_version"]] if a.get("first_patched_version") else []
    return {
        "vuln": vuln,
        "component": None,  # an installed version is not stated; linked by range below, or not at all
        "package": (eco, a["package_name"]),
        "range": a.get("vulnerable_version_range") or "",
        "fixed": fixed,
        "aliases": [a["ghsa_id"]] if vuln != a["ghsa_id"] else [],
    }


def version_key(v: str) -> tuple[int, ...] | None:
    """Numeric release tuple, or None when the version carries anything the comparison cannot order."""
    if not re.fullmatch(r"\d+(\.\d+)*", v):
        return None
    return tuple(int(p) for p in v.split("."))


def in_range(version: str, spec: str) -> bool:
    """Whether `version` satisfies Dependabot's `>= 2.1.0, <= 2.14.0`. Unorderable input is `False`, not a guess."""
    key = version_key(version)
    if key is None or not spec.strip():
        return False
    ops = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, "<": lambda a, b: a < b,
           "=": lambda a, b: a == b}
    for clause in spec.split(","):
        m = re.fullmatch(r"\s*(>=|<=|>|<|=)\s*(\S+)\s*", clause)
        if not m:
            return False
        bound = version_key(m.group(2))
        if bound is None:
            return False
        width = max(len(key), len(bound))
        pad = lambda t: t + (0,) * (width - len(t))  # noqa: E731
        if not ops[m.group(1)](pad(key), pad(bound)):
            return False
    return True


# --- public records ----------------------------------------------------------------------------------------


def cve_url(cve: str) -> str:
    _, year, num = cve.split("-")
    return CVE_URL.format(year=year, bucket=int(num) // 1000, cve=cve)


def first_en(descs: list[dict]) -> str | None:
    for d in descs or []:
        if d.get("lang", "").startswith("en"):
            return d.get("value")
    return None


CVSS_KEYS = ("cvssV3_1", "cvssV3_0", "cvssV4_0", "cvssV2_0")


def cvss_from(container: dict) -> dict | None:
    for m in container.get("metrics", []) or []:
        for k in CVSS_KEYS:
            if k in m and m[k].get("baseScore") is not None:
                c = m[k]
                return {
                    "cvss_score": c["baseScore"],
                    "cvss_vector": c.get("vectorString"),
                    "cvss_version": c.get("version") or k.replace("cvssV", "").replace("_", "."),
                    "cvss_source": container.get("providerMetadata", {}).get("shortName"),
                }
    return None


def cwes_from(container: dict) -> list[str]:
    out = []
    for pt in container.get("problemTypes", []) or []:
        for d in pt.get("descriptions", []) or []:
            if d.get("cweId"):
                out.append(d["cweId"])
    return out


def extract_record(rec: dict) -> dict:
    """Pull the fields the vulnerability node holds out of a CVE JSON 5 record (CNA plus CISA-ADP containers)."""
    cna = rec["containers"]["cna"]
    adps = rec["containers"].get("adp", []) or []
    cisa = next((a for a in adps if a.get("providerMetadata", {}).get("shortName") == "CISA-ADP"), None)
    out = {
        "found": True,
        "title": cna.get("title"),
        "description": first_en(cna.get("descriptions", [])),
        "published_at": rec["cveMetadata"].get("datePublished"),
        "record_updated_at": rec["cveMetadata"].get("dateUpdated"),
        "cvss": cvss_from(cna) or (cvss_from(cisa) if cisa else None),
        "cwes": cwes_from(cna) or (cwes_from(cisa) if cisa else []),
        "ssvc": None,
    }
    for m in (cisa or {}).get("metrics", []) or []:
        other = m.get("other") or {}
        if other.get("type") == "ssvc":
            opts = {k: v for o in other["content"].get("options", []) for k, v in o.items()}
            out["ssvc"] = {
                "exploitation": opts.get("Exploitation"),
                "automatable": opts.get("Automatable"),
                "technical_impact": opts.get("Technical Impact"),
                "assessed_at": other["content"].get("timestamp"),
            }
    return out


def fetch_record(cve: str) -> dict:
    url = cve_url(cve)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with urllib.request.urlopen(url, timeout=30) as r:  # noqa: S310 - fixed https host
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"found": False, "url": url, "fetched_at": now}
        raise
    return {**extract_record(data), "url": url, "fetched_at": now}


def fetch_kev() -> dict:
    """CISA's Known Exploited Vulnerabilities catalog: the one authoritative source for the KEV flag."""
    with urllib.request.urlopen(KEV_URL, timeout=60) as r:  # noqa: S310 - fixed https host
        data = json.loads(r.read().decode("utf-8"))
    return {
        "url": KEV_URL,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "catalog_version": data["catalogVersion"],
        "date_released": data["dateReleased"],
        "count": data["count"],
        "entries": {v["cveID"]: v["dateAdded"] for v in sorted(data["vulnerabilities"], key=lambda v: v["cveID"])},
    }


def load_kev() -> dict | None:
    return json.loads(KEV_CACHE.read_text(encoding="utf-8")) if KEV_CACHE.exists() else None


def save_kev(kev: dict) -> None:
    KEV_CACHE.parent.mkdir(parents=True, exist_ok=True)
    KEV_CACHE.write_text(json.dumps(kev, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_cache() -> dict:
    return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}


def save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(dict(sorted(cache.items())), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# --- building ----------------------------------------------------------------------------------------------


def node(entity_id: str, entity_type: str, name: str, dims: dict, body: dict) -> dict:
    return {"entity": {"entity_id": entity_id, "entity_type": entity_type, "name": name, "dimensions": dims},
            "node": body}


# Inventory rows the SBOM parser wrote carry a batch-local ref, not an entity id, and a ref cannot name a row in
# another batch. A component linked from here is therefore written into this batch again, as the same row with the
# same natural key, so the import merges it into the inventory's node. `REFS` holds those tokens.
REFS: set[str] = set()


def end(side: str, token: str) -> dict:
    return {f"{side}_ref" if token in REFS else f"{side}_entity_id": token}


def edge(from_id: str, to_id: str, edge_type: str, dims: dict, props: dict | None = None) -> dict:
    return {
        "entity": {
            "entity_id": nid("edge", edge_type, from_id, to_id),
            "entity_type": "edge",
            "name": f"{from_id} --[{edge_type}]--> {to_id}",
            "dimensions": dims,
        },
        "edge": {**end("from", from_id), **end("to", to_id), "edge_type": edge_type, "properties": props or {}},
    }


def vulnerability_body(vuln: str, aliases: set[str], record: dict | None, dependabot: list[dict],
                       kev: dict | None) -> dict:
    """Merge a record with Dependabot's advisory fields. A field neither supplies stays null (unobserved)."""
    rec = record if record and record.get("found") else None
    dep = dependabot[0] if dependabot else None
    cvss = rec["cvss"] if rec else None
    if cvss is None and dep and dep.get("cvss_score") is not None:
        vec = dep.get("cvss_vector") or ""
        ver = re.match(r"CVSS:(\d\.\d)/", vec)
        cvss = {"cvss_score": dep["cvss_score"], "cvss_vector": vec or None,
                "cvss_version": ver.group(1) if ver else None, "cvss_source": "GitHub Dependabot"}
    cwes = (rec["cwes"] if rec else []) or (dep.get("cwes") if dep else []) or ([] if rec or dep else None)
    ssvc = rec["ssvc"] if rec else None
    return {
        "vuln_id": vuln,
        "aliases": sorted(aliases),
        "title": (rec["title"] if rec else None) or (dep.get("advisory_summary") if dep else None),
        "description": (rec["description"] if rec else None) or (dep.get("advisory_description") if dep else None),
        "published_at": rec["published_at"] if rec else None,
        "cvss_score": cvss["cvss_score"] if cvss else None,
        "cvss_vector": cvss["cvss_vector"] if cvss else None,
        "cvss_version": cvss["cvss_version"] if cvss else None,
        "cvss_source": cvss["cvss_source"] if cvss else None,
        "cwes": cwes,
        "ssvc_exploitation": ssvc["exploitation"] if ssvc else None,
        "ssvc_automatable": ssvc["automatable"] if ssvc else None,
        "ssvc_technical_impact": ssvc["technical_impact"] if ssvc else None,
        "ssvc_assessed_at": ssvc["assessed_at"] if ssvc else None,
        "kev": (vuln in kev["entries"]) if kev and CVE_RE.match(vuln) else None,
        "kev_added": kev["entries"].get(vuln) if kev and CVE_RE.match(vuln) else None,
        "kev_catalog_version": kev["catalog_version"] if kev and CVE_RE.match(vuln) else None,
        "record_url": rec["url"] if rec else None,
        "record_updated_at": rec["record_updated_at"] if rec else None,
    }


def build(alerts_batch: dict, inventory_batch: dict, cache: dict, kev: dict | None) -> tuple[dict, dict]:
    types = {n["entity"]["entity_id"]: n["entity"]["entity_type"] for n in alerts_batch["nodes"]}
    finding_of = {}
    for e in alerts_batch["edges"]:
        x = e["edge"]
        if x["edge_type"].startswith("DETAILS_FINDING"):
            finding_of[x["from_entity_id"]] = x["to_entity_id"]

    # Inventory components by (ecosystem, normalised name, version), both packages and libraries.
    inventory = {}
    inventory_rows = {}
    REFS.clear()
    for n in inventory_batch["nodes"]:
        if n["entity"]["entity_type"] in ("computing_core__package", "computing_core__library"):
            b = n["node"]
            token = n["entity"].get("entity_id") or n["entity"]["ref"]
            if "ref" in n["entity"] and "entity_id" not in n["entity"]:
                REFS.add(token)
            inventory[(b["ecosystem"], norm_name(b["ecosystem"], b["name"]), b["version"])] = token
            inventory_rows[token] = n

    stats = defaultdict(Counter)
    parsed = []  # one per alert that has a vulnerability
    scanners = {}  # key -> name
    detects = []  # (scanner_key, finding_id, props)
    failures = []

    for n in alerts_batch["nodes"]:
        kind = short(n["entity"]["entity_type"])
        if kind not in ("code_scanning_alert", "dependabot_alert"):
            continue
        a, aid = n["node"], n["entity"]["entity_id"]
        finding = finding_of[aid]
        tool = a["tool_name"] if kind == "code_scanning_alert" else "Dependabot"
        key = scanners_key(tool)
        scanners[key] = tool
        props = {k: v for k, v in (("tool_version", a.get("tool_version")), ("category", a.get("category"))) if v}
        detects.append((key, finding, props))
        stats[tool]["read"] += 1
        try:
            if tool == "Trivy":
                p = parse_trivy(a)
            elif tool == "Grype":
                p = parse_grype(a)
            elif tool == "Dependabot":
                p = parse_dependabot(a)
            elif re.search(r"CVE-\d{4}-\d+|GHSA-", a["rule_id"]):
                raise ParseFailure(f"{tool} rule {a['rule_id']!r} names a vulnerability but no parser reads {tool}")
            else:
                stats[tool]["not parsed (no CVE by design)"] += 1  # a code rule, not a vulnerability in a component
                continue
        except ParseFailure as e:
            stats[tool]["failed"] += 1
            failures.append((tool, a["number"], str(e)))
            continue
        stats[tool]["parsed"] += 1
        parsed.append({"tool": tool, "finding": finding, "alert": a, **p})

    # Components named by Trivy and Grype.
    comp_ids: dict[tuple, str] = {}
    minted: dict[tuple, str] = {}
    for p in parsed:
        c = p["component"]
        if c is None:
            continue
        look = (c[0], norm_name(c[0], c[1]), c[2])
        if look in inventory:
            comp_ids[c] = inventory[look]
        else:
            comp_ids[c] = nid("component", *c)
            minted[c] = comp_ids[c]
    # Dependabot names no version: link it to the known components of that package that its range covers.
    known = {(c[0], norm_name(c[0], c[1]), c[2]): (c, cid) for c, cid in comp_ids.items()}
    for key, cid in inventory.items():
        known.setdefault(key, (None, cid))
    for p in parsed:
        p["components"] = [comp_ids[p["component"]]] if p["component"] else []
        if p["component"] is None:
            eco, name = p["package"]
            want = norm_name(eco, name)
            p["components"] = sorted({cid for (e, nn, v), (_, cid) in known.items()
                                      if e == eco and nn == want and in_range(v, p["range"])})

    # Vulnerabilities.
    by_vuln = defaultdict(list)
    for p in parsed:
        by_vuln[p["vuln"]].append(p)
    refresh_needed = sorted(v for v in by_vuln if CVE_RE.match(v) and v not in cache)

    nodes, edges = [], []
    vuln_ids = {}
    for vuln in sorted(by_vuln):
        group = by_vuln[vuln]
        aliases = {al for p in group for al in p["aliases"]}
        dep_alerts = [p["alert"] for p in group if p["tool"] == "Dependabot"]
        body = vulnerability_body(vuln, aliases, cache.get(vuln), dep_alerts, kev)
        vuln_ids[vuln] = nid("vulnerability", vuln)
        nodes.append(node(vuln_ids[vuln], "compliance_core__compliance_vulnerability", vuln,
                          {"compliance": "vulnerability"}, body))

    for key, name in sorted(scanners.items()):
        nodes.append(node(nid("scanner", key), "compliance_core__compliance_scanner", name,
                          {"compliance": "scanner"}, {"scanner_key": key, "name": name}))

    linked = {cid for p in parsed for cid in p["components"]}
    for token in sorted(linked & REFS):
        nodes.append(inventory_rows[token])  # the inventory's own row, so the import merges on its natural key
    for c, cid in sorted(minted.items()):
        eco, name, version = c
        etype = "computing_core__library" if eco == "generic" else "computing_core__package"
        body = {"ecosystem": eco, "name": name, "version": version}
        if etype == "computing_core__package":  # a library row has no source_document field
            body["source_document"] = "code scanning alert"
        nodes.append(node(cid, etype, name, {"tap.computing": "runtime"}, body))

    for p in sorted(parsed, key=lambda q: (q["vuln"], q["finding"])):
        edges.append(edge(p["finding"], vuln_ids[p["vuln"]], "CONCERNS_COMPLIANCE_VULNERABILITY__compliance_core",
                          {"compliance": "vulnerability"}, {"fixed_versions": p["fixed"]}))
        for cid in p["components"]:
            edges.append(edge(cid, p["finding"], "CARRIES_COMPLIANCE_FINDING__compliance_core",
                              {"compliance": "finding"}))
    for key, finding, props in sorted(detects, key=lambda d: (d[0], d[1])):
        edges.append(edge(nid("scanner", key), finding, "DETECTS_COMPLIANCE_FINDING__compliance_core",
                          {"compliance": "finding"}, props))

    seen, uniq = set(), []
    for e in edges:
        if e["entity"]["entity_id"] not in seen:
            seen.add(e["entity"]["entity_id"])
            uniq.append(e)

    report = {
        "stats": stats, "failures": failures, "vulns": by_vuln, "cache": cache, "refresh_needed": refresh_needed,
        "minted": minted, "reused": {c: cid for c, cid in comp_ids.items() if c not in minted},
        "kev": kev, "parsed": parsed, "findings": sum(1 for _ in detects),
        "dependabot_unlinked": sum(1 for p in parsed if p["tool"] == "Dependabot" and not p["components"]),
    }
    batch = {
        "batch_entity": {"entity_id": nid("batch"), "entity_type": "batch",
                         "name": "tap vulnerability enrichment (scanners, vulnerabilities, components)",
                         "dimensions": {}},
        "batch_node": {
            "source": "tap_plugin.rampart_20x_playground.grift.vulnerability-enrichment",
            "name": "tap vulnerability enrichment (scanners, vulnerabilities, components)",
            "description": (
                "GENERATED by scripts/enrich_vulnerabilities.py from security-alerts.grift.json, "
                "inventory-software.grift.json and the CVE records cached in scripts/vulnerability_enrichment. "
                "Adds one scanner node per tool, one vulnerability node per CVE or GHSA id (CVSS, CWE, SSVC and KEV "
                "from the CVE Program record and CISA's Vulnrichment container, each field null where no record "
                "says), the components the inventory does not already hold, and the edges that tie them to the "
                "existing findings. Demo post-processing standing in for a post-collection action; do not edit by "
                "hand."
            ),
        },
        "nodes": nodes,
        "edges": uniq,
    }
    return batch, report


def scanners_key(tool: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", tool.lower()).strip("-")


# --- reconciliation ----------------------------------------------------------------------------------------


def reconcile(report: dict, batch: dict) -> bool:
    ok = True
    print("\nReconciliation")
    print(f"{'source':<12}{'read':>6}{'parsed':>8}{'by design':>11}{'failed':>8}")
    for tool, c in sorted(report["stats"].items()):
        by_design = c["not parsed (no CVE by design)"]
        closes = c["parsed"] + by_design + c["failed"] == c["read"]
        ok &= closes
        print(f"{tool:<12}{c['read']:>6}{c['parsed']:>8}{by_design:>11}{c['failed']:>8}{'' if closes else '  DOES NOT CLOSE'}")
    for tool, number, why in report["failures"]:
        print(f"  FAILED {tool} #{number}: {why}")
    ok &= not report["failures"]

    cache, vulns = report["cache"], report["vulns"]
    with_rec = sum(1 for v in vulns if cache.get(v, {}).get("found"))
    print(f"\nvulnerabilities: {len(vulns)}  with a record: {with_rec}  "
          f"without: {len(vulns) - with_rec}  not yet fetched: {len(report['refresh_needed'])}")
    ssvc = sum(1 for v in vulns if cache.get(v, {}).get("ssvc"))
    kev = report["kev"]
    kev_text = (f"on the KEV list: {sum(1 for v in vulns if v in kev['entries'])} (catalog {kev['catalog_version']})"
                if kev else "KEV catalog not fetched")
    print(f"                 SSVC present: {ssvc}  {kev_text}")
    with_comp = sum(1 for p in report["parsed"] if p["components"])
    print(f"findings with a vulnerability: {len(report['parsed'])}  of those with a component: {with_comp}  "
          f"Dependabot with none: {report['dependabot_unlinked']}")
    print(f"components: reused from the inventory {len(report['reused'])}, minted {len(report['minted'])}")
    ids = [n["entity"].get("entity_id") or n["entity"]["ref"] for n in batch["nodes"]]
    ok &= len(ids) == len(set(ids))
    inbound = Counter(e["edge"]["to_entity_id"] for e in batch["edges"]
                      if e["edge"]["edge_type"].startswith("DETECTS"))
    ok &= all(c == 1 for c in inbound.values()) and len(inbound) == report["findings"]
    print(f"findings with exactly one scanner: {sum(1 for c in inbound.values() if c == 1)} of {report['findings']}")
    print("RESULT:", "closes" if ok else "DOES NOT CLOSE")
    return ok


# --- main --------------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--alerts", type=Path, default=GRIFT / ALERTS)
    ap.add_argument("--inventory", type=Path, default=GRIFT / INVENTORY)
    ap.add_argument("--out", type=Path, default=GRIFT / OUTPUT)
    ap.add_argument("--refresh", action="store_true", help="fetch CVE records missing from the cache")
    ap.add_argument("--refresh-all", action="store_true", help="refetch every CVE record")
    args = ap.parse_args(argv)

    alerts, inventory = load_batch(args.alerts), load_batch(args.inventory)
    cache, kev = load_cache(), load_kev()
    batch, report = build(alerts, inventory, cache, kev)

    if args.refresh or args.refresh_all:
        todo = sorted(v for v in report["vulns"] if CVE_RE.match(v) and (args.refresh_all or v not in cache))
        print(f"fetching {len(todo)} CVE record(s) from cvelistV5")
        for i, cve in enumerate(todo, 1):
            cache[cve] = fetch_record(cve)
            print(f"  [{i}/{len(todo)}] {cve} {'found' if cache[cve]['found'] else 'NOT FOUND'}")
            time.sleep(0.1)
        save_cache(cache)
        print("fetching the CISA KEV catalog")
        kev = fetch_kev()
        save_kev(kev)
        batch, report = build(alerts, inventory, cache, kev)

    args.out.write_text(json.dumps({"metadata": {"grift_version": "0"}, "_reserved": {}, "batches": [batch]},
                                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({len(batch['nodes'])} nodes, {len(batch['edges'])} edges)")
    return 0 if reconcile(report, batch) else 1


if __name__ == "__main__":
    sys.exit(main())
