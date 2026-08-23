"""Three-workspace presentation shell for the BidPilot refinement UI.

The module accepts already-reviewed display values and returns escaped HTML.
It intentionally has no domain, intake, persistence, or runner imports, which
keeps the existing verified data path in charge of every displayed fact.
"""

from __future__ import annotations

from dataclasses import dataclass

from bidpilot.ui_components import (
    PRODUCT_STATES,
    badge,
    boundary_panel,
    decision_path,
    esc,
    fact_receipt,
)

SYNTHETIC_BOUNDARY = (
    "LOCAL SYNTHETIC SIMULATION — no Snowflake, no CoCo, no persisted action."
)
UI_STATES = PRODUCT_STATES


@dataclass(frozen=True, slots=True)
class Workspace:
    """A navigation destination and its public trust-boundary note."""

    key: str
    label: str
    note: str


WORKSPACES = (
    Workspace(
        "tender-intake",
        "Tender Intake",
        "Public source · operator review before analysis",
    ),
    Workspace(
        "bid-room",
        "Authenticated Snowflake Bid Room",
        "Least-privilege reader · same-run evidence",
    ),
    Workspace(
        "synthetic-simulation",
        "Synthetic Decision Simulation",
        "Local policy demonstration · nothing persisted",
    ),
)
WORKSPACE_BY_KEY = {workspace.key: workspace for workspace in WORKSPACES}


def workspace_navigation(active_key: str) -> str:
    """Return stable desktop navigation plus a compact mobile selector."""
    if active_key not in WORKSPACE_BY_KEY:
        raise ValueError(f"Unknown workspace: {active_key}")

    desktop_items = []
    mobile_items = []
    for index, workspace in enumerate(WORKSPACES, start=1):
        current = ' aria-current="page"' if workspace.key == active_key else ""
        selected = " selected" if workspace.key == active_key else ""
        desktop_items.append(
            f'<a class="bpw-workspace-link" href="?workspace={workspace.key}" '
            f'data-workspace="{workspace.key}"{current}>'
            f'<span class="bpw-workspace-link__number">{index:02d}</span>'
            '<span class="bpw-workspace-link__copy">'
            f"<strong>{esc(workspace.label)}</strong>"
            f"<small>{esc(workspace.note)}</small>"
            "</span></a>"
        )
        mobile_items.append(
            f'<option value="?workspace={workspace.key}"{selected}>'
            f"{esc(workspace.label)}</option>"
        )

    return (
        '<nav class="bpw-desktop-workspaces" aria-label="BidPilot workspaces">'
        '<div class="bpw-brand"><span class="bpw-brand__mark" aria-hidden="true"></span>'
        "<div><strong>BidPilot</strong><small>Evidence-first pursuit</small></div></div>"
        '<p class="bpw-nav-overline">Workspaces</p>' + "".join(desktop_items) + "</nav>"
        '<div class="bpw-mobile-workspace">'
        '<label for="bpw-workspace-select">Workspace</label>'
        '<select id="bpw-workspace-select" aria-label="BidPilot workspaces" '
        'onchange="if(this.value) window.location.href=this.value">'
        + "".join(mobile_items)
        + "</select></div>"
    )


def workspace_route_navigation(active_key: str) -> str:
    """Return reachable in-document routing for an existing Streamlit shell.

    The desktop route bar uses ordinary links.  Mobile uses a native details
    drawer containing the same links, so routing never depends on a hidden
    Streamlit sidebar or on inline JavaScript surviving HTML sanitisation.
    """
    if active_key not in WORKSPACE_BY_KEY:
        raise ValueError(f"Unknown workspace: {active_key}")

    active = WORKSPACE_BY_KEY[active_key]
    links = []
    for index, workspace in enumerate(WORKSPACES, start=1):
        current = ' aria-current="page"' if workspace.key == active_key else ""
        links.append(
            f'<a href="?workspace={workspace.key}"{current}>'
            f'<span aria-hidden="true">{index:02d}</span>'
            f'<strong>{esc(workspace.label)}</strong>'
            f'<small>{esc(workspace.note)}</small>'
            "</a>"
        )

    return (
        '<div class="bpw-route-frame" aria-label="BidPilot workspace routes">'
        '<nav class="bpw-route-desktop" aria-label="BidPilot workspace routes">'
        + "".join(links)
        + "</nav>"
        '<details class="bpw-route-mobile">'
        '<summary><span>Workspace</span>'
        f'<strong>{esc(active.label)}</strong></summary>'
        '<nav aria-label="BidPilot workspace routes">'
        + "".join(links)
        + "</nav></details></div>"
    )


def tender_intake_first_viewport(
    *,
    source_title: object,
    official_status: object,
    digest: object,
    extraction_state: object,
    evaluation_total: object,
    next_action: object,
) -> str:
    """Render the intake receipt from official source to human review."""
    facts = fact_receipt(
        (
            ("Official source", source_title, official_status),
            ("Content digest", digest, "Content-level provenance"),
            (
                "Extraction state",
                extraction_state,
                "Facts require operator confirmation",
            ),
            ("Evaluation map", evaluation_total, "Official weights must total 100"),
            (
                "Supplier boundary",
                "Synthetic demo supplier profile",
                "No actual bidder eligibility or participation is claimed",
            ),
            ("Next review action", next_action, "Operator-owned before request export"),
        )
    )
    return (
        '<section class="bpw-first bpw-first--intake" data-workspace-view="tender-intake">'
        '<header class="bpw-first__header"><div>'
        '<p class="bpw-eyebrow">Workspace 01 · source review</p>'
        "<h1>Tender Intake</h1>"
        "<p>Verify the official notice, extracted score map, and evidence boundary before "
        "committing pursuit resources.</p></div>"
        f"{badge(official_status, 'positive')}</header>"
        f"{facts}"
        '<footer class="bpw-first__footer"><span>Public viewers inspect only</span>'
        "<span>Private runner approval remains operator-gated</span></footer>"
        "</section>"
    )


def bid_room_first_viewport(
    *,
    verdict: object,
    principal_reason: object,
    criterion: object,
    official_weight: object,
    evidence_state: object,
    selected_position: object,
    owner: object,
    next_action: object,
    run_id: object,
) -> str:
    """Render the executive decision brief before deeper Bid Room sections."""
    path = decision_path(
        (
            ("Decision", verdict, principal_reason),
            ("Official weight", official_weight, criterion),
            (
                "Evidence state",
                evidence_state,
                "Every score-bearing claim keeps its gaps",
            ),
            ("Owned action", next_action, owner),
        )
    )
    return (
        '<section class="bpw-first bpw-first--bid-room" data-workspace-view="bid-room">'
        '<header class="bpw-first__header"><div>'
        '<p class="bpw-eyebrow">Workspace 02 · authenticated readback</p>'
        "<h1>Authenticated Snowflake Bid Room</h1>"
        "<p>Read the decision, official weight, evidence state, and owned response as one "
        "causal record.</p></div>"
        f"{badge('Reader authenticated', 'brand')}</header>"
        f"{path}"
        '<footer class="bpw-first__footer">'
        f"<span>Selected Win Position <strong>{esc(selected_position)}</strong></span>"
        f"<span>Run <code>{esc(run_id)}</code> · same-run readback</span>"
        "</footer></section>"
    )


def synthetic_simulation_first_viewport(*, verdict: object, reason: object) -> str:
    """Render a local policy demonstration with no persisted-action affordance."""
    return (
        '<section class="bpw-first bpw-first--synthetic" '
        'data-workspace-view="synthetic-simulation">'
        '<header class="bpw-first__header"><div>'
        '<p class="bpw-eyebrow">Workspace 03 · isolated policy demonstration</p>'
        "<h1>Synthetic Decision Simulation</h1>"
        "<p>Change scenario inputs and inspect deterministic thresholds without touching a "
        "recorded run.</p></div>"
        f"{badge('Local only', 'caution')}</header>"
        f"{boundary_panel(SYNTHETIC_BOUNDARY, 'Scenario values are illustrative and remain in this browser view.', tone='caution')}"
        '<div class="bpw-simulation-result">'
        '<p class="bpw-overline">Scenario result</p>'
        f'<p class="bpw-simulation-result__verdict">{esc(verdict)}</p>'
        f"<p>{esc(reason)}</p>"
        "</div></section>"
    )


def workspace_shell(active_key: str, first_viewport: str, body: str = "") -> str:
    """Compose navigation and supplied view content without adding a scroll region."""
    return (
        '<div class="bpw-shell">'
        f"{workspace_navigation(active_key)}"
        '<main class="bpw-main" id="bpw-main">'
        f"{first_viewport}{body}"
        "</main></div>"
    )


def render_markup(markup: str) -> None:
    """Write trusted component markup through Streamlit's presentation seam."""
    import streamlit as st

    st.markdown(markup, unsafe_allow_html=True)


def render_workspace_shell(
    active_key: str, first_viewport: str, body: str = ""
) -> None:
    """Inject the shell tokens and render one workspace into the host page."""
    render_markup(shell_css())
    render_markup(workspace_shell(active_key, first_viewport, body))


def shell_css() -> str:
    """Return scoped WDS-informed styles with the document as scroll owner."""
    return """<style>
@import url("https://static.wanted.co.kr/fonts/wantedsans/WantedSansVariable.min.css");
:root {
  --bpw-blue:#0066ff; --bpw-blue-strong:#005eeb; --bpw-blue-heavy:#0054d1;
  --bpw-blue-95:#eaf2fe; --bpw-blue-99:#f7fbff;
  --bpw-ink:#171719; --bpw-neutral:rgba(46,47,51,.88);
  --bpw-muted:rgba(55,56,60,.61); --bpw-line:rgba(112,115,124,.22);
  --bpw-line-soft:rgba(112,115,124,.12); --bpw-surface:#f7f7f8;
  --bpw-green:#009632; --bpw-green-bg:#d9ffe6;
  --bpw-orange:#d17600; --bpw-orange-bg:#fef4e6; --bpw-red:#e52222;
  --bpw-font:"Wanted Sans Variable","Wanted Sans","Noto Sans KR",sans-serif;
  --bpw-shadow:0 4px 6px -2px rgba(23,23,23,.07),0 10px 15px -3px rgba(23,23,23,.07);
}
html, body { height: auto !important; overflow-y: auto !important; }
[data-testid="stAppViewContainer"], section.stMain, [data-testid="stMain"] {
  height: auto !important; overflow: visible !important;
}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stAppToolbar"],
[data-testid="stDecoration"],[data-testid="stStatusWidget"] {
  display:none !important; visibility:hidden !important; height:0 !important;
}
.stMainBlockContainer, .block-container { width:100% !important; max-width:1240px !important;
  padding:20px 24px 96px !important; }
.bpw-shell, .bpw-shell * { box-sizing:border-box; }
.bpw-shell { display:grid; grid-template-columns:248px minmax(0,1fr); gap:32px;
  max-width:1440px; margin:0 auto; color:var(--bpw-ink); font-family:var(--bpw-font); }
.bpw-main { min-width:0; padding:24px 32px 96px 0; }
.bpw-desktop-workspaces { padding:24px 16px; border-right:1px solid var(--bpw-line-soft); }
.bpw-brand { display:flex; align-items:center; gap:10px; margin:0 4px 36px; }
.bpw-brand strong,.bpw-brand small { display:block; }
.bpw-brand small { color:var(--bpw-muted); font-size:12px; }
.bpw-brand__mark { width:24px; height:24px; border-radius:7px; background:var(--bpw-blue);
  box-shadow:0 5px 18px -6px rgba(0,102,255,.7); }
.bpw-nav-overline,.bpw-overline,.bpw-eyebrow { margin:0; font-size:11px; line-height:16px;
  font-weight:600; text-transform:uppercase; letter-spacing:.09em; color:var(--bpw-muted); }
.bpw-nav-overline { margin:0 10px 8px; }
.bpw-workspace-link { display:grid; grid-template-columns:26px minmax(0,1fr); gap:8px;
  min-height:64px; padding:10px; border-radius:12px; color:var(--bpw-neutral);
  text-decoration:none; transition:background 220ms cubic-bezier(.4,0,.2,1),color 220ms cubic-bezier(.4,0,.2,1); }
.bpw-workspace-link:hover { background:rgba(112,115,124,.08); }
.bpw-workspace-link[aria-current="page"] { color:var(--bpw-blue-strong); background:var(--bpw-blue-95); }
.bpw-workspace-link__number { width:24px; height:24px; display:grid; place-items:center;
  border:1px solid var(--bpw-line); border-radius:6px; font-size:11px; font-weight:600; }
.bpw-workspace-link__copy strong,.bpw-workspace-link__copy small { display:block; }
.bpw-workspace-link__copy strong { font-size:13px; line-height:18px; }
.bpw-workspace-link__copy small { margin-top:2px; color:var(--bpw-muted); font-size:11px; line-height:15px; }
.bpw-mobile-workspace { display:none; }
.bpw-route-frame { width:100%; margin:0 auto 12px; font-family:var(--bpw-font); }
.bpw-route-desktop { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:6px;
  padding:6px; border:1px solid var(--bpw-line-soft); border-radius:14px; background:rgba(247,247,248,.86); }
.bpw-route-desktop a,.bpw-route-mobile nav a { min-width:0; min-height:52px; padding:8px 10px;
  border-radius:10px; color:var(--bpw-neutral); text-decoration:none; }
.bpw-route-desktop a { display:grid; grid-template-columns:24px minmax(0,1fr); gap:1px 8px; align-content:center; }
.bpw-route-desktop a > span { grid-row:1 / span 2; align-self:start; color:var(--bpw-blue-strong);
  font-size:10px; line-height:18px; font-weight:650; }
.bpw-route-desktop a strong,.bpw-route-mobile nav a strong { min-width:0; font-size:13px; line-height:18px; }
.bpw-route-desktop a small,.bpw-route-mobile nav a small { min-width:0; color:var(--bpw-muted);
  font-size:10px; line-height:14px; overflow-wrap:anywhere; }
.bpw-route-desktop a[aria-current="page"],.bpw-route-mobile nav a[aria-current="page"] {
  color:var(--bpw-blue-strong); background:#fff; box-shadow:0 1px 2px -1px rgba(23,23,23,.1); }
.bpw-route-desktop a:hover,.bpw-route-mobile nav a:hover { background:var(--bpw-blue-95); }
.bpw-route-mobile { display:none; }
.bpw-first { border-top:3px solid var(--bpw-blue); }
.bpw-first__header { display:flex; justify-content:space-between; align-items:flex-start; gap:24px;
  padding:20px 0 24px; }
.bpw-first__header h1 { margin:7px 0 5px; max-width:760px; font-size:30px; line-height:38px;
  letter-spacing:-.025em; }
.bpw-first__header p:not(.bpw-eyebrow) { margin:0; max-width:720px; color:var(--bpw-muted);
  font-size:14px; line-height:21px; }
.bpw-eyebrow { color:var(--bpw-blue-strong); }
.bpw-badge { display:inline-flex; align-items:center; min-height:24px; padding:3px 8px;
  border:1px solid transparent; border-radius:6px; font-size:11px; line-height:16px; font-weight:600; white-space:nowrap; }
.bpw-badge--brand { color:var(--bpw-blue-strong); background:var(--bpw-blue-95); }
.bpw-badge--positive { color:var(--bpw-green); background:var(--bpw-green-bg); }
.bpw-badge--caution { color:var(--bpw-orange); background:var(--bpw-orange-bg); }
.bpw-badge--negative { color:var(--bpw-red); background:#feecec; }
.bpw-badge--neutral { color:var(--bpw-neutral); background:rgba(112,115,124,.08); }
.bpw-badge--outline { color:var(--bpw-neutral); background:#fff; border-color:var(--bpw-line); }
.bpw-path,.bpw-receipt { display:grid; overflow:hidden; border:1px solid var(--bpw-line);
  border-radius:12px; background:#fff; box-shadow:var(--bpw-shadow); }
.bpw-path { grid-template-columns:repeat(4,minmax(0,1fr)); }
.bpw-path__item { min-width:0; padding:18px; border-left:1px solid var(--bpw-line-soft); }
.bpw-path__item:first-child { border-left:3px solid var(--bpw-blue); }
.bpw-path__label { display:flex; gap:8px; color:var(--bpw-muted); font-size:10px; line-height:14px;
  font-weight:600; letter-spacing:.08em; text-transform:uppercase; }
.bpw-path__label span:first-child { color:var(--bpw-blue); }
.bpw-path__value { margin:10px 0 5px; font-size:25px; line-height:30px; font-weight:650;
  letter-spacing:-.025em; overflow-wrap:anywhere; }
.bpw-path__value--caution { color:var(--bpw-orange); }
.bpw-path__value--brand { color:var(--bpw-ink); }
.bpw-caption { margin:0; color:var(--bpw-muted); font-size:12px; line-height:17px; }
.bpw-first__footer { display:flex; justify-content:space-between; gap:16px; padding:12px 16px;
  border:1px solid var(--bpw-line-soft); border-top:0; border-radius:0 0 12px 12px;
  color:var(--bpw-muted); font-size:11px; line-height:16px; }
.bpw-first__footer code { color:var(--bpw-neutral); font-family:ui-monospace,SFMono-Regular,monospace; }
.bpw-receipt { grid-template-columns:repeat(3,minmax(0,1fr)); box-shadow:none; }
.bpw-receipt__item { display:grid; grid-template-columns:30px minmax(0,1fr); gap:10px; padding:18px;
  border-left:1px solid var(--bpw-line-soft); border-bottom:1px solid var(--bpw-line-soft); }
.bpw-receipt__item:nth-child(3n + 1) { border-left:0; }
.bpw-receipt__item:nth-last-child(-n + 3) { border-bottom:0; }
.bpw-receipt__number { width:25px; height:25px; display:grid; place-items:center; border-radius:7px;
  color:var(--bpw-blue-strong); background:var(--bpw-blue-95); font-size:10px; font-weight:650; }
.bpw-receipt__value { margin:5px 0 3px; font-size:14px; line-height:19px; font-weight:600;
  overflow-wrap:anywhere; }
.bpw-boundary { display:flex; gap:12px; margin:0 0 16px; padding:14px 16px; border:1px solid var(--bpw-line);
  border-radius:12px; }
.bpw-boundary--caution { color:var(--bpw-orange); border-color:rgba(209,118,0,.3); background:var(--bpw-orange-bg); }
.bpw-boundary--brand { color:var(--bpw-blue-strong); border-color:rgba(0,102,255,.2); background:var(--bpw-blue-99); }
.bpw-boundary--neutral { color:var(--bpw-neutral); background:var(--bpw-surface); }
.bpw-boundary__mark { width:4px; min-height:34px; flex:none; border-radius:999px; background:currentColor; }
.bpw-boundary__title { margin:0 0 2px; color:currentColor; font-size:13px; line-height:18px; font-weight:650; }
.bpw-simulation-result { padding:24px; border:1px solid var(--bpw-line); border-radius:12px; }
.bpw-simulation-result__verdict { margin:8px 0; color:var(--bpw-red); font-size:34px; font-weight:650; }
.bpw-state { display:flex; gap:12px; min-height:152px; padding:16px; border:1px solid var(--bpw-line-soft);
  border-radius:12px; background:#fff; }
.bpw-state__glyph { width:28px; height:28px; flex:none; border:1px solid var(--bpw-line); border-radius:8px; }
.bpw-state__title { margin:4px 0; font-size:14px; line-height:19px; font-weight:600; }
.bpw-state__action { display:inline-flex; align-items:center; min-height:44px; margin-top:10px; padding:0 13px;
  border:1px solid var(--bpw-line); border-radius:10px; color:var(--bpw-ink); font-size:13px; font-weight:600; text-decoration:none; }
.bpw-state--error { border-color:rgba(229,34,34,.25); }
.bpw-state--disconnected { border-color:rgba(209,118,0,.28); }
.bpw-state__skeleton { width:72px; flex:none; }
.bpw-state__skeleton i { display:block; height:7px; margin-bottom:7px; border-radius:4px;
  background:linear-gradient(90deg,#eaebec,#f7f7f8,#eaebec); background-size:200% 100%; animation:bpw-load 1.6s ease infinite; }
.bpw-state__skeleton i:nth-child(2) { width:70%; }.bpw-state__skeleton i:nth-child(3) { width:45%; }
.bpw-section-heading { display:grid; grid-template-columns:28px minmax(0,1fr); gap:10px; margin:36px 0 12px;
  padding-bottom:12px; border-bottom:1px solid var(--bpw-line-soft); }
.bpw-section-heading__number { color:var(--bpw-blue); font-size:11px; font-weight:650; }
.bpw-section-heading h2 { margin:0; font-size:16px; line-height:22px; }.bpw-section-heading p { margin:3px 0 0; color:var(--bpw-muted); font-size:12px; }
:where(.bpw-shell a,.bpw-shell select):focus-visible { outline:2px solid var(--bpw-blue) !important; outline-offset:2px; }
@keyframes bpw-load { from { background-position:100% 0; } to { background-position:-100% 0; } }
@media (max-width: 900px) {
  .bpw-shell { grid-template-columns:210px minmax(0,1fr); gap:22px; }
  .bpw-main { padding-right:20px; }
  .bpw-path { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .bpw-path__item:nth-child(3) { border-left:3px solid var(--bpw-blue); }
  .bpw-receipt { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .bpw-receipt__item:nth-child(3n + 1) { border-left:1px solid var(--bpw-line-soft); }
  .bpw-receipt__item:nth-child(2n + 1) { border-left:0; }
  .bpw-receipt__item:nth-last-child(-n + 3) { border-bottom:1px solid var(--bpw-line-soft); }
  .bpw-receipt__item:nth-last-child(-n + 2) { border-bottom:0; }
}
@media (max-width: 760px) {
  .stMainBlockContainer, .block-container { padding:16px 16px 72px !important; }
  .bpw-shell { display:block; }
  .bpw-desktop-workspaces { display:none; }
  .bpw-mobile-workspace { display:block; padding:12px 16px; border-bottom:1px solid var(--bpw-line-soft); }
  .bpw-mobile-workspace label { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); }
  .bpw-mobile-workspace select { width:100%; min-height:44px; padding:0 38px 0 12px; border:1px solid var(--bpw-line);
    border-radius:10px; color:var(--bpw-ink); background:#fff; font:600 13px var(--bpw-font); }
  .bpw-route-desktop { display:none; }
  .bpw-route-mobile { display:block; border:1px solid var(--bpw-line); border-radius:12px; background:#fff; }
  .bpw-route-mobile summary { display:grid; grid-template-columns:auto minmax(0,1fr); gap:4px 10px;
    align-items:center; min-height:48px; padding:8px 12px; cursor:pointer; list-style:none; }
  .bpw-route-mobile summary::-webkit-details-marker { display:none; }
  .bpw-route-mobile summary::after { content:"⌄"; grid-column:3; grid-row:1 / span 2; color:var(--bpw-muted); }
  .bpw-route-mobile summary span { color:var(--bpw-muted); font-size:10px; line-height:13px;
    text-transform:uppercase; letter-spacing:.08em; }
  .bpw-route-mobile summary strong { grid-column:1 / span 2; font-size:13px; line-height:18px; }
  .bpw-route-mobile nav { display:grid; gap:4px; padding:4px 6px 6px; border-top:1px solid var(--bpw-line-soft); }
  .bpw-route-mobile nav a { display:grid; grid-template-columns:22px minmax(0,1fr); gap:1px 8px; }
  .bpw-route-mobile nav a > span { grid-row:1 / span 2; color:var(--bpw-blue-strong); font-size:10px; }
  .bpw-main { padding:20px 16px 72px; }
  .bpw-first__header { display:block; padding-top:16px; }
  .bpw-first__header .bpw-badge { margin-top:12px; }
  .bpw-first__header h1 { font-size:24px; line-height:31px; }
  .bpw-path,.bpw-receipt { grid-template-columns:minmax(0,1fr); }
  .bpw-path__item,.bpw-path__item:nth-child(3),.bpw-receipt__item,.bpw-receipt__item:nth-child(3n + 1),
  .bpw-receipt__item:nth-child(2n + 1) { border-left:0; border-top:1px solid var(--bpw-line-soft); }
  .bpw-path__item:first-child { border-top:0; border-left:3px solid var(--bpw-blue); }
  .bpw-receipt__item:first-child { border-top:0; }
  .bpw-receipt__item:nth-last-child(-n + 2),.bpw-receipt__item:nth-last-child(-n + 3) { border-bottom:0; }
  .bpw-path__value { font-size:22px; line-height:28px; }
  .bpw-first__footer { display:grid; }
}
@media (prefers-reduced-motion: reduce) {
  *,*::before,*::after { animation-duration:.01ms !important; animation-iteration-count:1 !important;
    transition-duration:.01ms !important; scroll-behavior:auto !important; }
}
</style>"""
