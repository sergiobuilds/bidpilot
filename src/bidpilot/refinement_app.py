"""Top-level routing for the three-workspace refinement application."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import streamlit as st

from bidpilot import ui
from bidpilot.g2b_source import G2BSourceError, load_public_source
from bidpilot.proposal_panel import render_proposal_panel
from bidpilot.tender_catalog import load_public_tender_catalog
from bidpilot.workspace_ui import (
    catalog_date,
    deadline_state,
    koat_css,
    koat_dashboard,
    koat_tender_detail,
    render_markup,
    shell_css,
    synthetic_simulation_first_viewport,
    tender_intake_first_viewport,
    workspace_route_navigation,
)

DEFAULT_WORKSPACE = "bid-room"
ALLOWED_WORKSPACES = frozenset({"tender-intake", "bid-room", "synthetic-simulation"})
NOTICE_NUMBER = "R26BK01680611-000"
DATA_ROOT = (
    Path(__file__).resolve().parents[2] / "data" / "public-tenders" / NOTICE_NUMBER
)


def resolve_workspace(value: object) -> str:
    """Resolve a query parameter without allowing an invented workspace."""
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    candidate = str(value or "").strip()
    return candidate if candidate in ALLOWED_WORKSPACES else DEFAULT_WORKSPACE


def resolve_walkthrough(value: object) -> bool:
    """Require an explicit action before opening the authenticated replay."""
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def current_clock() -> datetime:
    """Return the aware wall clock every public deadline state is judged against."""
    return datetime.now(UTC)


def official_status(deadline: object, now: datetime) -> str:
    """Describe a notice as open or closed from its deadline, never from a fixed word."""
    state = deadline_state(deadline, now)
    when = catalog_date(deadline)
    if state == "open":
        return f"Official G2B notice · open until {when}"
    if state == "closed":
        return f"Official G2B notice · closed {when}"
    return f"Official G2B notice · deadline {when}"


def _read_json(name: str) -> dict[str, Any]:
    path = DATA_ROOT / name
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TypeError(f"{name} must contain one JSON object.")
    return value


def curated_tender_view() -> dict[str, Any]:
    """Project the verified public fixture into the intake first viewport."""
    source = load_public_source()
    projection = source["public_projection"]
    source_facts = {item["field"]: item["value"] for item in projection["source_facts"]}
    labels = {item["field"]: item["value"] for item in projection["public_labels"]}
    notice = next(
        item for item in source["artifacts"] if item["artifact_id"] == "notice-pdf"
    )
    weights = source_facts["evaluation_weights"]
    eligibility = source_facts["eligibility_requirements"]
    return {
        "notice_number": source["notice_number"],
        "title": str(source_facts["title"]),
        "issuer": str(source_facts["issuer"]),
        "source_url": str(notice["official_url"]),
        "source_sha256": str(notice["sha256"]),
        "retrieved_at": str(notice["retrieved_at"]),
        "proposal_deadline": str(source_facts["proposal_deadline"]),
        "contract_value": f"KRW {int(source_facts['contract_value_krw']) // 1_000_000}M",
        "technical_weight": str(weights["technical"]),
        "price_weight": str(weights["price"]),
        "eligibility_count": str(len(eligibility)),
        "eligibility_requirements": tuple(str(item) for item in eligibility),
        "delivery_term": str(source_facts["delivery_term"]),
        "evaluation_total": f"Technical {weights['technical']} · Price {weights['price']}",
        "supplier_boundary": str(labels["supplier_profile_boundary"]),
        "analysis_gate": "Operator review required",
    }


def synthetic_demo_result(scenario: str) -> dict[str, object]:
    """Return a visibly local policy outcome for the isolated demo workspace."""
    scenarios = {
        "missing-eligibility": (
            "NO-GO",
            "A mandatory certification is absent from the synthetic supplier profile.",
        ),
        "capacity-gap": (
            "NO-GO",
            "The synthetic delivery plan exceeds the recorded available hours.",
        ),
        "evidence-gap": (
            "REVIEW",
            "Comparable delivery evidence must be confirmed before proposal drafting.",
        ),
        "qualified": (
            "PURSUE",
            "Synthetic eligibility, capacity, and comparable-delivery gates pass.",
        ),
    }
    verdict, reason = scenarios.get(scenario, scenarios["missing-eligibility"])
    return {
        "verdict": verdict,
        "reason": reason,
        "provider": "LOCAL_PYTHON_POLICY",
        "persisted": False,
    }


def _render_navigation(workspace: str) -> None:
    render_markup(shell_css())
    render_markup(workspace_route_navigation(workspace))


def _render_tender_intake() -> None:
    try:
        view = curated_tender_view()
    except (G2BSourceError, OSError, ValueError, KeyError, TypeError):
        st.error("The curated public-source manifest is unavailable.")
        return
    render_markup(shell_css())
    render_markup(
        tender_intake_first_viewport(
            source_title=view["title"],
            official_status=official_status(view["proposal_deadline"], current_clock()),
            digest=f"{view['source_sha256'][:12]}…{view['source_sha256'][-8:]}",
            extraction_state="Notice PDF extracted · operator review required",
            evaluation_total=view["evaluation_total"],
            next_action="Confirm eligibility evidence before private analysis",
        )
    )
    left, middle, right = st.columns(3)
    left.metric("Contract value", "KRW 250M")
    middle.metric("Technical", "90 points")
    right.metric("Price", "10 points")
    st.info(
        f"{view['supplier_boundary']}. Public viewers can inspect this source review; "
        "only an authenticated operator can create a new CoCo run."
    )
    st.link_button("Open official G2B notice PDF", view["source_url"])
    st.caption(
        f"Notice {view['notice_number']} · {view['issuer']} · retrieved "
        f"{view['retrieved_at']} · proposal deadline {view['proposal_deadline']}"
    )


def _render_synthetic_simulation() -> None:
    scenario = st.selectbox(
        "Synthetic scenario",
        options=("missing-eligibility", "capacity-gap", "evidence-gap", "qualified"),
        format_func=lambda value: value.replace("-", " ").title(),
    )
    result = synthetic_demo_result(scenario)
    render_markup(shell_css())
    render_markup(
        synthetic_simulation_first_viewport(
            verdict=result["verdict"],
            reason=result["reason"],
        )
    )
    st.caption("Provider: LOCAL_PYTHON_POLICY · no run ID · no publish or sync action")


def render() -> None:
    """Render the KOAT-grammar public catalogue, detail, or separate replay."""
    now = current_clock()
    tender = str(st.query_params.get("tender") or "").strip()
    if tender:
        try:
            catalogue = load_public_tender_catalog()
        except (G2BSourceError, OSError, ValueError, KeyError, TypeError):
            render_markup(koat_css())
            st.error("The public tender record is temporarily unavailable.")
            return
        row = next(
            (item for item in catalogue if item["notice_number"] == tender), None
        )
        render_markup(koat_css())
        if row is None:
            st.error("That public tender is not in the verified catalogue.")
            return
        reviewed_view = (
            curated_tender_view()
            if row["evidence_level"] == "source-reviewed"
            else None
        )
        render_markup(koat_tender_detail(row, now=now, reviewed_view=reviewed_view))
        if reviewed_view is not None:
            render_proposal_panel(row, now=now)
        return

    if resolve_walkthrough(st.query_params.get("walkthrough")):
        render_markup(shell_css())
        ui.render()
        return

    workspace_value = st.query_params.get("workspace")
    if isinstance(workspace_value, (list, tuple)):
        workspace_value = workspace_value[0] if workspace_value else None
    requested_workspace = str(workspace_value or "").strip()
    if requested_workspace in ALLOWED_WORKSPACES:
        workspace = resolve_workspace(requested_workspace)
        _render_navigation(workspace)
        if workspace == "tender-intake":
            _render_tender_intake()
        elif workspace == "synthetic-simulation":
            _render_synthetic_simulation()
        else:
            ui.render()
        return

    try:
        catalogue = load_public_tender_catalog()
    except (G2BSourceError, OSError, ValueError, KeyError, TypeError):
        render_markup(koat_css())
        st.error("The public tender record is temporarily unavailable.")
        return

    render_markup(koat_css())
    render_markup(koat_dashboard(catalogue, now=now))
