"""Live decision-and-draft panel for one reviewed public notice.

The panel runs the same local pursuit policy the agent surface exposes. It
never persists anything, never starts a Cortex run, and drafts only from the
synthetic demo supplier profile after every eligibility requirement is
evidenced by the operator in front of the screen.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

import streamlit as st

from bidpilot import agent_core

DRAFT_BUTTON_KEY = "bp-draft-run"
SUPPLIER_ID = "supplier-northstar"


def _badge(decision: str) -> str:
    colour = {"PURSUE": "green", "REVIEW": "orange", "NO-GO": "red"}.get(
        decision, "gray"
    )
    return f":{colour}[**{decision}**]"


def render_proposal_panel(row: Mapping[str, object], *, now: datetime) -> None:
    """Draw the evidence gate and, on PURSUE, the drafted proposal."""
    notice = str(row.get("notice_number") or "")
    tender = agent_core.get_tender(notice, now=now)
    requirements = list(tender.get("eligibility_requirements") or [])
    closed = tender.get("deadline_state") == "closed"

    st.markdown("### Run the decision and draft a proposal")
    st.caption(
        "Local pursuit policy on the synthetic demo supplier profile. Nothing is "
        "persisted and no Cortex run is started. Tick only the evidence the supplier "
        "actually holds; the draft appears only on PURSUE."
    )
    evidence: dict[str, bool] = {}
    for index, requirement in enumerate(requirements):
        if st.checkbox(f"Evidence on file: {requirement}", key=f"bp-evidence-{index}"):
            evidence[str(index)] = True
    if closed:
        st.caption(
            "This notice is closed, so any draft is a historical exercise and cannot be submitted."
        )
    if not st.button("Run decision and draft", key=DRAFT_BUTTON_KEY, type="primary"):
        return

    decision = agent_core.decide(notice, evidence, now=now)
    st.markdown(f"Decision {_badge(decision['decision'])} — {decision['reason']}")
    if decision["decision"] != "PURSUE":
        for action in decision.get("next_actions") or []:
            st.markdown(f"- {action}")
        st.info("No proposal is drafted until the decision is PURSUE.")
        return

    try:
        draft = agent_core.draft_proposal(
            notice,
            evidence,
            supplier_id=SUPPLIER_ID,
            historical_exercise=closed,
            now=now,
        )
    except agent_core.AgentCoreError as error:
        st.error(f"The proposal gate stayed closed: {error}")
        return

    supplier = draft.get("supplier") or {}
    st.markdown(
        f"Proposal gate **{draft.get('proposal_gate')}** · Win Position "
        f"**{(draft.get('selected_position') or {}).get('title', '')}** · supplier "
        f"**{supplier.get('name', '')}** (synthetic)"
    )
    st.warning(str(draft.get("disclosure") or ""))
    for section in draft.get("sections") or []:
        heading = str(section.get("heading") or section.get("criterion") or "")
        body = str(section.get("markdown") or "")
        if body.startswith("## "):
            body = body.split("\n", 1)[1] if "\n" in body else ""
        with st.expander(heading, expanded=True):
            st.markdown(body.strip())
    findings = list(draft.get("red_team") or [])
    if findings:
        st.markdown("**Red-team findings**")
        for finding in findings:
            st.markdown(f"- {finding}")
    else:
        st.markdown("**Red-team:** no open findings.")
    tasks = list(draft.get("tasks") or [])
    if tasks:
        st.markdown("**Owned work**")
        for task in tasks:
            st.markdown(f"- {task.get('title')} — {task.get('owner', 'Operator')}")
    st.download_button(
        "Download proposal draft",
        str(draft.get("markdown") or ""),
        file_name=f"{notice}-proposal-draft.md",
        mime="text/markdown",
        key="bp-draft-download",
    )
