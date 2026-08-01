from bidpilot.engine import create_proposal_tasks, decision_trace, evaluate_bid
from bidpilot.fixtures import COMPANY, RFPS
from bidpilot.proposal_packet import build_proposal_start_packet
from bidpilot.proposal_writer import write_proposal_draft
from bidpilot.public_tender import PUBLIC_TENDER, assess_public_tender


def test_high_value_opportunity_is_rejected_for_policy_failures() -> None:
    decision = evaluate_bid(RFPS[0], COMPANY)

    assert decision.recommendation == "NO-BID"
    assert decision.expected_margin < 0
    assert len(decision.hard_gate_failures) == 3
    assert create_proposal_tasks(RFPS[0], decision) == []


def test_next_opportunity_creates_internal_proposal_work() -> None:
    decision = evaluate_bid(RFPS[1], COMPANY)
    tasks = create_proposal_tasks(RFPS[1], decision)

    assert decision.recommendation == "BID"
    assert decision.expected_margin > 0
    assert len(tasks) == 4
    assert tasks[0]["owner"] == "Solutions lead"
    assert tasks[0]["outcome"] == "A scoped architecture and delivery assumptions"


def test_decision_trace_exposes_each_hard_gate_without_an_opaque_score() -> None:
    decision = evaluate_bid(RFPS[0], COMPANY)
    trace = decision_trace(RFPS[0], COMPANY, decision)

    assert [item["gate"] for item in trace] == [
        "Mandatory capability",
        "Delivery capacity",
        "Margin floor",
    ]
    assert all(not item["passed"] for item in trace)


def test_snowpark_execution_module_imports() -> None:
    import runpy

    module = runpy.run_path("snowflake/snowpark_decision.py")

    assert callable(module["evaluate_and_persist"])


def test_public_tender_never_claims_eligibility_without_supplier_evidence() -> None:
    assessment = assess_public_tender(PUBLIC_TENDER, {})

    assert assessment.recommendation == "HOLD — EVIDENCE REQUIRED"
    assert assessment.unknown == 6


def test_public_tender_rejects_a_confirmed_mandatory_requirement_failure() -> None:
    assessment = assess_public_tender(
        PUBLIC_TENDER,
        {"daejeon_headquarters": False, "software_business_1468": True},
    )

    assert assessment.recommendation == "NO-BID — INELIGIBLE"
    assert assessment.failed == 1


def test_public_tender_packet_locks_proposal_drafting_until_evidence_and_open_status_exist() -> None:
    assessment = assess_public_tender(PUBLIC_TENDER, {})
    packet = build_proposal_start_packet(PUBLIC_TENDER, assessment)

    assert packet["kind"] == "proposal-start-packet"
    assert packet["source"]["sha256"] == PUBLIC_TENDER["source_sha256"]
    assert packet["proposal_strategy"]["writing_gate"] == "LOCKED"
    assert len(packet["qualification"]["missing_evidence"]) == 6


def test_proposal_writer_blocks_a_closed_public_tender() -> None:
    try:
        write_proposal_draft(PUBLIC_TENDER, "Northstar Systems", "A public-data delivery team.")
    except ValueError as error:
        assert "versioned proposal-start packet" in str(error)
    else:
        raise AssertionError("A closed tender must not produce a full proposal draft")


def test_proposal_writer_rejects_a_raw_tender_even_with_a_forged_gate() -> None:
    forged = {**PUBLIC_TENDER, "is_open": True, "writing_gate": "OPEN"}
    try:
        write_proposal_draft(forged, "Northstar Systems", "A public-data delivery team.")
    except ValueError as error:
        assert "versioned proposal-start packet" in str(error)
    else:
        raise AssertionError("A raw tender must never bypass the qualified packet contract")


def test_proposal_writer_consumes_an_approved_packet_and_rejects_a_locked_packet() -> None:
    locked = build_proposal_start_packet(PUBLIC_TENDER, assess_public_tender(PUBLIC_TENDER, {}))
    approved = {
        **locked,
        "opportunity": {**locked["opportunity"], "is_open": True},
        "qualification": {**locked["qualification"], "missing_evidence": [], "failed_requirements": []},
        "proposal_strategy": {**locked["proposal_strategy"], "writing_gate": "OPEN"},
    }

    assert "## Executive summary" in write_proposal_draft(
        approved, "Northstar Systems", "A public-data delivery team."
    )
    try:
        write_proposal_draft(locked, "Northstar Systems", "A public-data delivery team.")
    except ValueError as error:
        assert "supplier evidence is approved" in str(error)
    else:
        raise AssertionError("A locked packet must not produce a proposal draft")
