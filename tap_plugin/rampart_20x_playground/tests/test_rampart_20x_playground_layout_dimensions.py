"""The six layout hint keys the bundles stamp each have a declared Dimension node (unified-systems-com/tap#711).

Core keys the dimension map by Dimension node id and refuses a key no installed seed declares. The
mock inventory and application-flow bundles stamp `icon`, `icon_form`, `icon_angle`, `label`, `line`
and `place` for the landing projection to read, and no seed declared them. They are declared here,
not in core, until the tap_viz runtime reads them. The ids are pinned: the map stores them, and a
node keeps its id when it moves to another seed.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

GRIFT = Path(__file__).resolve().parent.parent / "grift"
SEED = GRIFT / "dimensions-actors.grift.json"
BATCH = "rampart-20x-playground Layout Hint Dimensions v0.1.0"
PINNED = {
    "icon": "01a1e5a7-f563-730a-9386-83a0f97a6bdf",
    "icon_form": "01a1e5a7-f563-730a-9386-83a1c2da0e00",
    "icon_angle": "01a1e5a7-f563-730a-9386-83a218c90752",
    "label": "01a1e5a7-f563-730a-9386-83a3b01db297",
    "line": "01a1e5a7-f563-730a-9386-83a40feca1cd",
    "place": "01a1e5a7-f563-730a-9386-83a54dae6a60",
}


def _batches(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["batches"]


def test_the_layout_hint_nodes_are_pinned_uuid7s_in_their_own_batch() -> None:
    (batch,) = [b for b in _batches(SEED) if b["batch_node"]["name"] == BATCH]
    assert uuid.UUID(batch["batch_entity"]["entity_id"]).version == 7
    assert batch["edges"] == []
    assert {n["node"]["name"]: n["entity"]["entity_id"] for n in batch["nodes"]} == PINNED
    for node in batch["nodes"]:
        assert node["entity"]["entity_type"] == "dimension"
        assert uuid.UUID(node["entity"]["entity_id"]).version == 7
        assert node["entity"]["name"] == node["node"]["name"]
        assert node["entity"]["dimensions"] == {"tap.meta": "dimension"}
        assert node["node"]["description"].strip()


def test_every_layout_hint_a_bundle_stamps_is_declared_once() -> None:
    stamped: set[str] = set()
    declared: list[str] = []
    for path in sorted(GRIFT.glob("*.grift.json")):
        for batch in _batches(path):
            for row in [*batch.get("nodes", []), *batch.get("edges", [])]:
                entity = row.get("entity") or {}
                stamped |= set(entity.get("dimensions") or {})
                if entity.get("entity_type") == "dimension":
                    declared.append(entity["name"])
    assert set(PINNED) <= stamped, "a pinned layout hint is no longer stamped by any bundle; retire its node"
    for name in PINNED:
        assert declared.count(name) == 1, f"{name} is declared {declared.count(name)} times across the bundles"
