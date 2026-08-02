"""Proposal drafting from a qualified public tender and a supplier profile."""

from __future__ import annotations

from bidpilot.pursuit import PursuitBrief, WinPosition


def compose_persisted_proposal(response_plans: list[dict], sections: list[dict]) -> str:
    """Build one criterion-led editable draft from persisted section fragments."""
    blocks: list[str] = []
    for plan in response_plans:
        criterion = str(plan.get("criterion_name") or "").strip()
        if not criterion:
            continue
        assets = _parse_assets(plan.get("assets"))
        fragments = [
            str(section.get("section_markdown") or "").strip()
            for section in sections
            if str(section.get("criterion_name") or "").strip().casefold() == criterion.casefold()
            and str(section.get("section_markdown") or "").strip()
        ]
        demoted = [fragment.replace("## ", "### ", 1) if fragment.startswith("## ") else fragment for fragment in fragments]
        block = [f"## {criterion}"]
        claim = str(plan.get("claim") or "").strip()
        if claim:
            block.extend(["", claim])
        if assets:
            block.extend(["", "Evidence assets: " + ", ".join(assets) + "."])
        if demoted:
            block.extend(["", "\n\n".join(demoted)])
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def write_proposal_draft(packet: dict, company_name: str, positioning: str) -> str:
    """Produce a draft only from the qualification engine's packet contract."""
    if packet.get("kind") != "proposal-start-packet" or packet.get("packet_version") != "1.0":
        raise ValueError("Proposal drafting requires a versioned proposal-start packet.")
    tender = packet.get("opportunity", {})
    strategy = packet.get("proposal_strategy", {})
    qualification = packet.get("qualification", {})
    if (
        tender.get("is_open") is not True
        or strategy.get("writing_gate") != "OPEN"
        or qualification.get("missing_evidence")
        or qualification.get("failed_requirements")
    ):
        raise ValueError("Proposal drafting is locked until the tender is open and supplier evidence is approved.")
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
    top_weight = max(section.weight for section in brief.proposal_blueprint)
    for section in brief.proposal_blueprint:
        body = _section_body(draft, section.criterion)
        if body is None:
            findings.append(f"Add an explicit {section.criterion} section before review.")
        elif not any(asset in body for asset in section.assets):
            findings.append(f"Connect {section.criterion} to a selected supplier asset.")
        elif section.weight == top_weight and not _has_high_weight_detail(body):
            findings.append(f"Strengthen the high-weight {section.criterion} response with validation and buyer outcome detail.")
    position = brief.win_positions[brief.selected_position_index]
    if position.weakness:
        findings.append(position.mitigation or position.weakness)
    return tuple(findings)


def build_gap_closure_plan(brief: PursuitBrief) -> tuple[dict[str, str], ...]:
    """Turn REVIEW and NO-GO gaps into bounded reopening work."""
    if brief.status == "PURSUE":
        return ()
    tasks: list[dict[str, str]] = []
    for requirement in brief.missing_eligibility:
        tasks.append({"gap": requirement, "action": f"Verify or obtain {requirement} before reopening.", "owner": "Bid manager"})
    if brief.capacity_gap_hours:
        tasks.append({"gap": f"{brief.capacity_gap_hours} delivery hours", "action": "Secure named delivery capacity and rerun the pursuit policy.", "owner": "Delivery lead"})
    if brief.status == "REVIEW":
        tasks.append({"gap": "Comparable delivery evidence", "action": "Validate another directly comparable reference and its buyer outcome.", "owner": "Evidence owner"})
    return tuple(tasks)


def red_team_tasks(brief: PursuitBrief, draft: str) -> tuple[dict[str, str], ...]:
    """Return criterion-owned revision tasks instead of an undifferentiated warning."""
    tasks: list[dict[str, str]] = []
    top_weight = max(section.weight for section in brief.proposal_blueprint)
    for section in brief.proposal_blueprint:
        gaps: list[str] = []
        body = _section_body(draft, section.criterion)
        if body is None:
            gaps.append("missing explicit response section")
        elif not any(asset in body for asset in section.assets):
            gaps.append("missing selected supplier asset")
        elif section.weight == top_weight and not _has_high_weight_detail(body):
            gaps.append("high-weight response lacks validation or buyer outcome detail")
        if gaps:
            tasks.append({"criterion": section.criterion, "finding": "; ".join(gaps), "action": f"Revise the {section.criterion} response and re-run red-team review.", "owner": section.owner})
    position = brief.win_positions[brief.selected_position_index]
    if position.weakness:
        tasks.append({"criterion": "Win Position", "finding": position.weakness, "action": position.mitigation or "Resolve the strategy weakness before submission.", "owner": "Bid manager"})
    return tuple(tasks)


def red_team_persisted_draft(response_plans: list[dict], draft: str) -> tuple[dict[str, str], ...]:
    """Re-check an edited authenticated draft against persisted response plans."""
    if not response_plans:
        return ({"criterion": "Score map", "finding": "No persisted response plan is available."},)
    weights = [float(item.get("weight") or 0) for item in response_plans]
    top_weight = max(weights)
    findings: list[dict[str, str]] = []
    for item, weight in zip(response_plans, weights, strict=True):
        criterion = str(item.get("criterion_name") or "").strip()
        body = _section_body(draft, criterion) if criterion else None
        assets = _parse_assets(item.get("assets"))
        if body is None:
            finding = "Missing explicit score-bearing section."
        elif assets and not any(str(asset) in body for asset in assets):
            finding = "Selected supplier asset is missing from the edited response."
        elif weight == top_weight and not _has_high_weight_detail(body):
            finding = "Highest-weight response needs substantive validation and buyer outcome detail."
        else:
            continue
        findings.append({"criterion": criterion or "Unnamed criterion", "finding": finding})
    return tuple(findings)


def _section_body(draft: str, criterion: str) -> str | None:
    marker = f"## {criterion}"
    start = draft.find(marker)
    if start < 0:
        return None
    end = draft.find("\n## ", start + len(marker))
    return draft[start : end if end >= 0 else len(draft)]


def _has_high_weight_detail(body: str) -> bool:
    has_explicit_labels = "Validation:" in body or "Buyer outcome:" in body
    values = {}
    for label in ("Validation:", "Buyer outcome:"):
        start = body.find(label)
        if start < 0:
            if has_explicit_labels:
                return False
            break
        value_start = start + len(label)
        line_end = body.find("\n", value_start)
        values[label] = body[value_start : line_end if line_end >= 0 else len(body)].strip()
    placeholders = {"tbd", "todo", "pending", "n/a", "na", "not recorded", "unknown", "-"}
    if has_explicit_labels:
        return len(values) == 2 and all(
            value and value.casefold().strip(" .:;[]()") not in placeholders for value in values.values()
        )
    lowered = body.casefold()
    validation_signals = ("validation", "validate", "regression", "gate process", "checkpoint", "automated profiling")
    outcome_signals = ("outcome", "reduced", "elimination", "prevented", "zero public-service", "maintained service")
    return any(signal in lowered for signal in validation_signals) and any(signal in lowered for signal in outcome_signals)


def _parse_assets(raw_assets) -> list[str]:
    if not raw_assets:
        return []
    if isinstance(raw_assets, str):
        import json

        try:
            parsed = json.loads(raw_assets)
        except ValueError:
            parsed = [raw_assets]
    else:
        parsed = raw_assets
    return [str(asset).strip() for asset in parsed if str(asset).strip()]


def _strategy_markdown(tender: dict, supplier: dict, brief: PursuitBrief, position: WinPosition) -> str:
    proof_list = "\n".join(f"- **{card.label}** — {card.detail}" for card in position.proof_cards)
    top_weight = max(section.weight for section in brief.proposal_blueprint)
    sections = "\n\n".join(
        f"## {section.criterion} ({section.weight} points)\n\n"
        f"Response priority: {'lead response' if section.weight >= 30 else 'supporting response'} at {section.weight}% of the evaluation.\n\n"
        f"{section.claim}\n\n"
        f"Delivery assets: {', '.join(section.assets)}.\n\n"
        f"{_weighted_response_detail(section.weight, top_weight, tender['promised_outcome'], position.title)}\n\n"
        f"Proposal owner: {section.owner}."
        for section in brief.proposal_blueprint
    )
    criteria = {section.criterion.lower() for section in brief.proposal_blueprint}
    top_assets = ", ".join(card.label for card in position.proof_cards) or "the selected supplier profile"
    required_sections: list[str] = []
    if "technical approach" not in criteria:
        required_sections.append(f"## Technical Approach\n\nThe delivery method applies the selected Win Position to {tender['promised_outcome'].lower()} and keeps each technical claim linked to an accountable owner.")
    if "comparable delivery" not in criteria:
        required_sections.append(f"## Comparable Delivery\n\nRelevant delivery assets for this pursuit are {top_assets}. Their recorded outcomes define the reusable delivery pattern and the remaining proof gap.")
    required_text = "\n\n".join(required_sections)
    return f"""# {tender['title']}

## Executive Summary

{supplier['name']} will pursue the buyer objective through the selected Win Position: {position.statement} The response prioritizes the highest-weighted criteria and assigns each claim to an accountable proposal owner.

## Understanding of the Requirement

The buyer needs {brief.buyer_objective.lower()} The proposed response must address the weighted evaluation matrix while remaining deliverable within {tender['delivery_hours']} planned hours.

## Win Position

{position.statement}

## Buyer Objective

{brief.buyer_objective}

## Selected Delivery Assets

{proof_list}

{sections}

{required_text}

## Implementation Plan

{_strategy_plan(position.title)}

## Team and Governance

The proposal owners named in the blueprint coordinate the response. Delivery evidence is anchored in {top_assets} and the selected supplier profile has {supplier['available_hours']} available hours.

## Risk and Mitigation

{position.weakness or 'The current pursuit policy found no blocking eligibility or capacity gap.'}

Mitigation: {position.mitigation or 'Keep criterion owners and delivery assets traceable through the saved Bid Room run.'}

## Commercial Response

The commercial response will be completed against the Price criterion and reconciled with the planned {tender['delivery_hours']} delivery hours before submission.

## Delivery Action

{tender['promised_outcome'].capitalize()} is delivered within the planned effort of {tender['delivery_hours']} hours.
"""


def _strategy_plan(position_title: str) -> str:
    if position_title == "Operational continuity":
        return (
            "1. Map service dependencies, transition windows, and named rollback owners.\n"
            "2. Rehearse the highest-risk handoff while existing public interfaces remain available.\n"
            "3. Release through buyer-approved checkpoints and transfer the operating playbook."
        )
    return (
        "1. Confirm the evaluation response plan and evidence owners.\n"
        "2. Develop the highest-weighted response first and attach the selected delivery assets.\n"
        "3. Validate delivery capacity, operating handoff, and criterion coverage before red-team review."
    )


def _weighted_response_detail(weight: int, top_weight: int, promised_outcome: str, position_title: str) -> str:
    """Allocate substantive response depth in proportion to the published score."""
    if weight == top_weight:
        emphasis = (
            "\n\nScoring emphasis: include two acceptance checkpoints and a buyer-facing outcome summary."
            if weight >= 45
            else ""
        )
        approach = (
            "Approach: baseline the live service, rehearse the transition, and release through rollback-safe checkpoints."
            if position_title == "Operational continuity"
            else "Approach: define the baseline, execute the selected delivery pattern, and assign acceptance ownership."
        )
        return (
            f"{approach}\n\n"
            "Validation: agree measurable acceptance checks with the buyer and record the result in the Bid Room.\n\n"
            f"Buyer outcome: {promised_outcome.capitalize()}."
            f"{emphasis}"
        )
    if weight >= 20:
        return (
            "Approach: name the service owner, transition dependency, and rollback checkpoint for this response."
            if position_title == "Operational continuity"
            else "Approach: name the accountable owner, delivery inputs, and acceptance checkpoint for this response."
        )
    return "Approach: confirm the required input and reconcile it with the final submission before approval."
