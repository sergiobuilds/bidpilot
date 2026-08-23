"""Top-level routing for the three-workspace refinement application."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from bidpilot import ui
from bidpilot.workspace_ui import (
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


def _read_json(name: str) -> dict[str, Any]:
    path = DATA_ROOT / name
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TypeError(f"{name} must contain one JSON object.")
    return value


def curated_tender_view() -> dict[str, str]:
    """Project the verified public fixture into the intake first viewport."""
    manifest = _read_json("manifest.json")
    fixture = _read_json("public-fixture.json")
    source_facts = {
        item["field"]: item["value"]
        for item in fixture["public_projection"]["source_facts"]
    }
    labels = {
        item["field"]: item["value"]
        for item in fixture["public_projection"]["public_labels"]
    }
    notice = next(
        item for item in manifest["artifacts"] if item["artifact_id"] == "notice-pdf"
    )
    weights = source_facts["evaluation_weights"]
    return {
        "notice_number": manifest["notice_number"],
        "title": str(source_facts["title"]),
        "issuer": str(source_facts["issuer"]),
        "source_url": str(notice["official_url"]),
        "source_sha256": str(notice["sha256"]),
        "retrieved_at": str(notice["retrieved_at"]),
        "proposal_deadline": str(source_facts["proposal_deadline"]),
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
    except (OSError, ValueError, KeyError, TypeError):
        st.error("The curated public-source manifest is unavailable.")
        return
    render_markup(shell_css())
    render_markup(
        tender_intake_first_viewport(
            source_title=view["title"],
            official_status="Official G2B notice · open",
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
    """Render one workspace while keeping the verified Bid Room as default."""
    workspace = resolve_workspace(st.query_params.get("workspace"))
    _render_navigation(workspace)
    if workspace == "tender-intake":
        _render_tender_intake()
    elif workspace == "synthetic-simulation":
        _render_synthetic_simulation()
    else:
        ui.render()
