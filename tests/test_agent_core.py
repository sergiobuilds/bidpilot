"""Contract tests for the agent-facing core (no Streamlit, JSON-only outputs)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from test_app import RUN_ID, FakeConnection, product_responses

from bidpilot import agent_core
from bidpilot.agent_core import AgentCoreError

REVIEWED = "R26BK01680611-000"
BEFORE_DEADLINE = datetime(2026, 9, 3, 6, 0, tzinfo=UTC)
AFTER_DEADLINE = datetime(2026, 9, 3, 8, 0, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[1]


def test_agent_core_never_imports_streamlit() -> None:
    source = (ROOT / "src" / "bidpilot" / "agent_core.py").read_text(encoding="utf-8")
    assert "streamlit" not in source


def test_list_tenders_returns_the_catalogue_with_a_judged_deadline_state() -> None:
    rows = agent_core.list_tenders(now=BEFORE_DEADLINE)

    assert isinstance(rows, list)
    assert rows[0]["notice_number"] == REVIEWED
    assert rows[0]["deadline_state"] == "open"
    assert rows[0]["status"] == "REVIEW"
    assert rows[0]["evidence_level"] == "source-reviewed"
    assert rows[0]["technical_weight"] == 90
    assert rows[0]["price_weight"] == 10
    assert rows[0]["contract_value_krw"] == 250_000_000
    assert rows[0]["official_url"].startswith("https://www.g2b.go.kr/")
    assert len(rows) == 6
    for row in rows[1:]:
        assert row["status"] == "SOURCE FOUND"
        assert row["deadline_state"] == "closed"
    expected = {
        "notice_number",
        "title",
        "issuer",
        "deadline",
        "deadline_state",
        "evidence_level",
        "status",
        "official_url",
        "contract_value_krw",
        "technical_weight",
        "price_weight",
    }
    assert all(expected <= set(row) for row in rows)
    json.dumps(rows)


def test_list_tenders_closes_the_reviewed_notice_after_its_deadline() -> None:
    rows = agent_core.list_tenders(now=AFTER_DEADLINE)
    assert rows[0]["deadline_state"] == "closed"


def test_get_tender_adds_source_provenance_for_the_reviewed_notice() -> None:
    row = agent_core.get_tender(REVIEWED, now=BEFORE_DEADLINE)

    assert row["notice_number"] == REVIEWED
    assert len(row["eligibility_requirements"]) == 4
    assert row["source_url"] == row["official_url"]
    assert len(row["source_sha256"]) == 64
    assert row["retrieved_at"]
    assert row["delivery_term"]
    assert row["supplier_boundary"]
    json.dumps(row)


def test_get_tender_returns_a_source_found_row_without_inventing_provenance() -> None:
    rows = agent_core.list_tenders(now=BEFORE_DEADLINE)
    row = agent_core.get_tender(rows[1]["notice_number"], now=BEFORE_DEADLINE)
    assert row["status"] == "SOURCE FOUND"
    assert "eligibility_requirements" not in row
    assert "source_sha256" not in row


def test_get_tender_fails_closed_for_an_unknown_notice() -> None:
    with pytest.raises(AgentCoreError, match="tender_not_found"):
        agent_core.get_tender("R99BK00000000-000")


def test_decide_without_evidence_is_review_with_four_gaps() -> None:
    result = agent_core.decide(REVIEWED, now=BEFORE_DEADLINE)

    assert result["notice_number"] == REVIEWED
    assert result["decision"] == "REVIEW"
    assert result["evidence_gaps"] == 4
    assert [check["status"] for check in result["checks"]] == ["EVIDENCE REQUIRED"] * 4
    assert result["weights"] == {"technical": 90, "price": 10}
    assert result["proposal_gate"] == "LOCKED"
    assert result["provider"] == "LOCAL_PYTHON_POLICY"
    assert result["persisted"] is False
    assert result["deadline_state"] == "open"
    assert result["next_actions"]
    json.dumps(result)


def test_decide_with_every_requirement_evidenced_is_pursue_and_opens_the_gate() -> None:
    evidence = {str(index): True for index in range(4)}
    result = agent_core.decide(REVIEWED, evidence, now=BEFORE_DEADLINE)

    assert result["decision"] == "PURSUE"
    assert result["evidence_gaps"] == 0
    assert result["proposal_gate"] == "OPEN"


def test_decide_accepts_exact_requirement_text_as_an_evidence_key() -> None:
    requirements = agent_core.get_tender(REVIEWED)["eligibility_requirements"]
    evidence = {text: True for text in requirements}
    result = agent_core.decide(REVIEWED, evidence, now=BEFORE_DEADLINE)
    assert result["decision"] == "PURSUE"


def test_decide_with_one_failure_is_no_go_even_when_others_pass() -> None:
    evidence = {"0": False, "1": True, "2": True, "3": True}
    result = agent_core.decide(REVIEWED, evidence, now=BEFORE_DEADLINE)

    assert result["decision"] == "NO-GO"
    assert result["checks"][0]["status"] == "FAIL"
    assert result["proposal_gate"] == "LOCKED"


def test_decide_keeps_the_gate_locked_after_the_deadline() -> None:
    evidence = {str(index): True for index in range(4)}
    result = agent_core.decide(REVIEWED, evidence, now=AFTER_DEADLINE)

    assert result["decision"] == "PURSUE"
    assert result["proposal_gate"] == "LOCKED"
    assert result["deadline_state"] == "closed"
    assert "closed" in result["reason"]


def test_decide_rejects_evidence_for_a_requirement_that_does_not_exist() -> None:
    with pytest.raises(AgentCoreError, match="unknown_requirement"):
        agent_core.decide(REVIEWED, {"9": True})


def test_decide_on_a_source_found_row_reports_no_reviewed_requirements() -> None:
    rows = agent_core.list_tenders(now=BEFORE_DEADLINE)
    result = agent_core.decide(rows[1]["notice_number"], now=BEFORE_DEADLINE)
    assert result["decision"] == "REVIEW"
    assert result["checks"] == []
    assert result["proposal_gate"] == "LOCKED"


def test_list_runs_fails_closed_without_a_configured_connection(monkeypatch) -> None:
    monkeypatch.delenv("BIDPILOT_SNOWFLAKE_CONNECTION", raising=False)
    with pytest.raises(AgentCoreError, match="snowflake_not_configured"):
        agent_core.list_runs()
    with pytest.raises(AgentCoreError, match="snowflake_not_configured"):
        agent_core.replay(RUN_ID)


def test_list_runs_reads_the_reader_store(monkeypatch) -> None:
    monkeypatch.setenv("BIDPILOT_SNOWFLAKE_CONNECTION", "contest")
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        runs = agent_core.list_runs()

    assert [run["run_id"] for run in runs] == [RUN_ID, "run-app-0"]
    assert runs[0]["state"] == "COMPLETED"
    assert runs[0]["is_complete"] is True
    assert runs[0]["opportunity_id"] == "opp-1"
    assert isinstance(runs[0]["created_at"], str)
    json.dumps(runs)


def test_replay_shapes_the_persisted_run_for_an_agent(monkeypatch) -> None:
    monkeypatch.setenv("BIDPILOT_SNOWFLAKE_CONNECTION", "contest")
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        result = agent_core.replay(RUN_ID)

    assert result["run_id"] == RUN_ID
    assert result["decision"] == "PURSUE"
    assert result["selected_strategy"] == "Proven data quality operations"
    assert result["strategy_count"] == 3
    assert result["plan_count"] == 2
    assert result["section_count"] == 2
    assert result["task_count"] == 3
    assert result["sections"][0] == {
        "criterion": "Technical approach",
        "title": "Technical approach",
        "weight": 60,
    }
    assert result["tasks"][1] == {
        "title": "Own the Price response",
        "owner": "Commercial lead",
    }
    assert result["provenance"]["cortex_session_id"] == "session-1"
    assert result["provenance"]["query_ids"] == ["q-1", "q-2"]
    json.dumps(result)


def test_replay_reports_a_missing_run_as_not_found(monkeypatch) -> None:
    monkeypatch.setenv("BIDPILOT_SNOWFLAKE_CONNECTION", "contest")
    responses = product_responses()
    responses[1] = (responses[1][0], responses[1][1], [])
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(responses)
        with pytest.raises(AgentCoreError, match="run_not_found"):
            agent_core.replay("run-missing")


def _cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    import os

    merged = {**os.environ, **(env or {})}
    merged.pop("BIDPILOT_SNOWFLAKE_CONNECTION", None)
    return subprocess.run(
        [sys.executable, "-m", "bidpilot.agent_core", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={**merged, "PYTHONPATH": str(ROOT / "src")},
        check=False,
    )


def test_cli_prints_one_json_document_per_command() -> None:
    listed = _cli("list-tenders")
    assert listed.returncode == 0, listed.stderr
    assert json.loads(listed.stdout)[0]["notice_number"] == REVIEWED

    decided = _cli("decide", REVIEWED, "--evidence", json.dumps({"0": True}))
    assert decided.returncode == 0, decided.stderr
    payload = json.loads(decided.stdout)
    assert payload["decision"] == "REVIEW"
    assert payload["evidence_gaps"] == 3


def test_cli_fails_closed_with_a_json_error() -> None:
    failed = _cli("list-runs")
    assert failed.returncode == 1
    assert json.loads(failed.stdout)["error"] == "snowflake_not_configured"


FULL_EVIDENCE = {"0": True, "1": True, "2": True, "3": True}
FIXTURE_TENDER = "G2B-REPLAY-DATA-QUALITY"


def test_draft_proposal_for_the_reviewed_notice_when_every_requirement_is_evidenced() -> (
    None
):
    draft = agent_core.draft_proposal(REVIEWED, FULL_EVIDENCE, now=BEFORE_DEADLINE)

    assert draft["notice_number"] == REVIEWED
    assert draft["decision"] == "PURSUE"
    assert draft["proposal_gate"] == "OPEN"
    assert draft["deadline_state"] == "open"
    assert draft["supplier"] == {
        "id": "supplier-northstar",
        "name": "Northstar Systems",
        "synthetic": True,
    }
    assert draft["score_map"] == [
        {"name": "Technical", "weight": 90},
        {"name": "Price", "weight": 10},
    ]
    assert len(draft["win_positions"]) == 2
    assert draft["selected_position"]["title"] == draft["win_positions"][0]["title"]
    assert draft["selected_position"]["index"] == 0
    criteria = [
        section["criterion"] for section in draft["sections"] if section["criterion"]
    ]
    assert criteria == ["Technical", "Price"]
    assert all(
        {"criterion", "heading", "markdown"} <= set(section)
        for section in draft["sections"]
    )
    assert draft["markdown"].startswith("# K패스")
    assert isinstance(draft["red_team"], list)
    assert all({"title", "owner"} <= set(task) for task in draft["tasks"])
    assert draft["gap_closure_plan"] == []
    assert draft["provider"] == "LOCAL_PYTHON_POLICY"
    assert draft["persisted"] is False
    assert draft["disclosure"] == (
        "Synthetic demo supplier profile; nothing here is a real company claim."
    )
    assert any("delivery_hours" in item for item in draft["assumptions"])
    # Source facts, never embellished: the tender the writer saw quotes the notice.
    tender = draft["tender"]
    assert tender["id"] == REVIEWED
    assert tender["evaluation_criteria"] == [
        {"name": "Technical", "weight": 90},
        {"name": "Price", "weight": 10},
    ]
    assert len(tender["eligibility_requirements"]) == 4
    assert tender["title"] in tender["buyer_objective"]
    assert "Contract start through 2026-12-31" in tender["promised_outcome"]


def test_draft_proposal_locks_on_review_and_no_go_with_the_decision_payload() -> None:
    with pytest.raises(AgentCoreError) as review:
        agent_core.draft_proposal(REVIEWED, None, now=BEFORE_DEADLINE)
    assert review.value.code == "proposal_locked"
    detail = review.value.detail
    assert detail["decision"] == "REVIEW"
    assert len(detail["gaps"]) == 4
    assert detail["next_actions"]
    assert review.value.to_dict()["detail"]["proposal_gate"] == "LOCKED"

    with pytest.raises(AgentCoreError) as no_go:
        agent_core.draft_proposal(
            REVIEWED, {**FULL_EVIDENCE, "2": False}, now=BEFORE_DEADLINE
        )
    assert no_go.value.code == "proposal_locked"
    assert no_go.value.detail["decision"] == "NO-GO"
    assert no_go.value.detail["gaps"] == [
        "Valid SME or small-business confirmation for public procurement"
    ]


def test_draft_proposal_never_adds_credentials_without_true_evidence() -> None:
    with pytest.raises(AgentCoreError) as locked:
        agent_core.draft_proposal(
            REVIEWED, {"0": True, "1": True, "2": True}, now=BEFORE_DEADLINE
        )
    assert locked.value.detail["decision"] == "REVIEW"
    assert locked.value.detail["gaps"] == [
        "Not a large, mid-sized, or cross-shareholding-group software business excluded from sub-KRW-2B projects"
    ]


def test_draft_proposal_refuses_a_closed_notice_unless_it_is_a_historical_exercise() -> (
    None
):
    with pytest.raises(AgentCoreError) as closed:
        agent_core.draft_proposal(REVIEWED, FULL_EVIDENCE, now=AFTER_DEADLINE)
    assert closed.value.code == "notice_closed"
    assert closed.value.detail["deadline"] == "2026-09-03T16:00:00+09:00"

    draft = agent_core.draft_proposal(
        REVIEWED, FULL_EVIDENCE, historical_exercise=True, now=AFTER_DEADLINE
    )
    assert draft["proposal_gate"] == "HISTORICAL EXERCISE"
    assert draft["deadline_state"] == "closed"
    banner = draft["markdown"].splitlines()[0]
    assert "historical exercise" in banner.lower()
    assert "2026-09-03 16:00 KST" in banner


def test_draft_proposal_uses_fixture_tenders_directly() -> None:
    draft = agent_core.draft_proposal(FIXTURE_TENDER)

    assert draft["decision"] == "PURSUE"
    assert draft["proposal_gate"] == "OPEN"
    assert draft["deadline_state"] == "open"
    assert [row["name"] for row in draft["score_map"]] == [
        "Technical approach",
        "Comparable delivery",
        "Delivery team",
        "Price",
    ]
    criteria = [
        section["criterion"] for section in draft["sections"] if section["criterion"]
    ]
    assert criteria == [
        "Technical approach",
        "Comparable delivery",
        "Delivery team",
        "Price",
    ]
    assert draft["supplier"]["synthetic"] is True

    second = agent_core.draft_proposal(FIXTURE_TENDER, position_index=1)
    assert second["selected_position"]["title"] == "Operational continuity"
    assert second["selected_position"]["index"] == 1


def test_draft_proposal_locks_when_the_synthetic_supplier_cannot_qualify() -> None:
    with pytest.raises(AgentCoreError) as locked:
        agent_core.draft_proposal(FIXTURE_TENDER, supplier_id="supplier-atlas")
    assert locked.value.code == "proposal_locked"
    assert locked.value.detail["decision"] == "NO-GO"
    assert "Information-system maintenance certificate" in locked.value.detail["gaps"]
    assert locked.value.detail["gap_closure_plan"]


def test_draft_proposal_rejects_unknown_supplier_position_and_tender() -> None:
    with pytest.raises(AgentCoreError) as supplier:
        agent_core.draft_proposal(FIXTURE_TENDER, supplier_id="acme-real-corp")
    assert supplier.value.code == "supplier_not_found"
    with pytest.raises(AgentCoreError) as position:
        agent_core.draft_proposal(FIXTURE_TENDER, position_index=5)
    assert position.value.code == "invalid_position"
    with pytest.raises(AgentCoreError) as tender:
        agent_core.draft_proposal("NOPE-000")
    assert tender.value.code == "tender_not_found"


def test_cli_draft_proposal_prints_the_draft_or_a_json_error() -> None:
    drafted = _cli("draft-proposal", FIXTURE_TENDER, "--position", "1")
    assert drafted.returncode == 0, drafted.stderr
    payload = json.loads(drafted.stdout)
    assert payload["decision"] == "PURSUE"
    assert payload["selected_position"]["index"] == 1

    locked = _cli("draft-proposal", REVIEWED)
    assert locked.returncode == 1
    error = json.loads(locked.stdout)
    assert error["error"] == "proposal_locked"
    assert error["detail"]["decision"] == "REVIEW"

    closed = _cli(
        "draft-proposal",
        REVIEWED,
        "--evidence",
        json.dumps(FULL_EVIDENCE),
        "--now",
        "2026-09-03T08:00:00+00:00",
    )
    assert json.loads(closed.stdout)["error"] == "notice_closed"
    historical = _cli(
        "draft-proposal",
        REVIEWED,
        "--evidence",
        json.dumps(FULL_EVIDENCE),
        "--now",
        "2026-09-03T08:00:00+00:00",
        "--historical",
    )
    assert historical.returncode == 0, historical.stderr
    assert json.loads(historical.stdout)["proposal_gate"] == "HISTORICAL EXERCISE"
