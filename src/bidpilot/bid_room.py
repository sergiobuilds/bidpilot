"""Local development persistence for a Bid Room.

Snowflake is the production target.  This store keeps the same versioned run
contract available while account provisioning is externally blocked.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from bidpilot.pursuit import PursuitBrief


class BidRoomStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bid_runs (
                    run_id TEXT PRIMARY KEY,
                    opportunity_id TEXT NOT NULL,
                    supplier_profile_id TEXT NOT NULL,
                    opportunity_version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    selected_position TEXT NOT NULL,
                    brief_json TEXT NOT NULL,
                    proposal_markdown TEXT NOT NULL,
                    red_team_json TEXT NOT NULL,
                    tasks_json TEXT NOT NULL DEFAULT '[]',
                    agent_run_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            existing = {row[1] for row in connection.execute("PRAGMA table_info(bid_runs)")}
            if "tasks_json" not in existing:
                connection.execute("ALTER TABLE bid_runs ADD COLUMN tasks_json TEXT NOT NULL DEFAULT '[]'")
            if "agent_run_json" not in existing:
                connection.execute("ALTER TABLE bid_runs ADD COLUMN agent_run_json TEXT NOT NULL DEFAULT '{}'")

    def save(
        self,
        brief: PursuitBrief,
        opportunity_version: str,
        proposal_markdown: str,
        red_team_findings: tuple[str, ...],
        tasks: tuple[dict, ...] = (),
        agent_run: dict | None = None,
    ) -> str:
        run_id = str(uuid4())
        position = brief.win_positions[brief.selected_position_index]
        brief_json = json.dumps(asdict(brief))
        agent_run = agent_run or {
            "provider": "local-development-adapter",
            "state": "not-executed-in-snowflake-or-coco",
            "steps": ["pursuit", "strategy", "proposal", "red-team", "task-plan"],
        }
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO bid_runs (
                    run_id, opportunity_id, supplier_profile_id, opportunity_version,
                    status, selected_position, brief_json, proposal_markdown, red_team_json,
                    tasks_json, agent_run_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    brief.opportunity_id,
                    brief.supplier_profile_id,
                    opportunity_version,
                    brief.status,
                    position.statement,
                    brief_json,
                    proposal_markdown,
                    json.dumps(red_team_findings),
                    json.dumps(tasks),
                    json.dumps(agent_run),
                ),
            )
        return run_id

    def load(self, run_id: str) -> dict:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT * FROM bid_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            columns = [column[0] for column in connection.execute("SELECT * FROM bid_runs LIMIT 0").description]
        if row is None:
            raise KeyError(run_id)
        result = dict(zip(columns, row, strict=True))
        result["brief"] = json.loads(result.pop("brief_json"))
        result["red_team_findings"] = tuple(json.loads(result.pop("red_team_json")))
        result["tasks"] = tuple(json.loads(result.pop("tasks_json")))
        result["agent_run"] = json.loads(result.pop("agent_run_json"))
        return result

    def latest(self, opportunity_id: str, supplier_profile_id: str, opportunity_version: str, selected_position: str) -> dict | None:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                """
                SELECT run_id FROM bid_runs
                WHERE opportunity_id = ? AND supplier_profile_id = ?
                  AND opportunity_version = ? AND selected_position = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (opportunity_id, supplier_profile_id, opportunity_version, selected_position),
            ).fetchone()
        return self.load(row[0]) if row else None
