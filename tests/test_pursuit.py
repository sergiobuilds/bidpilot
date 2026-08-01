from pathlib import Path

from bidpilot.bid_room import BidRoomStore
from bidpilot.fixtures import SUPPLIER_PROFILES, TENDERS
from bidpilot.proposal_writer import red_team_proposal, write_strategy_proposal
from bidpilot.pursuit import build_pursuit_brief, select_win_position


def test_qualified_supplier_receives_pursue_and_strategy_bound_blueprint() -> None:
    brief = build_pursuit_brief(TENDERS[0], SUPPLIER_PROFILES[0])

    assert brief.status == "PURSUE"
    assert brief.can_generate_proposal
    assert brief.score_map[0]["name"] == "Technical approach"
    assert len(brief.win_positions[0].proof_cards) == 3
    assert brief.proposal_blueprint[0].criterion == "Technical approach"
    assert "Northstar Systems" in brief.proposal_blueprint[0].claim


def test_missing_eligibility_blocks_proposal_generation() -> None:
    brief = build_pursuit_brief(TENDERS[0], SUPPLIER_PROFILES[1])

    assert brief.status == "NO-GO"
    assert not brief.can_generate_proposal
    assert brief.missing_eligibility == ("Information-system maintenance certificate",)


def test_tender_and_supplier_matrix_changes_strategy_and_outcome() -> None:
    data_brief = build_pursuit_brief(TENDERS[0], SUPPLIER_PROFILES[0])
    analytics_brief = build_pursuit_brief(TENDERS[1], SUPPLIER_PROFILES[0])
    weak_analytics_brief = build_pursuit_brief(TENDERS[1], SUPPLIER_PROFILES[1])

    assert data_brief.win_positions[0].statement != analytics_brief.win_positions[0].statement
    assert data_brief.proposal_blueprint[0].criterion != analytics_brief.proposal_blueprint[0].criterion
    assert weak_analytics_brief.status == "REVIEW"
    assert not weak_analytics_brief.can_generate_proposal


def test_strategy_led_proposal_uses_the_selected_tender_and_supplier_assets() -> None:
    tender = TENDERS[0]
    supplier = SUPPLIER_PROFILES[0]
    brief = build_pursuit_brief(tender, supplier)

    draft = write_strategy_proposal(tender, supplier, brief)

    assert brief.win_positions[0].statement in draft
    assert "Technical approach (40 points)" in draft
    assert "City Open Data Reliability Program" in draft
    assert red_team_proposal(brief, draft) == ()


def test_selecting_a_position_changes_the_proposal_blueprint_claims() -> None:
    tender = TENDERS[0]
    supplier = SUPPLIER_PROFILES[0]
    brief = build_pursuit_brief(tender, supplier)
    continuity = select_win_position(brief, tender, supplier, 1)

    assert continuity.proposal_blueprint[0].claim != brief.proposal_blueprint[0].claim
    assert continuity.win_positions[1].title in continuity.proposal_blueprint[0].claim
    assert continuity.selected_position_index == 1
    assert continuity.win_positions[1].statement in write_strategy_proposal(tender, supplier, continuity)


def test_no_go_brief_cannot_create_a_strategy_proposal() -> None:
    tender = TENDERS[0]
    supplier = SUPPLIER_PROFILES[1]
    brief = build_pursuit_brief(tender, supplier)

    try:
        write_strategy_proposal(tender, supplier, brief)
    except ValueError as error:
        assert "blocked for NO-GO" in str(error)
    else:
        raise AssertionError("NO-GO proposal generation must be blocked")


def test_bid_room_persists_the_same_versioned_run_after_refresh(tmp_path: Path) -> None:
    tender = TENDERS[0]
    supplier = SUPPLIER_PROFILES[0]
    brief = build_pursuit_brief(tender, supplier)
    proposal = write_strategy_proposal(tender, supplier, brief)
    store = BidRoomStore(tmp_path / "bidpilot.sqlite")

    run_id = store.save(
        brief,
        opportunity_version="sha256:demo-replay-v1",
        proposal_markdown=proposal,
        red_team_findings=red_team_proposal(brief, proposal),
        tasks=({"owner": "Solution lead", "task": "Confirm proposal outline"},),
    )
    loaded = store.load(run_id)

    assert loaded["opportunity_id"] == tender["id"]
    assert loaded["supplier_profile_id"] == supplier["id"]
    assert loaded["opportunity_version"] == "sha256:demo-replay-v1"
    assert loaded["proposal_markdown"] == proposal
    assert loaded["red_team_findings"] == ()
    assert loaded["brief"]["win_positions"][0]["proof_cards"]
    assert loaded["tasks"][0]["owner"] == "Solution lead"
    assert loaded["agent_run"]["state"] == "not-executed-in-snowflake-or-coco"
    latest = store.latest(tender["id"], supplier["id"], "sha256:demo-replay-v1", brief.win_positions[0].statement)
    assert latest is not None
    assert latest["run_id"] == run_id
