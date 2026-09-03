"""Contract tests for the three-workspace refinement shell.

The shell is deliberately tested as deterministic HTML before it is wired to
Streamlit state or a Snowflake reader.  This keeps presentation assertions
independent of credentials and prevents the synthetic workspace from gaining
persisted-run actions by accident.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from bidpilot.tender_catalog import load_public_tender_catalog
from bidpilot.ui_components import decision_path, state_panel
from bidpilot.workspace_ui import (
    SYNTHETIC_BOUNDARY,
    UI_STATES,
    WORKSPACES,
    bid_room_first_viewport,
    judge_overview,
    judge_tender_detail,
    koat_css,
    koat_dashboard,
    koat_tender_detail,
    shell_css,
    synthetic_simulation_first_viewport,
    tender_intake_first_viewport,
    workspace_navigation,
    workspace_route_navigation,
)

FINALE_CLOCK = datetime.fromisoformat("2026-09-03T15:40:00+09:00")


def test_workspace_navigation_preserves_the_required_three_workspace_boundary() -> None:
    assert [(item.key, item.label) for item in WORKSPACES] == [
        ("tender-intake", "Tender Intake"),
        ("bid-room", "Authenticated Snowflake Bid Room"),
        ("synthetic-simulation", "Synthetic Decision Simulation"),
    ]

    markup = workspace_navigation("bid-room")

    assert 'aria-label="BidPilot workspaces"' in markup
    assert 'data-workspace="bid-room" aria-current="page"' in markup
    assert "bpw-mobile-workspace" in markup
    assert markup.count("Tender Intake") == 2
    assert markup.count("Authenticated Snowflake Bid Room") == 2
    assert markup.count("Synthetic Decision Simulation") == 2


def test_shell_uses_one_document_scroll_owner_and_compacts_navigation_on_mobile() -> (
    None
):
    css = shell_css()

    assert "html, body" in css
    assert "overflow-y: auto" in css
    assert "section.stMain" in css
    assert "overflow: visible" in css
    assert "height: auto" in css
    assert "@media (max-width: 760px)" in css
    assert ".bpw-desktop-workspaces" in css
    assert ".bpw-mobile-workspace" in css
    assert "prefers-reduced-motion: reduce" in css
    assert "height: 100vh" not in css
    assert "overflow-y: scroll" not in css


def test_koat_pages_release_streamlits_fixed_height_scroll_container() -> None:
    css = koat_css()

    assert ".stApp" in css
    assert "min-height:100vh!important" in css
    assert "overflow:visible!important" in css


def test_tender_intake_first_viewport_reads_source_to_next_review_action() -> None:
    markup = tender_intake_first_viewport(
        source_title="K패스 기반 수원시 사회초년생 청년 교통비 지원사업",
        official_status="Official G2B notice",
        digest="d196bed74cc6…476c",
        extraction_state="Notice facts extracted · operator review required",
        evaluation_total="Technical 90 · Price 10",
        next_action="Review eligibility evidence",
    )

    expected_order = (
        "Official source",
        "Content digest",
        "Extraction state",
        "Evaluation map",
        "Supplier boundary",
        "Next review action",
    )
    assert all(label in markup for label in expected_order)
    assert [markup.index(label) for label in expected_order] == sorted(
        markup.index(label) for label in expected_order
    )
    assert "Synthetic demo supplier profile" in markup
    assert "operator review required" in markup


def test_bid_room_first_viewport_connects_decision_weight_evidence_and_action() -> None:
    markup = bid_room_first_viewport(
        verdict="REVIEW — evidence required",
        principal_reason="A comparable-delivery proof is not recorded.",
        criterion="Technical approach",
        official_weight="35 points",
        evidence_state="1 cited · 1 open gap",
        selected_position="Evidence-led service continuity",
        owner="Proposal lead",
        next_action="Attach comparable-delivery evidence",
        run_id="refine-suwon-001",
    )

    expected_order = ("Decision", "Official weight", "Evidence state", "Owned action")
    assert [markup.index(label) for label in expected_order] == sorted(
        markup.index(label) for label in expected_order
    )
    assert "REVIEW — evidence required" in markup
    assert "35 points" in markup
    assert "Evidence-led service continuity" in markup
    assert "Proposal lead" in markup
    assert "refine-suwon-001" in markup


def test_synthetic_simulation_is_explicitly_local_and_has_no_persisted_actions() -> (
    None
):
    markup = synthetic_simulation_first_viewport(
        verdict="NO-GO",
        reason="Required certification is absent from the scenario.",
    )

    assert SYNTHETIC_BOUNDARY in markup
    assert "Scenario result" in markup
    assert "NO-GO" in markup
    for forbidden in ("Publish", "Sync", "Create run", "Save to Snowflake"):
        assert forbidden not in markup


@pytest.mark.parametrize("state", sorted(UI_STATES))
def test_all_product_states_are_explicit_and_recovery_is_reachable(state: str) -> None:
    markup = state_panel(
        state,
        title=f"{state.title()} state",
        detail="State-specific explanation.",
        recovery_label="Try again" if state in {"error", "disconnected"} else None,
        recovery_href="?retry=1" if state in {"error", "disconnected"} else None,
    )

    assert f'data-state="{state}"' in markup
    assert "State-specific explanation." in markup
    if state in {"error", "disconnected"}:
        assert 'role="alert"' in markup
        assert 'href="?retry=1"' in markup
    else:
        assert 'role="status"' in markup


def test_render_atoms_escape_untrusted_source_and_supplier_text() -> None:
    markup = decision_path(
        [
            ("Decision", '<script>alert("source")</script>', "Check"),
            ("Official weight", "35", "points"),
            ("Evidence state", "Open", "Supplier <unknown>"),
            ("Owned action", "Review", "Proposal lead"),
        ]
    )

    assert "<script>" not in markup
    assert "&lt;script&gt;" in markup
    assert "Supplier &lt;unknown&gt;" in markup


def test_navigation_rejects_an_unknown_workspace() -> None:
    with pytest.raises(ValueError, match="Unknown workspace"):
        workspace_navigation("invented")


def test_integrated_route_navigation_needs_no_streamlit_sidebar_or_inline_script() -> (
    None
):
    markup = workspace_route_navigation("bid-room")

    assert 'aria-label="BidPilot workspace routes"' in markup
    assert 'class="bpw-route-desktop"' in markup
    assert 'class="bpw-route-mobile"' in markup
    assert "<details" in markup
    assert "<summary" in markup
    assert 'href="?workspace=tender-intake"' in markup
    assert 'href="?workspace=bid-room" aria-current="page"' in markup
    assert 'href="?workspace=synthetic-simulation"' in markup
    assert "onchange=" not in markup
    assert "stSidebar" not in markup


def test_integrated_navigation_reflows_without_reserving_a_tablet_sidebar() -> None:
    css = shell_css()

    assert ".bpw-route-desktop" in css
    assert ".bpw-route-mobile" in css
    assert "grid-template-columns:repeat(3,minmax(0,1fr))" in css
    assert ".stMainBlockContainer, .block-container" in css
    assert "max-width:1240px !important" in css
    assert "padding:20px 24px 96px !important" in css
    assert "@media (max-width: 760px)" in css
    assert ".bpw-route-desktop { display:none; }" in css
    assert ".bpw-route-mobile { display:block;" in css


def test_judge_overview_is_a_source_backed_opportunity_dashboard() -> None:
    markup = judge_overview(
        notice_number="R26BK01680611-000",
        title="K-pass youth transport support service",
        issuer="Suwon City",
        deadline="2026-09-03 16:00 KST",
        contract_value="KRW 250M",
        technical_weight="90",
        price_weight="10",
        supplier_boundary="Synthetic demo supplier profile",
        eligibility_count="4",
        source_url="https://example.com/notice.pdf",
    )

    assert 'data-surface="judge-overview"' in markup
    assert markup.count('class="bpw-primary-cta"') == 1
    assert 'href="?tender=R26BK01680611-000"' in markup
    for value in (
        "Pursuit dashboard",
        "Verified public sources",
        "Pursuit funnel",
        "Recent activity",
        "Source-backed opportunities",
        "R26BK01680611-000",
        "REVIEW",
        "Synthetic demo supplier profile",
        "4 eligibility requirements",
        "Open pursuit review",
    ):
        assert value in markup
    for column in (
        "Tender",
        "Issuer",
        "Value",
        "Deadline",
        "Weights",
        "Status",
        "Action",
    ):
        assert f">{column}<" in markup
    for forbidden in (
        "Workspace 01",
        "Workspace 02",
        "least-privilege",
        "Reader authenticated",
        "Analysis history",
        "LOCAL SYNTHETIC SIMULATION",
    ):
        assert forbidden not in markup


def test_judge_overview_css_uses_wds_tokens_and_responsive_named_stages() -> None:
    css = shell_css()

    assert "--semantic-primary-normal:#0066FF" in css
    assert ".bpw-overview-metrics" in css
    assert ".bpw-flow-step strong" in css
    assert "@media (max-width: 760px)" in css
    assert "overflow-x:hidden" in css
    assert '[data-testid="stSkeleton"]' in css


def test_selected_real_tender_stops_before_an_unrecorded_run() -> None:
    markup = judge_tender_detail(
        notice_number="R26BK01680611-000",
        title="K-pass youth transport support service",
        issuer="Suwon City",
        deadline="2026-09-03 16:00 KST",
        contract_value="KRW 250M",
        delivery_term="Through 2026-12-31",
        technical_weight="90",
        price_weight="10",
        supplier_boundary="Synthetic demo supplier profile",
        eligibility_requirements=("Requirement A", "Requirement B"),
        source_digest="abc…123",
        source_url="https://example.com/notice.pdf",
    )

    assert 'data-surface="tender-detail"' in markup
    expected_order = (
        "Decision rationale",
        "Score-weighted Win Position",
        "Proposal & red-team result",
        "Owned work",
        "Snowflake proof",
    )
    assert [markup.index(label) for label in expected_order] == sorted(
        markup.index(label) for label in expected_order
    )
    assert "No run created for this notice" in markup
    assert "View separate verified capability replay" in markup
    assert "PURSUE" not in markup


def test_lean_koat_dashboard_shows_two_kpis_the_table_and_one_replay_button() -> None:
    markup = koat_dashboard(load_public_tender_catalog(), now=FINALE_CLOCK)

    for css_class in ("nav-in", "kpi-band", "tbl tender-table", "primary-cta"):
        assert css_class in markup
    assert (
        markup.count('<div class="kpi focal">') + markup.count('<div class="kpi">') == 2
    )
    for label in ("Needs review", "Open deadlines"):
        assert label in markup
    for gone in (
        'kpi-lab">Public sources',
        'kpi-lab">PURSUE',
        "Pursuit funnel",
        "Recent activity",
        'class="causal"',
        'class="tool-links"',
        'class="grid"',
    ):
        assert gone not in markup
    assert markup.count("<tr>") == 7
    assert markup.count('state-source-found">SOURCE FOUND</span>') == 5
    assert "R26BK01680611-000" in markup
    assert ">—<" in markup


def test_lean_koat_dashboard_reads_replay_button_then_table_then_footer_links() -> None:
    markup = koat_dashboard(load_public_tender_catalog(), now=FINALE_CLOCK)

    cta_at = markup.index('class="primary-cta" href="?walkthrough=1"')
    table_at = markup.index('<section class="tender-section">')
    first_row_action = markup.index('class="row-action"')
    footer_at = markup.index('class="foot-links"')
    assert cta_at < table_at < first_row_action < footer_at
    assert markup.index('href="?workspace=tender-intake"') > footer_at
    assert markup.index('href="?workspace=synthetic-simulation"') > footer_at
    assert markup.index('href="?workspace=bid-room"') > footer_at
    assert "Open verified PURSUE replay" in markup


def test_literal_koat_detail_keeps_public_tender_and_historical_replay_separate() -> (
    None
):
    rows = load_public_tender_catalog()
    reviewed = rows[0]
    found = rows[1]
    reviewed_view = {
        "eligibility_requirements": ("Requirement A", "Requirement B"),
    }

    detail = koat_tender_detail(reviewed, now=FINALE_CLOCK, reviewed_view=reviewed_view)
    discovered = koat_tender_detail(found, now=FINALE_CLOCK)

    for css_class in (
        "topbar-inner",
        "idhead",
        "id-contract",
        "timeline",
        "an",
        "panel",
    ):
        assert css_class in detail
    assert "REVIEW" in detail
    assert "No Snowflake run for this notice" in detail
    assert "separate synthetic fixture" in detail
    assert "SOURCE FOUND" in discovered
    assert "Supplier evidence required" not in discovered


def test_literal_koat_css_locks_source_container_widths_and_breakpoints() -> None:
    css = koat_css()

    assert "max-width:1200px" in css
    assert "max-width:1080px" in css
    assert "@media(max-width:768px)" in css
    assert '[data-testid="stElementContainer"]:not(:has(.bp-koat))' in css
    assert "grid-template-columns:repeat(4,1fr)" in css


def test_dashboard_never_lists_a_passed_deadline_as_due_soon() -> None:
    rows = load_public_tender_catalog()

    markup = koat_dashboard(rows, now=FINALE_CLOCK)

    assert "Due soon" not in markup
    assert "After 24 Aug 2026" not in markup
    assert markup.count('class="due-tag due-closed">Closed<') == 5
    assert markup.count('class="due-tag due-open">Open<') == 1
    assert "Open deadlines" in markup
    assert '<strong class="kpi-num">1</strong><span class="kpi-unit">notice' in markup
    assert "2026.09.03 · 15:40 KST" in markup

    later = datetime.fromisoformat("2026-09-10T00:00:00+00:00")
    markup = koat_dashboard(rows, now=later)

    assert markup.count('class="due-tag due-closed">Closed<') == 6
    assert "due-open" not in markup
    assert "All deadlines passed" in markup
    assert "historical public sources" in markup.lower()


def test_dashboard_and_detail_name_the_deadline_timezone() -> None:
    rows = load_public_tender_catalog()

    dashboard = koat_dashboard(rows, now=FINALE_CLOCK)
    reviewed = koat_tender_detail(rows[0], now=FINALE_CLOCK, reviewed_view=None)
    closed = koat_tender_detail(rows[1], now=FINALE_CLOCK)

    assert "2026.09.03 · 16:00 KST" in dashboard
    assert "2026.09.03 · 16:00 KST" in reviewed
    assert 'class="due-tag due-open">Open<' in reviewed
    assert "2026.09.02 · 10:00 KST" in closed
    assert 'class="due-tag due-closed">Closed<' in closed
    assert "REVIEW" in reviewed


def test_detail_offers_the_verified_replay_before_the_long_scroll() -> None:
    rows = load_public_tender_catalog()
    reviewed_view = {"eligibility_requirements": ("A", "B", "C", "D")}

    detail = koat_tender_detail(rows[0], now=FINALE_CLOCK, reviewed_view=reviewed_view)

    top_nav = detail.index('class="detail-nav"')
    history = detail.index("Processing history")
    first_replay_link = detail.index('href="?walkthrough=1"')
    assert top_nav < first_replay_link < history
    assert "REVIEW is the correct outcome" in detail
    assert "4 eligibility requirements" in detail
    summary = detail.index("Decision summary")
    win_position = detail.index("Score-weighted Win Position")
    assert summary < detail.index("REVIEW is the correct outcome") < win_position
    assert detail.count('href="?walkthrough=1"') >= 3


def test_dashboard_offers_exactly_one_primary_replay_button() -> None:
    markup = koat_dashboard(load_public_tender_catalog(), now=FINALE_CLOCK)

    assert markup.count('class="primary-cta"') == 1
    assert markup.count('href="?walkthrough=1"') == 2  # top nav + table button


def test_lean_detail_folds_history_and_source_evidence_under_the_decision() -> None:
    rows = load_public_tender_catalog()

    detail = koat_tender_detail(
        rows[0], now=FINALE_CLOCK, reviewed_view={"eligibility_requirements": ("A",)}
    )

    fold_at = detail.index('<details class="sec-fold">')
    assert detail.index("<summary") > fold_at
    assert fold_at < detail.index("Processing history")
    assert fold_at < detail.index("Source evidence")
    assert detail.index("Decision summary") < fold_at
    assert detail.index("Owned work") > fold_at


def test_lean_dashboard_tells_agents_how_to_mount_bidpilot() -> None:
    markup = koat_dashboard(load_public_tender_catalog(), now=FINALE_CLOCK)

    strip = markup.index('class="agent-access"')
    assert (
        markup.index('class="foot-links"')
        > strip
        > markup.index("Official tender catalogue")
    )
    assert "https://bidpilot-api-164282963747.us-central1.run.app/mcp" in markup
    assert (
        "https://bidpilot-api-164282963747.us-central1.run.app/openapi.json" in markup
    )
    assert "skills/bidpilot" in markup
    assert "Mount BidPilot in your agent" in markup
