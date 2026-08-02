"""Read authenticated Bid Room runs through a named Snowflake CLI connection."""

from __future__ import annotations

import json
import os
from contextlib import closing
from typing import Any

import snowflake.connector

from bidpilot.policy import POLICY_VERSION

EXPECTED_READER_ROLE = "BIDPILOT_READER"
EXPECTED_PROVIDER = "CORTEX_CODE_CLI"


RUN_COMPLETENESS_JOINS = """
    LEFT JOIN (
        SELECT run_id, COUNT(*) AS agent_count
        FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS GROUP BY run_id
    ) ar USING(run_id)
    LEFT JOIN (
        SELECT run_id, COUNT(*) AS decision_count,
               COUNT_IF(status = 'PURSUE') AS pursue_decision_count
        FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS GROUP BY run_id
    ) d USING(run_id)
    LEFT JOIN (
        SELECT run_id, COUNT(*) AS strategy_count,
               COUNT_IF(selected = TRUE) AS selected_strategy_count,
               COUNT_IF(NULLIF(TRIM(title), '') IS NULL
                     OR NULLIF(TRIM(statement), '') IS NULL
                     OR proof_cards IS NULL) AS invalid_strategy_count
        FROM BIDPILOT_DEMO.BIDPILOT.WIN_STRATEGIES GROUP BY run_id
    ) w USING(run_id)
    LEFT JOIN (
        SELECT run_id, COUNT(*) AS plan_count,
               COUNT_IF(NULLIF(TRIM(criterion_name), '') IS NULL
                     OR weight <= 0
                     OR NULLIF(TRIM(claim), '') IS NULL
                     OR assets IS NULL OR ARRAY_SIZE(assets) = 0
                     OR NULLIF(TRIM(owner), '') IS NULL) AS invalid_plan_count,
               SUM(weight) AS plan_weight_total
        FROM BIDPILOT_DEMO.BIDPILOT.RUBRIC_RESPONSE_PLANS GROUP BY run_id
    ) p USING(run_id)
    LEFT JOIN (
        SELECT run_id, COUNT(*) AS section_count,
               COUNT_IF(NULLIF(TRIM(section_id), '') IS NULL
                     OR NULLIF(TRIM(criterion_name), '') IS NULL
                     OR NULLIF(TRIM(section_markdown), '') IS NULL) AS invalid_section_count
        FROM BIDPILOT_DEMO.BIDPILOT.PROPOSAL_SECTIONS GROUP BY run_id
    ) s USING(run_id)
    LEFT JOIN (
        SELECT run_id, COUNT(*) AS task_count,
               COUNT_IF(NULLIF(TRIM(task_id), '') IS NULL
                     OR NULLIF(TRIM(task_name), '') IS NULL
                     OR NULLIF(TRIM(owner), '') IS NULL
                     OR NULLIF(TRIM(status), '') IS NULL) AS invalid_task_count
        FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_TASKS GROUP BY run_id
    ) t USING(run_id)
"""

RUN_COMPLETENESS_EXPRESSION = """
    a.state = 'COMPLETED'
    AND UPPER(a.provider) = %s
    AND a.policy_version = %s
    AND NULLIF(TRIM(a.supplier_profile_version), '') IS NOT NULL
    AND COALESCE(ar.agent_count, 0) = 1
    AND COALESCE(d.decision_count, 0) = 1
    AND COALESCE(d.pursue_decision_count, 0) = 1
    AND COALESCE(w.strategy_count, 0) >= 2
    AND COALESCE(w.selected_strategy_count, 0) = 1
    AND COALESCE(w.invalid_strategy_count, 0) = 0
    AND COALESCE(p.plan_count, 0) > 0
    AND COALESCE(p.invalid_plan_count, 0) = 0
    AND ABS(COALESCE(p.plan_weight_total, 0) - 100) <= 0.01
    AND COALESCE(s.section_count, 0) >= COALESCE(p.plan_count, 0)
    AND COALESCE(s.invalid_section_count, 0) = 0
    AND COALESCE(t.task_count, 0) > 0
    AND COALESCE(t.invalid_task_count, 0) = 0
    AND a.trace:execution_provenance:cortex_session_id::STRING IS NOT NULL
    AND a.trace:execution_provenance:cortex_cli_version::STRING IS NOT NULL
    AND a.trace:execution_provenance:snowpark_decision_query_id::STRING IS NOT NULL
    AND a.trace:execution_provenance:completion_audit_query_id::STRING IS NOT NULL
    AND a.trace:execution_provenance:cortex_write_query_ids IS NOT NULL
    AND ARRAY_SIZE(a.trace:execution_provenance:cortex_write_query_ids) > 0
"""


class SnowflakeBidRoomError(RuntimeError):
    """Raised when authenticated mode was requested but cannot be used."""


def configured_connection_name() -> str | None:
    return os.getenv("BIDPILOT_SNOWFLAKE_CONNECTION") or None


class SnowflakeBidRoomStore:
    def __init__(self, connection_name: str) -> None:
        if not connection_name.strip():
            raise ValueError("A named Snowflake connection is required.")
        self.connection_name = connection_name

    def _connect(self):
        connection = None
        try:
            connection = snowflake.connector.connect(connection_name=self.connection_name)
            with closing(connection.cursor()) as cursor:
                cursor.execute("SELECT CURRENT_ROLE()")
                row = cursor.fetchone()
            actual_role = str(row[0]).upper() if row and row[0] is not None else ""
            if actual_role != EXPECTED_READER_ROLE:
                raise SnowflakeBidRoomError(
                    f"Authenticated Bid Room requires role {EXPECTED_READER_ROLE}; "
                    f"connection '{self.connection_name}' uses {actual_role or 'UNKNOWN'}."
                )
            return connection
        except SnowflakeBidRoomError:
            if connection is not None:
                connection.close()
            raise
        except Exception as error:  # connector errors vary by auth mechanism
            if connection is not None:
                connection.close()
            raise SnowflakeBidRoomError(f"Snowflake connection '{self.connection_name}' failed: {error}") from error

    @staticmethod
    def _rows(cursor) -> list[dict[str, Any]]:
        columns = [item[0].lower() for item in cursor.description or ()]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def list_runs(self) -> list[dict[str, Any]]:
        try:
            with closing(self._connect()) as connection, closing(connection.cursor()) as cursor:
                cursor.execute(
                    f"""
                    SELECT a.run_id, a.opportunity_id, a.opportunity_version, a.supplier_profile_id,
                           a.policy_version, a.provider, a.state, a.created_at,
                           COALESCE(ar.agent_count, 0) AS agent_count,
                           COALESCE(d.decision_count, 0) AS decision_count,
                           COALESCE(d.pursue_decision_count, 0) AS pursue_decision_count,
                           COALESCE(w.strategy_count, 0) AS strategy_count,
                           COALESCE(w.selected_strategy_count, 0) AS selected_strategy_count,
                           COALESCE(w.invalid_strategy_count, 0) AS invalid_strategy_count,
                           COALESCE(p.plan_count, 0) AS plan_count,
                           COALESCE(p.invalid_plan_count, 0) AS invalid_plan_count,
                           COALESCE(p.plan_weight_total, 0) AS plan_weight_total,
                           COALESCE(s.section_count, 0) AS section_count,
                           COALESCE(s.invalid_section_count, 0) AS invalid_section_count,
                           COALESCE(t.task_count, 0) AS task_count,
                           COALESCE(t.invalid_task_count, 0) AS invalid_task_count,
                           IFF({RUN_COMPLETENESS_EXPRESSION}, TRUE, FALSE) AS is_complete
                    FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS a
                    {RUN_COMPLETENESS_JOINS}
                    ORDER BY a.created_at DESC
                    """,
                    (EXPECTED_PROVIDER, POLICY_VERSION),
                )
                return self._rows(cursor)
        except SnowflakeBidRoomError:
            raise
        except Exception as error:
            raise SnowflakeBidRoomError(f"Snowflake run listing failed: {error}") from error

    def load_run(self, run_id: str) -> dict[str, Any]:
        queries = {
            "run": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS WHERE run_id = %s",
            "opportunity": """
                SELECT o.* FROM BIDPILOT_DEMO.BIDPILOT.OPPORTUNITIES o
                JOIN BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS a
                  ON o.tenant_id = a.tenant_id AND o.opportunity_id = a.opportunity_id
                 AND o.opportunity_version = a.opportunity_version
                WHERE a.run_id = %s
            """,
            "supplier": """
                SELECT p.* FROM BIDPILOT_DEMO.BIDPILOT.SUPPLIER_PROFILES p
                JOIN BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS a
                  ON p.tenant_id = a.tenant_id AND p.supplier_profile_id = a.supplier_profile_id
                 AND p.profile_version = a.supplier_profile_version
                WHERE a.run_id = %s
            """,
            "decision": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS WHERE run_id = %s",
            "strategies": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.WIN_STRATEGIES WHERE run_id = %s ORDER BY selected DESC, strategy_id",
            "blueprint": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.RUBRIC_RESPONSE_PLANS WHERE run_id = %s ORDER BY weight DESC",
            "tasks": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_TASKS WHERE run_id = %s ORDER BY task_id",
            "sections": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PROPOSAL_SECTIONS WHERE run_id = %s ORDER BY section_id",
            "completeness": f"""
                SELECT COALESCE(ar.agent_count, 0) AS agent_count,
                       COALESCE(d.decision_count, 0) AS decision_count,
                       COALESCE(d.pursue_decision_count, 0) AS pursue_decision_count,
                       COALESCE(w.strategy_count, 0) AS strategy_count,
                       COALESCE(w.selected_strategy_count, 0) AS selected_strategy_count,
                       COALESCE(w.invalid_strategy_count, 0) AS invalid_strategy_count,
                       COALESCE(p.plan_count, 0) AS plan_count,
                       COALESCE(p.invalid_plan_count, 0) AS invalid_plan_count,
                       COALESCE(p.plan_weight_total, 0) AS plan_weight_total,
                       COALESCE(s.section_count, 0) AS section_count,
                       COALESCE(s.invalid_section_count, 0) AS invalid_section_count,
                       COALESCE(t.task_count, 0) AS task_count,
                       COALESCE(t.invalid_task_count, 0) AS invalid_task_count,
                       IFF({RUN_COMPLETENESS_EXPRESSION}, TRUE, FALSE) AS is_complete
                FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS a
                {RUN_COMPLETENESS_JOINS}
                WHERE a.run_id = %s
            """,
        }
        result: dict[str, Any] = {}
        try:
            with closing(self._connect()) as connection, closing(connection.cursor()) as cursor:
                for key, sql in queries.items():
                    params = (EXPECTED_PROVIDER, POLICY_VERSION, run_id) if key == "completeness" else (run_id,)
                    cursor.execute(sql, params)
                    rows = self._rows(cursor)
                    singular = {"run", "opportunity", "supplier", "decision", "completeness"}
                    result[key] = rows[0] if key in singular and rows else (rows if key not in singular else None)
        except SnowflakeBidRoomError:
            raise
        except Exception as error:
            raise SnowflakeBidRoomError(f"Snowflake run '{run_id}' could not be loaded: {error}") from error
        if not result["run"]:
            raise KeyError(run_id)
        completeness = result.pop("completeness", None)
        if not completeness or not completeness.get("is_complete"):
            raise SnowflakeBidRoomError(
                f"Snowflake run '{run_id}' is incomplete or lacks required Cortex provenance."
            )
        trace = result["run"].get("trace")
        if isinstance(trace, str):
            try:
                result["run"]["trace"] = json.loads(trace)
            except json.JSONDecodeError as error:
                raise SnowflakeBidRoomError(
                    f"Snowflake run '{run_id}' has a malformed execution trace."
                ) from error
        if not isinstance(result["run"].get("trace"), dict):
            raise SnowflakeBidRoomError(
                f"Snowflake run '{run_id}' has a malformed execution trace."
            )
        return result
