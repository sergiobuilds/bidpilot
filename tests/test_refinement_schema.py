from __future__ import annotations

import re
from pathlib import Path


SCHEMA_PATH = Path(__file__).parents[1] / "snowflake" / "sql" / "05_refinement_runs.sql"
V2_TABLES = {
    "REFINEMENT_RUNS",
    "RUN_EVENTS",
    "PROPOSAL_CITATIONS",
    "RED_TEAM_FINDINGS",
    "EXPORT_ARTIFACT_MANIFESTS",
    "APPROVED_PROPOSAL_SNAPSHOTS",
}
LEGACY_TABLES = {
    "AGENT_RUNS",
    "PURSUIT_DECISIONS",
    "WIN_STRATEGIES",
    "RUBRIC_RESPONSE_PLANS",
    "PROPOSAL_SECTIONS",
    "PURSUIT_TASKS",
}


def _schema() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8").upper()


def _table_block(schema: str, table: str) -> str:
    marker = f"CREATE TABLE IF NOT EXISTS BIDPILOT_DEMO.BIDPILOT.{table} ("
    return schema.split(marker, 1)[1].split(";", 1)[0]


def test_schema_adds_only_the_six_refinement_tables() -> None:
    schema = _schema()
    created_tables = set(
        re.findall(
            r"CREATE TABLE IF NOT EXISTS BIDPILOT_DEMO\.BIDPILOT\.([A-Z_]+)\s*\(",
            schema,
        )
    )

    assert created_tables == V2_TABLES
    assert not any(f"ALTER TABLE BIDPILOT_DEMO.BIDPILOT.{table}" in schema for table in LEGACY_TABLES)


def test_refinement_runs_has_immutable_identity_and_no_mutable_status_column() -> None:
    block = _table_block(_schema(), "REFINEMENT_RUNS")

    for column in (
        "REQUEST_ID STRING NOT NULL",
        "RUN_ID STRING NOT NULL",
        "EXECUTION_ATTEMPT NUMBER(10, 0) NOT NULL",
        "SOURCE_SHA256 STRING NOT NULL",
        "SUPPLIER_PROFILE_VERSION STRING NOT NULL",
        "POLICY_VERSION STRING NOT NULL",
        "REVIEWED_REQUEST_SHA256 STRING NOT NULL",
        "OPERATOR_LEASE_ID STRING NOT NULL",
        "CREATED_AT TIMESTAMP_TZ NOT NULL",
    ):
        assert column in block
    assert "STATUS STRING" not in block
    assert "STATE STRING" not in block
    assert "OUTCOME STRING" not in block


def test_run_events_carry_sanitized_execution_evidence() -> None:
    block = _table_block(_schema(), "RUN_EVENTS")

    for column in (
        "EVENT_SEQUENCE NUMBER(18, 0) NOT NULL",
        "STAGE STRING NOT NULL",
        "CAPABILITY STRING NOT NULL",
        "COMMAND_IDENTITY STRING",
        "EVENT_STATUS STRING NOT NULL",
        "EXIT_CODE NUMBER(10, 0)",
        "STARTED_AT TIMESTAMP_TZ",
        "COMPLETED_AT TIMESTAMP_TZ",
        "CORTEX_SESSION_ID STRING",
        "CORTEX_CLI_VERSION STRING",
        "INPUT_SHA256 STRING",
        "OUTPUT_SHA256 STRING",
        "QUERY_IDS ARRAY NOT NULL",
        "LOG_REFERENCE STRING",
        "OUTCOME STRING",
        "REASON_COUNT NUMBER(10, 0) NOT NULL DEFAULT 0",
        "EVIDENCE_GAP_COUNT NUMBER(10, 0) NOT NULL DEFAULT 0",
        "STRATEGY_COUNT NUMBER(10, 0) NOT NULL DEFAULT 0",
        "SCORE_PLAN_COUNT NUMBER(10, 0) NOT NULL DEFAULT 0",
        "PROPOSAL_SECTION_COUNT NUMBER(10, 0) NOT NULL DEFAULT 0",
        "OWNED_WORK_ITEM_COUNT NUMBER(10, 0) NOT NULL DEFAULT 0",
    ):
        assert column in block
    for forbidden in ("RAW_LOG", "STDOUT", "STDERR", "ENVIRONMENT", "PROMPT_TEXT"):
        assert forbidden not in block


def test_refinement_role_has_insert_only_dml_on_v2_and_no_legacy_dml() -> None:
    schema = _schema()
    role = "BIDPILOT_REFINEMENT_RUNNER"

    granted_insert_tables = set(
        re.findall(
            rf"GRANT INSERT ON TABLE BIDPILOT_DEMO\.BIDPILOT\.([A-Z_]+) TO ROLE {role}",
            schema,
        )
    )
    assert granted_insert_tables == V2_TABLES

    dml_grants = re.findall(
        rf"GRANT ([A-Z, ]+) ON TABLE BIDPILOT_DEMO\.BIDPILOT\.([A-Z_]+) TO ROLE {role}",
        schema,
    )
    for privileges, table in dml_grants:
        if table in LEGACY_TABLES:
            assert not {"INSERT", "UPDATE", "DELETE", "TRUNCATE"}.intersection(privileges.replace(" ", "").split(","))
        if table in V2_TABLES:
            assert privileges.strip() == "INSERT"

    assert "GRANT UPDATE" not in schema
    assert "GRANT DELETE" not in schema
    assert "GRANT TRUNCATE" not in schema
    assert (
        "GRANT SELECT ON VIEW BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_READBACK_V2 "
        f"TO ROLE {role}"
    ) in schema


def test_status_and_completeness_are_event_derived_and_outcome_aware() -> None:
    schema = _schema()

    assert "CREATE OR REPLACE SECURE VIEW BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_STATUS_V2" in schema
    assert "FROM BIDPILOT_DEMO.BIDPILOT.RUN_EVENTS" in schema
    assert "ROW_NUMBER() OVER" in schema
    assert "PARTITION BY RUN_ID" in schema
    assert "ORDER BY EVENT_SEQUENCE DESC" in schema
    assert "WHEN EVENT_STATUS = 'FAILED' THEN 'FAILED'" in schema
    assert "WHEN STAGE = 'FINALIZE' AND EVENT_STATUS = 'COMPLETED' THEN 'COMPLETED'" in schema

    assert "CREATE OR REPLACE SECURE VIEW BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_READBACK_V2" in schema
    assert "WHEN OUTCOME = 'NO-GO'" in schema
    assert "WHEN OUTCOME = 'REVIEW'" in schema
    assert "WHEN OUTCOME = 'PURSUE'" in schema
    for stage in (
        "SOURCE_CAPTURE",
        "PURSUIT_DECISION",
        "WIN_STRATEGY",
        "PROPOSAL_DRAFT",
        "RED_TEAM",
        "OWNED_WORK",
        "FINALIZE",
    ):
        assert stage in schema
    assert "PROPOSAL_CITATION_COUNT" in schema
    assert "RED_TEAM_FINDING_COUNT" in schema
    for count in (
        "NO_GO_REASON_COUNT",
        "REVIEW_EVIDENCE_GAP_COUNT",
        "STRATEGY_COUNT",
        "SCORE_PLAN_COUNT",
        "PROPOSAL_SECTION_COUNT",
        "OWNED_WORK_ITEM_COUNT",
    ):
        assert count in schema
