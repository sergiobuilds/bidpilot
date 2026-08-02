#!/usr/bin/env python3
"""Aggregate the frozen 30/40/30 blind league without revealing identities."""

from __future__ import annotations

import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "run"
AXES = {"relevance": 30, "technical": 40, "completeness": 30}


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def total(scores: dict[str, int]) -> int:
    return sum(scores.values())


def validate_scores(scores: dict[str, int]) -> None:
    if set(scores) != set(AXES):
        raise ValueError(f"score axes mismatch: {scores}")
    for axis, maximum in AXES.items():
        value = scores[axis]
        if not isinstance(value, int) or not 0 <= value <= maximum:
            raise ValueError(f"invalid {axis} score: {value}")


def main() -> None:
    anchors = {item["level"]: item["expected_total"] for item in load(ROOT / "anchors.json")}
    lane_packets = load(RUN / "judge" / "lane-packets.json")
    expected_assignments = {
        item["assignment_id"]: item["blind_id"]
        for lane in lane_packets
        for group in ("anchors", "candidates")
        for item in lane[group]
    }

    results = []
    offsets: dict[str, dict[str, float]] = {}
    for lane in (1, 2, 3):
        lane_results = load(RUN / "judge" / f"lane-{lane}-results.json")
        if len(lane_results) != 9:
            raise ValueError(f"lane {lane}: expected 9 results, got {len(lane_results)}")
        for item in lane_results:
            if item["assignment_id"] not in expected_assignments:
                raise ValueError(f"unknown assignment: {item['assignment_id']}")
            if item["blind_id"] != expected_assignments[item["assignment_id"]]:
                raise ValueError(f"assignment/blind mismatch: {item['assignment_id']}")
            validate_scores(item["scores"])
            validate_scores(item["source_locked_scores"])
            item["lane"] = lane
        results.extend(lane_results)

        lane_anchors = [item for item in lane_results if item["blind_id"].startswith("ANCHOR:")]
        if len(lane_anchors) != 3:
            raise ValueError(f"lane {lane}: expected 3 anchors")
        parity_deltas = []
        source_deltas = []
        for item in lane_anchors:
            level = item["blind_id"].rsplit(":", 1)[-1]
            parity_deltas.append(anchors[level] - total(item["scores"]))
            source_deltas.append(anchors[level] - total(item["source_locked_scores"]))
        offsets[str(lane)] = {
            "parity": statistics.median(parity_deltas),
            "source_locked": statistics.median(source_deltas),
        }

    if len({item["assignment_id"] for item in results}) != 27:
        raise ValueError("assignment coverage is incomplete or duplicated")

    candidate_ids = sorted({item["blind_id"] for item in results if not item["blind_id"].startswith("ANCHOR:")})
    rows = []
    for blind_id in candidate_ids:
        samples = [item for item in results if item["blind_id"] == blind_id]
        if len(samples) != 3:
            raise ValueError(f"{blind_id}: expected 3 measurements, got {len(samples)}")
        parity_raw = [total(item["scores"]) for item in samples]
        source_raw = [total(item["source_locked_scores"]) for item in samples]
        parity_calibrated = [max(0, min(100, score + offsets[str(item["lane"])]["parity"])) for score, item in zip(parity_raw, samples)]
        source_calibrated = [max(0, min(100, score + offsets[str(item["lane"])]["source_locked"])) for score, item in zip(source_raw, samples)]
        rows.append({
            "blind_id": blind_id,
            "measurements": 3,
            "parity": {
                "median_calibrated_total": statistics.median(parity_calibrated),
                "median_raw_total": statistics.median(parity_raw),
                "range_calibrated": [min(parity_calibrated), max(parity_calibrated)],
                "stdev_calibrated": round(statistics.pstdev(parity_calibrated), 3),
                "median_axes": {axis: statistics.median(item["scores"][axis] for item in samples) for axis in AXES},
            },
            "source_locked": {
                "median_calibrated_total": statistics.median(source_calibrated),
                "median_raw_total": statistics.median(source_raw),
                "range_calibrated": [min(source_calibrated), max(source_calibrated)],
                "stdev_calibrated": round(statistics.pstdev(source_calibrated), 3),
                "median_axes": {axis: statistics.median(item["source_locked_scores"][axis] for item in samples) for axis in AXES},
            },
            "median_confidence": statistics.median(item["confidence"] for item in samples),
            "evidence_gaps": sorted({gap for item in samples for gap in item.get("evidence_gaps", [])}),
        })

    parity_ranking = sorted(rows, key=lambda row: (-row["parity"]["median_calibrated_total"], row["blind_id"]))
    source_ranking = sorted(rows, key=lambda row: (-row["source_locked"]["median_calibrated_total"], row["blind_id"]))
    sealed = {
        "status": "SEALED_BEFORE_REVEAL",
        "rubric": "official 30 relevance / 40 technical / 30 completeness",
        "candidate_count": len(candidate_ids),
        "measurements_per_candidate": 3,
        "anchor_offsets": offsets,
        "parity_ranking": [{"rank": index, **row} for index, row in enumerate(parity_ranking, 1)],
        "source_locked_ranking": [
            {"rank": index, "blind_id": row["blind_id"], **row["source_locked"]}
            for index, row in enumerate(source_ranking, 1)
        ],
    }
    output = RUN / "sealed-aggregate.json"
    output.write_text(json.dumps(sealed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
