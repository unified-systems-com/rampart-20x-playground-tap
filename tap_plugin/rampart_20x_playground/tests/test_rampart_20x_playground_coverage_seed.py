"""The coverage history seed, read from the bundle as written (`req-rampart-20x-playground-coverage-seed-*`).

MOCK DATA. These tests read JSON files only; the live Summary is compared against the last mock point on a booted stack."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

GRIFT = Path(__file__).resolve().parents[1] / "grift"
RESPONSIBILITY_ID = "01a15fdf-61ef-710d-b5d3-e3a7ae238a40"
CLASSIFICATION_ID = "01a15b2f-df3b-7569-bf22-9ead3f816b84"
# The T4 column of each waypoint table: category -> mapped/denominator.
T4_RESPONSIBILITY = {"Applications": (8, 8), "Cloud Services": (18, 18), "Containers": (3, 3), "Crypto": (31, 31), "Libraries": (4, 4),
                     "Operating Systems": (1, 1), "Packages": (180, 180), "Secrets": (3, 4), "Third-Party SaaS": (2, 2)}
T4_CLASSIFICATION = {"Applications": (8, 8), "Cloud Services": (16, 18), "Containers": (2, 3), "Libraries": (3, 4), "Operating Systems": (1, 1),
                     "Packages": (162, 180), "Secrets": (2, 4), "Third-Party SaaS": (1, 2)}


def _batch() -> dict:
    return json.loads((GRIFT / "coverage-seed.grift.json").read_text(encoding="utf-8"))["batches"][0]


class TestCoverageSeed:
    def setup_method(self) -> None:
        self.batch = _batch()
        self.nodes = self.batch["nodes"]
        self.by_id = {n["entity"]["entity_id"]: n for n in self.nodes}
        self.by_search: dict[str, list[dict]] = {RESPONSIBILITY_ID: [], CLASSIFICATION_ID: []}
        for edge in self.batch["edges"]:
            assert edge["edge"]["edge_type"] == "CAPTURES_SEARCH__compliance_core"
            self.by_search[edge["edge"]["to_entity_id"]].append(self.by_id[edge["edge"]["from_entity_id"]])

    def test_thirty_mock_snapshots_per_search_every_four_hours(self) -> None:
        """`coverage-seed-5`, `-6`."""
        assert len(self.nodes) == 60 and len(self.batch["edges"]) == 60
        assert "MOCK DATA" in self.batch["batch_node"]["description"]
        start = datetime(2026, 10, 17, tzinfo=UTC)
        for search_id, snapshots in self.by_search.items():
            assert [s["node"]["observed_at"] for s in snapshots] == [
                (start + timedelta(hours=4 * k)).strftime("%Y-%m-%dT%H:%M:%S.000000Z") for k in range(30)
            ]
            for s in snapshots:
                node = s["node"]
                assert node["source"] == "rampart_20x_playground" and node["snapshot_key"] == f"{search_id}@{node['observed_at']}"
                assert node["truncated"] is False and node["row_count"] == len(node["rows"])

    def test_rows_are_as_the_runner_writes_them(self) -> None:
        """`coverage-seed-7`."""
        for search_id, snapshots in self.by_search.items():
            for s in snapshots:
                labels = [r["label"] for r in s["node"]["rows"]]
                assert labels == sorted(labels, key=lambda x: {"Applications": 0, "Cloud Services": 1, "Containers": 2, "Crypto": 3, "Libraries": 4,
                                                               "Operating Systems": 5, "Packages": 6, "Third-Party SaaS": 7, "Secrets": 8}[x])
                assert ("Crypto" in labels) == (search_id == RESPONSIBILITY_ID)
                for r in s["node"]["rows"]:
                    d = r["denominator"]
                    assert r["unmapped"] == d - r["mapped"] - r["mapped_incorrectly"] and r["no_rule"] == 0
                    assert r["percent_mapped"] == (round(100 * r["mapped"] / d, 1) if d else None)

    def test_the_last_point_is_the_end_state_and_each_chart_climbs(self) -> None:
        """`coverage-seed-3`, `-8`, `-9`."""
        for search_id, t4 in ((RESPONSIBILITY_ID, T4_RESPONSIBILITY), (CLASSIFICATION_ID, T4_CLASSIFICATION)):
            snapshots = self.by_search[search_id]
            last = {r["label"]: (r["mapped"], r["denominator"]) for r in snapshots[-1]["node"]["rows"]}
            assert last == t4

            def overall(s: dict) -> float:
                values = [r["percent_mapped"] for r in s["node"]["rows"] if r["percent_mapped"] is not None]
                return sum(values) / len(values)

            assert overall(snapshots[-1]) > overall(snapshots[0])
        wrong = [r for r in self.by_search[CLASSIFICATION_ID][-1]["node"]["rows"] if r["mapped_incorrectly"]]
        assert [(r["label"], r["mapped_incorrectly"]) for r in wrong] == [("Secrets", 1)]
