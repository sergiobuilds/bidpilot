from __future__ import annotations

from dataclasses import asdict

import pytest

from bidpilot.refinement_store import (
    ALLOWED_STAGES,
    ExecutionEvidence,
    RefinementStoreError,
    SnowflakeRefinementStore,
    deterministic_request_id,
    deterministic_run_id,
)


SOURCE_SHA256 = "a" * 64
REQUEST_SHA256 = "b" * 64


class FakeCursor:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.description: list[tuple[str]] = []
        self.rows: list[tuple] = []

    def execute(self, sql: str, params: tuple = ()) -> None:
        self.connection.executed.append((sql, params))
        if "CURRENT_ROLE()" in sql:
            self.description = [("CURRENT_ROLE",)]
            self.rows = [(self.connection.role,)]
            return
        if (
            "FROM BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_READBACK_V2" in sql
            and "WHERE request_id = %s AND execution_attempt = %s" in sql
        ):
            self.description = [
                ("REQUEST_ID",),
                ("RUN_ID",),
                ("EXECUTION_ATTEMPT",),
                ("REVIEWED_REQUEST_SHA256",),
                ("OPERATOR_LEASE_ID",),
            ]
            row = self.connection.run_identities.get((params[0], params[1]))
            self.rows = [row] if row else []
            return
        for marker, description, rows in self.connection.responses:
            if marker in sql:
                self.description = [(name,) for name in description]
                self.rows = list(rows)
                return
        if "INSERT INTO BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUNS" in sql:
            self.connection.run_identities[(params[0], params[2])] = (
                params[0],
                params[1],
                params[2],
                params[10],
                params[11],
            )
            self.description = []
            self.rows = []
            return
        if sql.lstrip().upper().startswith("INSERT INTO"):
            self.description = []
            self.rows = []
            return
        raise AssertionError(f"Unexpected SQL in fake Snowflake connection: {sql}")

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(
        self,
        role: str = "BIDPILOT_REFINEMENT_RUNNER",
        responses: list[tuple] | None = None,
    ) -> None:
        self.role = role
        self.responses = responses or []
        self.executed: list[tuple[str, tuple]] = []
        self.run_identities: dict[tuple[str, int], tuple] = {}

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)


def valid_evidence(**overrides) -> ExecutionEvidence:
    values = {
        "request_id": "req_123",
        "run_id": "run_123",
        "event_id": "evt_001",
        "event_sequence": 1,
        "stage": "SOURCE_CAPTURE",
        "capability": "coco.session.execute",
        "command_identity": "source-capture-v1",
        "event_status": "COMPLETED",
        "exit_code": 0,
        "started_at": "2026-08-24T00:00:00+00:00",
        "completed_at": "2026-08-24T00:00:01+00:00",
        "cortex_session_id": "session-123",
        "cortex_cli_version": "1.2.3",
        "input_sha256": "c" * 64,
        "output_sha256": "d" * 64,
        "query_ids": ("query-1", "query-2"),
        "log_reference": "evidence/run_123/evt_001.json",
        "outcome": None,
        "reason_count": 0,
        "evidence_gap_count": 0,
        "strategy_count": 0,
        "score_plan_count": 0,
        "proposal_section_count": 0,
        "owned_work_item_count": 0,
    }
    values.update(overrides)
    return ExecutionEvidence.from_mapping(values)


def test_request_and_run_identity_are_canonical_and_attempt_aware() -> None:
    request_id = deterministic_request_id(
        source_sha256=SOURCE_SHA256.upper(),
        supplier_profile_version=" supplier-v2 ",
        policy_version=" policy-v3 ",
    )

    assert request_id == deterministic_request_id(
        source_sha256=SOURCE_SHA256,
        supplier_profile_version="supplier-v2",
        policy_version="policy-v3",
    )
    assert request_id.startswith("req_")
    assert deterministic_run_id(request_id=request_id, execution_attempt=1).startswith("run_")
    assert deterministic_run_id(request_id=request_id, execution_attempt=1) != deterministic_run_id(
        request_id=request_id,
        execution_attempt=2,
    )
    assert request_id != deterministic_request_id(
        source_sha256=SOURCE_SHA256,
        supplier_profile_version="supplier-v3",
        policy_version="policy-v3",
    )


@pytest.mark.parametrize(
    ("source_sha256", "attempt"),
    [("not-a-digest", 1), (SOURCE_SHA256, 0), (SOURCE_SHA256, -1)],
)
def test_identity_rejects_invalid_digest_or_attempt(source_sha256: str, attempt: int) -> None:
    if source_sha256 != SOURCE_SHA256:
        with pytest.raises(ValueError, match="source_sha256"):
            deterministic_request_id(
                source_sha256=source_sha256,
                supplier_profile_version="supplier-v2",
                policy_version="policy-v3",
            )
        return

    request_id = deterministic_request_id(
        source_sha256=SOURCE_SHA256,
        supplier_profile_version="supplier-v2",
        policy_version="policy-v3",
    )
    with pytest.raises(ValueError, match="execution_attempt"):
        deterministic_run_id(request_id=request_id, execution_attempt=attempt)


def test_execution_evidence_is_a_sanitized_closed_model() -> None:
    evidence = valid_evidence()

    assert evidence.stage in ALLOWED_STAGES
    assert evidence.query_ids == ("query-1", "query-2")
    assert "stdout" not in asdict(evidence)
    assert "stderr" not in asdict(evidence)

    with pytest.raises(ValueError, match="raw execution field"):
        ExecutionEvidence.from_mapping({**asdict(evidence), "stdout": "secret-token"})
    with pytest.raises(ValueError, match="log_reference"):
        valid_evidence(log_reference="https://logs.example/e.json?token=secret")
    with pytest.raises(ValueError, match="query_ids"):
        valid_evidence(query_ids=("query-1\nsecret",))


@pytest.mark.parametrize(
    "session_id",
    (
        "session id",
        "https://cortex.example/session-1",
        "session-1?token=secret",
        "../session-1",
        "session-1/bearer-secret",
        "session-1@example.com",
    ),
)
def test_execution_evidence_rejects_unsafe_cortex_session_ids(session_id: str) -> None:
    with pytest.raises(ValueError, match="cortex_session_id"):
        valid_evidence(cortex_session_id=session_id)


@pytest.mark.parametrize(
    "source_locator",
    (
        "https://user:password@example.com/notice.pdf",
        "https://example.com/notice.pdf?token=secret",
        "notice.pdf?X-Amz-Signature=secret",
        "../notice.pdf#page=4",
        "%2e%2e/notice.pdf#page=4",
        "notice.pdf#token=secret",
    ),
)
def test_proposal_citation_rejects_credential_query_and_traversal_locators(
    source_locator: str,
) -> None:
    store = SnowflakeRefinementStore(FakeConnection())

    with pytest.raises(ValueError, match="source_locator"):
        store.append_proposal_citation(
            run_id="run_123",
            citation_id="citation-1",
            criterion_id="criterion-1",
            claim_id="claim-1",
            evidence_asset_id="asset-1",
            source_locator=source_locator,
        )


def test_proposal_citation_accepts_token_free_https_locator() -> None:
    connection = FakeConnection()

    SnowflakeRefinementStore(connection).append_proposal_citation(
        run_id="run_123",
        citation_id="citation-1",
        criterion_id="criterion-1",
        claim_id="claim-1",
        evidence_asset_id="asset-1",
        source_locator="https://www.g2b.go.kr/notices/notice.pdf#page=4",
    )

    assert any(
        "INSERT INTO BIDPILOT_DEMO.BIDPILOT.PROPOSAL_CITATIONS" in sql
        for sql, _ in connection.executed
    )


def test_execution_evidence_enforces_stage_status_outcome_and_exit_contract() -> None:
    with pytest.raises(ValueError, match="stage"):
        valid_evidence(stage="UNVERIFIED_NATIVE_SKILL")
    with pytest.raises(ValueError, match="event_status"):
        valid_evidence(event_status="SUCCEEDED")
    with pytest.raises(ValueError, match="outcome"):
        valid_evidence(outcome="MAYBE")
    with pytest.raises(ValueError, match="exit_code"):
        valid_evidence(event_status="COMPLETED", exit_code=1)
    with pytest.raises(ValueError, match="completed_at"):
        valid_evidence(
            event_status="RUNNING",
            exit_code=None,
            completed_at="2026-08-24T00:00:01+00:00",
        )
    with pytest.raises(ValueError, match="reason_count"):
        valid_evidence(reason_count=-1)

    evidence = valid_evidence(
        started_at="2026-08-24T09:00:00+09:00",
        completed_at="2026-08-24T00:01:00+00:00",
    )
    assert evidence.completed_at == "2026-08-24T00:01:00+00:00"


def test_store_inserts_run_and_event_without_update_or_legacy_dml() -> None:
    connection = FakeConnection()
    store = SnowflakeRefinementStore(connection)

    identity = store.create_run(
        tenant_id="demo-tenant",
        opportunity_id="R26BK01680611-000",
        opportunity_version="sha256:notice-v1",
        source_sha256=SOURCE_SHA256,
        supplier_profile_id="synthetic-demo",
        supplier_profile_version="supplier-v2",
        policy_version="policy-v3",
        reviewed_request_sha256=REQUEST_SHA256,
        execution_attempt=1,
        created_by="operator-1",
        operator_lease_id="lease-request-1",
    )
    store.append_event(valid_evidence(request_id=identity.request_id, run_id=identity.run_id))

    writes = [(sql, params) for sql, params in connection.executed if sql.lstrip().upper().startswith("INSERT")]
    assert len(writes) == 2
    assert "BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUNS" in writes[0][0]
    assert "BIDPILOT_DEMO.BIDPILOT.RUN_EVENTS" in writes[1][0]
    assert identity.request_id in writes[0][1]
    assert identity.run_id in writes[0][1]
    assert all("%s" in sql for sql, _ in writes)
    assert all(keyword not in sql.upper() for sql, _ in writes for keyword in ("UPDATE ", "DELETE ", "MERGE "))
    assert all("AGENT_RUNS" not in sql.upper() for sql, _ in writes)


def test_create_run_reuses_the_existing_identity_without_duplicate_insert() -> None:
    connection = FakeConnection()
    store = SnowflakeRefinementStore(connection)
    inputs = {
        "tenant_id": "demo-tenant",
        "opportunity_id": "R26BK01680611-000",
        "opportunity_version": "sha256:notice-v1",
        "source_sha256": SOURCE_SHA256,
        "supplier_profile_id": "synthetic-demo",
        "supplier_profile_version": "supplier-v2",
        "policy_version": "policy-v3",
        "reviewed_request_sha256": REQUEST_SHA256,
        "execution_attempt": 1,
        "created_by": "operator-1",
        "operator_lease_id": "lease-request-1",
    }

    first = store.create_run(**inputs)
    second = store.create_run(**inputs)
    with pytest.raises(RefinementStoreError, match="operator lease"):
        store.create_run(**{**inputs, "operator_lease_id": "lease-request-2"})

    assert second == first
    inserts = [
        sql
        for sql, _ in connection.executed
        if "INSERT INTO BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUNS" in sql
    ]
    existence_queries = [
        (sql, params)
        for sql, params in connection.executed
        if "WHERE request_id = %s AND execution_attempt = %s" in sql
    ]
    assert len(inserts) == 1
    assert len(existence_queries) == 3
    assert all(params == (first.request_id, 1) for _, params in existence_queries)


def test_store_exposes_explicit_insert_only_methods_for_all_v2_artifacts() -> None:
    connection = FakeConnection()
    store = SnowflakeRefinementStore(connection)

    store.append_proposal_citation(
        run_id="run_123",
        citation_id="citation-1",
        criterion_id="criterion-1",
        claim_id="claim-1",
        evidence_asset_id="asset-1",
        source_locator="notice.pdf#page=4",
    )
    store.append_red_team_finding(
        run_id="run_123",
        finding_id="finding-1",
        severity="HIGH",
        finding="The delivery proof is incomplete.",
        owner="proposal-lead",
        required_action="Attach the acceptance record.",
        resolution_status="OPEN",
    )
    store.append_export_manifest(
        run_id="run_123",
        export_id="export-1",
        artifact_kind="PROPOSAL_PDF",
        content_sha256="e" * 64,
        artifact_reference="exports/run_123/proposal.pdf",
    )
    store.append_approved_snapshot(
        run_id="run_123",
        approval_id="approval-1",
        proposal_sha256="f" * 64,
        approver_id="operator-1",
        artifact_reference="snapshots/run_123/proposal.json",
    )

    write_tables = {
        sql.upper().split("INSERT INTO BIDPILOT_DEMO.BIDPILOT.", 1)[1].split(" ", 1)[0]
        for sql, _ in connection.executed
        if sql.lstrip().upper().startswith("INSERT")
    }
    assert write_tables == {
        "PROPOSAL_CITATIONS",
        "RED_TEAM_FINDINGS",
        "EXPORT_ARTIFACT_MANIFESTS",
        "APPROVED_PROPOSAL_SNAPSHOTS",
    }


def test_store_rejects_write_through_a_non_refinement_role() -> None:
    store = SnowflakeRefinementStore(FakeConnection(role="BIDPILOT_RUNNER"))

    with pytest.raises(RefinementStoreError, match="requires role BIDPILOT_REFINEMENT_RUNNER"):
        store.append_event(valid_evidence())


def test_store_reads_event_derived_projection_and_dedicated_artifacts_only() -> None:
    responses = [
        (
            "FROM BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_READBACK_V2 WHERE run_id",
            ("RUN_ID", "REQUEST_ID", "CURRENT_STATE", "OUTCOME", "IS_COMPLETE"),
            [("run_123", "req_123", "COMPLETED", "REVIEW", True)],
        ),
        (
            "FROM BIDPILOT_DEMO.BIDPILOT.RUN_EVENTS WHERE run_id",
            ("EVENT_ID", "EVENT_SEQUENCE", "STAGE", "EVENT_STATUS"),
            [("evt_001", 1, "SOURCE_CAPTURE", "COMPLETED")],
        ),
        (
            "FROM BIDPILOT_DEMO.BIDPILOT.PROPOSAL_CITATIONS WHERE run_id",
            ("CITATION_ID",),
            [],
        ),
        (
            "FROM BIDPILOT_DEMO.BIDPILOT.RED_TEAM_FINDINGS WHERE run_id",
            ("FINDING_ID",),
            [("finding-1",)],
        ),
        (
            "FROM BIDPILOT_DEMO.BIDPILOT.EXPORT_ARTIFACT_MANIFESTS WHERE run_id",
            ("EXPORT_ID",),
            [],
        ),
        (
            "FROM BIDPILOT_DEMO.BIDPILOT.APPROVED_PROPOSAL_SNAPSHOTS WHERE run_id",
            ("APPROVAL_ID",),
            [],
        ),
    ]
    connection = FakeConnection(role="BIDPILOT_READER", responses=responses)

    result = SnowflakeRefinementStore(connection).load_run("run_123")

    assert result["run"]["current_state"] == "COMPLETED"
    assert result["run"]["outcome"] == "REVIEW"
    assert result["run"]["is_complete"] is True
    assert result["events"][0]["stage"] == "SOURCE_CAPTURE"
    sql = "\n".join(statement for statement, _ in connection.executed)
    assert "REFINEMENT_RUN_READBACK_V2" in sql
    assert "AGENT_RUNS" not in sql
    assert "PURSUIT_DECISIONS" not in sql
