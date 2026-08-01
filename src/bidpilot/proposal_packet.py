"""The narrow handoff from opportunity qualification to proposal production."""

from __future__ import annotations

from bidpilot.public_tender import TenderEligibility


def build_proposal_start_packet(tender: dict, eligibility: TenderEligibility) -> dict:
    """Build a source-bound packet that a proposal writer can consume safely.

    It deliberately contains no generated company claims.  A downstream writer
    may draft only after missing supplier evidence has been resolved and the
    opportunity is still open.
    """
    missing = [
        {
            "id": f"supplier-evidence:{check['key']}",
            "question": f"Provide evidence for: {check['label']}",
            "source": check["source"],
        }
        for check in eligibility.checks
        if check["status"] == "EVIDENCE REQUIRED"
    ]
    failed = [check["label"] for check in eligibility.checks if check["status"] == "FAIL"]
    is_draftable = eligibility.recommendation == "ELIGIBLE — COMMERCIAL REVIEW REQUIRED" and tender["is_open"]

    return {
        "packet_version": "1.0",
        "kind": "proposal-start-packet",
        "opportunity": {
            "id": tender["case_id"],
            "title": tender["title"],
            "issuer": tender["issuer"],
            "scope": tender["scope"],
            "contract_value_krw": tender["contract_value_krw"],
            "duration_days": tender["duration_days"],
            "bid_close": tender["bid_close"],
            "is_open": tender["is_open"],
        },
        "source": {
            "url": tender["source_url"],
            "sha256": tender["source_sha256"],
            "retrieved_on": tender["source_retrieved_on"],
            "pages": tender["source_pages"],
        },
        "qualification": {
            "recommendation": eligibility.recommendation,
            "checks": list(eligibility.checks),
            "failed_requirements": failed,
            "missing_evidence": missing,
        },
        "proposal_strategy": {
            "evaluation": tender["evaluation"],
            "writing_gate": "OPEN" if is_draftable else "LOCKED",
            "writing_gate_reason": (
                "All declared supplier requirements are evidenced and the opportunity is open."
                if is_draftable
                else "Resolve supplier evidence and confirm the opportunity is open before drafting."
            ),
        },
    }
