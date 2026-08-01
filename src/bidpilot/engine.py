"""Deterministic bid decisions kept separate from the presentation layer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class BidDecision:
    rfp_id: str
    recommendation: str
    expected_margin: float
    capacity_gap_hours: int
    hard_gate_failures: tuple[str, ...]
    risks: tuple[str, ...]
    rationale: tuple[str, ...]

    @property
    def can_proceed(self) -> bool:
        return self.recommendation == "BID"


def _missing_required(required: Iterable[str], available: Iterable[str]) -> list[str]:
    available_set = set(available)
    return sorted(set(required) - available_set)


def evaluate_bid(rfp: dict, company: dict) -> BidDecision:
    """Evaluate one RFP against a fixed, inspectable business policy."""
    failures: list[str] = []
    risks: list[str] = []
    rationale: list[str] = []

    missing = _missing_required(rfp["required_capabilities"], company["capabilities"])
    if missing:
        failures.append(f"Missing mandatory capability: {', '.join(missing)}")

    capacity_gap = max(0, rfp["required_hours"] - company["available_hours"])
    if capacity_gap:
        failures.append(f"Insufficient delivery capacity: {capacity_gap} hours short")

    estimated_cost = rfp.get(
        "estimated_delivery_cost",
        rfp["required_hours"] * company["loaded_hourly_cost"],
    )
    expected_margin = rfp["contract_value"] - estimated_cost
    margin_rate = expected_margin / rfp["contract_value"]
    if margin_rate < company["minimum_margin_rate"]:
        failures.append(
            f"Margin {margin_rate:.1%} is below policy minimum "
            f"{company['minimum_margin_rate']:.0%}"
        )

    if rfp["deadline_days"] < company["minimum_lead_days"]:
        risks.append("Compressed proposal deadline")
    if rfp["delivery_risk"] == "high":
        risks.append("High delivery complexity")
    if rfp["incumbent_competitor"]:
        risks.append("Incumbent competitor advantage")

    if failures:
        recommendation = "NO-BID"
        rationale.append("One or more non-negotiable bid policy gates failed.")
        rationale.append("Preserve proposal capacity for the next viable opportunity.")
    else:
        recommendation = "BID"
        rationale.append("All mandatory qualification, capacity, and margin gates passed.")
        rationale.append("Create a bounded proposal work plan while risks remain visible.")

    return BidDecision(
        rfp_id=rfp["id"],
        recommendation=recommendation,
        expected_margin=expected_margin,
        capacity_gap_hours=capacity_gap,
        hard_gate_failures=tuple(failures),
        risks=tuple(risks),
        rationale=tuple(rationale),
    )


def decision_trace(rfp: dict, company: dict, decision: BidDecision) -> list[dict]:
    """Return the policy checks shown in the product without hiding any failure."""
    missing = _missing_required(rfp["required_capabilities"], company["capabilities"])
    required_hours = rfp["required_hours"]
    available_hours = company["available_hours"]
    margin_rate = decision.expected_margin / rfp["contract_value"]

    return [
        {
            "gate": "Mandatory capability",
            "policy": "Every mandatory capability must be present",
            "observed": "All present" if not missing else f"Missing: {', '.join(missing)}",
            "passed": not missing,
        },
        {
            "gate": "Delivery capacity",
            "policy": "Available hours must cover delivery effort",
            "observed": f"{available_hours:,}h available / {required_hours:,}h required",
            "passed": decision.capacity_gap_hours == 0,
        },
        {
            "gate": "Margin floor",
            "policy": f"Margin must be at least {company['minimum_margin_rate']:.0%}",
            "observed": f"{margin_rate:.1%} expected margin",
            "passed": margin_rate >= company["minimum_margin_rate"],
        },
    ]


def create_proposal_tasks(rfp: dict, decision: BidDecision) -> list[dict]:
    """Create deterministic internal tasks only after a positive decision."""
    if not decision.can_proceed:
        return []
    return [
        {
            "task": "Confirm solution outline",
            "owner": "Solutions lead",
            "due_in_days": 1,
            "workstream": "Solution",
            "outcome": "A scoped architecture and delivery assumptions",
        },
        {
            "task": "Prepare pricing assumptions",
            "owner": "Commercial lead",
            "due_in_days": 2,
            "workstream": "Commercial",
            "outcome": "A reviewable cost and margin position",
        },
        {
            "task": "Draft compliance matrix",
            "owner": "Bid manager",
            "due_in_days": 2,
            "workstream": "Compliance",
            "outcome": "A requirement-to-evidence response matrix",
        },
        {
            "task": "Run proposal review",
            "owner": "Executive sponsor",
            "due_in_days": max(1, rfp["deadline_days"] - 1),
            "workstream": "Approval",
            "outcome": "A bid-ready decision before the deadline",
        },
    ]
