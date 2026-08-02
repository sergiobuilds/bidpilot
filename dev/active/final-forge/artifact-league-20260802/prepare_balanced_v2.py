#!/usr/bin/env python3
"""Prepare a balanced blind league where every lane sees every candidate once."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "run-v2"


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def digest(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    candidates = load(ROOT / "candidates.json")
    anchors = load(ROOT / "anchors.json")
    identities = load(ROOT / "run" / "private" / "identity-mapping.json")
    blind_by_name = {value["name"]: key for key, value in identities.items()}
    identities = {
        blind_by_name[candidate["identity"]["name"]]: candidate["identity"]
        for candidate in candidates
    }

    lane_packets = []
    assignments = []
    candidate_packets = []
    for lane in (1, 2, 3):
        lane_anchors = []
        lane_candidates = []
        for index, anchor in enumerate(anchors, 1):
            item = {
                "assignment_id": f"V2-L{lane}-A{index}",
                "blind_id": f"ANCHOR:{lane}:{anchor['level']}",
                "level": anchor["level"],
                "card": anchor["card"],
            }
            lane_anchors.append(item)
            assignments.append({"assignment_id": item["assignment_id"], "lane": lane, "blind_id": item["blind_id"]})
        for index, candidate in enumerate(candidates, 1):
            blind_id = blind_by_name[candidate["identity"]["name"]]
            item = {
                "assignment_id": f"V2-L{lane}-C{index}",
                "blind_id": blind_id,
                "card": candidate["card"],
            }
            lane_candidates.append(item)
            candidate_packets.append({**item, "lane": lane})
            assignments.append({"assignment_id": item["assignment_id"], "lane": lane, "blind_id": blind_id})
        lane_packets.append({"lane": lane, "anchors": lane_anchors, "candidates": lane_candidates})

    for lane in lane_packets:
        ids = [item["blind_id"] for item in lane["candidates"]]
        if len(ids) != 6 or len(set(ids)) != 6:
            raise ValueError(f"lane {lane['lane']} is not one-per-candidate balanced")

    dump(RUN / "judge" / "lane-packets.json", lane_packets)
    dump(RUN / "judge" / "candidate-packets.json", candidate_packets)
    dump(RUN / "protocol" / "assignments.json", assignments)
    dump(RUN / "private" / "identity-mapping.json", identities)
    dump(RUN / "protocol" / "freeze-manifest.json", {
        "protocol_version": 2,
        "candidate_count": 6,
        "lanes": 3,
        "candidate_measurements": 3,
        "one_candidate_per_lane": True,
        "candidates_sha256": digest(candidates),
        "lane_packets_sha256": digest(lane_packets),
    })
    print(json.dumps({
        "lanes": len(lane_packets),
        "assignments": len(assignments),
        "candidates_per_lane": [len(lane["candidates"]) for lane in lane_packets],
    }))


if __name__ == "__main__":
    main()
