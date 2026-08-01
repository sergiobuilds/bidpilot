"""BidPilot's judge-facing Streamlit prototype."""

from __future__ import annotations

import streamlit as st

from bidpilot.engine import create_proposal_tasks, evaluate_bid
from bidpilot.fixtures import COMPANY, RFPS

st.set_page_config(page_title="BidPilot", page_icon="◈", layout="wide")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
      :root { --ink: #112620; --paper: #f4f0e6; --lime: #ccff00; --clay: #e8653e; --line: #b9b1a2; }
      .stApp { background: var(--paper); color: var(--ink); }
      h1, h2, h3 { font-family: 'Fraunces', Georgia, serif !important; color: var(--ink); }
      p, span, label, .stMarkdown, .stMetric { font-family: 'DM Mono', monospace; }
      .hero { border-top: 3px solid var(--ink); border-bottom: 1px solid var(--ink); padding: 2.2rem 0 1.5rem; margin-bottom: 1.5rem; }
      .hero-kicker { color: #496159; font-size: .76rem; letter-spacing: .12em; text-transform: uppercase; }
      .hero-title { font-family: 'Fraunces', Georgia, serif; font-size: clamp(3rem, 8vw, 6.6rem); line-height: .84; letter-spacing: -.065em; margin: .35rem 0 .8rem; }
      .hero-copy { max-width: 52rem; font-size: .92rem; line-height: 1.6; }
      .stButton button { background: var(--ink); color: var(--paper); border: 0; border-radius: 0; font-family: 'DM Mono', monospace; font-weight: 500; width: 100%; min-height: 3rem; }
      .stButton button:hover { background: var(--clay); color: white; border: 0; }
      [data-testid="stMetric"] { border-top: 2px solid var(--ink); background: rgba(255,255,255,.32); padding: .7rem .2rem; }
      [data-testid="stMetricLabel"] { font-family: 'DM Mono', monospace; font-size: .68rem; text-transform: uppercase; letter-spacing: .08em; }
      .decision { border: 2px solid var(--ink); padding: 1.2rem; margin: .6rem 0 1rem; }
      .decision.no-bid { background: #f7c6b5; }
      .decision.bid { background: var(--lime); }
      .decision-label { font-family: 'DM Mono', monospace; font-size: .74rem; letter-spacing: .12em; }
      .decision-word { font-family: 'Fraunces', Georgia, serif; font-size: 3.6rem; line-height: .9; letter-spacing: -.05em; }
      .evidence-box { border-left: 3px solid var(--ink); padding: .25rem 0 .25rem 1rem; margin: .65rem 0; }
      .task-row { border-bottom: 1px solid var(--line); padding: .7rem 0; display: flex; justify-content: space-between; gap: 1rem; font-family: 'DM Mono', monospace; font-size: .84rem; }
      .source-note { color: #496159; font-size: .75rem; border-top: 1px solid var(--line); padding-top: .8rem; }
      div[data-baseweb="select"] > div { border-radius: 0; border-color: var(--ink); background: #fffdf7; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="hero">
      <div class="hero-kicker">Snowflake CoCo CLI Hackathon · Decision-to-action prototype</div>
      <div class="hero-title">BidPilot</div>
      <div class="hero-copy">A bid decision is only useful when it protects capacity. Compare RFP requirements with delivery reality, reject work that cannot succeed, and turn the viable opportunity into owned proposal work.</div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("## Opportunity queue")
labels = {rfp["id"]: f"{rfp['id']} · {rfp['title']}" for rfp in RFPS}
selected_id = st.sidebar.radio("Select an RFP", options=list(labels), format_func=labels.get)
selected = next(rfp for rfp in RFPS if rfp["id"] == selected_id)
decision = evaluate_bid(selected, COMPANY)

st.sidebar.markdown("---")
st.sidebar.caption("Local demo mode · synthetic contest fixture only")
st.sidebar.caption("No customer data, Snowflake connection, or persistent task store is active in this view.")

left, right = st.columns([1.1, 1], gap="large")
with left:
    st.markdown("### RFP brief")
    st.markdown(f"## {selected['title']}")
    st.caption(selected["summary"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Contract value", f"${selected['contract_value']:,.0f}")
    c2.metric("Delivery effort", f"{selected['required_hours']:,} h")
    c3.metric("Proposal due", f"{selected['deadline_days']} days")
    st.markdown("#### Mandatory capability")
    st.code(" · ".join(selected["required_capabilities"]), language=None)
    st.markdown("#### Decision policy")
    st.markdown(
        "Qualification, delivery capacity, and minimum margin are non-negotiable. "
        "Risks remain visible but do not replace a failed hard gate."
    )

with right:
    state_class = "bid" if decision.can_proceed else "no-bid"
    st.markdown(
        f"""
        <section class="decision {state_class}">
          <div class="decision-label">Recommendation</div>
          <div class="decision-word">{decision.recommendation}</div>
          <div class="decision-label">Policy result for {selected['id']}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    m1, m2 = st.columns(2)
    m1.metric("Expected margin", f"${decision.expected_margin:,.0f}")
    m2.metric("Capacity gap", f"{decision.capacity_gap_hours:,} h")

    if decision.hard_gate_failures:
        st.markdown("#### Hard gates that changed the answer")
        for failure in decision.hard_gate_failures:
            st.markdown(f'<div class="evidence-box">{failure}</div>', unsafe_allow_html=True)
    if decision.risks:
        st.markdown("#### Visible delivery risks")
        st.write(" · ".join(decision.risks))
    st.markdown("#### Why this is the recommendation")
    for reason in decision.rationale:
        st.write(f"• {reason}")

st.markdown("---")
if decision.can_proceed:
    st.markdown("### Turn the decision into work")
    if st.button("Create internal proposal work plan", type="primary"):
        st.session_state["tasks"] = create_proposal_tasks(selected, decision)

    if st.session_state.get("tasks"):
        for task in st.session_state["tasks"]:
            st.markdown(
                f'<div class="task-row"><span>{task["task"]}</span><span>{task["owner"]} · D+{task["due_in_days"]}</span></div>',
                unsafe_allow_html=True,
            )
        st.success("Proposal work plan created for this local demo session.")
else:
    next_viable = next(rfp for rfp in RFPS if evaluate_bid(rfp, COMPANY).can_proceed)
    st.markdown("### Capacity preserved. What opens next.")
    st.markdown(
        f"**{next_viable['id']} · {next_viable['title']}** is the next viable opportunity. "
        "Select it from the queue to create its proposal work plan."
    )

st.markdown(
    "<p class='source-note'>Prepared proof path: Snowflake will store the RFP and operating records; "
    "Snowpark will evaluate policy gates; CoCo CLI will produce the reproducible build and execution trace. "
    "This local demo exposes the same decision policy and in-session work-plan behavior.</p>",
    unsafe_allow_html=True,
)
