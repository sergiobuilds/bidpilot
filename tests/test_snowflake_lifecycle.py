from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SNOWFLAKE_DIR = Path(__file__).parents[1] / "snowflake"
if str(SNOWFLAKE_DIR) not in sys.path:
    sys.path.insert(0, str(SNOWFLAKE_DIR))

spec = importlib.util.spec_from_file_location("bidpilot_run_matrix", SNOWFLAKE_DIR / "run_matrix.py")
assert spec and spec.loader
run_matrix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_matrix)

decision_spec = importlib.util.spec_from_file_location("bidpilot_snowpark_decision", SNOWFLAKE_DIR / "snowpark_decision.py")
assert decision_spec and decision_spec.loader
snowpark_decision = importlib.util.module_from_spec(decision_spec)
decision_spec.loader.exec_module(snowpark_decision)


class MatrixCursor:
    def __init__(self, connection: MatrixConnection) -> None:
        self.connection = connection
        self.rows: list[tuple] = []

    def execute(self, sql: str, params: tuple = ()) -> None:
        self.connection.executed.append((sql, params))
        if "CURRENT_ROLE()" in sql:
            self.rows = [(self.connection.role,)]
        elif "SELECT tenant_id" in sql and "AGENT_RUNS" in sql:
            run = self.connection.runs.get(params[0])
            self.rows = [run] if run else []
        elif "SELECT COUNT(*)" in sql and "PURSUIT_DECISIONS" in sql:
            self.rows = [(self.connection.decisions.get(params[0], 0),)]
        elif "INSERT INTO BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS" in sql:
            run_id, tenant_id, opportunity_id, opportunity_version, supplier_id, supplier_version, policy, provider, _, _ = params
            self.connection.runs.setdefault(
                run_id,
                (tenant_id, opportunity_id, opportunity_version, supplier_id, supplier_version, policy, provider, "RUNNING"),
            )
            self.rows = []
        elif "UPDATE BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS" in sql:
            state, policy, trace_json, run_id = params
            current = self.connection.runs[run_id]
            self.connection.runs[run_id] = (*current[:5], policy, current[6], state)
            self.connection.traces[run_id] = json.loads(trace_json)
            self.rows = []
        elif "ALTER SESSION SET" in sql:
            self.rows = []
        else:
            raise AssertionError(f"Unexpected lifecycle SQL: {sql}")

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)

    def close(self) -> None:
        pass


class MatrixConnection:
    def __init__(self, role: str = "BIDPILOT_RUNNER") -> None:
        self.role = role
        self.runs: dict[str, tuple] = {}
        self.decisions: dict[str, int] = {}
        self.traces: dict[str, dict] = {}
        self.executed: list[tuple[str, tuple]] = []

    def cursor(self) -> MatrixCursor:
        return MatrixCursor(self)


def test_matrix_cell_persists_running_then_completed_with_exactly_one_decision(monkeypatch) -> None:
    connection = MatrixConnection()

    def persist(_session, *, run_id: str, **_kwargs) -> str:
        connection.decisions[run_id] = 1
        return "inserted"

    monkeypatch.setattr(run_matrix, "evaluate_and_persist", persist)
    outcome = run_matrix.execute_matrix_cell(
        object(), connection, "matrix-dq-northstar", "G2B-REPLAY-DATA-QUALITY", "supplier-northstar"
    )

    assert outcome == "inserted"
    assert connection.decisions["matrix-dq-northstar"] == 1
    assert connection.runs["matrix-dq-northstar"][7] == "COMPLETED"
    assert connection.traces["matrix-dq-northstar"]["decision_count"] == 1


def test_matrix_cell_reuses_a_valid_completed_run_without_duplicate_write(monkeypatch) -> None:
    connection = MatrixConnection()
    run_id = "matrix-dq-northstar"
    connection.runs[run_id] = (
        "demo-tenant", "G2B-REPLAY-DATA-QUALITY", "fixture-v1", "supplier-northstar",
        "fixture-v1", "2026-08-02.v1", "SNOWPARK", "COMPLETED",
    )
    connection.decisions[run_id] = 1

    def unexpected(*_args, **_kwargs):
        raise AssertionError("A completed idempotent retry must not execute Snowpark again.")

    monkeypatch.setattr(run_matrix, "evaluate_and_persist", unexpected)
    outcome = run_matrix.execute_matrix_cell(
        object(), connection, run_id, "G2B-REPLAY-DATA-QUALITY", "supplier-northstar"
    )

    assert outcome == "reused-completed"
    assert connection.decisions[run_id] == 1


def test_matrix_cell_marks_failed_when_policy_execution_raises(monkeypatch) -> None:
    connection = MatrixConnection()

    def fail(*_args, **_kwargs):
        raise RuntimeError("synthetic policy failure")

    monkeypatch.setattr(run_matrix, "evaluate_and_persist", fail)
    with pytest.raises(RuntimeError, match="synthetic policy failure"):
        run_matrix.execute_matrix_cell(
            object(), connection, "matrix-failed", "G2B-REPLAY-DATA-QUALITY", "supplier-atlas"
        )

    assert connection.runs["matrix-failed"][7] == "FAILED"
    assert connection.traces["matrix-failed"]["error_type"] == "RuntimeError"


def test_matrix_cell_marks_failed_when_more_than_one_decision_exists(monkeypatch) -> None:
    connection = MatrixConnection()

    def duplicate(_session, *, run_id: str, **_kwargs) -> str:
        connection.decisions[run_id] = 2
        return "inserted"

    monkeypatch.setattr(run_matrix, "evaluate_and_persist", duplicate)
    with pytest.raises(RuntimeError, match="persisted 2 decisions"):
        run_matrix.execute_matrix_cell(
            object(), connection, "matrix-duplicate", "G2B-REPLAY-ANALYTICS", "supplier-northstar"
        )

    assert connection.runs["matrix-duplicate"][7] == "FAILED"


def test_matrix_requires_runner_role_and_bounded_session_parameters() -> None:
    connection = MatrixConnection(role="ACCOUNTADMIN")
    with pytest.raises(RuntimeError, match="require role BIDPILOT_RUNNER"):
        run_matrix._require_runner_role(connection)

    with pytest.raises(ValueError, match="Statement timeout"):
        run_matrix._configure_session(MatrixConnection(), "prefix", 0, 60)
    with pytest.raises(ValueError, match="Queued timeout"):
        run_matrix._configure_session(MatrixConnection(), "prefix", 300, 601)


class ExistingDecisionFrame:
    def __init__(self, count: int) -> None:
        self._count = count

    def filter(self, *_args, **_kwargs):
        return self

    def count(self) -> int:
        return self._count


class ExistingDecisionSession:
    def __init__(self, count: int) -> None:
        self.frame = ExistingDecisionFrame(count)

    def table(self, name: str):
        assert name == "BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS"
        return self.frame


def test_snowpark_decision_reuses_one_existing_row_and_rejects_duplicates() -> None:
    reused = snowpark_decision.evaluate_and_persist(
        ExistingDecisionSession(1),
        run_id="run-1",
        tenant_id="demo-tenant",
        opportunity_id="opp-1",
        opportunity_version="v1",
        supplier_profile_id="supplier-1",
        supplier_profile_version="v1",
    )
    assert reused == "reused"

    with pytest.raises(RuntimeError, match="2 persisted decisions"):
        snowpark_decision.evaluate_and_persist(
            ExistingDecisionSession(2),
            run_id="run-1",
            tenant_id="demo-tenant",
            opportunity_id="opp-1",
            opportunity_version="v1",
            supplier_profile_id="supplier-1",
            supplier_profile_version="v1",
        )


def test_role_sql_separates_source_artifact_lifecycle_and_cost_privileges() -> None:
    sql = (SNOWFLAKE_DIR / "sql" / "03_roles.sql").read_text()

    assert "GRANT SELECT ON ALL TABLES" not in sql
    assert "GRANT SELECT, INSERT, UPDATE ON ALL TABLES" not in sql
    assert "GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.OPPORTUNITIES TO ROLE BIDPILOT_RUNNER" in sql
    assert "GRANT SELECT, INSERT ON TABLE BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS" in sql
    assert "GRANT SELECT, INSERT, UPDATE ON TABLE BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS" in sql
    assert "GRANT SELECT, INSERT, UPDATE ON TABLE BIDPILOT_DEMO.BIDPILOT.OPPORTUNITIES" not in sql
    assert "CREATE RESOURCE MONITOR IF NOT EXISTS BIDPILOT_COST_MONITOR" in sql
    assert "STATEMENT_TIMEOUT_IN_SECONDS = 300" in sql
    assert "STATEMENT_QUEUED_TIMEOUT_IN_SECONDS = 60" in sql


def test_schema_binds_every_supplier_record_and_run_to_a_profile_version() -> None:
    schema = (SNOWFLAKE_DIR / "sql" / "01_schema.sql").read_text()
    seed = (SNOWFLAKE_DIR / "sql" / "02_seed_fixture.sql").read_text()

    for table in ("CREDENTIALS", "PEOPLE", "AVAILABILITY", "PAST_PROJECTS", "PAST_PROPOSALS"):
        block = schema.split(f".{table} (", 1)[1].split(");", 1)[0]
        assert "profile_version STRING" in block
    runs = schema.split(".AGENT_RUNS (", 1)[1].split(");", 1)[0]
    assert "supplier_profile_version STRING" in runs
    assert seed.count("profile_version") >= 5
