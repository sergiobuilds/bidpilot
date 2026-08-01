"""Public-source tender case and evidence-first supplier eligibility checks.

The tender facts are a compact extraction from a public G2B attachment.  The
original file is not redistributed in this repository; the source URL and
SHA-256 let a reviewer verify every extracted requirement.
"""

from __future__ import annotations

from dataclasses import dataclass

PUBLIC_TENDER = {
    "case_id": "G2B-R26BK01490484",
    "title": "Information-system DB quality diagnosis and consulting service",
    "issuer": "Daejeon Metropolitan City",
    "notice_number": "Daejeon Metropolitan City Notice 2026-936",
    "contract_value_krw": 70_000_000,
    "duration_days": 180,
    "bid_close": "2026-05-12 10:00 KST",
    "source_url": "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do?bidPbancNo=R26BK01490484&bidPbancOrd=000&fileSeq=2&fileType=&prcmBsneSeCd=03",
    "source_sha256": "a458407f234ef6a827b4075c5dbf0d456f141c3e1f88a46e4be0b9455770a97e",
    "source_retrieved_on": "2026-08-01",
    "source_pages": 9,
    "is_open": False,
    "scope": "Information-system DB error correction and OpenAPI maintenance",
    "evaluation": "Technical 90% (quantitative 20%, qualitative 70%) and price 10%",
    "requirements": (
        {
            "key": "daejeon_headquarters",
            "label": "Head office located in Daejeon",
            "source": "Section 3(a)",
        },
        {
            "key": "software_business_1468",
            "label": "G2B registration as computer-related software business (code 1468)",
            "source": "Section 3(b)",
        },
        {
            "key": "direct_production_8111189901",
            "label": "Direct-production certificate for information-system maintenance service (8111189901)",
            "source": "Section 3(c)",
        },
        {
            "key": "sme_confirmation",
            "label": "Valid SME or small-business confirmation",
            "source": "Section 3(d)",
        },
        {
            "key": "not_large_or_mid_software_business",
            "label": "Not a large or mid-sized software business for this sub-KRW-2B project",
            "source": "Section 3(f)",
        },
        {
            "key": "no_joint_venture",
            "label": "Can perform as a single bidder because joint performance is not allowed",
            "source": "Section 4",
        },
    ),
}


@dataclass(frozen=True)
class TenderEligibility:
    recommendation: str
    passed: int
    failed: int
    unknown: int
    checks: tuple[dict, ...]


def assess_public_tender(tender: dict, supplier_evidence: dict[str, bool]) -> TenderEligibility:
    """Refuse to call a company eligible until every public requirement is evidenced."""
    checks: list[dict] = []
    for requirement in tender["requirements"]:
        value = supplier_evidence.get(requirement["key"])
        if value is True:
            status = "PASS"
        elif value is False:
            status = "FAIL"
        else:
            status = "EVIDENCE REQUIRED"
        checks.append({**requirement, "status": status})

    passed = sum(check["status"] == "PASS" for check in checks)
    failed = sum(check["status"] == "FAIL" for check in checks)
    unknown = sum(check["status"] == "EVIDENCE REQUIRED" for check in checks)
    recommendation = (
        "NO-BID — INELIGIBLE" if failed else "HOLD — EVIDENCE REQUIRED" if unknown else "ELIGIBLE — COMMERCIAL REVIEW REQUIRED"
    )
    return TenderEligibility(
        recommendation=recommendation,
        passed=passed,
        failed=failed,
        unknown=unknown,
        checks=tuple(checks),
    )
