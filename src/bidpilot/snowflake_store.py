"""Read authenticated Bid Room runs through a named Snowflake CLI connection."""

from __future__ import annotations

import json
import os
from contextlib import closing
from typing import Any

import snowflake.connector

from bidpilot.policy import POLICY_VERSION


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
        try:
            return snowflake.connector.connect(connection_name=self.connection_name)
        except Exception as error:  # connector errors vary by auth mechanism
            raise SnowflakeBidRoomError(f"Snowflake connection '{self.connection_name}' failed: {error}") from error

    @staticmethod
    def _rows(cursor) -> list[dict[str, Any]]:
        columns = [item[0].lower() for item in cursor.description or ()]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def list_runs(self) -> list[dict[str, Any]]:
        try:
            with closing(self._connect()) as connection, closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    SELECT a.run_id, a.opportunity_id, a.opportunity_version, a.supplier_profile_id,
                           a.policy_version, a.provider, a.state, a.created_at,
                           IFF(d.run_id IS NOT NULL AND w.run_id IS NOT NULL AND s.run_id IS NOT NULL
                               AND t.run_id IS NOT NULL AND a.policy_version = %s, TRUE, FALSE) AS is_complete
                    FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS a
                    LEFT JOIN (SELECT DISTINCT run_id FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS) d USING(run_id)
                    LEFT JOIN (SELECT DISTINCT run_id FROM BIDPILOT_DEMO.BIDPILOT.WIN_STRATEGIES) w USING(run_id)
                    LEFT JOIN (SELECT DISTINCT run_id FROM BIDPILOT_DEMO.BIDPILOT.PROPOSAL_SECTIONS) s USING(run_id)
                    LEFT JOIN (SELECT DISTINCT run_id FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_TASKS) t USING(run_id)
                    ORDER BY a.created_at DESC
                    """,
                    (POLICY_VERSION,),
                )
                return self._rows(cursor)
        except SnowflakeBidRoomError:
            raise
        except Exception as error:
            raise SnowflakeBidRoomError(f"Snowflake run listing failed: {error}") from error

    def load_run(self, run_id: str) -> dict[str, Any]:
        queries = {
            "run": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS WHERE run_id = %s",
            "decision": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS WHERE run_id = %s",
            "strategies": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.WIN_STRATEGIES WHERE run_id = %s ORDER BY selected DESC, strategy_id",
            "blueprint": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.RUBRIC_RESPONSE_PLANS WHERE run_id = %s ORDER BY weight DESC",
            "tasks": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PURSUIT_TASKS WHERE run_id = %s ORDER BY task_id",
            "sections": "SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PROPOSAL_SECTIONS WHERE run_id = %s ORDER BY section_id",
        }
        result: dict[str, Any] = {}
        try:
            with closing(self._connect()) as connection, closing(connection.cursor()) as cursor:
                for key, sql in queries.items():
                    cursor.execute(sql, (run_id,))
                    rows = self._rows(cursor)
                    result[key] = rows[0] if key in {"run", "decision"} and rows else (rows if key not in {"run", "decision"} else None)
        except SnowflakeBidRoomError:
            raise
        except Exception as error:
            raise SnowflakeBidRoomError(f"Snowflake run '{run_id}' could not be loaded: {error}") from error
        if not result["run"]:
            raise KeyError(run_id)
        trace = result["run"].get("trace")
        if isinstance(trace, str):
            result["run"]["trace"] = json.loads(trace)
        return result
