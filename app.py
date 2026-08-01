"""BidPilot's judge-facing decision-to-action workbench."""

from __future__ import annotations

import html

import streamlit as st

from bidpilot.engine import create_proposal_tasks, evaluate_bid
from bidpilot.fixtures import COMPANY, RFPS
from bidpilot.proposal_writer import write_proposal_draft
from bidpilot.public_tender import PUBLIC_TENDER, assess_public_tender

st.set_page_config(page_title="BidPilot · Bid Decision Workbench", page_icon="◈", layout="wide")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
      :root {
        --ink: #112620;
        --ink-soft: #4a635b;
        --paper: #f4f0e6;
        --paper-lift: #fbf8f0;
        --lime: #ccff00;
        --clay: #b8431f;
        --clay-wash: #f6cbba;
        --line: #c6bfb0;
        --serif: 'Fraunces', 'Iowan Old Style', Georgia, 'Times New Roman', serif;
        --mono: 'DM Mono', 'SFMono-Regular', 'Roboto Mono', Menlo, Consolas, monospace;
      }
      .stApp { background: var(--paper); color: var(--ink); }
      .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1200px; }
      h1, h2, h3, h4 { font-family: var(--serif) !important; color: var(--ink); letter-spacing: -.02em; }
      p, span, li, label, div, .stMarkdown { font-family: var(--mono); }
      hr { border-color: var(--line); }

      /* status rail */
      .bp-rail { display: flex; flex-wrap: wrap; align-items: baseline; gap: .35rem 2rem;
        border-top: 3px solid var(--ink); border-bottom: 1px solid var(--ink); padding: .55rem 0; margin-bottom: 1.35rem; }
      .bp-rail-item { display: flex; align-items: baseline; gap: .5rem; }
      .bp-rail-key { font-size: .63rem; letter-spacing: .14em; text-transform: uppercase; color: var(--ink-soft); }
      .bp-rail-val { font-size: .8rem; font-weight: 500; }
      .bp-rail-mode { margin-left: auto; font-size: .63rem; letter-spacing: .13em; text-transform: uppercase;
        color: var(--ink-soft); border: 1px solid var(--line); padding: .18rem .5rem; }

      /* masthead */
      .bp-mast { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 1rem 2.5rem; margin-bottom: .5rem; }
      .bp-mast-left { max-width: 36rem; flex: 1 1 24rem; }
      .bp-kicker { font-size: .65rem; letter-spacing: .15em; text-transform: uppercase; color: var(--ink-soft); }
      .bp-title { font-family: var(--serif); font-weight: 700; font-size: clamp(2.6rem, 5.4vw, 4.3rem);
        line-height: .86; letter-spacing: -.055em; margin: .3rem 0 .5rem; }
      .bp-lede { font-size: .82rem; line-height: 1.62; }
      .bp-mast-right { flex: 0 1 17rem; font-size: .72rem; line-height: 1.75; color: var(--ink-soft);
        border-left: 1px solid var(--line); padding-left: 1.1rem; }
      .bp-mast-right b { color: var(--ink); font-weight: 500; }

      /* section headers */
      .bp-sec { display: flex; flex-wrap: wrap; align-items: baseline; gap: .3rem .8rem;
        border-bottom: 1px solid var(--ink); padding-bottom: .3rem; margin: 1.5rem 0 .85rem; }
      .bp-sec-n { font-size: .65rem; letter-spacing: .12em; color: var(--ink-soft); }
      .bp-sec-t { font-family: var(--serif); font-weight: 600; font-size: 1.1rem; letter-spacing: -.02em; }
      .bp-sec-r { margin-left: auto; font-size: .65rem; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-soft); }

      /* decision block */
      .bp-decision { border: 2px solid var(--ink); padding: 1.05rem 1.1rem 1rem; }
      .bp-decision.is-bid { background: var(--lime); }
      .bp-decision.is-nobid { background: var(--clay-wash); }
      .bp-dec-top { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem;
        font-size: .63rem; letter-spacing: .14em; text-transform: uppercase; }
      .bp-dec-word { font-family: var(--serif); font-weight: 700; font-size: clamp(2.9rem, 6vw, 4rem);
        line-height: .88; letter-spacing: -.05em; margin: .25rem 0 .4rem; }
      .bp-dec-line { font-size: .81rem; line-height: 1.55; border-top: 1px solid rgba(17,38,32,.35); padding-top: .5rem; }
      .bp-dec-tally { display: flex; flex-wrap: wrap; gap: .25rem .9rem; margin-top: .45rem; font-size: .69rem; letter-spacing: .04em; }

      /* rationale + notes */
      .bp-reason { border-left: 3px solid var(--ink); padding: .1rem 0 .1rem .85rem; margin: .5rem 0; font-size: .81rem; line-height: 1.55; }
      .bp-note { font-size: .73rem; color: var(--ink-soft); line-height: 1.6; }

      /* trace */
      .bp-trace { font-size: .705rem; line-height: 1.72; white-space: pre-wrap; word-break: break-word;
        background: var(--paper-lift); border: 1px solid var(--line); border-left: 3px solid var(--ink);
        padding: .75rem .85rem; margin: 0; color: var(--ink); font-family: var(--mono); }

      /* scorecard */
      .bp-score { display: grid; grid-template-columns: repeat(auto-fit, minmax(8.4rem, 1fr));
        border-top: 2px solid var(--ink); border-left: 1px solid var(--line); }
      .bp-score-cell { border-right: 1px solid var(--line); border-bottom: 1px solid var(--line);
        padding: .6rem .7rem .65rem; background: rgba(255,255,255,.34); }
      .bp-score-k { font-size: .6rem; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-soft); }
      .bp-score-v { font-family: var(--serif); font-weight: 600; font-size: 1.42rem; line-height: 1.2; letter-spacing: -.03em; margin-top: .15rem; }
      .bp-score-v.is-neg { color: var(--clay); }
      .bp-score-s { font-size: .65rem; color: var(--ink-soft); }

      /* gate evidence */
      .bp-gate { border-top: 2px solid var(--ink); }
      .bp-gate-row { display: grid; grid-template-columns: minmax(6rem, .75fr) minmax(8rem, 1.7fr) auto;
        gap: .2rem .8rem; align-items: baseline; border-bottom: 1px solid var(--line); padding: .58rem 0 .6rem; }
      .bp-gate-name { font-size: .74rem; font-weight: 500; }
      .bp-gate-test { font-size: .71rem; line-height: 1.5; color: var(--ink-soft); }
      .bp-gate-test b { color: var(--ink); font-weight: 500; }
      .bp-gate-flag { font-size: .65rem; font-weight: 500; letter-spacing: .12em; padding: .16rem .45rem;
        justify-self: end; white-space: nowrap; }
      .bp-gate-flag.pass { background: var(--lime); color: var(--ink); border: 1px solid var(--ink); }
      .bp-gate-flag.fail { background: var(--clay-wash); color: var(--ink); border: 1px solid var(--clay); }
      .bp-gate-flag.info { background: transparent; color: var(--ink-soft); border: 1px solid var(--line); }

      /* work plan */
      .bp-work { border-top: 2px solid var(--ink); }
      .bp-work-row { display: grid; grid-template-columns: 1.6rem minmax(9rem, 1.7fr) minmax(6rem, .9fr) auto;
        gap: .25rem 1rem; align-items: baseline; border-bottom: 1px solid var(--line); padding: .6rem 0; font-size: .78rem; }
      .bp-work-n { color: var(--ink-soft); font-size: .67rem; }
      .bp-work-task b { font-weight: 500; }
      .bp-work-sub { display: block; font-size: .68rem; color: var(--ink-soft); line-height: 1.5; margin-top: .12rem; }
      .bp-work-owner { color: var(--ink-soft); font-size: .72rem; }
      .bp-work-due { font-weight: 500; letter-spacing: .04em; justify-self: end; }
      .bp-work-empty { border: 1px dashed var(--line); padding: .85rem; font-size: .76rem; color: var(--ink-soft); line-height: 1.6; }
      .bp-handoff { border: 2px solid var(--ink); background: var(--paper-lift); padding: .9rem 1rem; }
      .bp-handoff-k { font-size: .62rem; letter-spacing: .14em; text-transform: uppercase; color: var(--ink-soft); }
      .bp-handoff-v { font-family: var(--serif); font-weight: 600; font-size: 1.22rem; letter-spacing: -.02em; margin: .2rem 0 .35rem; }
      .bp-handoff-p { font-size: .77rem; line-height: 1.6; }

      .bp-foot { border-top: 1px solid var(--ink); margin-top: 2rem; padding-top: .8rem;
        font-size: .71rem; line-height: 1.65; color: var(--ink-soft); }
      .bp-foot b { color: var(--ink); font-weight: 500; }

      /* streamlit chrome */
      .stButton button { background: var(--ink); color: var(--paper); border: 0; border-radius: 0;
        font-family: var(--mono); font-weight: 500; letter-spacing: .06em; text-transform: uppercase;
        font-size: .73rem; width: 100%; min-height: 2.9rem; }
      .stButton button:hover, .stButton button:focus { background: var(--clay); color: #fff; border: 0; }
      .stButton button:focus-visible { outline: 3px solid var(--ink); outline-offset: 2px; }
      section[data-testid="stSidebar"] { background: var(--paper-lift); border-right: 1px solid var(--ink); }
      section[data-testid="stSidebar"] .stRadio label { font-family: var(--mono); font-size: .77rem; }
      div[data-baseweb="select"] > div { border-radius: 0; border-color: var(--ink); background: var(--paper-lift); }
      @media (max-width: 900px) {
        .bp-mast-right { border-left: 0; border-top: 1px solid var(--line); padding: .8rem 0 0; }
        .bp-gate-row, .bp-work-row { grid-template-columns: 1fr auto; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Derived display signals. These mirror the engine's arithmetic exactly and are
# used for presentation only; the recommendation always comes from evaluate_bid.
# ---------------------------------------------------------------------------


def derive_signals(rfp: dict, company: dict) -> dict:
    required = list(rfp["required_capabilities"])
    missing = sorted(set(required) - set(company["capabilities"]))
    capacity_gap = max(0, rfp["required_hours"] - company["available_hours"])
    coverage = min(1.0, company["available_hours"] / rfp["required_hours"])
    estimated_cost = rfp.get(
        "estimated_delivery_cost",
        rfp["required_hours"] * company["loaded_hourly_cost"],
    )
    expected_margin = rfp["contract_value"] - estimated_cost
    margin_rate = expected_margin / rfp["contract_value"]
    floor = company["minimum_margin_rate"]

    gates = [
        {
            "key": "capability",
            "name": "Qualification",
            "ok": not missing,
            "test": (
                f"<b>{len(required) - len(missing)}/{len(required)}</b> mandatory capabilities held"
                + (f" · missing <b>{', '.join(missing)}</b>" if missing else " · no exclusion")
            ),
            "trace": (
                f"required{{{len(required)}}} ∩ company{{{len(company['capabilities'])}}} → "
                + (f"missing[{', '.join(missing)}]" if missing else "missing[none]")
            ),
        },
        {
            "key": "capacity",
            "name": "Delivery capacity",
            "ok": capacity_gap == 0,
            "test": (
                f"<b>{company['available_hours']:,} h</b> available vs "
                f"<b>{rfp['required_hours']:,} h</b> required"
                + (f" · <b>{capacity_gap:,} h</b> short" if capacity_gap else " · covered")
            ),
            "trace": (
                f"{rfp['required_hours']:,}h required − {company['available_hours']:,}h available → "
                + (f"{capacity_gap:,}h short" if capacity_gap else "0h short")
            ),
        },
        {
            "key": "margin",
            "name": "Minimum margin",
            "ok": margin_rate >= floor,
            "test": f"<b>{margin_rate:.1%}</b> expected against a <b>{floor:.0%}</b> policy floor",
            "trace": (
                f"({rfp['contract_value']:,.0f} − {estimated_cost:,.0f}) / {rfp['contract_value']:,.0f}"
                f" = {margin_rate:.1%} {'≥' if margin_rate >= floor else '<'} {floor:.1%} floor"
            ),
        },
    ]
    for gate in gates:
        gate["flag"] = "PASS" if gate["ok"] else "FAIL"

    return {
        "gates": gates,
        "gates_passed": sum(1 for gate in gates if gate["ok"]),
        "gate_total": len(gates),
        "capacity_gap": capacity_gap,
        "coverage": coverage,
        "estimated_cost": estimated_cost,
        "expected_margin": expected_margin,
        "margin_rate": margin_rate,
        "margin_floor": floor,
    }


def build_trace(rfp: dict, gates: list[dict], recommendation: str) -> str:
    lines = [f"input.rfp     {rfp['id']} · contract {rfp['contract_value']:,.0f} USD"]
    lines += [f"gate.{gate['key']:<9} {gate['trace']} → {gate['flag']}" for gate in gates]
    failed = [gate["key"] for gate in gates if not gate["ok"]]
    verdict = f"any_gate_failed[{', '.join(failed)}]" if failed else "all_gates_passed"
    lines.append(f"policy        {verdict} → {recommendation}")
    return "\n".join(lines)


def work_row(index: str, title: str, subtitle: str, meta: str, due: str) -> str:
    sub = f'<span class="bp-work-sub">{subtitle}</span>' if subtitle else ""
    return (
        f'<div class="bp-work-row"><span class="bp-work-n">{index}</span>'
        f'<span class="bp-work-task"><b>{title}</b>{sub}</span>'
        f'<span class="bp-work-owner">{meta}</span>'
        f'<span class="bp-work-due">{due}</span></div>'
    )


def section(number: str, title: str, right: str = "") -> str:
    return (
        f'<div class="bp-sec"><span class="bp-sec-n">{number}</span>'
        f'<span class="bp-sec-t">{title}</span>'
        f'<span class="bp-sec-r">{right}</span></div>'
    )


def render_public_tender_case() -> None:
    """Render the buyer-facing fit decision and the proposal-writing surface."""
    st.sidebar.markdown('<div class="bp-kicker">Company profile</div>', unsafe_allow_html=True)
    company_name = st.sidebar.text_input("Company name", placeholder="Your company")
    positioning = st.sidebar.text_area("Why should the buyer choose you?", placeholder="Delivery strengths, comparable work, team, or differentiators", height=120)
    st.sidebar.markdown('<div class="bp-kicker">Tender qualification</div>', unsafe_allow_html=True)
    choices = ("Not sure", "Yes", "No")
    evidence: dict[str, bool] = {}
    for requirement in PUBLIC_TENDER["requirements"]:
        choice = st.sidebar.selectbox(requirement["label"], choices, key=f"tender-{requirement['key']}")
        evidence[requirement["key"]] = {"Yes": True, "No": False}.get(choice)  # type: ignore[assignment]

    assessment = assess_public_tender(PUBLIC_TENDER, evidence)
    state_class = "is-nobid" if assessment.recommendation.startswith("NO-BID") else "is-bid" if assessment.recommendation.startswith("ELIGIBLE") else "is-nobid"
    source_url = html.escape(PUBLIC_TENDER["source_url"], quote=True)

    st.markdown(
        '<div class="bp-rail"><span class="bp-rail-item"><span class="bp-rail-key">Public-source case</span>'
        f'<span class="bp-rail-val">{PUBLIC_TENDER["case_id"]}</span></span>'
        f'<span class="bp-rail-item"><span class="bp-rail-key">Source fingerprint</span><span class="bp-rail-val">{PUBLIC_TENDER["source_sha256"][:12]}…</span></span>'
        '<span class="bp-rail-mode">Historical notice · proposal drafting locked</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'''<div class="bp-mast"><div class="bp-mast-left"><div class="bp-kicker">B2G qualification → proposal drafting</div>
        <div class="bp-title">Can we win<br>this tender?</div><div class="bp-lede">BidPilot reads a real public notice, checks whether your company can participate, and turns a viable pursuit into an editable proposal draft. Qualification happens in the background; the output is a clear pursue decision and a proposal your team can refine.</div></div>
        <div class="bp-mast-right"><b>{PUBLIC_TENDER["issuer"]}</b><br>{PUBLIC_TENDER["notice_number"]}<br><br>Bid close: {PUBLIC_TENDER["bid_close"]}<br>Current status: historical and closed.</div></div>''',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown(
            f'''<div class="bp-decision {state_class}"><div class="bp-dec-top"><span>Pursuit decision</span><span>{PUBLIC_TENDER["case_id"]}</span></div>
            <div class="bp-dec-word">{assessment.recommendation}</div><div class="bp-dec-line">Complete the company profile in the sidebar. BidPilot will immediately show whether to pursue, stop, or resolve a qualification gap.</div></div>''',
            unsafe_allow_html=True,
        )
        st.markdown(section("01", "Public notice facts", "source-bound extraction"), unsafe_allow_html=True)
        st.markdown(
            f'<div class="bp-reason">{PUBLIC_TENDER["scope"]}</div><div class="bp-reason">KRW {PUBLIC_TENDER["contract_value_krw"]:,} · {PUBLIC_TENDER["duration_days"]} delivery days</div><div class="bp-reason">{PUBLIC_TENDER["evaluation"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<p class="bp-note">Source: <a href="{source_url}" target="_blank">official G2B attachment</a> · 9 pages · SHA-256 {PUBLIC_TENDER["source_sha256"]}</p>', unsafe_allow_html=True)

    with right:
        st.markdown(section("02", "Can your company enter?", f"{assessment.passed} yes · {assessment.failed} no · {assessment.unknown} to confirm"), unsafe_allow_html=True)
        rows = "".join(
            f'<div class="bp-gate-row"><span class="bp-gate-name">{html.escape(check["label"])}</span><span class="bp-gate-test">{check["source"]}</span><span class="bp-gate-flag {"pass" if check["status"] == "PASS" else "fail" if check["status"] == "FAIL" else "info"}>{"YES" if check["status"] == "PASS" else "NO" if check["status"] == "FAIL" else "CHECK"}</span></div>'
            for check in assessment.checks
        )
        st.markdown(f'<div class="bp-gate">{rows}</div>', unsafe_allow_html=True)

    st.markdown(section("03", "Write the proposal", "editable English draft"), unsafe_allow_html=True)
    st.markdown(
        '<div class="bp-handoff"><div class="bp-handoff-k">Proposal brief</div><div class="bp-handoff-v">From tender to first draft</div><div class="bp-handoff-p">Generate an English executive summary, technical approach, delivery plan, evaluation strategy, and submission checklist. Your team can then edit and export it in the buyer’s required format.</div></div>',
        unsafe_allow_html=True,
    )
    if st.button("Generate proposal draft", type="primary"):
        st.session_state["public_tender_draft"] = write_proposal_draft(PUBLIC_TENDER, company_name, positioning)
    draft = st.session_state.get("public_tender_draft")
    if draft:
        st.markdown("#### Proposal draft")
        st.text_area("Editable proposal draft", value=draft, height=520, key="proposal-draft-editor")
        st.download_button("Download proposal draft (Markdown)", data=draft, file_name="g2b-proposal-draft.md", mime="text/markdown")
    st.markdown('<p class="bp-foot"><b>Public-notice case.</b> This is a real historical G2B notice used to demonstrate the workflow. The product is designed for an open notice selected by the user, then outputs a pursuit decision and a proposal draft rather than an HWPX-only document process.</p>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

workflow = st.sidebar.radio(
    "Workflow",
    options=("Synthetic decision simulation", "Actual G2B notice → Proposal Start Packet"),
    label_visibility="collapsed",
)
if workflow == "Actual G2B notice → Proposal Start Packet":
    render_public_tender_case()
    st.stop()

st.sidebar.markdown('<div class="bp-kicker">Opportunity queue</div>', unsafe_allow_html=True)
labels = {rfp["id"]: f"{rfp['id']} · {rfp['title']}" for rfp in RFPS}
selected_id = st.sidebar.radio("Select an RFP", options=list(labels), format_func=labels.get)
selected = next(rfp for rfp in RFPS if rfp["id"] == selected_id)
decision = evaluate_bid(selected, COMPANY)
signals = derive_signals(selected, COMPANY)

st.sidebar.markdown("---")
queue_rows = "".join(
    f'<div class="bp-gate-row" style="grid-template-columns:1fr auto;">'
    f'<span class="bp-gate-name">{rfp["id"]}</span>'
    f'<span class="bp-gate-flag {"pass" if verdict.can_proceed else "fail"}">{verdict.recommendation}</span>'
    f"</div>"
    for rfp, verdict in ((rfp, evaluate_bid(rfp, COMPANY)) for rfp in RFPS)
)
st.sidebar.markdown(f'<div class="bp-gate">{queue_rows}</div>', unsafe_allow_html=True)
st.sidebar.markdown(
    '<p class="bp-note" style="margin-top:1rem;">Local demo mode · synthetic contest fixture. '
    "No customer data, no live warehouse session, and no persistent task store is active in this view.</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Status rail + masthead
# ---------------------------------------------------------------------------

rail_items = [
    ("Policy floor", f"{COMPANY['minimum_margin_rate']:.0%} margin"),
    ("Bench capacity", f"{COMPANY['available_hours']:,} h"),
    ("Loaded rate", f"${COMPANY['loaded_hourly_cost']}/h"),
    ("Lead time", f"≥ {COMPANY['minimum_lead_days']} days"),
    ("Queue", f"{len(RFPS)} open RFPs"),
]
st.markdown(
    '<div class="bp-rail">'
    + "".join(
        f'<span class="bp-rail-item"><span class="bp-rail-key">{key}</span>'
        f'<span class="bp-rail-val">{value}</span></span>'
        for key, value in rail_items
    )
    + '<span class="bp-rail-mode">Local demo · synthetic fixture · no warehouse session</span>'
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="bp-mast">
      <div class="bp-mast-left">
        <div class="bp-kicker">Snowflake CoCo CLI Hackathon · decision-to-action workbench</div>
        <div class="bp-title">BidPilot</div>
        <div class="bp-lede">A bid decision is only useful when it protects capacity. BidPilot tests every
        opportunity against three non-negotiable gates, declines work that cannot succeed, and turns the
        viable one into owned proposal work with named owners and dates.</div>
      </div>
      <div class="bp-mast-right">
        <b>Three hard gates</b><br>Qualification · Capacity · Margin<br><br>
        Delivery risks stay visible.<br>They never overturn a failed gate.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Decision narrative (left) · scorecard and gate evidence (right)
# ---------------------------------------------------------------------------

left, right = st.columns([1.05, 1], gap="large")

with left:
    state_class = "is-bid" if decision.can_proceed else "is-nobid"
    tally = "".join(f'<span>{gate["name"].lower()} · {gate["flag"]}</span>' for gate in signals["gates"])
    headline = (
        "Gates cleared. Commit proposal capacity."
        if decision.can_proceed
        else "Gate failure. Decline and hold capacity."
    )
    st.markdown(
        f"""
        <div class="bp-decision {state_class}">
          <div class="bp-dec-top"><span>Recommendation</span><span>{selected['id']}</span></div>
          <div class="bp-dec-word">{decision.recommendation}</div>
          <div class="bp-dec-line">{headline}
            <span class="bp-dec-tally">{tally}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(section("01", "Why this is the recommendation"), unsafe_allow_html=True)
    st.markdown(
        "".join(f'<div class="bp-reason">{reason}</div>' for reason in decision.rationale),
        unsafe_allow_html=True,
    )

    st.markdown(
        section("02", "Decision trace", f"{signals['gates_passed']}/{signals['gate_total']} gates passed"),
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<pre class="bp-trace">{build_trace(selected, signals["gates"], decision.recommendation)}</pre>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="bp-note" style="margin-top:.6rem;">Every line is fixed arithmetic over the fixture record. '
        "No model output, no score, no inferred customer data.</p>",
        unsafe_allow_html=True,
    )

with right:
    st.markdown(section("03", "Opportunity scorecard", selected["id"]), unsafe_allow_html=True)
    score_cells = [
        (
            "Contract value",
            f"${selected['contract_value']:,.0f}",
            f"{selected['required_hours']:,} h of delivery",
            "",
        ),
        (
            "Expected margin",
            f"${signals['expected_margin']:,.0f}",
            f"{signals['margin_rate']:.1%} vs {signals['margin_floor']:.0%} floor",
            " is-neg" if signals["margin_rate"] < signals["margin_floor"] else "",
        ),
        (
            "Capacity coverage",
            f"{signals['coverage']:.0%}",
            f"{signals['capacity_gap']:,} h short" if signals["capacity_gap"] else "fully covered",
            " is-neg" if signals["capacity_gap"] else "",
        ),
        (
            "Gates passed",
            f"{signals['gates_passed']}/{signals['gate_total']}",
            "hard, non-negotiable",
            " is-neg" if signals["gates_passed"] < signals["gate_total"] else "",
        ),
        (
            "Proposal window",
            f"{selected['deadline_days']} d",
            f"policy needs {COMPANY['minimum_lead_days']} d",
            " is-neg" if selected["deadline_days"] < COMPANY["minimum_lead_days"] else "",
        ),
        ("Open risks", f"{len(decision.risks)}", "visible, not blocking", ""),
    ]
    st.markdown(
        '<div class="bp-score">'
        + "".join(
            f'<div class="bp-score-cell"><div class="bp-score-k">{key}</div>'
            f'<div class="bp-score-v{cls}">{value}</div><div class="bp-score-s">{sub}</div></div>'
            for key, value, sub, cls in score_cells
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="bp-note" style="margin-top:.55rem;">{selected["summary"]}</p>',
        unsafe_allow_html=True,
    )

    st.markdown(section("04", "Gate-by-gate evidence"), unsafe_allow_html=True)
    gate_rows = "".join(
        f'<div class="bp-gate-row"><span class="bp-gate-name">{gate["name"]}</span>'
        f'<span class="bp-gate-test">{gate["test"]}</span>'
        f'<span class="bp-gate-flag {"pass" if gate["ok"] else "fail"}">{gate["flag"]}</span></div>'
        for gate in signals["gates"]
    )
    if decision.risks:
        risk_rows = "".join(
            f'<div class="bp-gate-row"><span class="bp-gate-name">Risk</span>'
            f'<span class="bp-gate-test">{risk}</span>'
            f'<span class="bp-gate-flag info">Visible</span></div>'
            for risk in decision.risks
        )
    else:
        risk_rows = (
            '<div class="bp-gate-row"><span class="bp-gate-name">Risk</span>'
            '<span class="bp-gate-test">0 open risks · nothing flagged by policy</span>'
            '<span class="bp-gate-flag info">None</span></div>'
        )
    st.markdown(f'<div class="bp-gate">{gate_rows}{risk_rows}</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="bp-note" style="margin-top:.55rem;">Qualification, capacity, and margin are hard gates. '
        "Risks are reported beside the decision and never overturn a failed gate.</p>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Decision → work transition
# ---------------------------------------------------------------------------

if not isinstance(st.session_state.get("tasks"), dict):
    st.session_state["tasks"] = {}
tasks_by_rfp = st.session_state["tasks"]

if decision.can_proceed:
    st.markdown(
        section("05", "Decision becomes owned work", "BID → proposal work plan"),
        unsafe_allow_html=True,
    )
    act, plan = st.columns([1, 1.85], gap="large")
    with act:
        st.markdown(
            f"""
            <div class="bp-handoff">
              <div class="bp-handoff-k">Handoff</div>
              <div class="bp-handoff-v">{selected['id']} → bid team</div>
              <div class="bp-handoff-p">Committing {selected['required_hours']:,} h of the
              {COMPANY['available_hours']:,} h bench at a {signals['margin_rate']:.1%} expected margin,
              with {selected['deadline_days']} days to the proposal date.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Create internal proposal work plan", type="primary"):
            tasks_by_rfp[selected_id] = create_proposal_tasks(selected, decision)
    with plan:
        tasks = tasks_by_rfp.get(selected_id)
        if tasks:
            rows = "".join(
                work_row(
                    f"{index:02d}",
                    task["task"],
                    task.get("outcome", ""),
                    task["owner"]
                    + (f" · {task['workstream']}" if task.get("workstream") else ""),
                    f"D+{task['due_in_days']}",
                )
                for index, task in enumerate(tasks, start=1)
            )
            st.markdown(f'<div class="bp-work">{rows}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<p class="bp-note" style="margin-top:.6rem;"><b>{len(tasks)} tasks</b> created for '
                f"{selected_id} and held in this browser session. Nothing is submitted externally, and "
                "Snowflake-backed task state is not connected in this local demo.</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="bp-work-empty">No work plan yet for this opportunity. Creating the plan '
                "assigns bounded tasks with named owners and due dates derived from the proposal window.</div>",
                unsafe_allow_html=True,
            )
else:
    st.markdown(
        section("05", "Capacity preserved", "NO-BID → next viable opportunity"),
        unsafe_allow_html=True,
    )
    held, nxt = st.columns([1, 1.85], gap="large")
    with held:
        st.markdown(
            f"""
            <div class="bp-handoff">
              <div class="bp-handoff-k">Protected this cycle</div>
              <div class="bp-handoff-v">{COMPANY['available_hours']:,} h held</div>
              <div class="bp-handoff-p">{selected['id']} would have consumed
              {selected['required_hours']:,} h at a {signals['margin_rate']:.1%} margin.
              No proposal tasks are created behind a failed gate.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nxt:
        next_viable = next(
            (
                rfp
                for rfp in RFPS
                if rfp["id"] != selected_id and evaluate_bid(rfp, COMPANY).can_proceed
            ),
            None,
        )
        if next_viable is None:
            st.markdown(
                '<div class="bp-work-empty">No other opportunity in the queue clears all three gates. '
                "The bench stays uncommitted until one does.</div>",
                unsafe_allow_html=True,
            )
        else:
            next_signals = derive_signals(next_viable, COMPANY)
            row = work_row(
                "→",
                f"{next_viable['id']} · {next_viable['title']}",
                "Select it in the queue to create its proposal work plan.",
                f"{next_signals['margin_rate']:.1%} margin · {next_viable['required_hours']:,} h",
                f"{next_signals['gates_passed']}/{next_signals['gate_total']} gates",
            )
            st.markdown(f'<div class="bp-work">{row}</div>', unsafe_allow_html=True)

st.markdown(
    '<p class="bp-foot"><b>Local demo mode.</b> Every number on this screen is computed in-process from a '
    "synthetic contest fixture. No customer data, no live Snowflake session, and no persistent task store is "
    "connected here. <b>Prepared proof path:</b> after an authenticated Snowflake account is connected, the "
    "repository can store the RFP and operating records, run the same policy in Snowpark, and capture a CoCo "
    "CLI execution trace. This view exposes that decision policy and its in-session work-plan behavior.</p>",
    unsafe_allow_html=True,
)
