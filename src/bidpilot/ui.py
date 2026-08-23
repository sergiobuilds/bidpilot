"""The BidPilot pursuit workspace: four stages over one persisted analysis.

Everything on screen is projected from a run that Snowflake already recorded.
This module supplies no value of its own: where a run has nothing, the screen
says so rather than filling the gap.

The seam is deliberate. Settled records are written as HTML so they read as
records; only the controls a person may actually operate — stage navigation,
opening a tender, the proposal draft, its download, and retry — are Streamlit
widgets.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import logging

import streamlit as st

from bidpilot.proposal_writer import (
    compose_persisted_proposal,
    red_team_persisted_draft,
)
from bidpilot.snowflake_store import (
    EXPECTED_READER_ROLE,
    SnowflakeBidRoomError,
    SnowflakeBidRoomStore,
    configured_connection_name,
)
from bidpilot.workspace_ui import bid_room_first_viewport

PRODUCT_NAME = "BidPilot"
PRODUCT_TAGLINE = "pursuit workspace"
NOT_RECORDED = "Not recorded in this analysis"
LOGGER = logging.getLogger(__name__)

STAGES = (
    "Opportunities",
    "Bid decision",
    "Win plan",
    "Proposal room",
)

STAGE_KEY = "bp_stage"
RUN_KEY = "bp_run_id"
LOST_RUN_KEY = "bp_lost_run"

CONNECTION_VARIABLE = "BIDPILOT_SNOWFLAKE_CONNECTION"


# ---------------------------------------------------------------------------
# Value helpers. None of these invent a value; they only read one safely.
# ---------------------------------------------------------------------------


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def as_records(value: object) -> list:
    """Read a stored ARRAY column, whether it arrives as JSON text or a list."""
    if value in (None, ""):
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value]
        value = parsed
    if isinstance(value, dict):
        return [value]
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def record_label(item: object) -> str:
    """Name one stored record without exposing its serialised form."""
    if isinstance(item, dict):
        for key in ("label", "title", "name", "project", "asset", "credential"):
            candidate = item.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return ", ".join(f"{key}: {value}" for key, value in item.items() if value not in (None, ""))
    return str(item).strip()


def record_detail(item: object) -> str:
    if not isinstance(item, dict):
        return ""
    for key in ("relevance", "detail", "outcome", "status", "note"):
        candidate = item.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def as_number(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def trim(value: float) -> str:
    return f"{value:g}"


def first_key(mapping: object, keys: tuple[str, ...]) -> object:
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        if mapping.get(key) not in (None, "", [], {}):
            return mapping[key]
    return None


def flatten(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(flatten(item) for item in value if item not in (None, ""))
    if isinstance(value, dict):
        return ", ".join(f"{key}: {flatten(item)}" for key, item in value.items() if item not in (None, ""))
    return str(value)


def display_date(value: object) -> str:
    """Render a stored timestamp as a readable date without shifting it."""
    if value in (None, ""):
        return ""
    if isinstance(value, (dt.datetime, dt.date)):
        return value.strftime("%-d %B %Y")
    text = str(value).strip()
    head = text.replace("T", " ").split(" ")[0]
    try:
        return dt.date.fromisoformat(head).strftime("%-d %B %Y")
    except ValueError:
        return text


def humanise(value: object) -> str:
    """Turn a stored slug into words. `historical-demo-replay` reads as prose."""
    text = str(value or "").strip()
    if not text:
        return ""
    return text.replace("_", " ").replace("-", " ")


# ---------------------------------------------------------------------------
# Projection. One recorded run becomes one view; nothing is added to it.
# ---------------------------------------------------------------------------


def build_run_view(result: dict, run_id: str, opportunity_id: str = "") -> dict:
    run = result.get("run") or {}
    trace = run.get("trace") if isinstance(run.get("trace"), dict) else {}
    opportunity = result.get("opportunity") or {}
    supplier = result.get("supplier") or {}
    decision = result.get("decision") or {}
    strategies = list(result.get("strategies") or [])
    selected = next((item for item in strategies if item.get("selected")), strategies[0] if strategies else {})

    criteria: list[dict] = []
    total_weight = 0.0
    covered_weight = 0.0
    for item in result.get("blueprint") or []:
        weight = as_number(item.get("weight")) or 0.0
        assets = [record_label(asset) for asset in as_records(item.get("assets")) if record_label(asset)]
        total_weight += weight
        if assets:
            covered_weight += weight
        criteria.append(
            {
                "name": str(item.get("criterion_name") or "").strip(),
                "weight": weight,
                "assets": assets,
                "claim": str(item.get("claim") or "").strip(),
                "owner": str(item.get("owner") or "").strip(),
                "gap": "covered" if assets else "uncovered",
            }
        )

    sections = list(result.get("sections") or [])
    status = str(decision.get("status") or first_key(trace, ("pursuit_status", "status")) or "RECORDED")
    return {
        "run_id": run_id,
        "run": run,
        "trace": trace,
        "opportunity": opportunity,
        "supplier": supplier,
        "decision": decision,
        "strategies": strategies,
        "selected": selected,
        "blueprint": list(result.get("blueprint") or []),
        "sections": sections,
        "tasks": list(result.get("tasks") or []),
        "criteria": criteria,
        "total_weight": total_weight,
        "covered_weight": covered_weight,
        "open_weight": total_weight - covered_weight,
        "status": status,
        # The tender names itself. A run identifier is provenance and never
        # stands in for the thing a bid lead is choosing.
        "headline": (
            opportunity.get("title")
            or first_key(trace, ("opportunity_title", "tender_title", "title"))
            or run.get("opportunity_id")
            or opportunity_id
            or NOT_RECORDED
        ),
        "opportunity_id": run.get("opportunity_id") or opportunity_id or "",
        "objective": opportunity.get("buyer_objective") or first_key(trace, ("buyer_objective", "objective")),
        "scope": opportunity.get("scope") or "",
        "source_type": humanise(opportunity.get("source_status")),
        "supplier_name": supplier.get("supplier_name") or run.get("supplier_profile_id"),
        "missing_eligibility": [record_label(item) for item in as_records(decision.get("missing_eligibility"))],
        "capacity_gap_hours": as_number(decision.get("capacity_gap_hours")),
        # The run records when it completed. Only when it does not is the row's
        # creation time used, and then it is labelled for what it is.
        "completed_on": display_date(first_key(trace, ("completed_at", "finished_at"))),
        "recorded_on": display_date(run.get("created_at")),
    }


def decision_summary(view: dict) -> str:
    """State the verdict in plain language over the two recorded policy facts."""
    if not view["decision"]:
        return "No pursuit decision is recorded for this analysis."
    missing = view["missing_eligibility"]
    gap = view["capacity_gap_hours"]
    eligibility = (
        f"{len(missing)} eligibility requirement{'s' if len(missing) > 1 else ''} is still unmet"
        if missing
        else "every recorded eligibility requirement was met"
    )
    if gap is None:
        capacity = "delivery capacity was not assessed"
    elif gap > 0:
        capacity = f"delivery capacity is {trim(gap)} hours short"
    else:
        capacity = "the delivery window fits the recorded supplier capacity"
    clear = (not missing, gap is not None and gap <= 0)
    joiner = ", and " if clear[0] == clear[1] else ", but "
    verdict = str(view["status"]).upper()
    tail = {
        "PURSUE": "so the recorded policy returned PURSUE. Everything in the later stages follows from this answer.",
        "REVIEW": "so the recorded policy returned REVIEW. The gap has to be closed before a proposal is written.",
        "NO-GO": "so the recorded policy returned NO-GO. No proposal is written against this analysis.",
    }.get(verdict, f"and the recorded policy returned {verdict}.")
    run = view.get("run") if isinstance(view.get("run"), dict) else {}
    policy_version = run.get("policy_version") or NOT_RECORDED
    return f"On recorded policy version {policy_version}, {eligibility}{joiner}{capacity} — {tail}"


def bid_room_causal_summary(view: dict) -> str:
    """Project one causal first viewport from the selected persisted run."""
    criteria = [item for item in view.get("criteria") or [] if isinstance(item, dict)]
    highest = max(criteria, key=lambda item: as_number(item.get("weight")) or 0.0, default={})
    weight = as_number(highest.get("weight"))
    assets = [item for item in highest.get("assets") or [] if str(item).strip()]
    open_gaps = 1 if highest and highest.get("gap") == "uncovered" else 0

    selected = view.get("selected") if isinstance(view.get("selected"), dict) else {}
    tasks = [item for item in view.get("tasks") or [] if isinstance(item, dict)]
    finished_states = {"COMPLETE", "COMPLETED", "CLOSED", "DONE"}
    next_task = next(
        (
            item
            for item in tasks
            if str(item.get("status") or "").upper() not in finished_states
        ),
        {},
    )

    return bid_room_first_viewport(
        verdict=view.get("status") or NOT_RECORDED,
        principal_reason=(decision_summary(view) if view.get("decision") else NOT_RECORDED),
        criterion=highest.get("name") or NOT_RECORDED,
        official_weight=f"{trim(weight)} points" if weight is not None else NOT_RECORDED,
        evidence_state=f"{len(assets)} cited · {open_gaps} open gaps",
        selected_position=selected.get("title") or NOT_RECORDED,
        owner=next_task.get("owner") or NOT_RECORDED,
        next_action=next_task.get("task_name") or NOT_RECORDED,
        run_id=view.get("run_id") or NOT_RECORDED,
    )


def policy_dimensions(view: dict) -> list[dict]:
    """The recorded policy inputs, each stated as its own pass or open item.

    The three dimensions are exactly the three inputs the versioned policy
    reads. Comparable delivery has no column of its own: a PURSUE verdict with
    no eligibility gap and no capacity gap is the policy's own statement that
    the comparable-delivery threshold was met, so it is reported that way and
    left unstated when the verdict is anything else.
    """
    missing = view["missing_eligibility"]
    gap = view["capacity_gap_hours"]
    verdict = str(view["status"]).upper()
    dimensions = [
        {
            "name": "Eligibility",
            "state": "pass" if not missing else "open",
            "badge": "Passed" if not missing else f"{len(missing)} unmet",
            "detail": (
                "Every eligibility requirement in the recorded policy set was met."
                if not missing
                else "Unmet: " + "; ".join(missing) + "."
            ),
        },
        {
            "name": "Delivery capacity",
            "state": "pass" if gap is not None and gap <= 0 else "open",
            "badge": (
                f"{trim(gap)} hour gap" if gap else ("0 hours" if gap is not None else "Not assessed")
            ),
            "detail": (
                "No capacity gap between the required delivery window and the recorded supplier profile."
                if gap is not None and gap <= 0
                else "The recorded supplier profile does not cover the required delivery window."
            ),
        },
    ]
    if verdict == "PURSUE":
        dimensions.append(
            {
                "name": "Comparable delivery",
                "state": "pass",
                "badge": "Passed",
                "detail": (
                    "The policy only returns PURSUE once enough comparable delivery records match "
                    "the tender scope, so this threshold was met by the recorded run."
                ),
            }
        )
    return dimensions


def group_by_opportunity(complete: list[dict]) -> list[dict]:
    """Group finished analyses by tender, newest analysis first.

    The store orders runs by creation time descending, so the first run in a
    group is that tender's current analysis and the rest are its history.
    """
    order: list[str] = []
    groups: dict[str, list[dict]] = {}
    for run in complete:
        key = str(run.get("opportunity_id") or run.get("run_id") or "")
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(run)
    return [{"opportunity_id": key, "current": groups[key][0], "history": groups[key][1:]} for key in order]


def review_state(criteria: list[dict], findings: tuple[dict, ...]) -> dict[str, str]:
    """Map each score-bearing criterion to its current open finding, if any."""
    open_findings = {str(item.get("criterion") or ""): str(item.get("finding") or "") for item in findings}
    return {item["name"]: open_findings.get(item["name"], "") for item in criteria}


# ---------------------------------------------------------------------------
# HTML atoms. New vocabulary, all prefixed so nothing collides with the host.
# ---------------------------------------------------------------------------

ICONS = {
    "check": "M19.67 6.58c.5.5.5 1.33 0 1.84l-9 9c-.51.5-1.34.5-1.84 0l-4.5-4.5a1.3 1.3 0 0 1 1.84-1.84l3.58 3.58 8.08-8.08a1.3 1.3 0 0 1 1.84 0Z",
    "check-circle": "M2.1 12A9.9 9.9 0 1 1 21.9 12 9.9 9.9 0 0 1 2.1 12Zm14.55-2.12a.9.9 0 1 0-1.3-1.25l-4.67 4.83-2.03-2.1a.9.9 0 1 0-1.3 1.25l2.68 2.77c.17.18.4.28.65.28.24 0 .48-.1.65-.28l5.32-5.5Z",
    "warning": "M10.82 3.1a2.7 2.7 0 0 1 2.36 0c.52.24.9.67 1.23 1.13.32.46.68 1.08 1.12 1.84l5.11 8.85c.44.75.8 1.37 1.03 1.89.24.51.42 1.05.36 1.62a2.7 2.7 0 0 1-1.18 1.97c-.47.34-1.03.45-1.6.5-.56.05-1.27.05-2.15.05H6.89c-.87 0-1.59 0-2.15-.05a2.9 2.9 0 0 1-1.6-.5 2.7 2.7 0 0 1-1.17-1.97c-.06-.57.12-1.11.36-1.62.23-.52.59-1.14 1.03-1.9l5.11-8.85c.44-.75.8-1.37 1.12-1.83.33-.46.71-.9 1.23-1.13ZM12 8.1c.5 0 .9.4.9.9v4a.9.9 0 1 1-1.8 0V9c0-.5.4-.9.9-.9Zm1 8.4a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z",
    "info": "M2.1 12A9.9 9.9 0 1 1 21.9 12 9.9 9.9 0 0 1 2.1 12ZM13 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0Zm-1 2.6c.5 0 .9.4.9.9V16a.9.9 0 1 1-1.8 0v-4.5c0-.5.4-.9.9-.9Z",
    "arrow-left": "M2.86 11.36a.9.9 0 0 0 0 1.28l7 7a.9.9 0 0 0 1.28-1.28L5.67 12.9H20.5a.9.9 0 0 0 0-1.8H5.67l5.47-5.46a.9.9 0 1 0-1.28-1.28l-7 7Z",
    "arrow-right": "M21.14 12.64a.9.9 0 0 0 0-1.28l-7-7a.9.9 0 1 0-1.28 1.28l5.47 5.46H3.5a.9.9 0 0 0 0 1.8h14.83l-5.47 5.46a.9.9 0 0 0 1.28 1.28l7-7Z",
    "doc": "M13.28 2.15c-.23-.05-.45-.05-.65-.05H7.91c-.53 0-.98 0-1.35.03-.39.03-.77.1-1.13.29-.55.27-.99.72-1.27 1.26-.18.36-.25.74-.28 1.13-.03.37-.03.82-.03 1.35v11.67c0 .53 0 .98.03 1.35.03.39.1.77.28 1.13.28.55.72.99 1.27 1.27.36.18.74.25 1.13.28.37.03.82.03 1.35.03h8.17c.53 0 .98 0 1.35-.03a2.9 2.9 0 0 0 1.13-.28c.55-.28.99-.72 1.27-1.27.18-.36.25-.74.28-1.13.03-.37.03-.82.03-1.35V9.66c0-.24 0-.47-.05-.69a1.8 1.8 0 0 0-.23-.55c-.12-.2-.28-.36-.42-.49L14.35 2.83a2 2 0 0 0-.53-.45 1.8 1.8 0 0 0-.54-.23ZM12.6 3.9H7.95c-.58 0-.95 0-1.24.02-.28.03-.39.07-.46.1a1.1 1.1 0 0 0-.48.48c-.03.07-.07.18-.1.46-.02.29-.02.66-.02 1.24v11.6c0 .58 0 .95.02 1.24.03.28.07.39.1.46.11.2.28.37.48.48.07.03.18.07.46.1.29.02.66.02 1.24.02h8.1c.57 0 .95 0 1.24-.02.28-.03.39-.07.46-.1.2-.11.37-.28.48-.48.03-.07.07-.18.1-.46.02-.29.02-.66.02-1.24V9.9h-3.28c-.25 0-.5 0-.7-.02a1.6 1.6 0 0 1-.57-.19 1.5 1.5 0 0 1-.66-.66 1.6 1.6 0 0 1-.19-.73 9 9 0 0 1-.01-.7V3.9Zm4.48 4.2-2.68-2.68V8.1h2.68ZM7.85 13.5c0-.5.4-.9.9-.9h4a.9.9 0 1 1 0 1.8h-4a.9.9 0 0 1-.9-.9Zm0 3.5c0-.5.4-.9.9-.9h4a.9.9 0 1 1 0 1.8h-4a.9.9 0 0 1-.9-.9Z",
    "clock": "M11.5 6.6c.5 0 .9.4.9.9v4.63l2.21 2.21a.9.9 0 1 1-1.27 1.27l-2.48-2.47a.94.94 0 0 1-.26-.64V7.5c0-.5.4-.9.9-.9ZM12 2.1A9.9 9.9 0 1 0 12 21.9 9.9 9.9 0 0 0 12 2.1ZM3.9 12A8.1 8.1 0 1 1 20.1 12 8.1 8.1 0 0 1 3.9 12Z",
    "history": "M12 2.1a.9.9 0 0 0 0 1.8 8.1 8.1 0 1 1-8.1 8.1.9.9 0 1 0-1.8 0A9.9 9.9 0 1 0 12 2.1Zm-2.52 1.2a.9.9 0 1 1-1.65.73.9.9 0 0 1 1.65-.73ZM6.34 4.93a.9.9 0 1 1-1.41 1.41.9.9 0 0 1 1.41-1.41ZM4.07 7.63a.9.9 0 1 1-.77 1.63.9.9 0 0 1 .77-1.63ZM11.5 6.6c.5 0 .9.4.9.9v4.63l2.21 2.21a.9.9 0 0 1-1.27 1.27l-2.48-2.47a.94.94 0 0 1-.26-.64V7.5c0-.5.4-.9.9-.9Z",
    "storage": "M14.02 11.63a.9.9 0 0 1 0 1.8h-4a.9.9 0 0 1 0-1.8h4ZM17.32 2.63c.55 0 1.01 0 1.39.03.39.03.77.1 1.13.29.55.28.99.72 1.27 1.26.18.37.25.74.28 1.13.03.38.03.84.03 1.39v10.6c0 .54 0 1-.03 1.38a2.9 2.9 0 0 1-.28 1.13c-.28.55-.72.99-1.27 1.27-.36.18-.74.25-1.13.28-.38.03-.84.03-1.39.03H6.73c-.55 0-1.01 0-1.39-.03a2.9 2.9 0 0 1-1.13-.28 2.9 2.9 0 0 1-1.27-1.27 2.9 2.9 0 0 1-.28-1.13c-.03-.38-.03-.84-.03-1.39V6.73c0-.55 0-1.01.03-1.39.03-.39.1-.77.28-1.13a2.9 2.9 0 0 1 1.27-1.27c.36-.18.74-.25 1.13-.28.38-.03.84-.03 1.39-.03h10.59ZM4.42 17.73c0 .81.01 1 .06 1.14.11.33.37.6.7.7.13.05.33.06 1.14.06h11.4c.82 0 1.01-.01 1.14-.06.34-.11.6-.37.71-.7.04-.14.05-.33.05-1.14V9.92H4.42v7.81Zm1.9-13.3c-.81 0-1 .01-1.14.05a1.1 1.1 0 0 0-.7.71c-.05.13-.06.33-.06 1.14v1.8h15.2v-1.8c0-.81-.01-1-.05-1.14a1.1 1.1 0 0 0-.71-.71c-.13-.04-.33-.05-1.14-.05H6.32Z",
    "lock": "M12 2.35a5.2 5.2 0 0 0-3.65 1.49c-.81.81-1.23 1.78-1.4 3.02-.07.6-.1 1.3-.1 2.34v.4c-.19 0-.37.01-.53.03-.39.03-.77.1-1.13.28a2.9 2.9 0 0 0-1.27 1.27c-.18.36-.25.74-.28 1.13-.03.37-.03.82-.03 1.35v4.17c0 .53 0 .98.03 1.35.03.39.1.77.28 1.13.28.55.72.99 1.27 1.27.36.18.74.25 1.13.28.37.03.82.03 1.35.03h8.67c.53 0 .98 0 1.35-.03a2.9 2.9 0 0 0 1.13-.28c.55-.28.99-.72 1.27-1.27.18-.36.25-.74.28-1.13.03-.37.03-.82.03-1.35v-4.17c0-.53 0-.98-.03-1.35a2.9 2.9 0 0 0-.28-1.13 2.9 2.9 0 0 0-1.27-1.27 2.9 2.9 0 0 0-1.13-.28c-.16-.02-.34-.03-.53-.03V9.2c0-1.09-.03-1.78-.09-2.33-.17-1.22-.59-2.2-1.4-3.02A5.2 5.2 0 0 0 12 2.35Zm3.35 7.25V9.2c0-1.07-.03-1.67-.08-2.1-.12-.9-.41-1.5-.89-1.98A3.4 3.4 0 0 0 12 4.15c-.88 0-1.77.37-2.38.97-.48.48-.76 1.05-.88 1.98-.06.47-.09 1.08-.09 2.1v.4h6.7Zm-9.19 1.85c.13-.04.33-.05 1.14-.05h9.4c.81 0 1.01.01 1.14.05.33.11.6.37.7.7.05.14.06.33.06 1.15v4.9c0 .81-.01 1-.06 1.14-.1.33-.37.59-.7.7-.13.04-.33.05-1.14.05h-9.4c-.81 0-1.01-.01-1.14-.05a1.1 1.1 0 0 1-.71-.7c-.04-.14-.05-.33-.05-1.15v-4.9c0-.81.01-1 .05-1.14.11-.33.38-.59.71-.7Z",
    "instance": "M3.35 9.12 9.13 3.35c.37-.38.69-.7.97-.94.3-.25.61-.47 1-.6a2.7 2.7 0 0 1 1.8 0c.38.13.7.35 1 .6.28.24.6.56.97.94l5.78 5.77c.37.38.7.7.93.98.25.3.47.61.6 1a2.7 2.7 0 0 1 0 1.79c-.13.39-.35.7-.6 1-.24.28-.56.6-.93.97l-5.78 5.78c-.37.37-.69.69-.97.93-.3.25-.62.47-1 .6a2.7 2.7 0 0 1-1.8 0c-.38-.13-.7-.35-1-.6-.28-.24-.6-.56-.97-.93l-5.78-5.78c-.37-.37-.69-.69-.93-.97a2.7 2.7 0 0 1-.6-1 2.7 2.7 0 0 1 0-1.8c.13-.38.35-.7.6-1 .24-.28.56-.6.93-.97Zm1.01 1.53c-.57.58-.7.73-.76.85a.9.9 0 0 0 0 1c.06.12.19.27.76.85l6.3 6.29c.57.58.72.7.85.76a.9.9 0 0 0 1 0c.12-.06.27-.18.84-.76l6.3-6.29c.57-.58.7-.73.76-.85a.9.9 0 0 0 0-1c-.06-.12-.19-.27-.76-.85l-6.3-6.29c-.57-.58-.72-.7-.84-.76a.9.9 0 0 0-1 0c-.13.06-.28.18-.85.76l-6.3 6.29Z",
    "minus": "M2.7 12c0-.72.58-1.3 1.3-1.3h16a1.3 1.3 0 0 1 0 2.6H4A1.3 1.3 0 0 1 2.7 12Z",
    "refresh": "M2.6 12A9.4 9.4 0 0 1 16.95 4.01l.95-.95a.9.9 0 0 1 1.54.64v3.18a.9.9 0 0 1-.9.9h-3.18a.9.9 0 0 1-.64-1.54l.92-.91A7.6 7.6 0 0 0 4.4 12c0 .51.05 1 .15 1.49a.9.9 0 0 1-1.77.35A9.6 9.6 0 0 1 2.6 12Zm17.56-2.54a.9.9 0 0 1 1.06.7c.12.6.18 1.21.18 1.84a9.4 9.4 0 0 1-14.35 7.99l-.95.95a.9.9 0 0 1-1.54-.64v-3.18a.9.9 0 0 1 .9-.9h3.18a.9.9 0 0 1 .64 1.54l-.91.91A7.6 7.6 0 0 0 19.6 12c0-.51-.05-1-.14-1.49a.9.9 0 0 1 .7-1.05Z",
}


def sprite() -> str:
    symbols = "".join(
        f'<symbol id="bpi-{name}" viewBox="0 0 24 24">'
        f'<path fill="currentColor" fill-rule="evenodd" clip-rule="evenodd" d="{path}"/></symbol>'
        for name, path in ICONS.items()
    )
    return (
        '<svg class="bp-sprite" aria-hidden="true" focusable="false" width="0" height="0" '
        f'style="position:absolute">{symbols}</svg>'
    )


def icon(name: str, cls: str = "bp-ic") -> str:
    return f'<svg class="{cls}" aria-hidden="true" focusable="false"><use href="#bpi-{name}"></use></svg>'


def badge(text: str, tone: str = "neutral", glyph: str = "") -> str:
    mark = icon(glyph, "bp-ic bp-ic--13") if glyph else ""
    return f'<span class="bp-badge bp-badge--{tone}">{mark}{esc(text)}</span>'


def notice(body: str, tone: str = "info", glyph: str = "info", role: str = "") -> str:
    attr = f' role="{role}"' if role else ""
    return (
        f'<div class="bp-notice bp-notice--{tone}"{attr}>'
        f'<span class="bp-notice__icon">{icon(glyph)}</span>'
        f'<div class="bp-notice__body">{body}</div></div>'
    )


def section_head(title: str, note: str = "") -> str:
    tail = f'<p class="bp-t-body2 bp-note">{esc(note)}</p>' if note else ""
    return f'<div class="bp-head"><h2 class="bp-t-heading1 bp-bold">{esc(title)}</h2>{tail}</div>'


def page_head(stage: int, title: str, lede: str = "") -> str:
    tail = f'<p class="bp-t-body1-reading bp-lede">{esc(lede)}</p>' if lede else ""
    return (
        '<header class="bp-pagehead">'
        f'<p class="bp-t-label2 bp-bold bp-eyebrow">Stage {stage} of {len(STAGES)}</p>'
        f'<h1 class="bp-t-title1 bp-bold">{esc(title)}</h1>{tail}</header>'
    )


def kv_rows(pairs: list[tuple[str, str]]) -> str:
    return "".join(
        f'<div class="bp-kv"><dt>{esc(key)}</dt><dd>{esc(value) if value else NOT_RECORDED}</dd></div>'
        for key, value in pairs
    )


def rail(title: str, body: str) -> str:
    return (
        f'<aside class="bp-rail" aria-label="{esc(title)}">'
        f'<h2 class="bp-t-label1 bp-bold bp-rail__title">{esc(title)}</h2>{body}</aside>'
    )


# ---------------------------------------------------------------------------
# Stylesheet
# ---------------------------------------------------------------------------

STYLE = """
<style>
@import url("https://static.wanted.co.kr/fonts/wantedsans/WantedSansVariable.min.css");

:root {
  --bp-blue-40:#0054D1; --bp-blue-45:#005EEB; --bp-blue-50:#0066FF; --bp-blue-80:#9EC5FF;
  --bp-blue-90:#C9DEFE; --bp-blue-95:#EAF2FE; --bp-blue-99:#F7FBFF;
  --bp-cn-10:#171719; --bp-cn-15:#1B1C1E; --bp-cn-25:#37383C; --bp-cn-80:#AEB0B6;
  --bp-cn-95:#DBDCDF; --bp-cn-96:#E1E2E4; --bp-cn-97:#EAEBEC; --bp-cn-98:#F4F4F5; --bp-cn-99:#F7F7F8;
  --bp-green-40:#009632; --bp-green-50:#00BF40; --bp-green-95:#D9FFE6;
  --bp-orange-39:#D17600; --bp-orange-50:#FF9200; --bp-orange-95:#FEF4E6;
  --bp-red-40:#E52222; --bp-red-95:#FEECEC;

  --bp-primary:var(--bp-blue-50); --bp-primary-strong:var(--bp-blue-45); --bp-primary-heavy:var(--bp-blue-40);
  --bp-label:var(--bp-cn-10);
  --bp-label-neutral:rgba(46,47,51,.88);
  --bp-label-alt:rgba(55,56,60,.61);
  --bp-label-assistive:rgba(55,56,60,.28);
  --bp-label-disable:rgba(55,56,60,.16);
  --bp-line:rgba(112,115,124,.22);
  --bp-line-neutral:rgba(112,115,124,.16);
  --bp-line-alt:rgba(112,115,124,.08);
  --bp-fill:rgba(112,115,124,.08);
  --bp-fill-strong:rgba(112,115,124,.16);
  --bp-fill-alt:rgba(112,115,124,.05);

  --bp-shadow-xs:0 1px 2px -1px rgba(23,23,23,.10);
  --bp-shadow-sm:0 2px 4px -2px rgba(23,23,23,.06), 0 4px 6px -1px rgba(23,23,23,.06);
  --bp-shadow-md:0 4px 6px -2px rgba(23,23,23,.07), 0 10px 15px -3px rgba(23,23,23,.07);

  --bp-r-6:6px; --bp-r-8:8px; --bp-r-10:10px; --bp-r-12:12px; --bp-r-16:16px; --bp-r-20:20px;
  --bp-ease:cubic-bezier(.4,0,.2,1); --bp-dur:220ms; --bp-dur-slow:300ms;
  --bp-font:"Wanted Sans Variable","Wanted Sans","Pretendard JP Variable",-apple-system,
    BlinkMacSystemFont,system-ui,"Noto Sans KR",sans-serif;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
  font-family: var(--bp-font);
  color: var(--bp-label);
  background: #fff;
}
/* the page scrolls as one document rather than inside a nested scroller, so
   the workspace behaves like an ordinary page at every width */
html, body { height: auto !important; }
[data-testid="stAppViewContainer"], section.stMain, [data-testid="stMain"] {
  overflow: visible !important; height: auto !important;
}
.stApp {
  background:
    radial-gradient(120% 58% at 50% -14%, rgba(0,102,255,.05) 0%, rgba(0,102,255,0) 62%), #fff;
}
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stAppToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stMainMenu"],
[data-testid="stAppDeployButton"], .stAppToolbar, .stAppHeader, #MainMenu, footer {
  display: none !important; visibility: hidden !important; height: 0 !important;
}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }

.stMainBlockContainer, .block-container {
  max-width: 1240px !important;
  padding: 20px 24px 96px !important;
}
/* the workspace supplies its own rhythm; the host's default stack is tightened
   to one step and widened again where a section break is wanted */
[data-testid="stVerticalBlock"] { gap: 0.75rem; }
.bp-gap-lg { display:block; height: 20px; }

/* ---- type ----
   The host styles its own headings and paragraphs, so every scale step is
   asserted rather than inherited. Margins are reset in the same breath: this
   layout supplies its own rhythm. */
.bp-t-title1, .bp-t-title3, .bp-t-heading1, .bp-t-heading2, .bp-t-headline1, .bp-t-headline2,
.bp-t-body1, .bp-t-body1-reading, .bp-t-body2, .bp-t-body2-reading,
.bp-t-label1, .bp-t-label2, .bp-t-caption1 {
  margin:0 !important; padding:0 !important; font-family: var(--bp-font) !important;
  font-weight:400;
}
.bp-t-title1 { font-size:2rem !important; line-height:2.5rem !important; letter-spacing:-.0253em; }
.bp-t-title3 { font-size:1.5rem !important; line-height:2rem !important; letter-spacing:-.023em; }
.bp-t-heading1 { font-size:1.375rem !important; line-height:1.875rem !important; letter-spacing:-.0194em; }
.bp-t-heading2 { font-size:1.25rem !important; line-height:1.75rem !important; letter-spacing:-.012em; }
.bp-t-headline1 { font-size:1.125rem !important; line-height:1.625rem !important; letter-spacing:-.002em; }
.bp-t-headline2 { font-size:1.0625rem !important; line-height:1.5rem !important; }
.bp-t-body1 { font-size:1rem !important; line-height:1.5rem !important; letter-spacing:.0057em; }
.bp-t-body1-reading { font-size:1rem !important; line-height:1.625rem !important; letter-spacing:.0057em; }
.bp-t-body2 { font-size:.9375rem !important; line-height:1.375rem !important; letter-spacing:.0096em; }
.bp-t-body2-reading { font-size:.9375rem !important; line-height:1.5rem !important; letter-spacing:.0096em; }
.bp-t-label1 { font-size:.875rem !important; line-height:1.25rem !important; letter-spacing:.0145em; }
.bp-t-label2 { font-size:.8125rem !important; line-height:1.125rem !important; letter-spacing:.0194em; }
.bp-t-caption1 { font-size:.75rem !important; line-height:1rem !important; letter-spacing:.0252em; }
.bp-bold { font-weight:600 !important; }
.bp-t-title1.bp-bold, .bp-t-title3.bp-bold { font-weight:700 !important; }
.bp-kv dt, .bp-kv dd, .bp-notice p, .bp-card p, .bp-plan p, .bp-pos p, .bp-tender p,
table.bp-crit p, .bp-verdict p { margin:0 !important; }
.bp-note { color: var(--bp-label-alt); }
.bp-lede { color: var(--bp-label-neutral); max-width: 62ch; }
.bp-num { font-variant-numeric: tabular-nums; }

.bp-sr {
  position:absolute; width:1px; height:1px; padding:0; margin:-1px;
  overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; border:0;
}
.bp-ic { width:1.25em; height:1.25em; flex:none; display:block; }
.bp-ic--13 { width:13px; height:13px; }
.bp-ic--18 { width:18px; height:18px; }

/* ---- app bar ---- */
.bp-appbar {
  display:flex; align-items:center; gap:10px;
  padding: 4px 0 14px;
}
.bp-mark {
  width:26px; height:26px; border-radius:var(--bp-r-8); flex:none;
  background:var(--bp-primary); color:#fff; display:grid; place-items:center;
  box-shadow: 0 4px 12px -4px rgba(0,102,255,.55);
}
.bp-brandname { letter-spacing:-.03em; }
.bp-brandsub { color: var(--bp-label-alt); }
.bp-rule { height:1px; background: var(--bp-line-alt); margin: 0 0 24px; }

/* ---- generic buttons ---- */
.stButton button, .stDownloadButton button {
  font-family: var(--bp-font); font-weight:600; font-size:.9375rem; letter-spacing:0;
  border-radius: var(--bp-r-12); min-height:44px;
  transition: background var(--bp-dur) var(--bp-ease), border-color var(--bp-dur) var(--bp-ease),
              color var(--bp-dur) var(--bp-ease), transform 120ms var(--bp-ease);
}
.stButton button[kind="primary"], .stDownloadButton button[kind="primary"],
.stButton button[data-testid="stBaseButton-primary"],
.stDownloadButton button[data-testid="stBaseButton-primary"] {
  background: var(--bp-primary); border-color: var(--bp-primary); color:#fff; box-shadow: var(--bp-shadow-xs);
}
.stButton button[kind="primary"]:hover, .stDownloadButton button[kind="primary"]:hover,
.stButton button[data-testid="stBaseButton-primary"]:hover,
.stDownloadButton button[data-testid="stBaseButton-primary"]:hover {
  background: var(--bp-primary-strong); border-color: var(--bp-primary-strong); color:#fff;
}
.stButton button[kind="primary"]:active,
.stButton button[data-testid="stBaseButton-primary"]:active {
  background: var(--bp-primary-heavy); transform: translateY(1px);
}
.stButton button[kind="secondary"], .stDownloadButton button[kind="secondary"],
.stButton button[data-testid="stBaseButton-secondary"],
.stDownloadButton button[data-testid="stBaseButton-secondary"] {
  background:#fff; border-color: var(--bp-line); color: var(--bp-label);
}
.stButton button[kind="secondary"]:hover,
.stButton button[data-testid="stBaseButton-secondary"]:hover {
  background: var(--bp-cn-99); border-color: var(--bp-cn-80); color: var(--bp-label);
}
.stButton button:disabled, .stDownloadButton button:disabled {
  background: var(--bp-cn-98) !important; color: var(--bp-label-disable) !important;
  border-color: transparent !important; box-shadow:none !important;
}
:where(a, button, input, textarea, summary, [tabindex]):focus-visible {
  outline: 2px solid var(--bp-primary) !important; outline-offset: 2px !important;
}

/* ---- stepper (streamlit buttons) ---- */
.st-key-bp-stepper { max-width: 660px; margin-left: auto; }
.st-key-bp-stepper [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 4px; }
.st-key-bp-stepper [data-testid="stColumn"] { min-width: 0 !important; flex: 1 1 0 !important; }
.st-key-bp-stepper .stButton button {
  width:100%; min-height:36px; height:auto; border-radius:1000px; border:1px solid transparent;
  background:transparent; color:var(--bp-label-alt); box-shadow:none;
  font-size:.875rem; font-weight:600; letter-spacing:0; padding:6px 10px;
  transition: background var(--bp-dur) var(--bp-ease), color var(--bp-dur) var(--bp-ease);
}
.st-key-bp-stepper .stButton button:hover { background: var(--bp-fill); color: var(--bp-label-neutral); }
.st-key-bp-stepper .stButton button[kind="primary"],
.st-key-bp-stepper .stButton button[data-testid="stBaseButton-primary"] {
  background: var(--bp-blue-95); color: var(--bp-primary-strong); border-color: transparent;
}
.st-key-bp-stepper .stButton button:disabled { color: var(--bp-label-assistive); background:transparent; }


/* ---- shell / rail ---- */
.bp-stack > [data-testid="stElementContainer"] { margin-bottom: 24px; }
.bp-rail {
  border:1px solid var(--bp-line-neutral); border-radius: var(--bp-r-16);
  background: var(--bp-cn-99); padding:20px; display:flex; flex-direction:column; gap:16px;
}
.bp-rail__title { color: var(--bp-label-alt); text-transform:uppercase; letter-spacing:.08em; }
.bp-pagehead { display:flex; flex-direction:column; gap:8px; padding-bottom:8px; }
.bp-eyebrow { color: var(--bp-primary-strong); text-transform:uppercase; letter-spacing:.1em; }
.bp-head { display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; margin-bottom:14px; }
.bp-head h2 { letter-spacing:-.02em; margin:0; }
.bp-block { margin-bottom: 28px; }

.bp-card {
  background:#fff; border:1px solid var(--bp-line-neutral);
  border-radius: var(--bp-r-16); padding:20px;
}
.bp-card--flat { background: var(--bp-cn-99); border-color: var(--bp-line-alt); }

.bp-kv { display:flex; flex-direction:column; gap:2px; }
.bp-kv dt { color: var(--bp-label-alt); font-size:.75rem; letter-spacing:.0252em; text-transform:uppercase; }
.bp-kv dd { margin:0; font-size:.9375rem; line-height:1.375rem; color: var(--bp-label); word-break: break-word; }
.bp-kvstack { display:flex; flex-direction:column; gap:14px; }
.bp-kvgrid { display:grid; gap:16px; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); }

.bp-badge {
  display:inline-flex; align-items:center; gap:4px; height:24px; padding:0 8px;
  border-radius: var(--bp-r-6); font-size:.75rem; font-weight:600; line-height:1;
  border:1px solid transparent; white-space:nowrap;
}
.bp-badge--neutral { background: var(--bp-fill); color: var(--bp-label-neutral); }
.bp-badge--outline { background:#fff; border-color: var(--bp-line); color: var(--bp-label-neutral); }
.bp-badge--pass { background: var(--bp-green-95); color: var(--bp-green-40); }
.bp-badge--pending { background: var(--bp-orange-95); color: var(--bp-orange-39); }
.bp-badge--open { background: var(--bp-red-95); color: var(--bp-red-40); }
.bp-badge--brand { background: var(--bp-blue-95); color: var(--bp-primary-strong); }

.bp-notice {
  display:flex; gap:12px; align-items:flex-start; padding:16px;
  border-radius: var(--bp-r-12); border:1px solid var(--bp-line-neutral); background: var(--bp-cn-99);
}
.bp-notice__icon { flex:none; margin-top:1px; }
.bp-notice__body { display:flex; flex-direction:column; gap:6px; min-width:0; }
.bp-notice--info { background: var(--bp-blue-95); border-color: rgba(0,94,235,.16); }
.bp-notice--info .bp-notice__icon { color: var(--bp-primary-strong); }
.bp-notice--ok { background: var(--bp-green-95); border-color: rgba(0,150,50,.2); }
.bp-notice--ok .bp-notice__icon { color: var(--bp-green-40); }
.bp-notice--warn { background: var(--bp-orange-95); border-color: rgba(209,118,0,.22); }
.bp-notice--warn .bp-notice__icon { color: var(--bp-orange-39); }
.bp-notice--error { background: var(--bp-red-95); border-color: rgba(229,34,34,.22); }
.bp-notice--error .bp-notice__icon { color: var(--bp-red-40); }

/* ---- stage 1 ---- */
.bp-tender {
  display:grid; gap:14px; padding:20px; border-radius: var(--bp-r-16);
  border:1px solid var(--bp-primary); background: var(--bp-blue-99);
  box-shadow: 0 0 0 1px var(--bp-primary) inset, var(--bp-shadow-sm);
}
.bp-tender--rest { border-color: var(--bp-line); background:#fff; box-shadow:none; }
.bp-tender__title { letter-spacing:-.02em; }
.bp-tender__meta { display:flex; gap:8px 10px; flex-wrap:wrap; align-items:center; }
.bp-tender__foot { color: var(--bp-label-alt); }
.bp-chip {
  display:inline-flex; align-items:center; gap:6px; height:26px; padding:0 10px;
  border-radius: var(--bp-r-8); background: var(--bp-fill-alt); border:1px solid var(--bp-line-alt);
  font-size:.8125rem; color: var(--bp-label-neutral);
}
.bp-chip .bp-ic { width:14px; height:14px; color: var(--bp-label-assistive); }

.bp-ladder { display:grid; gap:8px; grid-template-columns: repeat(2, minmax(0,1fr)); }
.bp-ladder__item {
  display:grid; grid-template-columns:auto minmax(0,1fr); gap:2px 12px;
  padding:14px 16px; border:1px solid var(--bp-line-alt); border-radius: var(--bp-r-12);
  background: var(--bp-cn-99);
}
.bp-ladder__n {
  grid-row: span 2; width:24px; height:24px; border-radius:1000px; display:grid; place-items:center;
  margin-top:2px; background:#fff; border:1px solid var(--bp-line);
  font-size:.75rem; font-weight:700; color: var(--bp-primary-strong);
}
.bp-hist { display:flex; flex-direction:column; gap:10px; }
.bp-hist__item {
  display:flex; flex-direction:column; gap:4px; padding:12px;
  border-radius: var(--bp-r-10); background:#fff; border:1px solid var(--bp-line-alt);
}
.bp-hist__item[data-current="true"] { border-color: var(--bp-blue-80); background: var(--bp-blue-99); }
.bp-mono { font-variant-numeric: tabular-nums; color: var(--bp-label-alt); word-break: break-all; }

.bp-empty {
  position:relative; overflow:hidden; border-radius: var(--bp-r-20);
  border:1px solid var(--bp-line-neutral); background:#fff;
  padding:56px 24px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:12px;
}
.bp-empty::before {
  content:""; position:absolute; inset:-55% -20% auto -20%; height:400px;
  background: conic-gradient(from 210deg at 45% 50%,
    rgba(0,102,255,.30), rgba(101,65,242,.24), rgba(0,189,222,.26), rgba(0,102,255,.30));
  filter: blur(78px); opacity:.5; pointer-events:none;
}
.bp-empty > * { position:relative; }
.bp-empty__icon {
  width:52px; height:52px; border-radius: var(--bp-r-16);
  background: rgba(255,255,255,.72); backdrop-filter: blur(32px);
  border:1px solid var(--bp-line-neutral); display:grid; place-items:center;
  color: var(--bp-primary); box-shadow: var(--bp-shadow-sm);
}

/* ---- stage 2 ---- */
.bp-verdict {
  border-radius: var(--bp-r-20); border:1px solid var(--bp-blue-90);
  background: linear-gradient(180deg, var(--bp-blue-99) 0%, #fff 78%);
  padding:32px; display:grid; gap:20px;
}
.bp-verdict__q { color: var(--bp-label-alt); }
.bp-verdict__word {
  font-size: clamp(2.25rem, 7vw, 3.25rem) !important; line-height:1.05 !important;
  font-weight:700 !important; letter-spacing:-.04em; color: var(--bp-primary);
}
.bp-verdict__word[data-tone="open"] { color: var(--bp-orange-39); }
.bp-verdict__word[data-tone="stop"] { color: var(--bp-red-40); }
.bp-verdict__say { color: var(--bp-label-neutral); max-width:64ch; }

.bp-dims { display:grid; gap:10px; }
.bp-dim {
  display:grid; gap:4px 14px; grid-template-columns:26px minmax(0,1fr) auto; align-items:center;
  padding:14px 16px; border-radius: var(--bp-r-12); border:1px solid var(--bp-line-neutral); background:#fff;
}
.bp-dim__icon { display:grid; place-items:center; }
.bp-dim[data-state="pass"] { border-left:4px solid var(--bp-green-50); }
.bp-dim[data-state="pass"] .bp-dim__icon { color: var(--bp-green-40); }
.bp-dim[data-state="open"] { border-left:4px solid var(--bp-orange-50); border-color: rgba(209,118,0,.32); }
.bp-dim[data-state="open"] .bp-dim__icon { color: var(--bp-orange-39); }
.bp-dim__detail { grid-column:2 / -1; color: var(--bp-label-alt); }

/* ---- stage 3 ---- */
.bp-band {
  display:flex; min-height:70px; border-radius: var(--bp-r-12); overflow:hidden;
  border:1px solid var(--bp-line-neutral); background:#fff;
}
.bp-band__seg {
  display:flex; flex-direction:column; justify-content:center; gap:2px;
  padding:10px 12px; min-width:0; border-right:1px solid var(--bp-line-alt);
}
.bp-band__seg:last-child { border-right:0; }
.bp-band__seg[data-gap="covered"] { background: var(--bp-blue-95); }
.bp-band__seg[data-gap="uncovered"] {
  background: repeating-linear-gradient(135deg, var(--bp-cn-97) 0 5px, #fff 5px 10px);
}
.bp-band__w { font-weight:700 !important; font-size:1.125rem !important; line-height:1.2 !important; letter-spacing:-.02em; }
.bp-band__n { font-size:.6875rem !important; line-height:1.05rem !important; color: var(--bp-label-alt); }
.bp-band__n b { font-weight:600; color: var(--bp-label-neutral); display:block; }
.bp-bandkey { display:flex; gap:14px; flex-wrap:wrap; margin-top:10px; }
.bp-bandkey__item { display:flex; align-items:center; gap:6px; color: var(--bp-label-alt); }
.bp-swatch { width:16px; height:16px; border-radius:2px; border:1px solid var(--bp-line); flex:none; }
.bp-swatch[data-gap="covered"] { background: var(--bp-blue-95); }
.bp-swatch[data-gap="uncovered"] {
  background: repeating-linear-gradient(135deg, var(--bp-cn-97) 0 3px, #fff 3px 6px);
}

.bp-positions { display:grid; gap:12px; grid-template-columns: repeat(3, minmax(0,1fr)); }
.bp-pos {
  display:flex; flex-direction:column; gap:10px; padding:16px;
  border-radius: var(--bp-r-16); border:1px solid var(--bp-line); background:#fff;
}
.bp-pos[data-selected="true"] {
  border-color: var(--bp-primary); background: var(--bp-blue-99);
  box-shadow: 0 0 0 1px var(--bp-primary) inset, var(--bp-shadow-sm);
}
.bp-pos__head { display:flex; align-items:flex-start; justify-content:space-between; gap:8px; flex-wrap:wrap; }
.bp-pos__head .bp-badge { flex:none; margin-top:2px; }
.bp-pos__name { letter-spacing:-.015em; }
.bp-pos__desc { color: var(--bp-label-neutral); }
.bp-pos__foot { margin-top:auto; padding-top:6px; color: var(--bp-label-alt); }

.bp-tablewrap { border:1px solid var(--bp-line-neutral); border-radius: var(--bp-r-16); overflow:hidden; background:#fff; }
table.bp-crit { width:100%; border-collapse:collapse; }
table.bp-crit th, table.bp-crit td { text-align:left; vertical-align:top; padding:16px; }
table.bp-crit thead th {
  background: var(--bp-cn-99); color: var(--bp-label-alt); font-size:.75rem; font-weight:600;
  text-transform:uppercase; letter-spacing:.06em; border-bottom:1px solid var(--bp-line-neutral);
  padding-top:12px; padding-bottom:12px;
}
table.bp-crit tbody tr { border-bottom:1px solid var(--bp-line-alt); }
table.bp-crit tbody tr:last-child { border-bottom:0; }
table.bp-crit tbody tr[data-gap="uncovered"] { background: var(--bp-cn-99); }
.bp-cell { display:flex; flex-direction:column; gap:4px; min-width:0; }
.bp-crit__w { font-weight:700 !important; font-size:1.5rem !important; line-height:1.6rem !important; letter-spacing:-.02em; }
.bp-crit__wsub { color: var(--bp-label-alt); font-size:.6875rem; text-transform:uppercase; letter-spacing:.08em; }
.bp-assets { display:flex; flex-direction:column; gap:6px; }
.bp-asset { display:flex; gap:6px; align-items:flex-start; color: var(--bp-label-neutral); }
.bp-asset .bp-ic { color: var(--bp-label-assistive); margin-top:3px; width:15px; height:15px; }
.bp-asset--missing {
  border:1px dashed var(--bp-cn-80); border-radius: var(--bp-r-8);
  padding:6px 8px; color: var(--bp-label-alt);
}

/* ---- stage 4 ---- */
.bp-statrow { display:grid; gap:12px; grid-template-columns: repeat(4, minmax(0,1fr)); }
.bp-stat {
  border:1px solid var(--bp-line-neutral); border-radius: var(--bp-r-12);
  padding:14px 16px; background:#fff; display:flex; flex-direction:column; gap:2px;
}
.bp-stat__n { font-weight:700 !important; font-size:1.75rem !important; line-height:2.125rem !important; letter-spacing:-.03em; }
.bp-stat__l { color: var(--bp-label-alt); }
.bp-plan {
  display:flex; flex-direction:column; gap:8px; padding:16px; margin-bottom:10px;
  border:1px solid var(--bp-line-alt); border-radius: var(--bp-r-12); background: var(--bp-cn-99);
}
.bp-plan__top { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
.bp-plan__meta { color: var(--bp-label-alt); }
.bp-secnav { display:flex; flex-direction:column; gap:4px; }
.bp-secnav__item {
  display:grid; grid-template-columns:minmax(0,1fr) auto; align-items:center; gap:8px;
  padding:10px 12px; border-radius: var(--bp-r-10); border:1px solid transparent;
  background:#fff; color: var(--bp-label-neutral); font-size:.875rem;
}
.bp-secnav__item[data-open="true"] { border-color: var(--bp-orange-39); background: var(--bp-orange-95); }
.bp-secnav__w {
  font-size:.6875rem; font-weight:700; padding:2px 6px; border-radius: var(--bp-r-6);
  background: var(--bp-blue-95); color: var(--bp-primary-strong); white-space:nowrap;
}
.bp-secnav__s { color: var(--bp-label-alt); font-size:.75rem; grid-column:1 / -1; }
.bp-secnav__item--stack { display:flex; flex-direction:column; gap:2px; align-items:flex-start; text-align:left; }
.bp-secnav__item--stack .bp-mono { word-break:break-all; }

.bp-tasks { display:grid; gap:8px; grid-template-columns: repeat(2, minmax(0,1fr)); }
.bp-task {
  display:grid; grid-template-columns:auto minmax(0,1fr); gap:4px 10px;
  padding:12px 14px; border:1px solid var(--bp-line-alt); border-radius: var(--bp-r-10); background:#fff;
}
.bp-task__i { grid-row: span 2; margin-top:2px; color: var(--bp-green-40); }
.bp-task[data-state="open"] .bp-task__i { color: var(--bp-primary); }
.bp-task__owner { color: var(--bp-label-alt); }

.bp-queries { display:grid; gap:6px; }
.bp-query {
  display:flex; align-items:center; gap:8px; padding:10px 12px; border-radius: var(--bp-r-8);
  background: var(--bp-cn-99); border:1px solid var(--bp-line-alt); color: var(--bp-label-neutral);
  font-size:.8125rem; word-break: break-all;
}
.bp-query .bp-ic { color: var(--bp-label-assistive); flex:none; }

/* streamlit widget skins */
.stTextArea textarea {
  font-family: var(--bp-font) !important; font-size:.9375rem !important; line-height:1.625rem !important;
  border-radius: var(--bp-r-12) !important; border:1px solid var(--bp-line) !important;
  background:#fff !important; color: var(--bp-label) !important; padding:14px 16px !important;
}
.stTextArea textarea:focus { border-color: var(--bp-primary) !important; box-shadow: 0 0 0 3px var(--bp-blue-95) !important; }
.stTextArea label p, .stTextInput label p { font-weight:600; color: var(--bp-label); }
[data-testid="stExpander"] details {
  border:1px solid var(--bp-line-neutral) !important; border-radius: var(--bp-r-16) !important;
  background: var(--bp-cn-99) !important; overflow:hidden;
}
[data-testid="stExpander"] summary { padding:14px 20px !important; font-weight:600; }
[data-testid="stExpander"] summary:hover { background: var(--bp-cn-98); }

.bp-foot {
  border-top:1px solid var(--bp-line-alt); margin-top:56px !important; padding:24px 0 0;
  color: var(--bp-label-alt);
}

/* one orchestrated reveal per stage */
@keyframes bp-rise { from { opacity:0; transform: translateY(10px); } to { opacity:1; transform:none; } }
.bp-reveal { animation: bp-rise var(--bp-dur-slow) var(--bp-ease) both; }
.bp-d1 { animation-delay: 0ms; } .bp-d2 { animation-delay: 60ms; }
.bp-d3 { animation-delay: 120ms; } .bp-d4 { animation-delay: 180ms; }

/* ---- responsive ---- */
@media (max-width: 1080px) {
  .bp-positions { grid-template-columns: minmax(0,1fr); }
}
@media (max-width: 900px) {
  [data-testid="stHorizontalBlock"] { flex-direction: column; }
  [data-testid="stColumn"] { width:100% !important; flex:1 1 100% !important; min-width:0 !important; }
  .st-key-bp-stepper { max-width: none; }
  /* the proposal review summary leads the long stage-4 column on narrow screens */
  .st-key-bp-stage4 [data-testid="stColumn"]:nth-of-type(2) { order: -1; }
  /* the forward action leads the stacked stage navigation, as the reference does */
  .st-key-bp-nav-2 [data-testid="stColumn"]:nth-of-type(1),
  .st-key-bp-nav-3 [data-testid="stColumn"]:nth-of-type(1) { order: 2; }
  .st-key-bp-nav-2 [data-testid="stColumn"]:nth-of-type(2),
  .st-key-bp-nav-3 [data-testid="stColumn"]:nth-of-type(2) { order: 1; }
  .st-key-bp-stepper [data-testid="stHorizontalBlock"] { flex-direction: row !important; }
  .st-key-bp-stepper [data-testid="stColumn"] { width:auto !important; flex:1 1 0 !important; }
  .bp-tablewrap { border:0; border-radius:0; background:transparent; overflow:visible; }
  table.bp-crit, table.bp-crit tbody, table.bp-crit tr, table.bp-crit td { display:block; width:100%; }
  table.bp-crit thead { display:none; }
  table.bp-crit tbody tr {
    border:1px solid var(--bp-line); border-radius: var(--bp-r-16);
    margin-bottom:12px; padding:8px 0; background:#fff;
  }
  table.bp-crit tbody tr[data-gap="uncovered"] { border-style: dashed; }
  table.bp-crit td {
    display:grid; grid-template-columns:74px minmax(0,1fr); gap:12px;
    padding:10px 16px; align-items:start;
  }
  table.bp-crit td::before {
    content: attr(data-label); color: var(--bp-label-alt); font-size:.6875rem;
    text-transform:uppercase; letter-spacing:.06em; font-weight:600; padding-top:4px;
  }
  .bp-statrow { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
@media (max-width: 760px) {
  .stMainBlockContainer, .block-container { padding: 16px 16px 72px !important; }
  .bp-verdict { padding:20px; }
  .bp-card { padding:16px; }
  .bp-rail { padding:16px; }
  .bp-dim { grid-template-columns:24px minmax(0,1fr); }
  .bp-dim > .bp-badge { grid-column:2; justify-self:start; }
  .bp-dim__detail { grid-column:2; }
  .bp-band { flex-direction:column; min-height:0; }
  .bp-band__seg { border-right:0; border-bottom:1px solid var(--bp-line-alt); }
  .bp-band__seg:last-child { border-bottom:0; }
  .bp-tasks, .bp-ladder { grid-template-columns: minmax(0,1fr); }
  .bp-statrow { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .bp-brandsub { display:none; }
  /* the stage name stays in the accessible name; only its pixels are folded away */
  .st-key-bp-stepper .stButton button > * {
    position:absolute !important; width:1px !important; height:1px !important;
    overflow:hidden !important; clip:rect(0 0 0 0) !important; white-space:nowrap !important;
    margin:0 !important; padding:0 !important;
  }
  .st-key-bp-stepper .stButton button { position:relative; min-height:40px; }
  .st-key-bp-stepper [data-testid="stColumn"] .stButton button::before {
    font-size:.875rem; font-weight:700;
  }
  .st-key-bp-stepper [data-testid="stColumn"]:nth-of-type(1) .stButton button::before { content:"1" / ""; }
  .st-key-bp-stepper [data-testid="stColumn"]:nth-of-type(2) .stButton button::before { content:"2" / ""; }
  .st-key-bp-stepper [data-testid="stColumn"]:nth-of-type(3) .stButton button::before { content:"3" / ""; }
  .st-key-bp-stepper [data-testid="stColumn"]:nth-of-type(4) .stButton button::before { content:"4" / ""; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration:.01ms !important; animation-iteration-count:1 !important;
    transition-duration:.01ms !important;
  }
}
</style>
"""


def write(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Navigation state
# ---------------------------------------------------------------------------


def current_stage() -> int:
    return int(st.session_state.get(STAGE_KEY, 0))


def go_to_stage(index: int) -> None:
    bounded = max(0, min(index, len(STAGES) - 1))
    st.session_state[STAGE_KEY] = bounded
    st.query_params["stage"] = str(bounded + 1)
    st.rerun()


def adopt_stage_from_query() -> None:
    """A stage is addressable, so a screen can be linked to and reloaded."""
    if STAGE_KEY in st.session_state:
        return
    raw = st.query_params.get("stage")
    try:
        requested = int(raw) - 1
    except (TypeError, ValueError):
        requested = 0
    st.session_state[STAGE_KEY] = max(0, min(requested, len(STAGES) - 1))


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------


def render_shell_header(stage: int, enabled: bool) -> None:
    write(STYLE + sprite())
    write(
        '<div class="bp-appbar">'
        f'<span class="bp-mark">{icon("instance", "bp-ic bp-ic--18")}</span>'
        f'<span class="bp-t-headline2 bp-bold bp-brandname">{esc(PRODUCT_NAME)}</span>'
        f'<span class="bp-t-caption1 bp-brandsub">{esc(PRODUCT_TAGLINE)}</span>'
        "</div>"
    )
    with st.container(key="bp-stepper"):
        columns = st.columns(len(STAGES), gap="small")
        for index, (column, label) in enumerate(zip(columns, STAGES, strict=True)):
            with column:
                if st.button(
                    f"{index + 1} · {label}",
                    key=f"bp-step-{index}",
                    type="primary" if index == stage else "secondary",
                    disabled=not enabled and index > 0,
                    width="stretch",
                    help=f"Go to stage {index + 1} of {len(STAGES)}: {label}",
                ):
                    go_to_stage(index)
    write('<div class="bp-rule"></div>')
    write(
        f'<p class="bp-sr" role="status">Stage {stage + 1} of {len(STAGES)} — {esc(STAGES[stage])}</p>'
    )


def render_footer() -> None:
    write(
        '<p class="bp-foot bp-t-caption1">Every status on these screens is read back from the recorded '
        "analysis. Nothing is generated at display time.</p>"
    )


# ---------------------------------------------------------------------------
# Stage 1 — Opportunities
# ---------------------------------------------------------------------------


def tender_card(group: dict, view: dict | None, primary: bool) -> str:
    run = group["current"]
    title = (view or {}).get("headline") if primary and view else None
    title = title or str(run.get("opportunity_id") or NOT_RECORDED)
    supplier = (view or {}).get("supplier_name") if primary and view else None
    supplier = supplier or str(run.get("supplier_profile_id") or "")
    status = str(((view or {}).get("status") if primary else "") or "").upper()
    source = (view or {}).get("source_type") if primary and view else ""
    completed = (view or {}).get("completed_on") if primary and view else ""
    completed_label = "Completed"
    if not completed:
        completed = display_date(run.get("created_at"))
        completed_label = "Recorded"

    chips = [
        badge(f"Decision {status}", "brand", "check") if status else "",
        badge("Analysis completed", "pass", "check-circle"),
    ]
    facts = [
        f'<span class="bp-chip">{icon("clock")}{esc(completed_label)} {esc(completed)}</span>'
        if completed
        else ""
    ]
    if source:
        facts.append(f'<span class="bp-chip">{icon("storage")}Source type: {esc(source)}</span>')
    history = group["history"]
    history_line = (
        f"Current analysis {esc(run.get('run_id'))} · {len(history)} earlier "
        f"{'analysis' if len(history) == 1 else 'analyses'} in history"
        if history
        else f"Current analysis {esc(run.get('run_id'))} · no earlier analysis recorded"
    )
    return (
        f'<div class="bp-tender{"" if primary else " bp-tender--rest"}">'
        f'<div><p class="bp-t-heading2 bp-bold bp-tender__title">{esc(title)}</p>'
        f'<p class="bp-t-body2 bp-note">Supplier {esc(supplier or NOT_RECORDED)}</p></div>'
        f'<div class="bp-tender__meta">{"".join(chips)}{"".join(facts)}</div>'
        f'<p class="bp-t-caption1 bp-tender__foot">{history_line}</p>'
        "</div>"
    )


def render_opportunities(groups: list[dict], all_runs: list[dict], view: dict | None) -> None:
    write(page_head(1, "Opportunities", (
        "Pick the tender you are pursuing. Each tender carries one current completed analysis; "
        "earlier analyses stay in its history."
    )))

    if st.session_state.pop(LOST_RUN_KEY, None):
        write(notice(
            '<p class="bp-t-body2 bp-bold">That analysis is no longer available.</p>'
            '<p class="bp-t-body2">The run you had open is not in the current list of completed analyses, '
            "so the workspace returned here. Choose a tender to continue.</p>",
            "warn", "warning", role="status",
        ))

    main, side = st.columns([1, 0.44], gap="medium")

    if not groups:
        with main:
            write(
                '<div class="bp-empty bp-reveal bp-d1">'
                f'<span class="bp-empty__icon">{icon("storage", "bp-ic bp-ic--18")}</span>'
                '<p class="bp-t-heading2 bp-bold">No tender has a completed analysis</p>'
                '<p class="bp-t-body2 bp-lede">Nothing is opened here until a run records a decision, a '
                "selected win position, a weighted plan, its proposal sections and its owned work together. "
                "No tender is invented in the meantime.</p>"
                "</div>"
            )
            if all_runs:
                rows = "".join(
                    f'<div class="bp-hist__item"><span class="bp-t-caption1 bp-mono">'
                    f'{esc(item.get("run_id"))}</span>'
                    f'<span class="bp-t-body2">{esc(item.get("opportunity_id") or NOT_RECORDED)}</span>'
                    f'<span class="bp-t-caption1 bp-note">State {esc(item.get("state") or NOT_RECORDED)} · '
                    f'{esc(item.get("decision_count"))} decision · {esc(item.get("plan_count"))} plan · '
                    f'{esc(item.get("section_count"))} section · {esc(item.get("task_count"))} task</span></div>'
                    for item in all_runs[:8]
                )
                write(
                    '<span class="bp-gap-lg"></span>'
                    + section_head("Analyses that did not finish", f"{len(all_runs)} recorded in total")
                    + f'<div class="bp-hist">{rows}</div>'
                )
        with side:
            write(rail("Analysis history", '<p class="bp-t-body2 bp-note">No completed analysis is recorded yet.</p>'))
        return

    with main:
        write(
            section_head("Tenders with a completed analysis", f"{len(groups)} recorded")
            + '<div class="bp-reveal bp-d1">'
            + "".join(
                tender_card(group, view if index == 0 else None, index == 0)
                + ('<span class="bp-gap-lg"></span>' if index < len(groups) - 1 else "")
                for index, group in enumerate(groups)
            )
            + "</div>"
        )
        for index, group in enumerate(groups):
            write('<span class="bp-gap-lg"></span>')
            title = (view or {}).get("headline") if index == 0 and view else group["opportunity_id"]
            if st.button(
                f"Open bid decision — {title}",
                key=f"bp-open-{group['current']['run_id']}",
                type="primary" if index == 0 else "secondary",
            ):
                st.session_state[RUN_KEY] = group["current"]["run_id"]
                go_to_stage(1)

        write(
            '<span class="bp-gap-lg"></span>'
            + section_head("What each stage answers", "Opening a tender walks these four in order.")
            + '<div class="bp-ladder bp-reveal bp-d2">'
            + "".join(
                f'<div class="bp-ladder__item"><span class="bp-ladder__n">{number}</span>'
                f'<span class="bp-t-headline2 bp-bold">{esc(name)}</span>'
                f'<span class="bp-t-body2 bp-note">{esc(text)}</span></div>'
                for number, name, text in (
                    (1, "Opportunities", "Which tender you are working, and which analysis is the current one."),
                    (2, "Bid decision", "Whether to bid — and which recorded policy facts that rests on."),
                    (3, "Win plan", "Where the score weight sits, and which win position was recorded."),
                    (4, "Proposal room", "What is written, what the review found, and whether it can be sent."),
                )
            )
            + "</div>"
        )

    with side:
        current = groups[0]["current"]
        history = groups[0]["history"]
        items = (
            f'<div class="bp-hist__item" data-current="true">'
            f'<span class="bp-t-caption1 bp-mono">{esc(current.get("run_id"))}</span>'
            f'<span class="bp-t-body2 bp-bold">Recorded {esc(display_date(current.get("created_at")))}</span>'
            f'{badge("Current analysis", "pass", "check-circle")}</div>'
        )
        items += "".join(
            f'<div class="bp-hist__item"><span class="bp-t-caption1 bp-mono">{esc(item.get("run_id"))}</span>'
            f'<span class="bp-t-body2">Recorded {esc(display_date(item.get("created_at")))}</span>'
            f'{badge("Superseded", "neutral", "clock")}</div>'
            for item in history
        )
        note = (
            "The current analysis is what every later stage reads. Earlier analyses stay here and are not "
            "carried forward. Each date is when the run was recorded."
            if history
            else "The current analysis is what every later stage reads. No earlier completed analysis is "
            "recorded for this tender. The date is when the run was recorded."
        )
        write(rail("Analysis history", f'<p class="bp-t-body2 bp-note">{note}</p><div class="bp-hist">{items}</div>'))


# ---------------------------------------------------------------------------
# Stage 2 — Bid decision
# ---------------------------------------------------------------------------


def render_decision(view: dict) -> None:
    write(page_head(2, "Bid decision"))
    verdict = str(view["status"]).upper()
    tone = {"PURSUE": "go", "REVIEW": "open", "NO-GO": "stop"}.get(verdict, "open")
    dimensions = policy_dimensions(view)
    passed = sum(1 for item in dimensions if item["state"] == "pass")

    main, side = st.columns([1, 0.44], gap="medium")

    with main:
        write(
            '<div class="bp-verdict bp-reveal bp-d1">'
            f'<div><p class="bp-t-body1 bp-verdict__q">Should we bid on {esc(view["headline"])}?</p>'
            f'<p class="bp-verdict__word" data-tone="{tone}">{esc(verdict)}</p></div>'
            f'<p class="bp-t-body1-reading bp-verdict__say">{esc(decision_summary(view))}</p>'
            '<div class="bp-kvgrid">'
            + kv_rows([
                ("Buyer objective", str(view["objective"] or "")),
                ("Supplier", str(view["supplier_name"] or "")),
                ("Scope", str(view["scope"] or "")),
            ])
            + "</div></div>"
        )
        write(
            '<span class="bp-gap-lg"></span>'
            + section_head(
                "Policy dimensions",
                f"{passed} of {len(dimensions)} passed — each one is stated in words, not by colour alone.",
            )
            + '<div class="bp-dims bp-reveal bp-d2">'
            + "".join(
                f'<div class="bp-dim" data-state="{item["state"]}">'
                f'<span class="bp-dim__icon">{icon("check-circle" if item["state"] == "pass" else "warning")}</span>'
                f'<span class="bp-t-headline2 bp-bold">{esc(item["name"])}</span>'
                + badge(item["badge"], "pass" if item["state"] == "pass" else "pending")
                + f'<span class="bp-t-body2 bp-dim__detail">{esc(item["detail"])}</span></div>'
                for item in dimensions
            )
            + "</div>"
        )
        write(
            '<span class="bp-gap-lg"></span>'
            + notice(
                '<p class="bp-t-body2-reading">Nothing on this screen is editable. The verdict, the versions '
                "and the policy results are settled facts from the recorded analysis; their identifiers sit "
                "beside this panel so a reader can check them without crowding the answer.</p>",
                "info",
                "info",
            )
            + '<span class="bp-gap-lg"></span>'
        )
        with st.container(key="bp-nav-2"):
            back, forward = st.columns(2, gap="small")
        with back:
            if st.button("← Back to opportunities", key="bp-back-1", width="stretch"):
                go_to_stage(0)
        with forward:
            if st.button("Open win plan →", key="bp-next-3", type="primary", width="stretch"):
                go_to_stage(2)

    with side:
        run = view["run"]
        write(rail("Record identifiers", '<div class="bp-kvstack">' + kv_rows([
            ("Tender version", str(run.get("opportunity_version") or "")),
            ("Supplier profile version", str(run.get("supplier_profile_version") or "")),
            ("Policy version", str(run.get("policy_version") or "")),
            ("Analysis run", str(view["run_id"])),
            ("Provider", str(run.get("provider") or "")),
            ("Run state", str(run.get("state") or "")),
            ("Source type", str(view["source_type"] or "")),
            (
                "Completed" if view["completed_on"] else "Recorded",
                str(view["completed_on"] or view["recorded_on"] or ""),
            ),
        ]) + "</div>"))


# ---------------------------------------------------------------------------
# Stage 3 — Win plan
# ---------------------------------------------------------------------------


def render_win_plan(view: dict) -> None:
    write(page_head(3, "Win plan", (
        "The official score map decides where effort is worth spending. The recorded run selected one win "
        "position; the criteria below are the plan it carries into the proposal."
    )))
    criteria = view["criteria"]

    main, side = st.columns([1, 0.44], gap="medium")

    with main:
        if not criteria:
            write(notice(
                '<p class="bp-t-body2">This analysis recorded no weighted response plan, so there is no '
                "score map to show.</p>", "warn", "warning",
            ))
        else:
            segments = "".join(
                f'<div class="bp-band__seg" data-gap="{item["gap"]}" style="flex:{item["weight"]:g} 1 0">'
                f'<span class="bp-band__w bp-num">{trim(item["weight"])}</span>'
                f'<span class="bp-band__n"><b>{esc(item["name"])}</b>'
                f'{"Covered" if item["gap"] == "covered" else "No recorded asset"}</span></div>'
                for item in criteria
            )
            write(
                section_head(
                    "Official score map",
                    f"Weights are fixed by the tender and total {trim(view['total_weight'])}.",
                )
                + f'<div class="bp-band bp-reveal bp-d1">{segments}</div>'
                + '<div class="bp-bandkey bp-t-caption1">'
                '<span class="bp-bandkey__item"><span class="bp-swatch" data-gap="covered"></span>'
                "Covered — an evidence asset is recorded</span>"
                '<span class="bp-bandkey__item"><span class="bp-swatch" data-gap="uncovered"></span>'
                "No recorded asset</span></div>"
            )

        strategies = view["strategies"]
        if strategies:
            cards = ""
            for item in strategies:
                chosen = bool(item.get("selected"))
                proof = as_records(item.get("proof_cards"))
                proof_line = "; ".join(
                    " — ".join(part for part in (record_label(card), record_detail(card)) if part)
                    for card in proof
                ) or "No proof card is recorded."
                weakness = str(item.get("weakness") or "").strip()
                mark = (
                    badge("Selected", "brand", "check")
                    if chosen
                    else badge("Comparative record", "outline")
                )
                cards += (
                    f'<div class="bp-pos" data-selected="{"true" if chosen else "false"}">'
                    '<div class="bp-pos__head">'
                    f'<p class="bp-t-headline1 bp-bold bp-pos__name">{esc(item.get("title") or NOT_RECORDED)}</p>'
                    f"{mark}"
                    "</div>"
                    f'<p class="bp-t-body2-reading bp-pos__desc">{esc(item.get("statement") or NOT_RECORDED)}</p>'
                    f'<p class="bp-t-caption1 bp-pos__foot">Proof: {esc(proof_line)}</p>'
                    + (
                        f'<p class="bp-t-caption1 bp-pos__foot">Recorded weakness: {esc(weakness)}</p>'
                        if weakness
                        else ""
                    )
                    + "</div>"
                )
            write(
                '<span class="bp-gap-lg"></span>'
                + section_head(
                    "Win positions",
                    "The submitted analysis is immutable: one position is selected and the others stay as "
                    "the comparative records that were considered.",
                )
                + f'<div class="bp-positions bp-reveal bp-d2">{cards}</div>'
            )

        if criteria:
            selected_title = str(view["selected"].get("title") or "the selected win position")
            rows = ""
            for item in criteria:
                assets = (
                    "".join(
                        f'<div class="bp-asset">{icon("doc")}<span class="bp-t-body2">{esc(asset)}</span></div>'
                        for asset in item["assets"]
                    )
                    if item["assets"]
                    else f'<div class="bp-asset bp-asset--missing">{icon("minus")}'
                    '<span class="bp-t-body2">No asset recorded</span></div>'
                )
                gap = (
                    badge("Covered", "pass", "check-circle")
                    + '<p class="bp-t-caption1 bp-note" style="margin-top:6px">An evidence asset is recorded '
                    "against this criterion.</p>"
                    if item["gap"] == "covered"
                    else badge("No recorded asset", "outline", "minus")
                    + '<p class="bp-t-caption1 bp-note" style="margin-top:6px">No evidence asset was recorded '
                    "for this criterion.</p>"
                )
                rows += (
                    f'<tr data-gap="{item["gap"]}">'
                    f'<td data-label="Weight"><div class="bp-cell">'
                    f'<span class="bp-crit__w bp-num">{trim(item["weight"])}</span>'
                    f'<span class="bp-crit__wsub">of {trim(view["total_weight"])}</span></div></td>'
                    f'<td data-label="Criterion"><div class="bp-cell">'
                    f'<p class="bp-t-headline2 bp-bold">{esc(item["name"])}</p>'
                    f'<p class="bp-t-body2-reading">{esc(item["claim"] or NOT_RECORDED)}</p></div></td>'
                    f'<td data-label="Assets"><div class="bp-cell"><div class="bp-assets">{assets}</div></div></td>'
                    f'<td data-label="Gap state"><div class="bp-cell">{gap}</div></td>'
                    f'<td data-label="Owner"><div class="bp-cell">'
                    f'<span class="bp-t-body2">{esc(item["owner"] or NOT_RECORDED)}</span></div></td>'
                    "</tr>"
                )
            write(
                '<span class="bp-gap-lg"></span>'
                + section_head(
                    f"Criteria under “{selected_title}”",
                    "Every row states its own gap in words, not only in colour.",
                )
                + '<div class="bp-tablewrap bp-reveal bp-d3"><table class="bp-crit"><thead><tr>'
                "<th>Weight</th><th>Criterion and recorded claim</th><th>Evidence assets</th>"
                "<th>Gap state</th><th>Owner</th></tr></thead>"
                f"<tbody>{rows}</tbody></table></div>"
            )
        with st.container(key="bp-nav-3"):
            back, forward = st.columns(2, gap="small")
        with back:
            if st.button("← Back to bid decision", key="bp-back-2", width="stretch"):
                go_to_stage(1)
        with forward:
            if st.button("Open proposal room →", key="bp-next-4", type="primary", width="stretch"):
                go_to_stage(3)

    with side:
        selected_title = str(view["selected"].get("title") or NOT_RECORDED)
        uncovered = [item["name"] for item in criteria if item["gap"] == "uncovered"]
        body = '<div class="bp-kvstack">' + kv_rows([
            ("Selected position", selected_title),
            ("Weight covered", f"{trim(view['covered_weight'])} of {trim(view['total_weight'])}"),
            ("Weight with no recorded asset", trim(view["open_weight"])),
            ("Positions recorded", str(len(view["strategies"]))),
        ]) + "</div>"
        if uncovered:
            body += notice(
                f'<p class="bp-t-body2">{trim(view["open_weight"])} points of score weight carry no recorded '
                f"asset: {esc(', '.join(uncovered))}. Each one is named in the table rather than signalled by "
                "colour alone.</p>",
                "warn",
                "warning",
            )
        else:
            body += notice(
                '<p class="bp-t-body2">Every criterion in the score map carries at least one recorded '
                "evidence asset.</p>",
                "ok",
                "check-circle",
            )
        write(rail("Coverage", body))


# ---------------------------------------------------------------------------
# Stage 4 — Proposal room
# ---------------------------------------------------------------------------


def _is_complete(task: dict) -> bool:
    return str(task.get("status") or "").upper() in {"COMPLETE", "COMPLETED", "DONE"}


def render_proposal(view: dict) -> None:
    write(page_head(4, "Proposal room"))
    run_id = view["run_id"]
    criteria = view["criteria"]

    if not view["sections"] or not criteria:
        write(notice(
            '<p class="bp-t-body2 bp-bold">This analysis recorded no proposal section.</p>'
            '<p class="bp-t-body2">There is nothing to draft here, and no text is generated to stand in for '
            "it. Choose another tender on the Opportunities stage.</p>",
            "warn", "warning",
        ))
        if st.button("← Back to win plan", key="bp-back-3-empty"):
            go_to_stage(2)
        return

    composed = compose_persisted_proposal(view["blueprint"], view["sections"])
    draft_key = f"bp-draft::{run_id}"

    with st.container(key="bp-stage4"):
        main, side = st.columns([1, 0.44], gap="medium")

    with main:
        # What the run recorded comes first; the draft is the one thing a
        # person may change, and the review follows the change immediately.
        counters = st.empty()

        write(
            '<span class="bp-gap-lg"></span>'
            + section_head(
                "Response plans",
                f'Carried in from the recorded win position “{esc(view["selected"].get("title") or NOT_RECORDED)}”.',
            )
            + "".join(
                '<div class="bp-plan"><div class="bp-plan__top">'
                f'<p class="bp-t-headline2 bp-bold">{esc(item["name"])}</p>'
                + badge(f"Weight {trim(item['weight'])}", "brand")
                + "</div>"
                f'<p class="bp-t-body2-reading">{esc(item["claim"] or NOT_RECORDED)}</p>'
                f'<p class="bp-t-caption1 bp-plan__meta">Owner: {esc(item["owner"] or NOT_RECORDED)} · '
                f'Assets: {esc(", ".join(item["assets"]) or "none recorded")}</p></div>'
                for item in criteria
            )
        )

        write('<span class="bp-gap-lg"></span>' + section_head(
            "Proposal draft",
            "Composed from the recorded response plans and their written fragments. Editing changes only "
            "this session; Snowflake keeps the analysis as it was submitted.",
        ))
        edited = st.text_area(
            "Proposal draft — the only editable text in the workspace",
            value=st.session_state.get(draft_key, composed),
            height=460,
            key=draft_key,
            help="Edits stay in this session. The recorded analysis in Snowflake is not changed.",
        )
        findings = red_team_persisted_draft(view["blueprint"], edited)

        with counters:
            write(
                '<div class="bp-statrow bp-reveal bp-d1">'
                + "".join(
                    f'<div class="bp-stat"><span class="bp-stat__n bp-num">{value}</span>'
                    f'<span class="bp-t-caption1 bp-stat__l">{esc(label)}</span></div>'
                    for value, label in (
                        (len(view["blueprint"]), "response plans"),
                        (len(view["sections"]), "proposal sections"),
                        (len(view["tasks"]), "tasks"),
                        (len(findings), "open review findings"),
                    )
                )
                + "</div>"
            )

        if findings:
            write(
                '<span class="bp-gap-lg"></span>'
                + notice(
                    f'<p class="bp-t-body2 bp-bold">Review failed — {len(findings)} open '
                    f'finding{"s" if len(findings) != 1 else ""}.</p>'
                    + "".join(
                        f'<p class="bp-t-body2">{esc(item.get("criterion"))}: {esc(item.get("finding"))}</p>'
                        for item in findings
                    )
                    + '<p class="bp-t-body2 bp-note">Download stays closed until every score-bearing '
                    "criterion carries its recorded asset and the highest-weight response records both "
                    "validation and buyer-outcome detail.</p>",
                    "error",
                    "warning",
                    role="status",
                )
            )
        else:
            write(
                '<span class="bp-gap-lg"></span>'
                + notice(
                    '<p class="bp-t-body2 bp-bold">Review passed — no open finding.</p>'
                    '<p class="bp-t-body2">Every score-bearing criterion carries its recorded asset, and the '
                    "highest-weight response records both validation and buyer-outcome detail.</p>",
                    "ok",
                    "check-circle",
                    role="status",
                )
            )
        st.download_button(
            "Download proposal draft",
            edited,
            file_name=f"{run_id}.md",
            mime="text/markdown",
            type="primary",
            disabled=bool(findings),
            key=f"bp-download::{run_id}",
            help=(
                "Resolve the open review findings before downloading."
                if findings
                else "Downloads exactly the edited text above."
            ),
        )

        tasks = view["tasks"]
        write(
            '<span class="bp-gap-lg"></span>'
            + section_head(
                "Owned work",
                f"{len(tasks)} recorded task{'s' if len(tasks) != 1 else ''}, each with the role that owns it.",
            )
            + '<div class="bp-tasks">'
            + "".join(
                f'<div class="bp-task" data-state="{"recorded" if _is_complete(task) else "open"}">'
                f'<span class="bp-task__i">{icon("check-circle" if _is_complete(task) else "clock")}</span>'
                f'<span class="bp-t-body2 bp-bold">{esc(task.get("task_name") or NOT_RECORDED)}</span>'
                f'<span class="bp-t-caption1 bp-task__owner">{esc(task.get("owner") or NOT_RECORDED)} · '
                f'{esc(str(task.get("status") or NOT_RECORDED).capitalize())}</span></div>'
                for task in tasks
            )
            + "</div>"
        )

        with st.expander("Execution provenance"):
            render_provenance(view)
        if st.button("← Back to win plan", key="bp-back-3"):
            go_to_stage(2)

    with side:
        states = review_state(criteria, findings)
        items = "".join(
            f'<div class="bp-secnav__item" data-open="{"true" if states.get(item["name"]) else "false"}">'
            f'<span>{esc(item["name"])}</span>'
            f'<span class="bp-secnav__w bp-num">{trim(item["weight"])}</span>'
            f'<span class="bp-secnav__s">'
            f'{esc(states.get(item["name"]) or "Present with its recorded asset.")}</span></div>'
            for item in criteria
        )
        fragments = "".join(
            f'<div class="bp-secnav__item bp-secnav__item--stack">'
            f'<span class="bp-t-body2">{esc(section.get("criterion_name") or NOT_RECORDED)}</span>'
            f'<span class="bp-t-caption1 bp-mono">{esc(section.get("section_id"))}</span></div>'
            for section in view["sections"]
        )
        write(rail("Proposal review", (
            '<p class="bp-t-body2 bp-note">Score-bearing criteria, with the weight each one carries and its '
            "current review state.</p>"
            f'<div class="bp-secnav">{items}</div>'
            '<p class="bp-t-label1 bp-bold bp-rail__title" style="margin-top:6px">Persisted fragments</p>'
            f'<div class="bp-secnav">{fragments}</div>'
        )))


def render_provenance(view: dict) -> None:
    run = view["run"]
    trace = view["trace"]
    provenance = trace.get("execution_provenance") if isinstance(trace.get("execution_provenance"), dict) else {}
    session_id = first_key(provenance, ("cortex_session_id", "session_id")) or first_key(
        trace, ("session_id", "snowflake_session_id")
    )
    query_ids = as_records(first_key(provenance, ("cortex_write_query_ids", "query_ids")))
    write(
        '<div class="bp-kvgrid">'
        + kv_rows([
            ("Analysis run", str(view["run_id"])),
            ("Provider", str(run.get("provider") or "")),
            ("Run state", str(run.get("state") or "")),
            ("Policy version", str(run.get("policy_version") or "")),
            ("Supplier profile version", str(run.get("supplier_profile_version") or "")),
            ("Cortex session", flatten(session_id) if session_id else ""),
            ("Connection", str(configured_connection_name() or "")),
            ("Reader role", EXPECTED_READER_ROLE),
        ])
        + "</div>"
    )
    if query_ids:
        write(
            f'<p class="bp-t-label1 bp-bold" style="margin-top:16px">Query evidence '
            f'({len(query_ids)} recorded)</p>'
            + '<div class="bp-queries">'
            + "".join(
                f'<div class="bp-query">{icon("lock")}<span>{esc(flatten(item))}</span></div>'
                for item in query_ids
            )
            + "</div>"
        )
    else:
        write('<p class="bp-t-body2 bp-note">No query evidence is recorded for this run.</p>')


# ---------------------------------------------------------------------------
# Production states
# ---------------------------------------------------------------------------


def render_configuration_error() -> None:
    write(page_head(1, "Workspace is not configured"))
    write(notice(
        '<p class="bp-t-body2 bp-bold">No Snowflake connection is configured.</p>'
        f'<p class="bp-t-body2-reading">{esc(PRODUCT_NAME)} reads every screen from an authenticated '
        f"Snowflake run and does not fall back to local fixtures. Set <code>{CONNECTION_VARIABLE}</code> to "
        f"a named Snowflake CLI connection that uses the {EXPECTED_READER_ROLE} role, then reload this "
        "page.</p>"
        f'<p class="bp-t-caption1 bp-note">For example: {CONNECTION_VARIABLE}=bidpilot-reader '
        "streamlit run app.py</p>",
        "error",
        "warning",
        role="alert",
    ))


def render_connection_error() -> None:
    write(page_head(1, "Opportunities"))
    write(notice(
        '<p class="bp-t-body2 bp-bold">Snowflake could not be reached.</p>'
        '<p class="bp-t-body2-reading">The recorded analysis is temporarily unavailable.</p>'
        f'<p class="bp-t-body2">Authenticated mode stays authenticated: no fixture is shown in place of a '
        f"failed query. Check that the connection is reachable and uses the {EXPECTED_READER_ROLE} role, "
        "then try again.</p>",
        "error",
        "warning",
        role="alert",
    ))
    if st.button("Retry the connection", key="bp-retry", type="primary"):
        st.cache_data.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def load_runs(connection_name: str) -> list[dict]:
    return SnowflakeBidRoomStore(connection_name).list_runs()


@st.cache_data(show_spinner=False)
def load_run(connection_name: str, run_id: str) -> dict:
    return SnowflakeBidRoomStore(connection_name).load_run(run_id)


def render() -> None:
    """Draw the workspace for whatever the configured connection can supply."""
    adopt_stage_from_query()
    st.session_state.setdefault(RUN_KEY, None)

    connection_name = configured_connection_name()
    if not connection_name:
        render_shell_header(0, enabled=False)
        render_configuration_error()
        render_footer()
        return

    # Loading is announced above the workspace and then taken away, so a
    # finished screen never carries the scaffolding that produced it.
    loading = st.empty()
    runs: list[dict] = []
    listing_failed = False
    with loading.container(), st.spinner("Reading completed analyses from Snowflake…"):
        try:
            runs = load_runs(connection_name)
        except (SnowflakeBidRoomError, KeyError):
            LOGGER.exception("Snowflake run listing failed")
            listing_failed = True
    loading.empty()

    if listing_failed:
        render_shell_header(0, enabled=False)
        render_connection_error()
        render_footer()
        return

    complete = [run for run in runs if str(run.get("state")) == "COMPLETED" and run.get("is_complete")]
    groups = group_by_opportunity(complete)
    known = {run["run_id"] for run in complete}

    selected_id = st.session_state.get(RUN_KEY)
    if selected_id is not None and selected_id not in known:
        # A run that vanished does not silently become a different run.
        st.session_state[RUN_KEY] = None
        st.session_state[LOST_RUN_KEY] = True
        st.session_state[STAGE_KEY] = 0
        st.query_params["stage"] = "1"
        selected_id = None
    if selected_id is None and complete:
        selected_id = complete[0]["run_id"]
        st.session_state[RUN_KEY] = selected_id

    stage = current_stage()
    if not complete:
        stage = 0
        st.session_state[STAGE_KEY] = 0

    view: dict | None = None
    detail_failed = False
    if selected_id:
        with loading.container(), st.spinner("Opening the recorded analysis from Snowflake…"):
            try:
                result = load_run(connection_name, selected_id)
            except (SnowflakeBidRoomError, KeyError):
                LOGGER.exception("Snowflake run detail failed for %s", selected_id)
                detail_failed = True
            else:
                view = build_run_view(result, selected_id, str((
                    next((run for run in complete if run["run_id"] == selected_id), {})
                ).get("opportunity_id") or ""))
        loading.empty()

    render_shell_header(stage, enabled=bool(view))

    if view is not None:
        write(bid_room_causal_summary(view))

    if detail_failed and stage > 0:
        render_connection_error()
        render_footer()
        return

    if stage == 0:
        if detail_failed:
            write(notice(
                '<p class="bp-t-body2">The current analysis is temporarily unavailable. '
                "Retry before continuing to its bid decision.</p>",
                "error", "warning", role="alert",
            ))
        render_opportunities(groups, runs, view)
    elif view is None:
        st.session_state[STAGE_KEY] = 0
        render_opportunities(groups, runs, None)
    elif stage == 1:
        render_decision(view)
    elif stage == 2:
        render_win_plan(view)
    else:
        render_proposal(view)

    render_footer()
