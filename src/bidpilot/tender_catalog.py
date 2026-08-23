"""Public-safe G2B opportunity catalogue for the BidPilot dashboard."""

from __future__ import annotations

import json
from pathlib import Path

from bidpilot.g2b_source import load_public_source

_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "public-tenders" / "catalog.json"
)


def _load_source_found_contract() -> dict[str, object]:
    contract = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    if not isinstance(contract, dict) or not isinstance(contract.get("records"), list):
        raise TypeError("public tender catalogue must contain a records list")
    return contract


def load_public_tender_catalog() -> tuple[dict[str, object], ...]:
    """Return one reviewed contract plus source-found discovery records."""
    source = load_public_source()
    facts = {
        item["field"]: item["value"]
        for item in source["public_projection"]["source_facts"]
    }
    weights = facts["evaluation_weights"]
    notice = next(
        item for item in source["artifacts"] if item["artifact_id"] == "notice-pdf"
    )
    reviewed = {
        "notice_number": source["notice_number"],
        "title": facts["title"],
        "issuer": facts["issuer"],
        "deadline": facts["proposal_deadline"],
        "contract_value_krw": facts["contract_value_krw"],
        "technical_weight": weights["technical"],
        "price_weight": weights["price"],
        "status": "REVIEW",
        "evidence_level": "source-reviewed",
        "retrieved_at": notice["retrieved_at"],
        "official_url": notice["official_url"],
    }
    contract = _load_source_found_contract()
    records = contract["records"]
    discovered = tuple(
        {
            "notice_number": row["notice_number"],
            "title": row["title"],
            "issuer": row["issuer"],
            "deadline": row["proposal_deadline"],
            "official_url": row["official_url"],
            "contract_value_krw": None,
            "technical_weight": None,
            "price_weight": None,
            "status": "SOURCE FOUND",
            "evidence_level": "source-found",
            "retrieved_at": contract["retrieved_at"],
            "verification_method": contract["verification_method"],
            "verified_fields": tuple(contract["verified_fields"]),
            "unverified_fields": tuple(contract["unverified_fields"]),
        }
        for row in records
    )
    return (reviewed, *discovered)
