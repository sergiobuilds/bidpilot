"""Contract tests for the three-workspace refinement shell.

The shell is deliberately tested as deterministic HTML before it is wired to
Streamlit state or a Snowflake reader.  This keeps presentation assertions
independent of credentials and prevents the synthetic workspace from gaining
persisted-run actions by accident.
"""

from __future__ import annotations

import pytest

from bidpilot.ui_components import decision_path, state_panel
from bidpilot.workspace_ui import (
    SYNTHETIC_BOUNDARY,
    UI_STATES,
    WORKSPACES,
    bid_room_first_viewport,
    shell_css,
    synthetic_simulation_first_viewport,
    tender_intake_first_viewport,
    workspace_navigation,
    workspace_route_navigation,
)


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


def test_integrated_route_navigation_needs_no_streamlit_sidebar_or_inline_script() -> None:
    markup = workspace_route_navigation("bid-room")

    assert 'aria-label="BidPilot workspace routes"' in markup
    assert 'class="bpw-route-desktop"' in markup
    assert 'class="bpw-route-mobile"' in markup
    assert '<details' in markup
    assert '<summary' in markup
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
