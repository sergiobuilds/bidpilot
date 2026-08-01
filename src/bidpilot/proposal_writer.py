"""Proposal drafting from a qualified public tender and a supplier profile."""

from __future__ import annotations


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
