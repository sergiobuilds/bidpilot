from pathlib import Path
import runpy

from bidpilot.bid_room import BidRoomStore
from bidpilot.fixtures import SUPPLIER_PROFILES, TENDERS
from bidpilot.proposal_writer import build_gap_closure_plan, red_team_proposal, red_team_tasks, write_strategy_proposal
from bidpilot.pursuit import build_pursuit_brief, select_win_position
from bidpilot.policy import POLICY_VERSION, pursue_status


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
    assert red_team_tasks(brief, draft) == ()
    for heading in (
        "Executive Summary", "Understanding of the Requirement", "Technical approach",
        "Comparable delivery", "Team and Governance", "Implementation Plan",
        "Risk and Mitigation", "Commercial Response",
    ):
        assert f"## {heading}" in draft


def test_selecting_a_position_changes_the_proposal_blueprint_claims() -> None:
    tender = TENDERS[0]
    supplier = SUPPLIER_PROFILES[0]
    brief = build_pursuit_brief(tender, supplier)
    continuity = select_win_position(brief, tender, supplier, 1)

    assert continuity.proposal_blueprint[0].claim != brief.proposal_blueprint[0].claim
    assert continuity.win_positions[1].title in continuity.proposal_blueprint[0].claim
    assert continuity.selected_position_index == 1
    assert continuity.win_positions[1].statement in write_strategy_proposal(tender, supplier, continuity)


def test_red_team_requires_assets_inside_each_criterion_section() -> None:
    tender, supplier = TENDERS[0], SUPPLIER_PROFILES[0]
    brief = build_pursuit_brief(tender, supplier)
    draft = write_strategy_proposal(tender, supplier, brief)
    first = brief.proposal_blueprint[0]
    broken = draft.replace(f"Delivery assets: {', '.join(first.assets)}.", "Delivery assets: pending.", 1)
    assert any(task["criterion"] == first.criterion for task in red_team_tasks(brief, broken))


def test_high_weight_response_requires_validation_and_buyer_outcome() -> None:
    tender, supplier = TENDERS[0], SUPPLIER_PROFILES[0]
    brief = build_pursuit_brief(tender, supplier)
    draft = write_strategy_proposal(tender, supplier, brief)
    broken = draft.replace("Validation:", "Review:", 1)

    assert any("validation" in task["finding"] for task in red_team_tasks(brief, broken))
    assert any("high-weight" in finding for finding in red_team_proposal(brief, broken))


def test_published_weight_changes_response_substance() -> None:
    tender, supplier = TENDERS[0], SUPPLIER_PROFILES[0]
    high = build_pursuit_brief(tender, supplier)
    raised_tender = {
        **tender,
        "evaluation_criteria": tuple(
            {**item, "weight": 50 if item["name"] == "Technical approach" else item["weight"]}
            for item in tender["evaluation_criteria"]
        ),
    }
    raised = build_pursuit_brief(raised_tender, supplier)

    high_draft = write_strategy_proposal(tender, supplier, high)
    raised_draft = write_strategy_proposal(raised_tender, supplier, raised)

    assert "Validation:" in high_draft
    assert "Buyer outcome:" in high_draft
    assert "Scoring emphasis:" not in high_draft
    assert "Scoring emphasis:" in raised_draft


def test_red_team_uses_relative_top_weight_and_rejects_empty_detail() -> None:
    tender, supplier = TENDERS[0], SUPPLIER_PROFILES[0]
    lowered = {
        **tender,
        "evaluation_criteria": tuple(
            {**item, "weight": 29 - index}
            for index, item in enumerate(tender["evaluation_criteria"])
        ),
    }
    brief = build_pursuit_brief(lowered, supplier)
    draft = write_strategy_proposal(lowered, supplier, brief)
    broken = draft.replace(
        "Validation: agree measurable acceptance checks with the buyer and record the result in the Bid Room.",
        "Validation:",
        1,
    )
    broken = broken.replace(
        f"Buyer outcome: {lowered['promised_outcome'].capitalize()}.",
        "Buyer outcome:",
        1,
    )

    assert any(task["criterion"] == brief.proposal_blueprint[0].criterion for task in red_team_tasks(brief, broken))


def test_canonical_sections_survive_nonstandard_evaluation_names() -> None:
    tender, supplier = TENDERS[0], SUPPLIER_PROFILES[0]
    renamed = {
        **tender,
        "evaluation_criteria": (
            {"name": "Service quality", "weight": 50},
            {"name": "Relevant experience", "weight": 30},
            {"name": "Price", "weight": 20},
        ),
    }
    brief = build_pursuit_brief(renamed, supplier)
    draft = write_strategy_proposal(renamed, supplier, brief)

    assert "## Technical Approach" in draft
    assert "## Comparable Delivery" in draft


def test_blueprint_uses_criterion_specific_supplier_evidence() -> None:
    brief = build_pursuit_brief(TENDERS[0], SUPPLIER_PROFILES[0])
    by_name = {section.criterion: section for section in brief.proposal_blueprint}
    assert by_name["Technical approach"].assets != by_name["Delivery team"].assets
    assert by_name["Delivery team"].assets != by_name["Price"].assets
    assert "900 available hours" in by_name["Price"].assets


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
    plan = build_gap_closure_plan(brief)
    assert any("Information-system maintenance certificate" in task["gap"] for task in plan)


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


def test_python_and_snowpark_policy_contract_share_version_and_decision_vectors() -> None:
    module = runpy.run_path("snowflake/snowpark_decision.py")

    assert module["POLICY_VERSION"] == POLICY_VERSION
    assert [
        pursue_status(missing, capacity, projects)
        for missing, capacity, projects in ((1, 0, 3), (0, 4, 3), (0, 0, 1), (0, 0, 2))
    ] == ["NO-GO", "NO-GO", "REVIEW", "PURSUE"]
    assert callable(module["pursue_status_expression"])
