"""Local development persistence for a Bid Room.

Snowflake is the production target.  This store keeps the same versioned run
contract available while account provisioning is externally blocked.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from bidpilot.pursuit import PursuitBrief, WinPosition


class BidRoomStore:
    def __init__(self, path: Path) -> None:
        self.path = path
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
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def save(
        self,
        brief: PursuitBrief,
        opportunity_version: str,
        position: WinPosition,
        proposal_markdown: str,
        red_team_findings: tuple[str, ...],
    ) -> str:
        run_id = str(uuid4())
        brief_json = json.dumps(
            {
                "status": brief.status,
                "buyer_objective": brief.buyer_objective,
                "missing_eligibility": brief.missing_eligibility,
                "capacity_gap_hours": brief.capacity_gap_hours,
                "score_map": brief.score_map,
                "next_actions": brief.next_actions,
            }
        )
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO bid_runs (
                    run_id, opportunity_id, supplier_profile_id, opportunity_version,
                    status, selected_position, brief_json, proposal_markdown, red_team_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        return result
