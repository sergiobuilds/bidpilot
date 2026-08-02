#!/usr/bin/env python3
"""Reveal a previously sealed aggregate and prepare a blind top-two packet."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "run-v2"


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    sealed_path = RUN / "sealed-aggregate.json"
    sealed_bytes = sealed_path.read_bytes()
    sealed = json.loads(sealed_bytes)
    if sealed.get("status") != "SEALED_BEFORE_REVEAL":
        raise ValueError("aggregate was not sealed before reveal")
    identities = load(RUN / "private" / "identity-mapping.json")
    revealed = {
        "status": "REVEALED_AFTER_SEAL",
        "sealed_aggregate_sha256": hashlib.sha256(sealed_bytes).hexdigest(),
        "parity_ranking": [],
        "source_locked_ranking": [],
    }
    for row in sealed["parity_ranking"]:
        revealed["parity_ranking"].append({**row, "identity": identities[row["blind_id"]]})
    for row in sealed["source_locked_ranking"]:
        revealed["source_locked_ranking"].append({**row, "identity": identities[row["blind_id"]]})
    (RUN / "revealed-ranking.json").write_text(
        json.dumps(revealed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    top_ids = [row["blind_id"] for row in sealed["parity_ranking"][:2]]
    cards = load(RUN / "judge" / "candidate-packets.json")
    by_id = {}
    for item in cards:
        by_id.setdefault(item["blind_id"], item["card"])
    packet = {
        "rubric": "official 30 relevance / 40 technical / 30 completeness",
        "pair": top_ids,
        "cards": {blind_id: by_id[blind_id] for blind_id in top_ids},
        "instructions": "Judge only the supplied evidence. Do not infer identities.",
    }
    (RUN / "judge" / "top-two-packet.json").write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(RUN / "revealed-ranking.json")
    print(RUN / "judge" / "top-two-packet.json")


if __name__ == "__main__":
    main()
