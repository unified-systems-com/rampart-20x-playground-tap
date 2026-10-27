"""A page and the panels its layout names seed in an order a fresh database accepts.

The page-panels hotlink needs, at the moment a page node is created, a USES_PANEL edge from that page to each
panel its layout names. An edge needs both endpoints, so the page's own bundle must carry the edge and a bundle
holding the panel node must be seeded no later than the page's. A database that already held the page hides the
fault; the first fresh `manage.py boot` of the demo record failed on the Overview page for exactly this reason
(the edge sat in the bundle seeded after the page)."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _bundles() -> dict[str, dict]:
    manifest = tomllib.loads((PACKAGE_ROOT / "tap-plugin.toml").read_text(encoding="utf-8"))["grift"]
    return {name: json.loads((PACKAGE_ROOT / rel).read_text(encoding="utf-8")) for name, rel in manifest.items()}


def _panel_ids(layout: dict) -> list[str]:
    return [
        row["panel-id"]
        for column in layout.get("columns", {}).values()
        for row in column.get("rows", {}).values()
        if "panel-id" in row
    ]


def test_every_page_carries_its_panel_edges_and_follows_its_panel_nodes() -> None:
    bundles = _bundles()
    order = list(bundles)
    edge_home: dict[tuple[str, str], str] = {}  # (page id, panel slug) -> bundle holding the USES_PANEL edge
    panel_home: dict[str, str] = {}  # panel slug -> bundle holding the panel node
    pages: list[tuple[str, str, list[str]]] = []  # (bundle, page id, panel ids named in its layout)
    for name, doc in bundles.items():
        for batch in doc["batches"]:
            for node in batch.get("nodes", []):
                if node["entity"]["entity_type"] == "panel":
                    panel_home[node["node"]["slug"]] = name
                if node["entity"]["entity_type"] == "page" and "layout" in node["node"]:
                    pages.append((name, node["entity"]["entity_id"], _panel_ids(node["node"]["layout"])))
            for edge in batch.get("edges", []):
                hotlink = edge["edge"].get("properties", {}).get("hotlink")
                if edge["edge"]["edge_type"] == "USES_PANEL" and hotlink:
                    edge_home[(edge["edge"]["from_entity_id"], hotlink["value"])] = name
    checked = 0
    for bundle, page_id, panel_ids in pages:
        for panel_id in panel_ids:
            if (page_id, panel_id) not in edge_home:
                continue  # a panel of another plugin or of core: not this plugin's edge to order
            checked += 1
            assert edge_home[(page_id, panel_id)] == bundle, (
                f"page {page_id} in {bundle!r} names panel {panel_id!r}, but its USES_PANEL edge is in "
                f"{edge_home[(page_id, panel_id)]!r}: the page cannot be created without the edge"
            )
            if panel_id in panel_home:
                assert order.index(panel_home[panel_id]) <= order.index(bundle), (
                    f"panel {panel_id!r} (bundle {panel_home[panel_id]!r}) is seeded after page bundle {bundle!r}"
                )
    assert checked >= 2
