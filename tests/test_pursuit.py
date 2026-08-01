from bidpilot.fixtures import SUPPLIER_PROFILES, TENDERS
from bidpilot.pursuit import build_pursuit_brief


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
