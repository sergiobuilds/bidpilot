"""Execute the BidPilot 2x2 policy matrix through an authenticated Snowpark session."""

from __future__ import annotations

import argparse
import json
from contextlib import closing
from typing import Any

import snowflake.connector
from snowflake.snowpark import Session

from snowpark_decision import POLICY_VERSION, evaluate_and_persist


MATRIX = (
    ("dq-northstar", "G2B-REPLAY-DATA-QUALITY", "supplier-northstar"),
    ("dq-atlas", "G2B-REPLAY-DATA-QUALITY", "supplier-atlas"),
    ("analytics-northstar", "G2B-REPLAY-ANALYTICS", "supplier-northstar"),
    ("analytics-atlas", "G2B-REPLAY-ANALYTICS", "supplier-atlas"),
)

EXPECTED_ROLE = "BIDPILOT_RUNNER"
TENANT_ID = "demo-tenant"
OPPORTUNITY_VERSION = "fixture-v1"
PROVIDER = "SNOWPARK"
DEFAULT_STATEMENT_TIMEOUT_SECONDS = 300
DEFAULT_QUEUED_TIMEOUT_SECONDS = 60


def _query_one(connection, sql: str, params: tuple[Any, ...] = ()) -> tuple[Any, ...] | None:
    with closing(connection.cursor()) as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()


def _query_all(connection, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with closing(connection.cursor()) as cursor:
        cursor.execute(sql, params)
        return list(cursor.fetchall())


def _execute(connection, sql: str, params: tuple[Any, ...] = ()) -> None:
    with closing(connection.cursor()) as cursor:
        cursor.execute(sql, params)


def _require_runner_role(connection) -> None:
    row = _query_one(connection, "SELECT CURRENT_ROLE()")
    actual = str(row[0]).upper() if row and row[0] is not None else ""
    if actual != EXPECTED_ROLE:
        raise RuntimeError(f"Matrix writes require role {EXPECTED_ROLE}; connected role is {actual or 'UNKNOWN'}.")


def _configure_session(connection, run_prefix: str, statement_timeout: int, queued_timeout: int) -> None:
    if not 1 <= statement_timeout <= 3600:
        raise ValueError("Statement timeout must be between 1 and 3600 seconds.")
    if not 1 <= queued_timeout <= 600:
        raise ValueError("Queued timeout must be between 1 and 600 seconds.")
    _execute(connection, f"ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = {statement_timeout}")
    _execute(connection, f"ALTER SESSION SET STATEMENT_QUEUED_TIMEOUT_IN_SECONDS = {queued_timeout}")
    query_tag = json.dumps({"app": "bidpilot_run_matrix", "run_prefix": run_prefix}, sort_keys=True)
    _execute(connection, "ALTER SESSION SET QUERY_TAG = %s", (query_tag,))


def _load_run(connection, run_id: str) -> list[tuple[Any, ...]]:
    return _query_all(
        connection,
        """
        SELECT tenant_id, opportunity_id, opportunity_version, supplier_profile_id,
               policy_version, provider, state
        FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS
        WHERE run_id = %s
        """,
        (run_id,),
    )


def _decision_count(connection, run_id: str) -> int:
    row = _query_one(
        connection,
        "SELECT COUNT(*) FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS WHERE run_id = %s",
        (run_id,),
    )
    return int(row[0]) if row else 0


def _trace(state: str, run_id: str, opportunity_id: str, supplier_profile_id: str, **extra: Any) -> str:
    payload: dict[str, Any] = {
        "lifecycle_state": state,
        "matrix": "2x2",
        "run_id": run_id,
        "opportunity_id": opportunity_id,
        "opportunity_version": OPPORTUNITY_VERSION,
        "supplier_profile_id": supplier_profile_id,
        "policy_version": POLICY_VERSION,
        "provider": PROVIDER,
    }
    payload.update(extra)
    return json.dumps(payload, sort_keys=True)


def _set_state(
    connection,
    run_id: str,
    state: str,
    opportunity_id: str,
    supplier_profile_id: str,
    **extra: Any,
) -> None:
    _execute(
        connection,
        """
        UPDATE BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS
        SET state = %s, policy_version = %s, trace = PARSE_JSON(%s)
        WHERE run_id = %s
        """,
        (state, POLICY_VERSION, _trace(state, run_id, opportunity_id, supplier_profile_id, **extra), run_id),
    )
    rows = _load_run(connection, run_id)
    if len(rows) != 1 or str(rows[0][6]).upper() != state:
        raise RuntimeError(f"Could not persist lifecycle state {state} for run {run_id!r}.")


def _validate_existing_run(
    row: tuple[Any, ...],
    run_id: str,
    opportunity_id: str,
    supplier_profile_id: str,
) -> str:
    expected = (TENANT_ID, opportunity_id, OPPORTUNITY_VERSION, supplier_profile_id, POLICY_VERSION, PROVIDER)
    actual = tuple(str(value) for value in row[:6])
    if actual != expected:
        raise RuntimeError(
            f"Run ID {run_id!r} already belongs to different inputs or execution metadata: {actual!r}."
        )
    return str(row[6]).upper()


def _start_run(connection, run_id: str, opportunity_id: str, supplier_profile_id: str) -> bool:
    rows = _load_run(connection, run_id)
    if len(rows) > 1:
        raise RuntimeError(f"Run ID {run_id!r} has {len(rows)} AGENT_RUNS rows; expected exactly one.")
    if rows:
        previous_state = _validate_existing_run(rows[0], run_id, opportunity_id, supplier_profile_id)
        decision_count = _decision_count(connection, run_id)
        if previous_state == "COMPLETED":
            if decision_count == 1:
                return False
            _set_state(
                connection,
                run_id,
                "FAILED",
                opportunity_id,
                supplier_profile_id,
                error="A completed run did not contain exactly one decision.",
                decision_count=decision_count,
            )
            raise RuntimeError(
                f"Completed run {run_id!r} has {decision_count} decisions; it was marked FAILED."
            )
        _set_state(
            connection,
            run_id,
            "RUNNING",
            opportunity_id,
            supplier_profile_id,
            retry_from_state=previous_state,
            decision_count_before_retry=decision_count,
        )
        return True

    _execute(
        connection,
        """
        INSERT INTO BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS (
            run_id, tenant_id, opportunity_id, opportunity_version, supplier_profile_id,
            policy_version, provider, state, trace
        )
        SELECT %s, %s, %s, %s, %s, %s, %s, 'RUNNING', PARSE_JSON(%s)
        WHERE NOT EXISTS (
            SELECT 1 FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS WHERE run_id = %s
        )
        """,
        (
            run_id,
            TENANT_ID,
            opportunity_id,
            OPPORTUNITY_VERSION,
            supplier_profile_id,
            POLICY_VERSION,
            PROVIDER,
            _trace("RUNNING", run_id, opportunity_id, supplier_profile_id),
            run_id,
        ),
    )
    rows = _load_run(connection, run_id)
    if len(rows) != 1:
        raise RuntimeError(f"Run ID {run_id!r} has {len(rows)} AGENT_RUNS rows after initialization.")
    _validate_existing_run(rows[0], run_id, opportunity_id, supplier_profile_id)
    return True


def execute_matrix_cell(
    session: Session,
    connection,
    run_id: str,
    opportunity_id: str,
    supplier_profile_id: str,
) -> str:
    """Execute one idempotent matrix cell with an explicit persisted lifecycle."""
    should_execute = _start_run(connection, run_id, opportunity_id, supplier_profile_id)
    if not should_execute:
        return "reused-completed"

    try:
        persistence = evaluate_and_persist(
            session,
            run_id=run_id,
            tenant_id=TENANT_ID,
            opportunity_id=opportunity_id,
            opportunity_version=OPPORTUNITY_VERSION,
            supplier_profile_id=supplier_profile_id,
        )
        decision_count = _decision_count(connection, run_id)
        if decision_count != 1:
            raise RuntimeError(f"Run {run_id!r} persisted {decision_count} decisions; expected exactly one.")
        _set_state(
            connection,
            run_id,
            "COMPLETED",
            opportunity_id,
            supplier_profile_id,
            decision_count=decision_count,
            decision_persistence=persistence,
        )
        return persistence
    except Exception as error:
        try:
            _set_state(
                connection,
                run_id,
                "FAILED",
                opportunity_id,
                supplier_profile_id,
                error_type=type(error).__name__,
                error=str(error)[:500],
                decision_count=_decision_count(connection, run_id),
            )
        except Exception as lifecycle_error:
            raise RuntimeError(
                f"Run {run_id!r} failed and its FAILED lifecycle state could not be persisted: {lifecycle_error}"
            ) from error
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--connection", default="bidpilot-runner")
    parser.add_argument("--run-prefix", required=True, help="Unique append-safe prefix for the four run IDs")
    parser.add_argument("--statement-timeout-seconds", type=int, default=DEFAULT_STATEMENT_TIMEOUT_SECONDS)
    parser.add_argument("--queued-timeout-seconds", type=int, default=DEFAULT_QUEUED_TIMEOUT_SECONDS)
    args = parser.parse_args()

    connector = snowflake.connector.connect(connection_name=args.connection)
    session: Session | None = None
    try:
        _require_runner_role(connector)
        _configure_session(connector, args.run_prefix, args.statement_timeout_seconds, args.queued_timeout_seconds)
        session = Session.builder.configs({"connection": connector}).create()
        for suffix, opportunity_id, supplier_profile_id in MATRIX:
            run_id = f"{args.run_prefix}-{suffix}"
            outcome = execute_matrix_cell(session, connector, run_id, opportunity_id, supplier_profile_id)
            print(f"{run_id}\t{outcome}")
    finally:
        if session is not None:
            session.close()
        else:
            connector.close()


if __name__ == "__main__":
    main()
