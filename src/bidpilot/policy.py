"""Versioned deterministic policy shared with the Snowpark implementation."""

from __future__ import annotations

POLICY_VERSION = "2026-08-02.v1"


def pursue_status(missing_eligibility_count: int, capacity_gap_hours: int, comparable_project_count: int) -> str:
    if missing_eligibility_count or capacity_gap_hours:
        return "NO-GO"
    if comparable_project_count < 2:
        return "REVIEW"
    return "PURSUE"
