from bidpilot.engine import create_proposal_tasks, decision_trace, evaluate_bid
from bidpilot.fixtures import COMPANY, RFPS


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
