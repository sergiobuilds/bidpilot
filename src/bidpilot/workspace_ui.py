"""Three-workspace presentation shell for the BidPilot refinement UI.

The module accepts already-reviewed display values and returns escaped HTML.
It intentionally has no domain, intake, persistence, or runner imports, which
keeps the existing verified data path in charge of every displayed fact.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

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


KST = timezone(timedelta(hours=9))


def catalog_date(value: object) -> str:
    """Format a stored ISO timestamp for display, naming KST when it is aware."""
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return str(value or "—")
    if parsed.tzinfo is None:
        return parsed.strftime("%Y.%m.%d · %H:%M")
    return parsed.astimezone(KST).strftime("%Y.%m.%d · %H:%M KST")


_catalog_date = catalog_date


def deadline_state(value: object, now: datetime) -> str | None:
    """Return "open" or "closed" against an aware clock, or None when unknown."""
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None or now.tzinfo is None:
        return None
    return "open" if parsed > now else "closed"


def _due_tag(value: object, now: datetime) -> str:
    state = deadline_state(value, now)
    if state is None:
        return ""
    label = "Open" if state == "open" else "Closed"
    return f' <span class="due-tag due-{state}">{label}</span>'


def _catalog_value(value: object) -> str:
    if value is None:
        return "—"
    return f"KRW {int(value) / 1_000_000:g}M"


def _catalog_weights(row: Mapping[str, object]) -> str:
    technical = row.get("technical_weight")
    price = row.get("price_weight")
    return "—" if technical is None or price is None else f"T {technical} · P {price}"


def koat_dashboard(rows: Sequence[Mapping[str, object]], *, now: datetime) -> str:
    """Render the verified-source catalogue with the literal KOAT dashboard grammar."""
    reviewed = [row for row in rows if row.get("evidence_level") == "source-reviewed"]
    found = [row for row in rows if row.get("evidence_level") == "source-found"]
    review_count = sum(row.get("status") == "REVIEW" for row in rows)
    open_rows = [
        row for row in rows if deadline_state(row.get("deadline"), now) == "open"
    ]
    closed_count = sum(
        deadline_state(row.get("deadline"), now) == "closed" for row in rows
    )
    if open_rows:
        next_close = min(str(row.get("deadline")) for row in open_rows)
        deadline_context = f"{closed_count} closed · next {_catalog_date(next_close)}"
    else:
        deadline_context = "All deadlines passed · historical public sources"
    body_rows = "".join(
        "<tr>"
        '<td class="tender-cell">'
        f"<strong>{esc(row.get('title'))}</strong><small>{esc(row.get('notice_number'))}</small></td>"
        f'<td data-label="Issuer">{esc(row.get("issuer"))}</td>'
        f'<td data-label="Value" class="num">{esc(_catalog_value(row.get("contract_value_krw")))}</td>'
        f'<td data-label="Deadline" class="num">{esc(_catalog_date(row.get("deadline")))}'
        f"{_due_tag(row.get('deadline'), now)}</td>"
        f'<td data-label="Weights" class="num">{esc(_catalog_weights(row))}</td>'
        f'<td data-label="Status"><span class="state-tag state-{esc(str(row.get("evidence_level")))}">'
        f"{esc(row.get('status'))}</span></td>"
        f'<td data-label="Action"><a class="row-action" href="?tender={esc(row.get("notice_number"))}">'
        f"{'Review' if row.get('evidence_level') == 'source-reviewed' else 'Inspect'} →</a></td>"
        "</tr>"
        for row in rows
    )
    return (
        '<div id="bp-koat" class="bp-koat dashboard">'
        '<header class="nav"><div class="nav-in"><a class="brand" href="?">'
        '<span class="brand-mark">B</span><span class="brand-name">BidPilot</span>'
        '<span class="brand-sub">Pursuit workspace</span></a>'
        '<nav class="nav-links"><a class="nav-link active" href="?">Opportunities</a>'
        '<a class="nav-link" href="?walkthrough=1">Verified replay</a></nav>'
        '<span class="nav-spacer"></span><span class="nav-acct"><i class="nav-dot"></i>Public sources</span>'
        "</div></header>"
        '<main class="wrap">'
        '<header class="phead"><div><span class="eyebrow"><i class="pip"></i>G2B opportunities</span>'
        '<h1 class="t-title1 w-bold">Pursuit dashboard</h1>'
        '<p class="psub">Official public notices, separated by evidence level.</p></div>'
        '<div class="controls" aria-label="Catalogue filters"><span class="filter-label">All</span>'
        f'<span class="filter-chip">Source reviewed {len(reviewed)}</span>'
        f'<span class="filter-chip">Source found {len(found)}</span>'
        '<a class="primary-cta" href="?walkthrough=1">Open verified PURSUE replay →</a></div></header>'
        '<section class="kpi-band">'
        f'<div class="kpi focal"><i class="tick"></i><span class="kpi-lab">Needs review</span>'
        f'<div class="kpi-val"><strong class="kpi-num">{review_count}</strong><span class="kpi-unit">notice</span></div>'
        '<p class="kpi-ctx">Supplier evidence required · no proposal until PURSUE</p></div>'
        f'<div class="kpi"><i class="tick"></i><span class="kpi-lab">Open deadlines</span>'
        f'<div class="kpi-val"><strong class="kpi-num">{len(open_rows)}</strong>'
        f'<span class="kpi-unit">{"notice" if len(open_rows) == 1 else "notices"}</span></div>'
        f'<p class="kpi-ctx">{esc(deadline_context)}</p></div></section>'
        '<section class="tender-section"><div class="shead"><h2 class="t-headline1">Official tender catalogue</h2>'
        f'<span class="badge">{len(rows)} rows</span></div><div class="table-wrap"><table class="tbl tender-table">'
        "<thead><tr><th>Tender</th><th>Issuer</th><th>Value</th><th>Deadline</th><th>Weights</th><th>Status</th><th>Action</th></tr></thead>"
        f"<tbody>{body_rows}</tbody></table></div>"
        '<p class="note">Source found means the official listing URL and deadline were captured. '
        "Source reviewed means the notice facts and score map passed the committed source contract. "
        f"Deadline states are computed against {esc(_catalog_date(now.isoformat()))}.</p></section>"
        '<section class="agent-access" aria-label="Mount BidPilot in your agent">'
        "<div><strong>Mount BidPilot in your agent</strong>"
        "<p>The same judgement engine and Snowflake record behind this dashboard, as tools any agent can call. Read-only.</p></div>"
        '<div class="agent-links">'
        '<a href="https://bidpilot-api-164282963747.us-central1.run.app/mcp" target="_blank" rel="noreferrer">MCP server ↗</a>'
        '<a href="https://bidpilot-api-164282963747.us-central1.run.app/openapi.json" target="_blank" rel="noreferrer">OpenAPI · ChatGPT Actions ↗</a>'
        '<a href="https://github.com/sergiobuilds/bidpilot/tree/main/skills/bidpilot" target="_blank" rel="noreferrer">Cortex Code skill (skills/bidpilot) ↗</a>'
        '<a href="https://github.com/sergiobuilds/bidpilot/tree/main/integrations" target="_blank" rel="noreferrer">Claude Code · Cursor · Gemini mounts ↗</a>'
        "</div></section>"
        '<nav class="foot-links" aria-label="Evaluator workspaces"><span>Evaluator workspaces</span>'
        '<a href="?workspace=tender-intake">Tender intake</a>'
        '<a href="?workspace=bid-room">Authenticated Bid Room</a>'
        '<a href="?workspace=synthetic-simulation">Synthetic decision simulation</a></nav>'
        "</main></div>"
    )


def koat_tender_detail(
    row: Mapping[str, object],
    *,
    now: datetime,
    reviewed_view: Mapping[str, object] | None = None,
) -> str:
    """Render a selected public notice with the literal KOAT detail grammar."""
    reviewed = (
        row.get("evidence_level") == "source-reviewed" and reviewed_view is not None
    )
    requirements = (
        tuple(reviewed_view.get("eligibility_requirements") or ())
        if reviewed_view
        else ()
    )
    timeline = (
        ("Source found", row.get("retrieved_at"), "Official G2B listing captured"),
        (
            "Source reviewed" if reviewed else "Awaiting source review",
            "",
            "Notice facts and score map verified"
            if reviewed
            else "Detailed extraction not completed",
        ),
        (
            "Decision",
            "",
            "REVIEW — supplier evidence required" if reviewed else "Not started",
        ),
        ("Strategy", "", "Pending pursuit clearance"),
        ("Proposal", "", "Not started"),
    )
    timeline_html = "".join(
        '<li class="tl"><span class="tl-rail"><i class="tl-node">✓</i></span><div class="tl-body">'
        f'<div class="tl-top"><strong class="tl-lab">{esc(label)}</strong>'
        f'<span class="tl-ts">{esc(_catalog_date(at) if at else "")}</span></div>'
        f'<p class="tl-detail">{esc(detail)}</p></div></li>'
        for label, at, detail in timeline
    )
    work = "".join(
        '<li class="work-item"><span class="work-no">'
        f"{index:02d}</span><strong>{esc(item)}</strong><small>Operator review</small></li>"
        for index, item in enumerate(requirements, start=1)
    )
    work_markup = work or '<li class="work-empty">Available after source review</li>'
    status = "REVIEW" if reviewed else "SOURCE FOUND"
    return (
        '<div id="bp-koat" class="bp-koat detail">'
        '<header class="topbar"><div class="topbar-inner"><a class="brand" href="?">'
        '<span class="mark">B</span><span>BidPilot <span class="sub">· pursuit workspace</span></span></a>'
        '<nav class="detail-nav"><a href="?">Dashboard</a><a class="current" href="#">Tender detail</a>'
        '<a href="?walkthrough=1">Verified replay</a></nav>'
        '</div></header><main class="detail-wrap"><nav class="crumb"><a href="?">‹ Opportunities</a>'
        f"<span>/</span><strong>{esc(row.get('notice_number'))}</strong></nav>"
        '<section class="idhead"><div class="idhead-top"><div class="id-left">'
        f'<span class="id-eyebrow"><i class="pip"></i>Official G2B · {esc(row.get("notice_number"))}</span>'
        f'<div class="id-name"><h1>{esc(row.get("title"))}</h1></div>'
        f'<div class="id-sub"><span>{esc(row.get("issuer"))}</span>'
        f"<span>Retrieved {esc(_catalog_date(row.get('retrieved_at')))}</span></div></div>"
        f'<div class="id-right"><span class="statechip {"sc-orange" if reviewed else "sc-grey"}"><i class="sd"></i>{status}</span>'
        f'<span class="id-due">Deadline <b>{esc(_catalog_date(row.get("deadline")))}</b>'
        f"{_due_tag(row.get('deadline'), now)}</span></div></div>"
        '<div class="id-contract">'
        f'<div class="id-cell"><span class="k">Value</span><strong class="v big">{esc(_catalog_value(row.get("contract_value_krw")))}</strong></div>'
        f'<div class="id-cell"><span class="k">Technical</span><strong class="v big">{esc(row.get("technical_weight") if reviewed else "—")}</strong></div>'
        f'<div class="id-cell"><span class="k">Price</span><strong class="v big">{esc(row.get("price_weight") if reviewed else "—")}</strong></div>'
        f'<div class="id-cell"><span class="k">Run ID</span><strong class="v">{"Not created" if reviewed else "—"}</strong></div>'
        "</div></section>"
        '<section class="sec"><div class="sec-head"><span class="sec-ic">✓</span><h2 class="sec-title">Decision summary</h2></div>'
        '<div class="panel"><div class="an">'
        f'<div class="an-cell"><span class="an-k">Decision</span><strong class="an-v flag">{status if reviewed else "—"}</strong></div>'
        f'<div class="an-cell"><span class="an-k">Eligibility gaps</span><strong class="an-v">{len(requirements) if reviewed else "—"}</strong></div>'
        f'<div class="an-cell"><span class="an-k">Run state</span><strong class="an-v">{"Not created" if reviewed else "—"}</strong></div></div>'
        f'<div class="an-foot"><span class="flagbadge">{"Supplier evidence required" if reviewed else "Source review required"}</span>'
        + (
            '<p class="an-why">REVIEW is the correct outcome for this notice: the synthetic supplier '
            f"profile has no evidence for {len(requirements)} eligibility requirements, so no strategy or "
            "proposal is generated. The complete PURSUE chain is shown in the "
            '<a href="?walkthrough=1">separate verified replay →</a></p>'
            if reviewed
            else ""
        )
        + "</div></div></section>"
        '<details class="sec-fold"><summary>Processing history and source evidence</summary>'
        '<div class="pair"><section class="sec"><div class="sec-head"><span class="sec-ic">↻</span>'
        '<h2 class="sec-title">Processing history</h2></div><div class="panel panel-pad"><ol class="timeline">'
        f'{timeline_html}</ol></div></section><section class="sec"><div class="sec-head"><span class="sec-ic">▣</span>'
        '<h2 class="sec-title">Source evidence</h2></div><div class="panel evidence-panel">'
        f"<div><span>Evidence level</span><strong>{esc(str(row.get('evidence_level')).replace('-', ' ').title())}</strong></div>"
        f'<div><span>Official URL</span><a href="{esc(row.get("official_url"))}" target="_blank" rel="noreferrer">Open G2B source ↗</a></div>'
        f"<div><span>Supplier</span><strong>{'Synthetic demo supplier profile' if reviewed else 'Not assessed'}</strong></div>"
        "</div></section></div></details>"
        '<section class="sec"><div class="sec-head"><span class="sec-ic">◎</span><h2 class="sec-title">Score-weighted Win Position</h2></div>'
        '<div class="panel state-panel"><strong>Pending pursuit clearance</strong><p>Strategy starts only after a supported PURSUE decision.</p></div></section>'
        '<section class="sec"><div class="sec-head"><span class="sec-ic">✎</span><h2 class="sec-title">Proposal & red-team</h2></div>'
        '<div class="panel state-panel"><strong>Not started</strong><p>No proposal is created while the decision remains REVIEW.</p></div></section>'
        '<section class="sec"><div class="sec-head"><span class="sec-ic">☑</span><h2 class="sec-title">Owned work</h2></div>'
        f'<div class="panel"><ol class="work-list">{work_markup}</ol></div></section>'
        '<section class="sec"><div class="sec-head"><span class="sec-ic">◇</span><h2 class="sec-title">Snowflake history</h2></div>'
        '<div class="panel replay-panel"><div><strong>No Snowflake run for this notice</strong>'
        "<p>The historical replay below is a separate synthetic fixture.</p></div>"
        '<a href="?walkthrough=1">View verified capability replay →</a></div></section>'
        "</main></div>"
    )


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
            f"<strong>{esc(workspace.label)}</strong>"
            f"<small>{esc(workspace.note)}</small>"
            "</a>"
        )

    return (
        '<div class="bpw-route-frame" aria-label="BidPilot workspace routes">'
        '<nav class="bpw-route-desktop" aria-label="BidPilot workspace routes">'
        + "".join(links)
        + "</nav>"
        '<details class="bpw-route-mobile">'
        "<summary><span>Workspace</span>"
        f"<strong>{esc(active.label)}</strong></summary>"
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
        '<p class="bpw-eyebrow">Verified capability replay · separate synthetic fixture</p>'
        "<h1>Pursuit decision</h1>"
        "<p>Decision, score weight, evidence, and next owner from one recorded run.</p></div>"
        f"{badge('Same run', 'brand')}</header>"
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


def judge_overview(
    *,
    notice_number: object,
    title: object,
    issuer: object,
    deadline: object,
    contract_value: object,
    technical_weight: object,
    price_weight: object,
    supplier_boundary: object,
    eligibility_count: object,
    source_url: object,
) -> str:
    """Render an instant KOAT-grammar dashboard of verified public sources."""
    return (
        '<main class="bpw-overview" data-surface="judge-overview">'
        '<nav class="bpw-overview-nav" aria-label="BidPilot">'
        '<a class="bpw-overview-brand" href="?" aria-label="BidPilot home">'
        '<span class="bpw-overview-brand__mark" aria-hidden="true">B</span>'
        "<span><strong>BidPilot</strong><small>Pursuit workspace</small></span></a>"
        '<span class="bpw-overview-nav__state"><i aria-hidden="true"></i>Public source</span>'
        "</nav>"
        '<header class="bpw-dashboard-head">'
        '<div class="bpw-overview-head__copy">'
        '<p class="bpw-eyebrow">Verified public sources</p>'
        "<h1>Pursuit dashboard</h1>"
        "<p>Select an official G2B notice to review its pursuit readiness.</p></div>"
        "</header>"
        '<section class="bpw-overview-metrics" aria-label="Opportunity summary">'
        '<div class="bpw-overview-metric">'
        "<p>Verified sources</p><strong>1</strong><small>Official G2B notice</small></div>"
        '<div class="bpw-overview-metric bpw-overview-metric--decision">'
        "<p>REVIEW</p><strong>1</strong><small>Supplier evidence required</small></div>"
        '<div class="bpw-overview-metric">'
        "<p>PURSUE</p><strong>0</strong><small>No cleared opportunity</small></div>"
        '<div class="bpw-overview-metric">'
        "<p>NO-GO</p><strong>0</strong><small>No rejected opportunity</small></div>"
        "</section>"
        '<section class="bpw-dashboard-lower">'
        '<div class="bpw-funnel"><header><h2>Pursuit funnel</h2><span>1 source-backed record</span></header>'
        '<div class="bpw-funnel-row"><b>Discovered</b><i style="--value:100%"></i><strong>1</strong></div>'
        '<div class="bpw-funnel-row"><b>Source verified</b><i style="--value:100%"></i><strong>1</strong></div>'
        '<div class="bpw-funnel-row"><b>Decision</b><i style="--value:100%"></i><strong>1 REVIEW</strong></div>'
        '<div class="bpw-funnel-row"><b>Strategy</b><i style="--value:0%"></i><strong>0</strong></div>'
        '<div class="bpw-funnel-row"><b>Proposal</b><i style="--value:0%"></i><strong>0</strong></div>'
        '<div class="bpw-funnel-row"><b>Owned work</b><i style="--value:0%"></i><strong>Pending</strong></div>'
        "</div>"
        '<aside class="bpw-recent"><header><h2>Recent activity</h2></header>'
        '<div class="bpw-recent-row"><span aria-hidden="true"></span><div>'
        f"<strong>{esc(notice_number)}</strong><small>Source contract verified</small></div>"
        "<em>Current</em></div>"
        '<div class="bpw-recent-row"><span aria-hidden="true"></span><div>'
        "<strong>Supplier evidence</strong><small>Operator review required</small></div>"
        "<em>Open</em></div></aside>"
        "</section>"
        '<section class="bpw-opportunities">'
        '<header class="bpw-opportunities__head"><div><h2>Source-backed opportunities</h2>'
        "<p>Only notices with a verified public-source record appear here.</p></div>"
        '<div class="bpw-opportunity-filters" aria-label="Status filter"><span>Status</span>'
        '<b>All 1</b><b class="is-active">REVIEW 1</b></div></header>'
        '<div class="bpw-tender-table" role="table" aria-label="Verified public tenders">'
        '<div class="bpw-tender-table__head" role="row">'
        "<span>Tender</span><span>Issuer</span><span>Value</span><span>Deadline</span>"
        "<span>Weights</span><span>Status</span><span>Action</span></div>"
        '<article class="bpw-tender-row" role="row">'
        f'<div data-label="Tender"><small>Official G2B · {esc(notice_number)}</small><strong>{esc(title)}</strong>'
        f"<em>{esc(supplier_boundary)} · {esc(eligibility_count)} eligibility requirements</em></div>"
        f'<div data-label="Issuer">{esc(issuer)}</div>'
        f'<div data-label="Value">{esc(contract_value)}</div>'
        f'<div data-label="Deadline">{esc(deadline)}</div>'
        f'<div data-label="Weights">T {esc(technical_weight)} · P {esc(price_weight)}</div>'
        '<div data-label="Status"><span class="bpw-badge bpw-badge--caution">REVIEW</span></div>'
        f'<div data-label="Action"><a class="bpw-primary-cta" href="?tender={esc(notice_number)}">'
        'Open pursuit review <span aria-hidden="true">→</span></a></div>'
        "</article></div>"
        '<p class="bpw-opportunities__empty">Additional notices appear only after source verification.</p>'
        "</section>"
        "</main>"
    )


def judge_tender_detail(
    *,
    notice_number: object,
    title: object,
    issuer: object,
    deadline: object,
    contract_value: object,
    delivery_term: object,
    technical_weight: object,
    price_weight: object,
    supplier_boundary: object,
    eligibility_requirements: tuple[object, ...],
    source_digest: object,
    source_url: object,
) -> str:
    """Render the selected real tender without implying a persisted run."""
    work = "".join(
        '<li class="bpw-detail-work">'
        f'<span aria-hidden="true">{index:02d}</span><p>{esc(requirement)}</p>'
        "<small>Operator review</small></li>"
        for index, requirement in enumerate(eligibility_requirements, start=1)
    )
    return (
        '<main class="bpw-overview bpw-detail" data-surface="tender-detail">'
        '<nav class="bpw-overview-nav" aria-label="BidPilot">'
        '<a class="bpw-overview-brand" href="?" aria-label="Back to pursuit dashboard">'
        '<span class="bpw-overview-brand__mark" aria-hidden="true">B</span>'
        "<span><strong>BidPilot</strong><small>Pursuit dashboard</small></span></a>"
        '<span class="bpw-overview-nav__state"><i aria-hidden="true"></i>Verified public source</span></nav>'
        '<header class="bpw-detail-head"><div>'
        f'<p class="bpw-eyebrow">Official G2B · {esc(notice_number)}</p>'
        f"<h1>{esc(title)}</h1><p>{esc(issuer)} · Deadline {esc(deadline)}</p></div>"
        '<span class="bpw-detail-verdict">REVIEW<small>Supplier evidence required</small></span></header>'
        '<section class="bpw-overview-metrics" aria-label="Pursuit result">'
        '<div class="bpw-overview-metric bpw-overview-metric--decision"><p>Decision</p>'
        "<strong>REVIEW</strong><small>Eligibility evidence missing</small></div>"
        f'<div class="bpw-overview-metric"><p>Contract value</p><strong>{esc(contract_value)}</strong>'
        f"<small>{esc(delivery_term)}</small></div>"
        f'<div class="bpw-overview-metric"><p>Official weight</p><strong>{esc(technical_weight)}</strong>'
        f"<small>Technical · Price {esc(price_weight)}</small></div>"
        '<div class="bpw-overview-metric"><p>Run ID</p><strong>Not created</strong>'
        "<small>Stops before private analysis</small></div></section>"
        '<section class="bpw-detail-section"><header><span>01</span><h2>Decision rationale</h2></header>'
        '<div class="bpw-detail-rows">'
        "<div><b>Official source</b><p>Notice facts and score weights are verified.</p><em>Ready</em></div>"
        f"<div><b>Supplier profile</b><p>{esc(supplier_boundary)}</p><em>Evidence required</em></div>"
        "<div><b>Pursuit gate</b><p>Eligibility must be confirmed before a Win Position is scored.</p>"
        "<em>REVIEW</em></div></div></section>"
        '<section class="bpw-detail-section"><header><span>02</span><h2>Score-weighted Win Position</h2></header>'
        '<div class="bpw-detail-empty"><strong>Pending pursuit clearance</strong>'
        "<p>The 90 / 10 score map is ready. Strategy starts after supplier eligibility evidence is attached.</p>"
        "</div></section>"
        '<section class="bpw-detail-section"><header><span>03</span><h2>Proposal & red-team result</h2></header>'
        '<div class="bpw-detail-empty"><strong>Not started</strong>'
        "<p>No proposal or red-team result is created while the pursuit decision remains REVIEW.</p>"
        "</div></section>"
        '<section class="bpw-detail-section"><header><span>04</span><h2>Owned work</h2></header>'
        f'<ol class="bpw-detail-worklist">{work}</ol></section>'
        '<section class="bpw-detail-section"><header><span>05</span><h2>Snowflake proof</h2></header>'
        '<div class="bpw-detail-proof"><div><strong>No run created for this notice</strong>'
        f"<p>Source digest <code>{esc(source_digest)}</code></p></div>"
        '<a href="?walkthrough=1">View separate verified capability replay →</a></div></section>'
        '<footer class="bpw-detail-foot">'
        f'<a href="{esc(source_url)}" target="_blank" rel="noreferrer">Open official G2B notice ↗</a></footer>'
        "</main>"
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


def koat_css() -> str:
    """Return the BidPilot adaptation of the literal KOAT dashboard/detail CSS."""
    return """<style>
@import url("https://static.wanted.co.kr/fonts/wantedsans/WantedSansVariable.min.css");
:root{--blue-40:#0054D1;--blue-45:#005EEB;--blue-50:#0066FF;--blue-80:#9EC5FF;--blue-90:#C9DEFE;--blue-95:#EAF2FE;--blue-99:#F7FBFF;--cn-10:#171719;--cn-22:#2E2F33;--cn-50:#70737C;--cn-96:#E1E2E4;--cn-97:#EAEBEC;--cn-98:#F4F4F5;--cn-99:#F7F7F8;--green-40:#009632;--green-50:#00BF40;--green-95:#D9FFE6;--orange-39:#D17600;--orange-50:#FF9200;--orange-95:#FEF4E6;--primary:var(--blue-50);--primary-strong:var(--blue-45);--primary-heavy:var(--blue-40);--label-normal:var(--cn-10);--label-neutral:rgba(46,47,51,.88);--label-alt:rgba(55,56,60,.61);--label-assist:rgba(55,56,60,.61);--bg:#fff;--bg-alt:var(--cn-99);--line-normal:rgba(112,115,124,.22);--line-neutral:rgba(112,115,124,.16);--line-alt:rgba(112,115,124,.08);--line-solid:var(--cn-96);--fill-normal:rgba(112,115,124,.08);--fill-strong:rgba(112,115,124,.16);--fill-alt:rgba(112,115,124,.05);--shadow-xs:0 1px 2px -1px rgba(23,23,23,.10);--shadow-sm:0 2px 4px -2px rgba(23,23,23,.06),0 4px 6px -1px rgba(23,23,23,.06);--radius-6:6px;--radius-8:8px;--radius-10:10px;--radius-12:12px;--radius-16:16px;--radius-20:20px;--radius-pill:1000px;--font:"Wanted Sans Variable","Wanted Sans",-apple-system,BlinkMacSystemFont,system-ui,"Noto Sans KR",sans-serif;--ease:cubic-bezier(.4,0,.2,1)}
html,body,.stApp,[data-testid="stAppViewContainer"],section.stMain,[data-testid="stMain"]{height:auto!important;min-height:100vh!important;overflow:visible!important}body{overflow-x:hidden!important}[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stAppToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],[data-testid="stSkeleton"],.stSkeleton{display:none!important}.stMainBlockContainer,.block-container{max-width:none!important;padding:0!important}.bp-koat,.bp-koat *{box-sizing:border-box}.bp-koat{font-family:var(--font);font-size:16px;color:var(--label-normal);background:radial-gradient(120% 60% at 100% -10%,rgba(0,102,255,.05) 0%,rgba(0,102,255,0) 55%),var(--bg);min-height:100vh}.bp-koat a{color:inherit;text-decoration:none}.bp-koat h1,.bp-koat h2,.bp-koat h3,.bp-koat p{margin:0}.t-title1{font-size:2rem;line-height:2.75rem;letter-spacing:-.0253em}.t-headline1{font-size:1.125rem;line-height:1.625rem}.w-bold{font-weight:700}.num{font-variant-numeric:tabular-nums}
.bp-koat .nav{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.72);backdrop-filter:blur(32px) saturate(180%);border-bottom:1px solid var(--line-neutral)}.bp-koat .nav-in{max-width:1200px;margin:0 auto;padding:0 32px;height:64px;display:flex;align-items:center;gap:28px}.bp-koat .brand{display:flex;align-items:center;gap:10px;margin-right:8px}.bp-koat .brand-mark{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;color:#fff;background:linear-gradient(145deg,var(--blue-50),var(--blue-40));box-shadow:0 3px 8px -2px rgba(0,84,209,.45);font-weight:700}.bp-koat .brand-name{font-weight:700}.bp-koat .brand-sub{color:var(--label-alt);font-size:.8125rem}.bp-koat .nav-links{display:flex;gap:4px}.bp-koat .nav-link{position:relative;padding:8px 14px;border-radius:var(--radius-8);color:var(--label-alt);font-weight:600;font-size:.875rem}.bp-koat .nav-link.active{color:var(--primary)}.bp-koat .nav-link.active::after{content:"";position:absolute;left:14px;right:14px;bottom:-15px;height:2px;background:var(--primary)}.bp-koat .nav-spacer{flex:1}.bp-koat .nav-acct{display:flex;align-items:center;gap:8px;color:var(--label-alt);font-size:.8125rem}.bp-koat .nav-dot{width:7px;height:7px;border-radius:50%;background:var(--green-50);box-shadow:0 0 0 3px rgba(0,191,64,.16)}
.bp-koat .wrap{max-width:1200px;margin:0 auto;padding:36px 32px 56px}.bp-koat .phead{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;flex-wrap:wrap}.bp-koat .eyebrow{display:inline-flex;align-items:center;gap:7px;color:var(--primary);font-weight:600;margin-bottom:10px;font-size:.875rem}.bp-koat .eyebrow .pip{width:6px;height:6px;border-radius:50%;background:var(--primary)}.bp-koat .psub{color:var(--label-alt);margin-top:6px}.bp-koat .controls{display:flex;align-items:center;gap:8px}.bp-koat .filter-label,.bp-koat .filter-chip{display:inline-flex;align-items:center;height:36px;padding:0 12px;border-radius:var(--radius-10);border:1px solid var(--line-normal);font-size:.8125rem;font-weight:600;color:var(--label-neutral);background:#fff}.bp-koat .filter-chip{background:var(--bg-alt);border-color:var(--line-alt)}
.bp-koat .causal{margin-top:24px;border:1px solid var(--line-neutral);border-radius:var(--radius-16);background:var(--blue-99);overflow:hidden}.bp-koat .causal-flow{display:grid;grid-template-columns:1.45fr .8fr 1.25fr 1fr .8fr 1.3fr}.bp-koat .causal-flow span{position:relative;min-width:0;min-height:70px;padding:14px 16px;display:flex;flex-direction:column;justify-content:center;gap:4px;border-right:1px solid var(--line-neutral);font-size:.8125rem;font-weight:600;line-height:1.3;overflow-wrap:anywhere}.bp-koat .causal-flow span:last-child{border-right:0}.bp-koat .causal-flow b{font-size:.6875rem;color:var(--primary);letter-spacing:.04em}.bp-koat .tool-links{display:flex;align-items:center;flex-wrap:wrap;gap:4px 8px;padding:8px 12px;border-top:1px solid var(--line-neutral);background:#fff}.bp-koat .tool-links-lab{margin-right:auto;color:var(--label-alt);font-size:.75rem;font-weight:600}.bp-koat .tool-links a{display:inline-flex;align-items:center;min-height:44px;padding:0 12px;border-radius:var(--radius-8);color:var(--primary-strong);font-size:.75rem;font-weight:700}.bp-koat .tool-links a:hover{background:var(--blue-95)}
.bp-koat .kpi-band{margin-top:24px;border-top:1px solid var(--line-solid);border-bottom:1px solid var(--line-solid);display:grid;grid-template-columns:repeat(2,1fr)}.bp-koat .primary-cta{display:inline-flex;align-items:center;min-height:44px;padding:0 16px;border-radius:var(--radius-10);background:var(--primary);color:#fff!important;font-weight:700;font-size:.875rem;box-shadow:0 3px 8px -2px rgba(0,84,209,.45)}.bp-koat .primary-cta:hover{background:var(--primary-strong)}.bp-koat .agent-access{margin-top:36px;display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap;padding:20px 22px;border:1px solid var(--line-neutral);border-radius:var(--radius-16);background:var(--blue-99)}.bp-koat .agent-access strong{font-size:1rem}.bp-koat .agent-access p{margin-top:4px;color:var(--label-alt);font-size:.8125rem;max-width:520px}.bp-koat .agent-links{display:flex;flex-wrap:wrap;gap:8px}.bp-koat .agent-links a{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border-radius:var(--radius-10);border:1px solid var(--line-normal);background:#fff;color:var(--primary-strong);font-size:.8125rem;font-weight:700}.bp-koat .agent-links a:hover{background:var(--blue-95)}.bp-koat .foot-links{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:center;margin-top:40px;padding-top:16px;border-top:1px solid var(--line-alt);font-size:.75rem}.bp-koat .foot-links span{color:var(--label-assist);margin-right:auto}.bp-koat .foot-links a{display:inline-flex;align-items:center;min-height:44px;color:var(--primary-strong);font-weight:600}.bp-koat .sec-fold{margin-top:34px}.bp-koat .sec-fold summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:10px;min-height:44px;font-size:1.125rem;font-weight:600}.bp-koat .sec-fold summary::before{content:"›";display:inline-grid;place-items:center;width:28px;height:28px;border-radius:8px;background:var(--blue-95);color:var(--primary);transition:transform .15s var(--ease)}.bp-koat .sec-fold[open] summary::before{transform:rotate(90deg)}.bp-koat .sec-fold .pair{margin-top:16px}.bp-koat .sec-fold .sec{margin-top:0}.bp-koat .kpi{position:relative;padding:18px 22px 17px;border-right:1px solid var(--line-alt)}.bp-koat .kpi:last-child{border-right:0}.bp-koat .kpi-lab{color:var(--label-alt);font-weight:600;font-size:.875rem}.bp-koat .kpi-val{display:flex;align-items:baseline;gap:6px;margin-top:9px}.bp-koat .kpi-num{font-size:2.25rem;line-height:1;font-weight:700}.bp-koat .kpi-unit{color:var(--label-alt);font-weight:600;font-size:.9375rem}.bp-koat .kpi-ctx{margin-top:7px;color:var(--label-alt);font-size:.75rem}.bp-koat .kpi.focal .kpi-num{color:var(--primary)}.bp-koat .kpi .tick{position:absolute;left:22px;top:0;width:26px;height:2px;background:var(--line-solid)}.bp-koat .kpi.focal .tick{background:var(--primary)}
.bp-koat .grid{margin-top:38px;display:grid;grid-template-columns:1.55fr 1fr;gap:34px;align-items:start}.bp-koat .panel{min-width:0}.bp-koat .shead{display:flex;align-items:baseline;gap:10px;margin-bottom:14px}.bp-koat .shead .meta{color:var(--label-alt);font-size:.8125rem}.bp-koat .badge{display:inline-flex;height:22px;padding:0 9px;align-items:center;border-radius:var(--radius-pill);background:var(--blue-95);color:var(--primary-strong);font-size:.75rem;font-weight:700}.bp-koat .frow{display:grid;grid-template-columns:110px 1fr;gap:16px;align-items:center;padding:10px 0;border-bottom:1px solid var(--line-alt)}.bp-koat .fstep{display:flex;flex-direction:column}.bp-koat .fstep .nm{font-weight:600;font-size:.9375rem}.bp-koat .fstep .rt{font-size:.6875rem;color:var(--label-assist)}.bp-koat .ftrack{position:relative;height:34px;border-radius:var(--radius-8);background:var(--fill-alt);overflow:hidden}.bp-koat .fbar{position:absolute;inset:0 auto 0 0;height:100%;border-radius:var(--radius-8);background:linear-gradient(90deg,var(--blue-50),var(--blue-45))}.bp-koat .fcount{position:absolute;top:50%;transform:translateY(-50%);left:14px;color:#fff;font-weight:700;font-size:.9375rem}.bp-koat .fcount.outside{color:var(--label-neutral)}.bp-koat .ritem{display:flex;gap:13px;padding:13px 10px;border-bottom:1px solid var(--line-alt);align-items:flex-start}.bp-koat .rmark{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;background:var(--blue-95);color:var(--primary)}.bp-koat .rbody{min-width:0;flex:1}.bp-koat .rtop{display:flex;gap:8px;flex-wrap:wrap}.bp-koat .rcompany{font-weight:600;font-size:.9375rem}.bp-koat .rtype{font-size:.6875rem;font-weight:700;padding:1px 7px;border-radius:var(--radius-pill);background:var(--fill-normal)}.bp-koat .rdetail{color:var(--label-alt);font-size:.8125rem;margin-top:3px;line-height:1.3}.bp-koat .rts{color:var(--label-assist);font-size:.6875rem;white-space:nowrap}
.bp-koat .tender-section{margin-top:32px}.bp-koat .table-wrap{overflow:hidden;border-top:1px solid var(--line-solid)}.bp-koat .tbl{width:100%;border-collapse:collapse}.bp-koat .tbl th{text-align:left;font-weight:600;font-size:.75rem;color:var(--label-alt);padding:12px 10px;border-bottom:1px solid var(--line-solid);white-space:nowrap}.bp-koat .tbl td{padding:15px 10px;border-bottom:1px solid var(--line-alt);font-size:.8125rem;vertical-align:middle}.bp-koat .tbl tr:hover{background:var(--fill-alt)}.bp-koat .tender-cell{min-width:260px}.bp-koat .tender-cell strong,.bp-koat .tender-cell small{display:block}.bp-koat .tender-cell strong{font-size:.875rem;line-height:1.3rem}.bp-koat .tender-cell small{margin-top:3px;color:var(--label-alt)}.bp-koat .state-tag{display:inline-flex;height:24px;align-items:center;padding:0 9px;border-radius:var(--radius-pill);font-size:.6875rem;font-weight:700;white-space:nowrap}.bp-koat .state-source-reviewed{background:var(--orange-95);color:var(--orange-39)}.bp-koat .state-source-found{background:var(--fill-strong);color:var(--label-neutral)}.bp-koat .due-tag{display:inline-flex;height:20px;align-items:center;margin-left:6px;padding:0 7px;border-radius:var(--radius-pill);font-size:.6875rem;font-weight:700;white-space:nowrap;vertical-align:middle}.bp-koat .due-open{background:var(--green-95);color:var(--green-40)}.bp-koat .due-closed{background:var(--fill-strong);color:var(--label-neutral)}.bp-koat .row-action{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 14px;border-radius:var(--radius-10);border:1px solid var(--line-normal);color:var(--primary-strong);font-weight:700;white-space:nowrap}.bp-koat .note{margin-top:18px;padding-top:16px;border-top:1px solid var(--line-alt);color:var(--label-assist);font-size:.75rem;line-height:1.55}
.bp-koat.detail{--maxw:1080px}[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:not(:has(.bp-koat)),[data-testid="stMainBlockContainer"] [data-testid="stExpander"],[data-testid="stMainBlockContainer"] [data-testid="stDownloadButton"]{width:100%!important;max-width:1080px;margin-left:auto;margin-right:auto;padding-left:32px;padding-right:32px;box-sizing:border-box;font-family:var(--font)}[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:not(:has(.bp-koat)) h3{font-size:1.125rem;font-weight:600;margin-top:34px;padding-left:0}[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:not(:has(.bp-koat)) p,[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:not(:has(.bp-koat)) li,[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:not(:has(.bp-koat)) label{font-size:.875rem}[data-testid="stMainBlockContainer"] [data-testid="stCheckbox"] label{min-height:44px;align-items:center}.bp-koat .topbar{position:sticky;top:0;z-index:40;border-bottom:1px solid var(--line-neutral);background:rgba(255,255,255,.72);backdrop-filter:saturate(180%) blur(32px)}.bp-koat .topbar::before{content:"";position:absolute;left:0;top:0;height:2px;width:100%;background:linear-gradient(90deg,var(--blue-50),var(--blue-45) 45%,transparent 92%)}.bp-koat .topbar-inner{max-width:1080px;margin:0 auto;padding:0 32px;height:60px;display:flex;align-items:center}.bp-koat .topbar .brand{font-size:.9375rem;font-weight:600}.bp-koat .topbar .mark{width:24px;height:24px;border-radius:7px;background:linear-gradient(145deg,var(--blue-50),var(--blue-40));display:grid;place-items:center;color:#fff}.bp-koat .detail-nav{display:flex;margin-left:auto;gap:4px}.bp-koat .detail-nav a{padding:7px 13px;border-radius:var(--radius-8);font-size:.875rem;color:var(--label-neutral)}.bp-koat .detail-nav a.current{color:var(--primary);background:var(--blue-95)}.bp-koat .detail-wrap{max-width:1080px;margin:0 auto;padding:30px 32px 64px}.bp-koat .crumb{display:flex;align-items:center;gap:7px;font-size:.8125rem;color:var(--label-alt);margin-bottom:18px}.bp-koat .idhead{position:relative;border:1px solid var(--line-neutral);border-radius:var(--radius-20);overflow:hidden;background:#fff;box-shadow:var(--shadow-sm)}.bp-koat .idhead::before{content:"";position:absolute;inset:0;background:radial-gradient(130% 120% at 0% 0%,var(--blue-95) 0%,rgba(234,242,254,0) 46%);opacity:.7}.bp-koat .idhead-top{position:relative;display:flex;gap:20px 28px;justify-content:space-between;align-items:flex-start;padding:26px 28px 22px}.bp-koat .id-left{min-width:0;display:flex;flex-direction:column;gap:11px}.bp-koat .id-eyebrow{display:flex;align-items:center;gap:7px;font-size:.75rem;font-weight:600;color:var(--primary-strong)}.bp-koat .id-eyebrow .pip{width:6px;height:6px;border-radius:50%;background:var(--primary)}.bp-koat .id-name h1{margin:0;font-size:1.875rem;line-height:2.375rem;letter-spacing:-.025em}.bp-koat .id-sub{display:flex;flex-wrap:wrap;gap:7px 16px;font-size:.875rem;color:var(--label-alt)}.bp-koat .id-right{display:flex;flex-direction:column;align-items:flex-end;gap:11px}.bp-koat .statechip{display:inline-flex;align-items:center;gap:8px;height:34px;padding:0 14px;border-radius:var(--radius-pill);font-size:.875rem;font-weight:700}.bp-koat .statechip .sd{width:8px;height:8px;border-radius:50%}.bp-koat .sc-orange{background:var(--orange-95);color:var(--orange-39)}.bp-koat .sc-orange .sd{background:var(--orange-50)}.bp-koat .sc-grey{background:var(--fill-strong);color:var(--label-neutral)}.bp-koat .sc-grey .sd{background:var(--cn-50)}.bp-koat .id-due{font-size:.8125rem;color:var(--label-alt)}.bp-koat .id-contract{position:relative;display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line-alt)}.bp-koat .id-cell{padding:15px 28px 17px;border-right:1px solid var(--line-alt)}.bp-koat .id-cell:last-child{border-right:0}.bp-koat .id-cell .k{display:block;font-size:.75rem;color:var(--label-alt);margin-bottom:5px}.bp-koat .id-cell .v{font-size:.9375rem}.bp-koat .id-cell .big{font-size:1.0625rem}.bp-koat .sec{margin-top:34px}.bp-koat .sec-head{display:flex;align-items:center;gap:11px;margin-bottom:16px}.bp-koat .sec-ic{width:28px;height:28px;border-radius:8px;display:grid;place-items:center;background:var(--blue-95);color:var(--primary)}.bp-koat .sec-title{font-size:1.125rem;font-weight:600}.bp-koat .pair{display:grid;grid-template-columns:1fr 1fr;gap:28px}.bp-koat.detail .panel{border:1px solid var(--line-neutral);border-radius:var(--radius-16);background:#fff;box-shadow:var(--shadow-xs);overflow:hidden}.bp-koat .panel-pad{padding:20px 22px}.bp-koat .timeline{list-style:none;margin:0;padding:4px 2px}.bp-koat .tl{display:grid;grid-template-columns:30px 1fr;gap:14px;padding-bottom:18px}.bp-koat .tl-rail{position:relative;display:flex;justify-content:center}.bp-koat .tl-rail::before{content:"";position:absolute;top:26px;bottom:-18px;width:2px;background:var(--line-solid)}.bp-koat .tl:last-child .tl-rail::before{display:none}.bp-koat .tl-node{z-index:1;width:30px;height:30px;border-radius:50%;display:grid;place-items:center;background:#fff;border:1.5px solid var(--line-solid);color:var(--label-assist);font-style:normal}.bp-koat .tl-top{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}.bp-koat .tl-lab{font-size:.9375rem}.bp-koat .tl-ts{font-size:.75rem;color:var(--label-assist)}.bp-koat .tl-detail{font-size:.8125rem;color:var(--label-alt);margin-top:3px}.bp-koat .evidence-panel>div{display:flex;justify-content:space-between;gap:14px;padding:16px 20px;border-bottom:1px solid var(--line-alt);font-size:.875rem}.bp-koat .evidence-panel>div:last-child{border-bottom:0}.bp-koat .evidence-panel span{color:var(--label-alt)}.bp-koat .evidence-panel a{color:var(--primary);font-weight:600}.bp-koat .an{display:grid;grid-template-columns:repeat(3,1fr)}.bp-koat .an-cell{padding:20px 22px;border-right:1px solid var(--line-alt)}.bp-koat .an-cell:last-child{border-right:0}.bp-koat .an-k{display:block;font-size:.8125rem;color:var(--label-alt);margin-bottom:9px}.bp-koat .an-v{font-size:1.875rem;line-height:1;font-weight:700}.bp-koat .an-v.flag{color:var(--orange-39)}.bp-koat .an-foot{padding:16px 22px;border-top:1px solid var(--line-alt);background:var(--bg-alt)}.bp-koat .an-why{margin-top:12px;font-size:.875rem;line-height:1.5;color:var(--label-neutral)}.bp-koat .an-why a,.bp-koat .kpi-ctx a{color:var(--primary);font-weight:700}.bp-koat .flagbadge{display:inline-flex;align-items:center;height:30px;padding:0 13px;border-radius:var(--radius-pill);background:var(--orange-95);color:var(--orange-39);font-size:.8125rem;font-weight:700}.bp-koat .state-panel{padding:24px 22px}.bp-koat .state-panel p{margin-top:6px;color:var(--label-alt);font-size:.875rem}.bp-koat .work-list{list-style:none;margin:0;padding:0}.bp-koat .work-item{display:grid;grid-template-columns:28px minmax(0,1fr) 120px;gap:12px;align-items:center;padding:14px 20px;border-bottom:1px solid var(--line-alt)}.bp-koat .work-no{width:24px;height:24px;border-radius:7px;display:grid;place-items:center;background:var(--blue-95);color:var(--primary);font-size:.75rem}.bp-koat .work-item small{color:var(--label-alt)}.bp-koat .work-empty{padding:24px 20px;color:var(--label-alt)}.bp-koat .replay-panel{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:20px 22px}.bp-koat .replay-panel p{margin-top:5px;color:var(--label-alt);font-size:.8125rem}.bp-koat .replay-panel a{color:var(--primary);font-size:.875rem;font-weight:700}
@media(max-width:992px){.bp-koat .grid{grid-template-columns:1fr}.bp-koat .pair{grid-template-columns:1fr}}
@media(max-width:768px){[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:not(:has(.bp-koat)),[data-testid="stMainBlockContainer"] [data-testid="stExpander"],[data-testid="stMainBlockContainer"] [data-testid="stDownloadButton"]{padding-left:18px;padding-right:18px}.bp-koat .nav-in,.bp-koat .topbar-inner{padding:0 18px;gap:14px}.bp-koat .brand-sub,.bp-koat .brand .sub{display:none}.bp-koat .wrap,.bp-koat .detail-wrap{padding:26px 18px 44px}.bp-koat .causal-flow{grid-template-columns:1fr 1fr}.bp-koat .causal-flow span{border-bottom:1px solid var(--line-neutral)}.bp-koat .causal-flow span:nth-child(2n){border-right:0}.bp-koat .tool-links{align-items:stretch;flex-direction:column}.bp-koat .tool-links::before{margin:2px 0 0}.bp-koat .tool-links a{width:100%}.bp-koat .kpi-band{grid-template-columns:repeat(2,1fr)}.bp-koat .kpi:nth-child(2n){border-right:0}.bp-koat .table-wrap{overflow:visible}.bp-koat .tender-table thead{display:none}.bp-koat .tender-table,.bp-koat .tender-table tbody,.bp-koat .tender-table tr,.bp-koat .tender-table td{display:block;width:100%}.bp-koat .tender-table tr{padding:12px 0;border-bottom:1px solid var(--line-neutral)}.bp-koat .tender-table td{display:flex;justify-content:space-between;gap:16px;border:0;padding:6px 0;text-align:right}.bp-koat .tender-table td::before{content:attr(data-label);color:var(--label-alt);font-weight:500}.bp-koat .tender-table .tender-cell{display:block;text-align:left}.bp-koat .tender-table .tender-cell::before{display:none}.bp-koat .idhead-top{padding:22px 20px 18px;flex-wrap:wrap}.bp-koat .id-name h1{font-size:1.5rem;line-height:2rem}.bp-koat .id-right{align-items:flex-start;width:100%}.bp-koat .id-contract{grid-template-columns:1fr 1fr}.bp-koat .id-cell{border-bottom:1px solid var(--line-alt)}.bp-koat .id-cell:nth-child(2n){border-right:0}.bp-koat .an{grid-template-columns:1fr}.bp-koat .an-cell{border-right:0;border-bottom:1px solid var(--line-alt)}.bp-koat .work-item{grid-template-columns:28px minmax(0,1fr)}.bp-koat .work-item small{grid-column:2}.bp-koat .replay-panel{display:block}.bp-koat .replay-panel a{display:inline-block;margin-top:14px}}
@media(max-width:480px){.bp-koat .nav-acct{display:none}.bp-koat .nav-link{padding:8px}.bp-koat .phead{align-items:stretch}.bp-koat .controls{width:100%;overflow-x:auto}.bp-koat .kpi-num{font-size:1.875rem}.bp-koat .frow{grid-template-columns:90px 1fr}.bp-koat .rts{display:none}.bp-koat .detail-nav a:first-child{display:none}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style>"""


def shell_css() -> str:
    """Return scoped WDS-informed styles with the document as scroll owner."""
    return """<style>
@import url("https://static.wanted.co.kr/fonts/wantedsans/WantedSansVariable.min.css");
:root {
  --semantic-primary-normal:#0066FF;
  --semantic-label-normal:#171719;
  --semantic-background-normal-normal:#ffffff;
  --semantic-line-normal-normal:rgba(112,115,124,.22);
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
html, body { height: auto !important; overflow-y: auto !important; overflow-x:hidden !important; }
[data-testid="stApp"], .stApp { height:auto !important; min-height:100vh !important; overflow:visible !important; }
[data-testid="stAppViewContainer"], section.stMain, [data-testid="stMain"] {
  height: auto !important; overflow: visible !important;
}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stAppToolbar"],
[data-testid="stDecoration"],[data-testid="stStatusWidget"] {
  display:none !important; visibility:hidden !important; height:0 !important;
}
[data-testid="stSkeleton"],.stSkeleton { display:none !important; }
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
.bpw-overview { max-width:1136px; margin:0 auto; color:var(--bpw-ink); font-family:var(--bpw-font); }
.bpw-dashboard-head { padding:38px 0 26px; }
.bpw-dashboard-head h1 { margin:7px 0 6px; font-size:38px; line-height:46px; letter-spacing:-.035em; }
.bpw-dashboard-head p:last-child { margin:0; color:var(--bpw-muted); font-size:14px; line-height:21px; }
.bpw-overview-nav { display:flex; align-items:center; justify-content:space-between; min-height:48px;
  padding:0 0 16px; border-bottom:1px solid var(--bpw-line-soft); }
.bpw-overview-brand { display:flex; align-items:center; gap:10px; color:var(--bpw-ink); text-decoration:none; }
.bpw-overview-brand__mark { width:30px; height:30px; display:grid; place-items:center; border-radius:9px;
  color:#fff; background:var(--semantic-primary-normal); font-size:14px; font-weight:700;
  box-shadow:0 5px 14px -5px rgba(0,102,255,.62); }
.bpw-overview-brand strong,.bpw-overview-brand small { display:block; }
.bpw-overview-brand strong { font-size:15px; line-height:19px; letter-spacing:-.02em; }
.bpw-overview-brand small { color:var(--bpw-muted); font-size:10px; line-height:13px; }
.bpw-overview-nav__state { display:inline-flex; align-items:center; gap:7px; color:var(--bpw-muted);
  font-size:12px; font-weight:600; }
.bpw-overview-nav__state i { width:7px; height:7px; border-radius:50%; background:var(--bpw-green);
  box-shadow:0 0 0 4px var(--bpw-green-bg); }
.bpw-overview-head { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:32px; align-items:end;
  padding:38px 0 28px; }
.bpw-overview-head h1 { max-width:850px; margin:8px 0 10px; font-size:clamp(28px,3.1vw,42px);
  line-height:1.18; letter-spacing:-.035em; font-weight:700; text-wrap:balance; }
.bpw-overview-meta { display:flex; flex-wrap:wrap; gap:5px 18px; margin:0; color:var(--bpw-muted);
  font-size:13px; line-height:19px; }
.bpw-supplier-note { display:flex; align-items:center; gap:7px; margin:14px 0 0; color:var(--bpw-neutral);
  font-size:12px; line-height:17px; font-weight:600; }
.bpw-supplier-note span { width:6px; height:6px; border-radius:50%; background:var(--bpw-orange); }
.bpw-primary-cta { display:inline-flex; align-items:center; justify-content:center; gap:12px; min-height:48px;
  padding:0 20px; border-radius:12px; color:#fff !important; background:var(--semantic-primary-normal);
  box-shadow:0 6px 18px -7px rgba(0,102,255,.7); font-size:14px; font-weight:650; text-decoration:none !important;
  white-space:nowrap; transition:background 180ms ease,transform 180ms ease; }
.bpw-primary-cta b,.bpw-primary-cta small { display:block; }
.bpw-primary-cta b { font-weight:650; }
.bpw-primary-cta small { margin-top:1px; color:rgba(255,255,255,.74); font-size:9px; line-height:12px; font-weight:500; }
.bpw-primary-cta:hover { background:var(--bpw-blue-strong); transform:translateY(-1px); }
.bpw-overview-metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); overflow:hidden;
  border-top:1px solid var(--bpw-line); border-bottom:1px solid var(--bpw-line); background:#fff; }
.bpw-overview-metric { min-width:0; min-height:134px; padding:22px; border-left:1px solid var(--bpw-line-soft); }
.bpw-overview-metric:first-child { border-left:0; }
.bpw-overview-metric::before { content:""; display:block; width:24px; height:2px; margin:-22px 0 20px;
  background:var(--bpw-line); }
.bpw-overview-metric--decision::before { background:var(--bpw-orange); }
.bpw-overview-metric p { margin:0 0 8px; color:var(--bpw-muted); font-size:11px; line-height:16px; font-weight:600; }
.bpw-overview-metric strong { display:block; color:var(--bpw-ink); font-size:24px; line-height:30px;
  letter-spacing:-.025em; overflow-wrap:anywhere; }
.bpw-overview-metric--decision strong { color:var(--bpw-orange); font-size:32px; line-height:36px; }
.bpw-overview-metric strong small { display:inline; color:var(--bpw-muted); font-size:12px; font-weight:500; }
.bpw-overview-metric > small,.bpw-overview-metric > span { display:block; margin-top:6px; color:var(--bpw-muted);
  font-size:11px; line-height:16px; }
.bpw-overview-proof { display:flex; justify-content:space-between; gap:16px 28px; padding:12px 16px;
  border-bottom:1px solid var(--bpw-line-soft); color:var(--bpw-muted); font-size:11px; line-height:16px; }
.bpw-overview-proof b { color:var(--bpw-neutral); margin-right:6px; font-weight:650; }
.bpw-flow { display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); margin:36px 0 0; padding:0;
  list-style:none; border-top:1px solid var(--bpw-line-soft); border-bottom:1px solid var(--bpw-line-soft); }
.bpw-flow-step { position:relative; min-width:0; min-height:74px; padding:14px 12px; border-left:1px solid var(--bpw-line-soft); }
.bpw-flow-step:first-child { border-left:0; }
.bpw-flow-step span { display:block; margin-bottom:7px; color:var(--bpw-blue); font-size:10px; line-height:13px; font-weight:700; }
.bpw-flow-step strong { display:block; color:var(--bpw-neutral); font-size:12px; line-height:17px; font-weight:650; }
.bpw-overview-foot { display:flex; justify-content:space-between; align-items:center; gap:20px; padding:18px 0; }
.bpw-overview-foot p { margin:0; color:var(--bpw-muted); font-size:12px; line-height:17px; }
.bpw-overview-foot a { min-height:44px; display:inline-flex; align-items:center; color:var(--bpw-blue-strong);
  font-size:12px; line-height:17px; font-weight:650; text-decoration:none; white-space:nowrap; }
.bpw-opportunities { margin-top:42px; }
.bpw-opportunities__head { display:flex; justify-content:space-between; align-items:end; gap:18px;
  margin-bottom:14px; }
.bpw-opportunities__head h2 { margin:0; font-size:20px; line-height:28px; letter-spacing:-.02em; }
.bpw-opportunities__head p,.bpw-opportunities__head > span { margin:3px 0 0; color:var(--bpw-muted);
  font-size:12px; line-height:17px; }
.bpw-opportunity-card { overflow:hidden; border:1px solid var(--bpw-line); border-radius:16px; background:#fff;
  box-shadow:0 1px 2px -1px rgba(23,23,23,.1); }
.bpw-opportunity-card__title { display:flex; justify-content:space-between; gap:18px; align-items:start; padding:22px; }
.bpw-opportunity-card__title p { margin:0 0 6px; color:var(--bpw-blue-strong); font-size:11px; line-height:16px;
  font-weight:650; text-transform:uppercase; letter-spacing:.08em; }
.bpw-opportunity-card__title h3 { max-width:850px; margin:0; font-size:21px; line-height:29px; letter-spacing:-.02em; }
.bpw-opportunity-facts { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); margin:0;
  border-top:1px solid var(--bpw-line-soft); border-bottom:1px solid var(--bpw-line-soft); }
.bpw-opportunity-facts > div { min-width:0; padding:15px 18px; border-left:1px solid var(--bpw-line-soft); }
.bpw-opportunity-facts > div:first-child { border-left:0; }
.bpw-opportunity-facts dt { color:var(--bpw-muted); font-size:10px; line-height:14px; text-transform:uppercase;
  letter-spacing:.08em; }
.bpw-opportunity-facts dd { margin:5px 0 0; color:var(--bpw-neutral); font-size:13px; line-height:18px; font-weight:600; }
.bpw-opportunity-card__foot { display:flex; justify-content:space-between; align-items:center; gap:20px; padding:16px 20px; }
.bpw-opportunity-card__foot small { display:block; margin-top:3px; color:var(--bpw-muted); font-size:11px; }
.bpw-opportunity-card__foot .bpw-supplier-note { margin:0; }
.bpw-opportunities__empty { margin:14px 2px 0; color:var(--bpw-muted); font-size:11px; line-height:16px; }
.bpw-detail-head { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:26px; align-items:end; padding:38px 0 26px; }
.bpw-detail-head h1 { max-width:850px; margin:7px 0 7px; font-size:34px; line-height:43px; letter-spacing:-.035em; }
.bpw-detail-head p:last-child { margin:0; color:var(--bpw-muted); font-size:13px; }
.bpw-detail-verdict { display:flex; flex-direction:column; align-items:flex-end; color:var(--bpw-orange);
  font-size:26px; line-height:32px; font-weight:700; }
.bpw-detail-verdict small { color:var(--bpw-muted); font-size:10px; line-height:14px; font-weight:500; }
.bpw-detail-section { margin-top:40px; }
.bpw-detail-section > header { display:grid; grid-template-columns:28px minmax(0,1fr); gap:10px; align-items:baseline;
  padding-bottom:11px; margin-bottom:12px; border-bottom:1px solid var(--bpw-line); }
.bpw-detail-section > header span { color:var(--bpw-blue); font-size:11px; font-weight:700; }
.bpw-detail-section > header h2 { margin:0; font-size:18px; line-height:25px; }
.bpw-detail-rows > div { display:grid; grid-template-columns:170px minmax(0,1fr) auto; gap:18px; align-items:center;
  min-height:62px; padding:11px 4px; border-bottom:1px solid var(--bpw-line-soft); }
.bpw-detail-rows p { margin:0; color:var(--bpw-neutral); font-size:13px; line-height:19px; }
.bpw-detail-rows em { color:var(--bpw-muted); font-size:11px; font-style:normal; }
.bpw-detail-empty { padding:22px; border:1px solid var(--bpw-line-soft); border-radius:12px; background:var(--bpw-surface); }
.bpw-detail-empty strong { font-size:14px; }
.bpw-detail-empty p { margin:5px 0 0; color:var(--bpw-muted); font-size:12px; line-height:18px; }
.bpw-detail-worklist { margin:0; padding:0; list-style:none; }
.bpw-detail-work { display:grid; grid-template-columns:28px minmax(0,1fr) 120px; gap:12px; align-items:center;
  min-height:62px; padding:11px 4px; border-bottom:1px solid var(--bpw-line-soft); }
.bpw-detail-work > span { width:24px; height:24px; display:grid; place-items:center; border-radius:7px;
  color:var(--bpw-blue-strong); background:var(--bpw-blue-95); font-size:10px; font-weight:700; }
.bpw-detail-work p { margin:0; font-size:13px; line-height:19px; }
.bpw-detail-work small { color:var(--bpw-muted); font-size:11px; }
.bpw-detail-proof { display:flex; justify-content:space-between; align-items:center; gap:20px; padding:18px;
  border:1px solid var(--bpw-line-soft); border-radius:12px; }
.bpw-detail-proof p { margin:5px 0 0; color:var(--bpw-muted); font-size:11px; }
.bpw-detail-proof code { overflow-wrap:anywhere; }
.bpw-detail-proof a,.bpw-detail-foot a { min-height:44px; display:inline-flex; align-items:center; color:var(--bpw-blue-strong);
  font-size:12px; font-weight:650; text-decoration:none; }
.bpw-detail-foot { display:flex; justify-content:flex-end; padding:18px 0 0; }
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
.bpw-path__value--positive { color:var(--bpw-green); }
.bpw-path__value--negative { color:var(--bpw-red); }
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
  .bpw-overview-head { align-items:start; }
  .bpw-overview-metrics { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .bpw-overview-metric:nth-child(3) { border-left:0; border-top:1px solid var(--bpw-line-soft); }
  .bpw-overview-metric:nth-child(4) { border-top:1px solid var(--bpw-line-soft); }
  .bpw-flow { grid-template-columns:repeat(3,minmax(0,1fr)); }
  .bpw-flow-step:nth-child(4) { border-left:0; border-top:1px solid var(--bpw-line-soft); }
  .bpw-flow-step:nth-child(n+4) { border-top:1px solid var(--bpw-line-soft); }
  .bpw-opportunity-facts { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .bpw-opportunity-facts > div:nth-child(3) { border-left:0; border-top:1px solid var(--bpw-line-soft); }
  .bpw-opportunity-facts > div:nth-child(4) { border-top:1px solid var(--bpw-line-soft); }
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
  .bpw-overview-nav { padding-top:2px; }
  .bpw-overview-head { display:block; padding:28px 0 22px; }
  .bpw-overview-head h1 { font-size:27px; line-height:34px; text-wrap:pretty; }
  .bpw-primary-cta { width:100%; margin-top:22px; }
  .bpw-overview-metrics { grid-template-columns:minmax(0,1fr); }
  .bpw-overview-metric,.bpw-overview-metric:nth-child(3),.bpw-overview-metric:nth-child(4) {
    min-height:0; padding:18px 4px; border-left:0; border-top:1px solid var(--bpw-line-soft); }
  .bpw-overview-metric:first-child { border-top:0; }
  .bpw-overview-metric::before { display:none; }
  .bpw-overview-metric strong { font-size:21px; line-height:27px; }
  .bpw-overview-metric--decision strong { font-size:28px; line-height:34px; }
  .bpw-overview-proof { display:grid; padding:12px 4px; }
  .bpw-flow { display:grid; grid-template-columns:minmax(0,1fr); margin-top:28px; }
  .bpw-flow-step,.bpw-flow-step:nth-child(4),.bpw-flow-step:nth-child(n+4) { display:grid;
    grid-template-columns:24px minmax(0,1fr); align-items:center; min-height:44px; padding:8px 4px;
    border-left:0; border-top:1px solid var(--bpw-line-soft); }
  .bpw-flow-step:first-child { border-top:0; }
  .bpw-flow-step span { margin:0; }
  .bpw-overview-foot { align-items:flex-start; }
  .bpw-dashboard-head h1 { font-size:30px; line-height:38px; }
  .bpw-opportunities { margin-top:34px; }
  .bpw-opportunity-card__title,.bpw-opportunity-card__foot { display:block; padding:18px; }
  .bpw-opportunity-card__title .bpw-badge { margin-top:12px; }
  .bpw-opportunity-facts { grid-template-columns:minmax(0,1fr); }
  .bpw-opportunity-facts > div,.bpw-opportunity-facts > div:nth-child(3),.bpw-opportunity-facts > div:nth-child(4) {
    border-left:0; border-top:1px solid var(--bpw-line-soft); }
  .bpw-opportunity-facts > div:first-child { border-top:0; }
  .bpw-opportunity-card__foot .bpw-primary-cta { margin-top:16px; }
  .bpw-detail-head { display:block; padding:28px 0 22px; }
  .bpw-detail-head h1 { font-size:27px; line-height:34px; }
  .bpw-detail-verdict { align-items:flex-start; margin-top:16px; }
  .bpw-detail-rows > div { grid-template-columns:minmax(0,1fr) auto; gap:5px 10px; }
  .bpw-detail-rows p { grid-column:1 / -1; }
  .bpw-detail-work { grid-template-columns:28px minmax(0,1fr); }
  .bpw-detail-work small { grid-column:2; }
  .bpw-detail-proof { display:block; }
  .bpw-detail-proof a { margin-top:12px; }
}
@media (prefers-reduced-motion: reduce) {
  *,*::before,*::after { animation-duration:.01ms !important; animation-iteration-count:1 !important;
    transition-duration:.01ms !important; scroll-behavior:auto !important; }
}
</style>"""
