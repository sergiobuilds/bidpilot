"""Proposal drafting from a qualified public tender and a supplier profile."""

from __future__ import annotations

from bidpilot.pursuit import PursuitBrief, WinPosition


def write_proposal_draft(tender: dict, company_name: str, positioning: str) -> str:
    """Produce an editable proposal brief without binding the product to HWPX."""
    supplier = company_name.strip() or "[Supplier name]"
    strengths = positioning.strip() or "[Describe the delivery team, comparable work, and differentiators]"
    return f"""# {tender['title']}

## Executive summary

{supplier} proposes a focused delivery program for {tender['scope'].lower()}. The program is designed to improve operational reliability, resolve priority data-quality issues, and establish a maintainable OpenAPI operating model within the {tender['duration_days']}-day delivery window.

## Understanding of the engagement

The engagement requires two outcomes: measurable improvement of information-system DB quality and sustainable OpenAPI maintenance. The delivery approach therefore combines an early diagnosis of priority defects with controlled remediation, regression checks, and an operating handoff for the responsible public-sector team.

## Technical approach

1. **Baseline and prioritization.** Inventory critical DB domains, define quality rules, and rank defects by service impact and remediation complexity.
2. **Remediation and OpenAPI maintenance.** Correct approved defects, document data contracts, and maintain API behavior through versioned change control.
3. **Validation and handoff.** Run agreed quality checks, record unresolved items, and transfer operating guidance with an implementation backlog.

## Delivery plan

| Phase | Indicative timing | Deliverable |
|---|---:|---|
| Diagnose | Days 1–30 | Baseline quality report and prioritized remediation backlog |
| Remediate | Days 31–130 | Corrected priority defects and maintained OpenAPI changes |
| Validate and hand over | Days 131–{tender['duration_days']} | Validation report, operating guide, and handoff backlog |

## Delivery capability

{strengths}

## Evaluation strategy

The notice weights technical evaluation at 90% and price at 10%. The proposal should therefore lead with a credible technical delivery plan, measurable quality-control approach, clear operating handoff, and the delivery team’s relevant execution capability.

## Submission checklist

- Confirm every participation condition before bid submission.
- Tailor team and delivery capability statements to the final company profile.
- Convert this brief into the buyer’s required proposal format and submit it with the required administrative documents.
"""


def write_strategy_proposal(tender: dict, supplier: dict, brief: PursuitBrief) -> str:
    """Write criterion-led sections from a persisted Pursuit Brief contract."""
    if not brief.can_generate_proposal:
        raise ValueError(f"Proposal generation is blocked for {brief.status} opportunities.")
    if brief.opportunity_id != tender["id"] or brief.supplier_profile_id != supplier["id"]:
        raise ValueError("Tender and supplier must match the Pursuit Brief version.")
    position = brief.win_positions[brief.selected_position_index]
    return _strategy_markdown(tender, supplier, brief, position)


def red_team_proposal(brief: PursuitBrief, draft: str) -> tuple[str, ...]:
    """Review only score-bearing sections using the same evaluation matrix."""
    findings: list[str] = []
    for section in brief.proposal_blueprint:
        if section.criterion not in draft:
            findings.append(f"Add an explicit {section.criterion} section before review.")
        if not any(asset in draft for asset in section.assets):
            findings.append(f"Connect {section.criterion} to a selected supplier asset.")
    position = brief.win_positions[brief.selected_position_index]
    if position.weakness:
        findings.append(position.mitigation or position.weakness)
    return tuple(findings)


def _strategy_markdown(tender: dict, supplier: dict, brief: PursuitBrief, position: WinPosition) -> str:
    proof_list = "\n".join(f"- **{card.label}** — {card.detail}" for card in position.proof_cards)
    sections = "\n\n".join(
        f"## {section.criterion} ({section.weight} points)\n\n"
        f"{section.claim}\n\n"
        f"Delivery assets: {', '.join(section.assets)}.\n\n"
        f"Proposal owner: {section.owner}."
        for section in brief.proposal_blueprint
    )
    return f"""# {tender['title']}

## Win Position

{position.statement}

## Buyer Objective

{brief.buyer_objective}

## Selected Delivery Assets

{proof_list}

{sections}

## Delivery Action

{tender['promised_outcome'].capitalize()} is delivered within the planned effort of {tender['delivery_hours']} hours.
"""
