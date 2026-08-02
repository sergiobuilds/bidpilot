from __future__ import annotations

from unittest.mock import patch

import pytest

from bidpilot.snowflake_store import (
    SnowflakeBidRoomError,
    SnowflakeBidRoomStore,
    configured_connection_name,
)


class FakeCursor:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.description = []
        self.rows: list[tuple] = []

    def execute(self, sql: str, params: tuple = ()) -> None:
        self.connection.executed.append((sql, params))
        if "CURRENT_ROLE()" in sql:
            self.description = [("CURRENT_ROLE",)]
            self.rows = [(self.connection.role,)]
            return
        for marker, description, rows in self.connection.responses:
            if marker in sql:
                self.description = [(name,) for name in description]
                self.rows = list(rows)
                return
        raise AssertionError(f"Unexpected SQL in fake Snowflake connection: {sql}")

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self, role: str = "BIDPILOT_READER", responses: list[tuple] | None = None) -> None:
        self.role = role
        self.responses = responses or []
        self.executed: list[tuple[str, tuple]] = []
        self.closed = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def close(self) -> None:
        self.closed = True


def complete_run_responses(is_complete: bool = True, trace: str = '{"status":"PURSUE"}') -> list[tuple]:
    return [
        (
            "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS WHERE run_id",
            ("RUN_ID", "PROVIDER", "TRACE"),
            [("run-1", "CORTEX_CODE_CLI", trace)],
        ),
        ("SELECT o.*", ("OPPORTUNITY_ID",), []),
        ("SELECT p.*", ("SUPPLIER_PROFILE_ID",), []),
        ("SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS", ("RUN_ID",), [("run-1",)]),
        ("SELECT * FROM BIDPILOT_DEMO.BIDPILOT.WIN_STRATEGIES", ("RUN_ID",), [("run-1",)]),
        ("SELECT * FROM BIDPILOT_DEMO.BIDPILOT.RUBRIC_RESPONSE_PLANS", ("RUN_ID",), [("run-1",)]),
        ("SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_TASKS", ("RUN_ID",), [("run-1",)]),
        ("SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PROPOSAL_SECTIONS", ("RUN_ID",), [("run-1",)]),
        (
            "AS is_complete",
            (
                "AGENT_COUNT",
                "DECISION_COUNT",
                "PURSUE_DECISION_COUNT",
                "STRATEGY_COUNT",
                "SELECTED_STRATEGY_COUNT",
                "INVALID_STRATEGY_COUNT",
                "PLAN_COUNT",
                "INVALID_PLAN_COUNT",
                "PLAN_WEIGHT_TOTAL",
                "SECTION_COUNT",
                "INVALID_SECTION_COUNT",
                "TASK_COUNT",
                "INVALID_TASK_COUNT",
                "IS_COMPLETE",
            ),
            [(1, 1, 1, 3, 1, 0, 4, 0, 100, 8, 0, 11, 0, is_complete)],
        ),
    ]


def test_connection_name_is_explicit_environment_configuration(monkeypatch) -> None:
    monkeypatch.delenv("BIDPILOT_SNOWFLAKE_CONNECTION", raising=False)
    assert configured_connection_name() is None
    monkeypatch.setenv("BIDPILOT_SNOWFLAKE_CONNECTION", "contest")
    assert configured_connection_name() == "contest"


@patch("bidpilot.snowflake_store.snowflake.connector.connect")
def test_authenticated_store_rejects_non_reader_role(connect) -> None:
    connection = FakeConnection(role="ACCOUNTADMIN")
    connect.return_value = connection

    with pytest.raises(SnowflakeBidRoomError, match="requires role BIDPILOT_READER"):
        SnowflakeBidRoomStore("bootstrap").list_runs()

    assert connection.closed


@patch("bidpilot.snowflake_store.snowflake.connector.connect")
def test_authenticated_store_preserves_provenance_for_a_complete_run(connect) -> None:
    connection = FakeConnection(responses=complete_run_responses())
    connect.return_value = connection

    result = SnowflakeBidRoomStore("contest").load_run("run-1")

    connect.assert_called_with(connection_name="contest")
    assert result["run"]["provider"] == "CORTEX_CODE_CLI"
    assert result["run"]["trace"]["status"] == "PURSUE"
    completeness_call = next(call for call in connection.executed if "AS is_complete" in call[0])
    assert completeness_call[1] == ("CORTEX_CODE_CLI", "2026-08-02.v1", "run-1")


@patch("bidpilot.snowflake_store.snowflake.connector.connect")
def test_authenticated_store_rejects_direct_load_of_partial_run(connect) -> None:
    connection = FakeConnection(responses=complete_run_responses(is_complete=False))
    connect.return_value = connection

    with pytest.raises(SnowflakeBidRoomError, match="incomplete or lacks required Cortex provenance"):
        SnowflakeBidRoomStore("contest").load_run("run-1")


@patch("bidpilot.snowflake_store.snowflake.connector.connect")
def test_authenticated_store_normalizes_malformed_trace_as_domain_error(connect) -> None:
    connection = FakeConnection(responses=complete_run_responses(trace="{not-json"))
    connect.return_value = connection

    with pytest.raises(SnowflakeBidRoomError, match="malformed execution trace"):
        SnowflakeBidRoomStore("contest").load_run("run-1")


@patch("bidpilot.snowflake_store.snowflake.connector.connect")
def test_run_listing_completeness_checks_provider_plans_selected_strategy_and_provenance(connect) -> None:
    row = (
        "run-1", "opp-1", "v1", "supplier-1", "2026-08-02.v1", "CORTEX_CODE_CLI",
        "COMPLETED", "2026-08-02", 1, 1, 1, 3, 1, 0, 4, 0, 100, 8, 0, 11, 0, True,
    )
    response = [
        (
            "SELECT a.run_id",
            (
                "RUN_ID", "OPPORTUNITY_ID", "OPPORTUNITY_VERSION", "SUPPLIER_PROFILE_ID",
                "POLICY_VERSION", "PROVIDER", "STATE", "CREATED_AT", "AGENT_COUNT",
                "DECISION_COUNT", "PURSUE_DECISION_COUNT", "STRATEGY_COUNT",
                "SELECTED_STRATEGY_COUNT", "INVALID_STRATEGY_COUNT", "PLAN_COUNT",
                "INVALID_PLAN_COUNT", "PLAN_WEIGHT_TOTAL", "SECTION_COUNT",
                "INVALID_SECTION_COUNT", "TASK_COUNT", "INVALID_TASK_COUNT", "IS_COMPLETE",
            ),
            [row],
        )
    ]
    connection = FakeConnection(responses=response)
    connect.return_value = connection

    runs = SnowflakeBidRoomStore("contest").list_runs()

    assert runs[0]["is_complete"] is True
    sql = next(call[0] for call in connection.executed if "SELECT a.run_id" in call[0])
    assert "selected_strategy_count" in sql
    assert "pursue_decision_count" in sql
    assert "invalid_strategy_count" in sql
    assert "invalid_plan_count" in sql
    assert "plan_weight_total" in sql
    assert "invalid_section_count" in sql
    assert "invalid_task_count" in sql
    assert "supplier_profile_version" in sql
    assert "plan_count" in sql
    assert "CORTEX_CODE_CLI" not in sql  # provider stays bound, not interpolated
    assert "cortex_session_id" in sql
    assert "completion_audit_query_id" in sql
