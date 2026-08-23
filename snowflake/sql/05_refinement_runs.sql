-- Additive refinement-run persistence. The v2 writer can append to these
-- objects but cannot mutate the verified legacy run or artifact tables.
-- Sequential retry reuse requires one private operator process to serialize
-- create_run calls and reuse its serialized_operator_token. Snowflake standard
-- tables do not enforce atomic uniqueness here.
-- Concurrent callers are not supported.
-- Public async multi-worker execution is out of scope.

CREATE TABLE IF NOT EXISTS BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUNS (
    request_id STRING NOT NULL,
    run_id STRING NOT NULL,
    execution_attempt NUMBER(10, 0) NOT NULL,
    tenant_id STRING NOT NULL,
    opportunity_id STRING NOT NULL,
    opportunity_version STRING NOT NULL,
    source_sha256 STRING NOT NULL,
    supplier_profile_id STRING NOT NULL,
    supplier_profile_version STRING NOT NULL,
    policy_version STRING NOT NULL,
    reviewed_request_sha256 STRING NOT NULL,
    serialized_operator_token STRING NOT NULL,
    created_by STRING NOT NULL,
    created_at TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS BIDPILOT_DEMO.BIDPILOT.RUN_EVENTS (
    request_id STRING NOT NULL,
    run_id STRING NOT NULL,
    event_id STRING NOT NULL,
    event_sequence NUMBER(18, 0) NOT NULL,
    stage STRING NOT NULL,
    capability STRING NOT NULL,
    command_identity STRING,
    event_status STRING NOT NULL,
    exit_code NUMBER(10, 0),
    started_at TIMESTAMP_TZ,
    completed_at TIMESTAMP_TZ,
    cortex_session_id STRING,
    cortex_cli_version STRING,
    input_sha256 STRING,
    output_sha256 STRING,
    query_ids ARRAY NOT NULL,
    log_reference STRING,
    outcome STRING,
    reason_count NUMBER(10, 0) NOT NULL DEFAULT 0,
    evidence_gap_count NUMBER(10, 0) NOT NULL DEFAULT 0,
    strategy_count NUMBER(10, 0) NOT NULL DEFAULT 0,
    score_plan_count NUMBER(10, 0) NOT NULL DEFAULT 0,
    proposal_section_count NUMBER(10, 0) NOT NULL DEFAULT 0,
    owned_work_item_count NUMBER(10, 0) NOT NULL DEFAULT 0,
    recorded_at TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS BIDPILOT_DEMO.BIDPILOT.PROPOSAL_CITATIONS (
    run_id STRING NOT NULL,
    citation_id STRING NOT NULL,
    criterion_id STRING NOT NULL,
    claim_id STRING NOT NULL,
    evidence_asset_id STRING NOT NULL,
    source_locator STRING NOT NULL,
    created_at TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS BIDPILOT_DEMO.BIDPILOT.RED_TEAM_FINDINGS (
    run_id STRING NOT NULL,
    finding_id STRING NOT NULL,
    severity STRING NOT NULL,
    finding STRING NOT NULL,
    owner STRING NOT NULL,
    required_action STRING NOT NULL,
    resolution_status STRING NOT NULL,
    created_at TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS BIDPILOT_DEMO.BIDPILOT.EXPORT_ARTIFACT_MANIFESTS (
    run_id STRING NOT NULL,
    export_id STRING NOT NULL,
    artifact_kind STRING NOT NULL,
    content_sha256 STRING NOT NULL,
    artifact_reference STRING NOT NULL,
    created_at TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS BIDPILOT_DEMO.BIDPILOT.APPROVED_PROPOSAL_SNAPSHOTS (
    run_id STRING NOT NULL,
    approval_id STRING NOT NULL,
    proposal_sha256 STRING NOT NULL,
    approver_id STRING NOT NULL,
    artifact_reference STRING NOT NULL,
    approved_at TIMESTAMP_TZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE SECURE VIEW BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_STATUS_V2 AS
WITH ranked_events AS (
    SELECT
        run_id,
        request_id,
        event_id,
        event_sequence,
        stage,
        event_status,
        recorded_at,
        ROW_NUMBER() OVER (
            PARTITION BY run_id
            ORDER BY event_sequence DESC, recorded_at DESC, event_id DESC
        ) AS event_rank
    FROM BIDPILOT_DEMO.BIDPILOT.RUN_EVENTS
),
latest_outcomes AS (
    SELECT run_id, outcome
    FROM BIDPILOT_DEMO.BIDPILOT.RUN_EVENTS
    WHERE outcome IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY run_id
        ORDER BY event_sequence DESC, recorded_at DESC, event_id DESC
    ) = 1
)
SELECT
    ranked_events.run_id,
    ranked_events.request_id,
    CASE
        WHEN event_status = 'FAILED' THEN 'FAILED'
        WHEN stage = 'FINALIZE' AND event_status = 'COMPLETED' THEN 'COMPLETED'
        WHEN event_status = 'QUEUED' THEN 'QUEUED'
        ELSE 'RUNNING'
    END AS current_state,
    latest_outcomes.outcome,
    ranked_events.event_id AS latest_event_id,
    ranked_events.event_sequence AS latest_event_sequence,
    ranked_events.recorded_at AS latest_event_at
FROM ranked_events
LEFT JOIN latest_outcomes USING (run_id)
WHERE ranked_events.event_rank = 1;

CREATE OR REPLACE SECURE VIEW BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_READBACK_V2 AS
WITH event_counts AS (
    SELECT
        run_id,
        COUNT(*) AS event_count,
        COUNT_IF(event_status = 'FAILED') AS failed_event_count,
        COUNT_IF(stage = 'SOURCE_CAPTURE' AND event_status = 'COMPLETED'
                 AND output_sha256 IS NOT NULL) AS source_capture_count,
        COUNT_IF(stage = 'PURSUIT_DECISION' AND event_status = 'COMPLETED'
                 AND outcome IS NOT NULL AND output_sha256 IS NOT NULL) AS pursuit_decision_count,
        COUNT_IF(stage = 'WIN_STRATEGY' AND event_status = 'COMPLETED'
                 AND output_sha256 IS NOT NULL) AS win_strategy_count,
        COUNT_IF(stage = 'PROPOSAL_DRAFT' AND event_status = 'COMPLETED'
                 AND output_sha256 IS NOT NULL) AS proposal_draft_count,
        COUNT_IF(stage = 'RED_TEAM' AND event_status = 'COMPLETED'
                 AND output_sha256 IS NOT NULL) AS red_team_count,
        COUNT_IF(stage = 'OWNED_WORK' AND event_status = 'COMPLETED'
                 AND output_sha256 IS NOT NULL) AS owned_work_count,
        COUNT_IF(stage = 'FINALIZE' AND event_status = 'COMPLETED'
                 AND output_sha256 IS NOT NULL) AS finalize_count,
        MAX(IFF(stage = 'PURSUIT_DECISION' AND outcome = 'NO-GO'
                AND event_status = 'COMPLETED', reason_count, 0)) AS no_go_reason_count,
        MAX(IFF(stage = 'PURSUIT_DECISION' AND outcome = 'REVIEW'
                AND event_status = 'COMPLETED', evidence_gap_count, 0)) AS review_evidence_gap_count,
        MAX(IFF(stage = 'WIN_STRATEGY' AND event_status = 'COMPLETED',
                strategy_count, 0)) AS strategy_count,
        MAX(IFF(stage = 'WIN_STRATEGY' AND event_status = 'COMPLETED',
                score_plan_count, 0)) AS score_plan_count,
        MAX(IFF(stage = 'PROPOSAL_DRAFT' AND event_status = 'COMPLETED',
                proposal_section_count, 0)) AS proposal_section_count,
        MAX(IFF(stage = 'OWNED_WORK' AND event_status = 'COMPLETED',
                owned_work_item_count, 0)) AS owned_work_item_count
    FROM BIDPILOT_DEMO.BIDPILOT.RUN_EVENTS
    GROUP BY run_id
),
citation_counts AS (
    SELECT run_id, COUNT(*) AS proposal_citation_count
    FROM BIDPILOT_DEMO.BIDPILOT.PROPOSAL_CITATIONS
    GROUP BY run_id
),
finding_counts AS (
    SELECT run_id, COUNT(*) AS red_team_finding_count
    FROM BIDPILOT_DEMO.BIDPILOT.RED_TEAM_FINDINGS
    GROUP BY run_id
)
SELECT
    runs.*,
    status.current_state,
    status.outcome,
    status.latest_event_id,
    status.latest_event_sequence,
    status.latest_event_at,
    COALESCE(events.event_count, 0) AS event_count,
    COALESCE(citations.proposal_citation_count, 0) AS proposal_citation_count,
    COALESCE(findings.red_team_finding_count, 0) AS red_team_finding_count,
    CASE
        WHEN COALESCE(events.failed_event_count, 0) > 0 THEN FALSE
        WHEN status.current_state <> 'COMPLETED' THEN FALSE
        WHEN outcome = 'NO-GO' THEN
            COALESCE(events.source_capture_count, 0) > 0
            AND COALESCE(events.pursuit_decision_count, 0) > 0
            AND COALESCE(events.no_go_reason_count, 0) > 0
            AND COALESCE(events.finalize_count, 0) > 0
        WHEN outcome = 'REVIEW' THEN
            COALESCE(events.source_capture_count, 0) > 0
            AND COALESCE(events.pursuit_decision_count, 0) > 0
            AND COALESCE(events.review_evidence_gap_count, 0) > 0
            AND COALESCE(events.owned_work_count, 0) > 0
            AND COALESCE(events.owned_work_item_count, 0) > 0
            AND COALESCE(findings.red_team_finding_count, 0) > 0
            AND COALESCE(events.finalize_count, 0) > 0
        WHEN outcome = 'PURSUE' THEN
            COALESCE(events.source_capture_count, 0) > 0
            AND COALESCE(events.pursuit_decision_count, 0) > 0
            AND COALESCE(events.win_strategy_count, 0) > 0
            AND COALESCE(events.strategy_count, 0) >= 2
            AND COALESCE(events.score_plan_count, 0) > 0
            AND COALESCE(events.proposal_draft_count, 0) > 0
            AND COALESCE(events.proposal_section_count, 0) > 0
            AND COALESCE(citations.proposal_citation_count, 0) > 0
            AND COALESCE(events.red_team_count, 0) > 0
            AND COALESCE(events.owned_work_count, 0) > 0
            AND COALESCE(events.owned_work_item_count, 0) > 0
            AND COALESCE(events.finalize_count, 0) > 0
        ELSE FALSE
    END AS is_complete
FROM BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUNS AS runs
LEFT JOIN BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_STATUS_V2 AS status USING (run_id, request_id)
LEFT JOIN event_counts AS events USING (run_id)
LEFT JOIN citation_counts AS citations USING (run_id)
LEFT JOIN finding_counts AS findings USING (run_id);

CREATE ROLE IF NOT EXISTS BIDPILOT_REFINEMENT_RUNNER;

REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA BIDPILOT_DEMO.BIDPILOT
  FROM ROLE BIDPILOT_REFINEMENT_RUNNER;

GRANT USAGE ON WAREHOUSE BIDPILOT_WH TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT USAGE ON DATABASE BIDPILOT_DEMO TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT USAGE ON SCHEMA BIDPILOT_DEMO.BIDPILOT TO ROLE BIDPILOT_REFINEMENT_RUNNER;

-- The refinement writer reads verified inputs and appends only to v2 tables.
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.OPPORTUNITIES TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.OPPORTUNITY_DOCUMENTS TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.REQUIREMENTS TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.EVALUATION_CRITERIA TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.SUBMISSION_ITEMS TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.SUPPLIER_PROFILES TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.CREDENTIALS TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.PEOPLE TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.AVAILABILITY TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.PAST_PROJECTS TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.PAST_PROPOSALS TO ROLE BIDPILOT_REFINEMENT_RUNNER;

GRANT INSERT ON TABLE BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUNS TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT INSERT ON TABLE BIDPILOT_DEMO.BIDPILOT.RUN_EVENTS TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT INSERT ON TABLE BIDPILOT_DEMO.BIDPILOT.PROPOSAL_CITATIONS TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT INSERT ON TABLE BIDPILOT_DEMO.BIDPILOT.RED_TEAM_FINDINGS TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT INSERT ON TABLE BIDPILOT_DEMO.BIDPILOT.EXPORT_ARTIFACT_MANIFESTS TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT INSERT ON TABLE BIDPILOT_DEMO.BIDPILOT.APPROVED_PROPOSAL_SNAPSHOTS TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON VIEW BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_STATUS_V2 TO ROLE BIDPILOT_REFINEMENT_RUNNER;
GRANT SELECT ON VIEW BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_READBACK_V2 TO ROLE BIDPILOT_REFINEMENT_RUNNER;

-- The existing authenticated reader can inspect v2 readback and its evidence.
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.RUN_EVENTS TO ROLE BIDPILOT_READER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.PROPOSAL_CITATIONS TO ROLE BIDPILOT_READER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.RED_TEAM_FINDINGS TO ROLE BIDPILOT_READER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.EXPORT_ARTIFACT_MANIFESTS TO ROLE BIDPILOT_READER;
GRANT SELECT ON TABLE BIDPILOT_DEMO.BIDPILOT.APPROVED_PROPOSAL_SNAPSHOTS TO ROLE BIDPILOT_READER;
GRANT SELECT ON VIEW BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_STATUS_V2 TO ROLE BIDPILOT_READER;
GRANT SELECT ON VIEW BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_READBACK_V2 TO ROLE BIDPILOT_READER;
