"""Insert-only refinement evidence persistence and event-derived readback."""

from __future__ import annotations

import hashlib
import json
import re
from contextlib import closing
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, Mapping, Sequence
from urllib.parse import unquote, urlsplit


EXPECTED_WRITER_ROLE = "BIDPILOT_REFINEMENT_RUNNER"
EXPECTED_READER_ROLE = "BIDPILOT_READER"

ALLOWED_STAGES = frozenset(
    {
        "SOURCE_CAPTURE",
        "STRUCTURE_REVIEW",
        "SUPPLIER_RETRIEVAL",
        "PURSUIT_DECISION",
        "WIN_STRATEGY",
        "PROPOSAL_DRAFT",
        "RED_TEAM",
        "OWNED_WORK",
        "FINALIZE",
    }
)
ALLOWED_EVENT_STATUSES = frozenset({"QUEUED", "RUNNING", "COMPLETED", "FAILED"})
ALLOWED_OUTCOMES = frozenset({"PURSUE", "REVIEW", "NO-GO"})

_HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
_SAFE_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,254}")
_SAFE_QUERY_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,254}")
_SAFE_SOURCE_FRAGMENT = re.compile(r"(?:page=[1-9][0-9]*|section=[A-Za-z0-9][A-Za-z0-9_.:-]{0,127})")
_SECRET_LOCATOR_COMPONENT = re.compile(
    r"(?:authorization|bearer|credential|password|secret|signature|token|api[_-]?key)\s*=",
    re.IGNORECASE,
)
_FORBIDDEN_EVIDENCE_FIELDS = frozenset(
    {
        "raw_log",
        "raw_command",
        "command_args",
        "stdout",
        "stderr",
        "environment",
        "env",
        "prompt",
        "prompt_text",
        "source_text",
    }
)


class RefinementStoreError(RuntimeError):
    """Raised when the refinement persistence contract cannot be satisfied."""


def _required_text(name: str, value: str, *, maximum: int = 255) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} is required.")
    if len(normalized) > maximum or any(ord(character) < 32 for character in normalized):
        raise ValueError(f"{name} contains unsupported content.")
    return normalized


def _optional_text(name: str, value: str | None, *, maximum: int = 255) -> str | None:
    if value is None:
        return None
    return _required_text(name, value, maximum=maximum)


def _sha256(name: str, value: str | None, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    normalized = _required_text(name, value or "").lower()
    if not _HEX_SHA256.fullmatch(normalized):
        raise ValueError(f"{name} must be a 64-character SHA-256 digest.")
    return normalized


def _safe_token(name: str, value: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    normalized = _required_text(name, value)
    if not _SAFE_TOKEN.fullmatch(normalized):
        raise ValueError(f"{name} contains unsupported characters.")
    return normalized


def _safe_reference(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _required_text(name, value, maximum=1024)
    parts = normalized.split("/")
    if (
        normalized.startswith(("/", "\\"))
        or "://" in normalized
        or "?" in normalized
        or "#" in normalized
        or "\\" in normalized
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ValueError(f"{name} must be a relative, token-free artifact reference.")
    return normalized


def _safe_evidence_identifier(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _required_text(name, value)
    if not _SAFE_QUERY_ID.fullmatch(normalized):
        raise ValueError(f"{name} must be a sanitized execution identifier.")
    return normalized


def _safe_source_locator(value: str) -> str:
    normalized = _required_text("source_locator", value, maximum=1024)
    parsed = urlsplit(normalized)
    decoded_path = unquote(parsed.path)
    decoded_locator = unquote(normalized)
    checked_path = decoded_path[1:] if parsed.scheme and decoded_path.startswith("/") else decoded_path
    path_parts = checked_path.split("/")
    if parsed.scheme and parsed.scheme.lower() != "https":
        raise ValueError("source_locator must use HTTPS or a relative artifact path.")
    if parsed.scheme and not parsed.netloc:
        raise ValueError("source_locator has an invalid HTTPS authority.")
    if not parsed.scheme and parsed.netloc:
        raise ValueError("source_locator cannot use a scheme-relative authority.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("source_locator cannot contain credentials.")
    if parsed.query:
        raise ValueError("source_locator cannot contain a query string.")
    if (
        not decoded_path
        or decoded_path.startswith(("/", "\\")) and not parsed.scheme
        or "\\" in decoded_path
        or "?" in decoded_path
        or "#" in decoded_path
        or any(part in {"", ".", ".."} for part in path_parts)
        or any(ord(character) < 32 for character in decoded_path)
    ):
        raise ValueError("source_locator contains an unsafe artifact path.")
    if parsed.fragment and not _SAFE_SOURCE_FRAGMENT.fullmatch(parsed.fragment):
        raise ValueError("source_locator contains an unsupported fragment.")
    if _SECRET_LOCATOR_COMPONENT.search(decoded_locator):
        raise ValueError("source_locator cannot contain credential or token material.")
    return normalized


def _timestamp(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _required_text(name, value)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO-8601 timestamp.") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{name} must include a timezone.")
    return parsed.isoformat()


def deterministic_request_id(
    *,
    source_sha256: str,
    supplier_profile_version: str,
    policy_version: str,
) -> str:
    """Return the canonical identity shared by retries of one reviewed request."""

    payload = {
        "policy_version": _required_text("policy_version", policy_version),
        "source_sha256": _sha256("source_sha256", source_sha256),
        "supplier_profile_version": _required_text(
            "supplier_profile_version", supplier_profile_version
        ),
    }
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return f"req_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def deterministic_run_id(*, request_id: str, execution_attempt: int) -> str:
    """Return a stable run identity for one deterministic request attempt."""

    normalized_request_id = _required_text("request_id", request_id)
    if not re.fullmatch(r"req_[0-9a-f]{64}", normalized_request_id):
        raise ValueError("request_id must be a deterministic refinement request ID.")
    if isinstance(execution_attempt, bool) or not isinstance(execution_attempt, int) or execution_attempt < 1:
        raise ValueError("execution_attempt must be a positive integer.")
    canonical = json.dumps(
        {"execution_attempt": execution_attempt, "request_id": normalized_request_id},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"run_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


@dataclass(frozen=True)
class RefinementRunIdentity:
    request_id: str
    run_id: str
    execution_attempt: int


@dataclass(frozen=True)
class ExecutionEvidence:
    """Closed, sanitized execution evidence accepted by the insert-only store."""

    request_id: str
    run_id: str
    event_id: str
    event_sequence: int
    stage: str
    capability: str
    command_identity: str | None
    event_status: str
    exit_code: int | None
    started_at: str | None
    completed_at: str | None
    cortex_session_id: str | None
    cortex_cli_version: str | None
    input_sha256: str | None
    output_sha256: str | None
    query_ids: tuple[str, ...]
    log_reference: str | None
    outcome: str | None
    reason_count: int
    evidence_gap_count: int
    strategy_count: int
    score_plan_count: int
    proposal_section_count: int
    owned_work_item_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", _required_text("request_id", self.request_id))
        object.__setattr__(self, "run_id", _required_text("run_id", self.run_id))
        object.__setattr__(self, "event_id", _safe_token("event_id", self.event_id))
        if (
            isinstance(self.event_sequence, bool)
            or not isinstance(self.event_sequence, int)
            or self.event_sequence < 1
        ):
            raise ValueError("event_sequence must be a positive integer.")

        stage = _required_text("stage", self.stage).upper()
        if stage not in ALLOWED_STAGES:
            raise ValueError(f"stage must be one of {sorted(ALLOWED_STAGES)}.")
        object.__setattr__(self, "stage", stage)
        object.__setattr__(self, "capability", _safe_token("capability", self.capability))
        object.__setattr__(
            self,
            "command_identity",
            _safe_token("command_identity", self.command_identity, optional=True),
        )

        status = _required_text("event_status", self.event_status).upper()
        if status not in ALLOWED_EVENT_STATUSES:
            raise ValueError(f"event_status must be one of {sorted(ALLOWED_EVENT_STATUSES)}.")
        object.__setattr__(self, "event_status", status)

        if self.exit_code is not None and (
            isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int)
        ):
            raise ValueError("exit_code must be an integer or None.")
        if status == "COMPLETED" and self.exit_code not in {None, 0}:
            raise ValueError("exit_code must be zero or unrecorded for a completed event.")
        if status in {"QUEUED", "RUNNING"} and self.exit_code is not None:
            raise ValueError("exit_code must be unrecorded before an event is terminal.")

        started_at = _timestamp("started_at", self.started_at)
        completed_at = _timestamp("completed_at", self.completed_at)
        if status in {"QUEUED", "RUNNING"} and completed_at is not None:
            raise ValueError("completed_at must be unrecorded before an event is terminal.")
        if status in {"COMPLETED", "FAILED"} and completed_at is None:
            raise ValueError("completed_at is required for a terminal event.")
        if (
            started_at
            and completed_at
            and datetime.fromisoformat(completed_at) < datetime.fromisoformat(started_at)
        ):
            raise ValueError("completed_at cannot precede started_at.")
        object.__setattr__(self, "started_at", started_at)
        object.__setattr__(self, "completed_at", completed_at)

        object.__setattr__(
            self,
            "cortex_session_id",
            _safe_evidence_identifier("cortex_session_id", self.cortex_session_id),
        )
        object.__setattr__(
            self,
            "cortex_cli_version",
            _optional_text("cortex_cli_version", self.cortex_cli_version),
        )
        object.__setattr__(
            self,
            "input_sha256",
            _sha256("input_sha256", self.input_sha256, optional=True),
        )
        object.__setattr__(
            self,
            "output_sha256",
            _sha256("output_sha256", self.output_sha256, optional=True),
        )

        if isinstance(self.query_ids, (str, bytes)):
            raise ValueError("query_ids must be a sequence of sanitized identifiers.")
        normalized_query_ids: list[str] = []
        for query_id in self.query_ids:
            normalized = _required_text("query_ids item", query_id)
            if not _SAFE_QUERY_ID.fullmatch(normalized):
                raise ValueError("query_ids contains an unsupported identifier.")
            normalized_query_ids.append(normalized)
        object.__setattr__(self, "query_ids", tuple(normalized_query_ids))
        object.__setattr__(self, "log_reference", _safe_reference("log_reference", self.log_reference))

        outcome = _optional_text("outcome", self.outcome)
        if outcome is not None:
            outcome = outcome.upper()
            if outcome not in ALLOWED_OUTCOMES:
                raise ValueError(f"outcome must be one of {sorted(ALLOWED_OUTCOMES)}.")
            if stage != "PURSUIT_DECISION" or status != "COMPLETED":
                raise ValueError("outcome is accepted only on a completed PURSUIT_DECISION event.")
        object.__setattr__(self, "outcome", outcome)

        for name in (
            "reason_count",
            "evidence_gap_count",
            "strategy_count",
            "score_plan_count",
            "proposal_section_count",
            "owned_work_item_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer.")

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> ExecutionEvidence:
        lowered = {str(key).lower() for key in values}
        forbidden = lowered.intersection(_FORBIDDEN_EVIDENCE_FIELDS)
        if forbidden:
            raise ValueError(f"raw execution field is not accepted: {sorted(forbidden)[0]}")
        allowed = {field.name for field in fields(cls)}
        unknown = set(values).difference(allowed)
        if unknown:
            raise ValueError(f"unsupported execution evidence field: {sorted(unknown)[0]}")
        return cls(**values)


class SnowflakeRefinementStore:
    """Use an injected Snowflake connection for v2 writes or reader readback."""

    def __init__(self, connection: Any) -> None:
        if connection is None or not callable(getattr(connection, "cursor", None)):
            raise ValueError("A Snowflake-compatible connection is required.")
        self.connection = connection
        self._actual_role: str | None = None

    def _role(self) -> str:
        if self._actual_role is None:
            try:
                with closing(self.connection.cursor()) as cursor:
                    cursor.execute("SELECT CURRENT_ROLE()")
                    row = cursor.fetchone()
            except Exception as error:
                raise RefinementStoreError(f"Snowflake role verification failed: {error}") from error
            self._actual_role = str(row[0]).upper() if row and row[0] is not None else ""
        return self._actual_role

    def _require_role(self, expected: str) -> None:
        actual = self._role()
        if actual != expected:
            raise RefinementStoreError(
                f"Refinement operation requires role {expected}; connection uses {actual or 'UNKNOWN'}."
            )

    @staticmethod
    def _rows(cursor: Any) -> list[dict[str, Any]]:
        columns = [item[0].lower() for item in cursor.description or ()]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def _insert(self, sql: str, params: tuple[Any, ...]) -> None:
        self._require_role(EXPECTED_WRITER_ROLE)
        try:
            with closing(self.connection.cursor()) as cursor:
                cursor.execute(sql, params)
        except RefinementStoreError:
            raise
        except Exception as error:
            raise RefinementStoreError(f"Refinement evidence insert failed: {error}") from error

    def _query(self, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        self._require_role(EXPECTED_READER_ROLE)
        try:
            with closing(self.connection.cursor()) as cursor:
                cursor.execute(sql, params)
                return self._rows(cursor)
        except RefinementStoreError:
            raise
        except Exception as error:
            raise RefinementStoreError(f"Refinement readback failed: {error}") from error

    def _writer_query(self, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        self._require_role(EXPECTED_WRITER_ROLE)
        try:
            with closing(self.connection.cursor()) as cursor:
                cursor.execute(sql, params)
                return self._rows(cursor)
        except RefinementStoreError:
            raise
        except Exception as error:
            raise RefinementStoreError(
                f"Refinement retry identity lookup failed: {error}"
            ) from error

    def create_run(
        self,
        *,
        tenant_id: str,
        opportunity_id: str,
        opportunity_version: str,
        source_sha256: str,
        supplier_profile_id: str,
        supplier_profile_version: str,
        policy_version: str,
        reviewed_request_sha256: str,
        execution_attempt: int,
        created_by: str,
        serialized_operator_token: str,
    ) -> RefinementRunIdentity:
        """Create or reuse a sequential retry from one serialized private operator.

        The caller must serialize create_run calls in one private operator process
        and reuse its token. The pre-insert lookup is not an atomic uniqueness
        guarantee; concurrent or public async multi-worker callers are unsupported.
        """

        normalized_source_sha256 = _sha256("source_sha256", source_sha256)
        normalized_supplier_version = _required_text(
            "supplier_profile_version", supplier_profile_version
        )
        normalized_policy_version = _required_text("policy_version", policy_version)
        request_id = deterministic_request_id(
            source_sha256=normalized_source_sha256,
            supplier_profile_version=normalized_supplier_version,
            policy_version=normalized_policy_version,
        )
        run_id = deterministic_run_id(
            request_id=request_id,
            execution_attempt=execution_attempt,
        )
        identity = RefinementRunIdentity(request_id, run_id, execution_attempt)
        normalized_request_sha256 = _sha256(
            "reviewed_request_sha256", reviewed_request_sha256
        )
        normalized_operator_token = _safe_evidence_identifier(
            "serialized_operator_token", serialized_operator_token
        )
        existing = self._writer_query(
            """
            SELECT request_id, run_id, execution_attempt, reviewed_request_sha256,
                   serialized_operator_token
            FROM BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_READBACK_V2
            WHERE request_id = %s AND execution_attempt = %s
            ORDER BY created_at
            LIMIT 2
            """,
            (request_id, execution_attempt),
        )
        if len(existing) > 1:
            raise RefinementStoreError(
                "Refinement identity has duplicate persisted rows; manual reconciliation is required."
            )
        if existing:
            persisted = existing[0]
            if persisted.get("run_id") != run_id:
                raise RefinementStoreError("Refinement request identity resolved to a different run ID.")
            if persisted.get("reviewed_request_sha256") != normalized_request_sha256:
                raise RefinementStoreError(
                    "Refinement request identity conflicts with the reviewed request digest."
                )
            if persisted.get("serialized_operator_token") != normalized_operator_token:
                raise RefinementStoreError(
                    "Refinement request belongs to a different serialized operator token."
                )
            return identity
        self._insert(
            """
            INSERT INTO BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUNS (
                request_id, run_id, execution_attempt, tenant_id, opportunity_id,
                opportunity_version, source_sha256, supplier_profile_id,
                supplier_profile_version, policy_version, reviewed_request_sha256,
                serialized_operator_token, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                request_id,
                run_id,
                execution_attempt,
                _required_text("tenant_id", tenant_id),
                _required_text("opportunity_id", opportunity_id),
                _required_text("opportunity_version", opportunity_version),
                normalized_source_sha256,
                _required_text("supplier_profile_id", supplier_profile_id),
                normalized_supplier_version,
                normalized_policy_version,
                normalized_request_sha256,
                normalized_operator_token,
                _required_text("created_by", created_by),
            ),
        )
        return identity

    def append_event(self, evidence: ExecutionEvidence) -> None:
        if not isinstance(evidence, ExecutionEvidence):
            raise ValueError("evidence must be validated ExecutionEvidence.")
        self._insert(
            """
            INSERT INTO BIDPILOT_DEMO.BIDPILOT.RUN_EVENTS (
                request_id, run_id, event_id, event_sequence, stage, capability,
                command_identity, event_status, exit_code, started_at, completed_at,
                cortex_session_id, cortex_cli_version, input_sha256, output_sha256,
                query_ids, log_reference, outcome, reason_count, evidence_gap_count,
                strategy_count, score_plan_count, proposal_section_count, owned_work_item_count
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                TO_TIMESTAMP_TZ(%s), TO_TIMESTAMP_TZ(%s), %s, %s, %s, %s,
                PARSE_JSON(%s)::ARRAY, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                evidence.request_id,
                evidence.run_id,
                evidence.event_id,
                evidence.event_sequence,
                evidence.stage,
                evidence.capability,
                evidence.command_identity,
                evidence.event_status,
                evidence.exit_code,
                evidence.started_at,
                evidence.completed_at,
                evidence.cortex_session_id,
                evidence.cortex_cli_version,
                evidence.input_sha256,
                evidence.output_sha256,
                json.dumps(evidence.query_ids, separators=(",", ":")),
                evidence.log_reference,
                evidence.outcome,
                evidence.reason_count,
                evidence.evidence_gap_count,
                evidence.strategy_count,
                evidence.score_plan_count,
                evidence.proposal_section_count,
                evidence.owned_work_item_count,
            ),
        )

    def append_proposal_citation(
        self,
        *,
        run_id: str,
        citation_id: str,
        criterion_id: str,
        claim_id: str,
        evidence_asset_id: str,
        source_locator: str,
    ) -> None:
        self._insert(
            """
            INSERT INTO BIDPILOT_DEMO.BIDPILOT.PROPOSAL_CITATIONS (
                run_id, citation_id, criterion_id, claim_id, evidence_asset_id, source_locator
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                _required_text("run_id", run_id),
                _safe_token("citation_id", citation_id),
                _safe_token("criterion_id", criterion_id),
                _safe_token("claim_id", claim_id),
                _safe_token("evidence_asset_id", evidence_asset_id),
                _safe_source_locator(source_locator),
            ),
        )

    def append_red_team_finding(
        self,
        *,
        run_id: str,
        finding_id: str,
        severity: str,
        finding: str,
        owner: str,
        required_action: str,
        resolution_status: str,
    ) -> None:
        normalized_severity = _required_text("severity", severity).upper()
        if normalized_severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise ValueError("severity must be LOW, MEDIUM, HIGH, or CRITICAL.")
        normalized_resolution = _required_text("resolution_status", resolution_status).upper()
        if normalized_resolution not in {"OPEN", "RESOLVED", "ACCEPTED"}:
            raise ValueError("resolution_status must be OPEN, RESOLVED, or ACCEPTED.")
        self._insert(
            """
            INSERT INTO BIDPILOT_DEMO.BIDPILOT.RED_TEAM_FINDINGS (
                run_id, finding_id, severity, finding, owner, required_action, resolution_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                _required_text("run_id", run_id),
                _safe_token("finding_id", finding_id),
                normalized_severity,
                _required_text("finding", finding, maximum=4000),
                _required_text("owner", owner),
                _required_text("required_action", required_action, maximum=4000),
                normalized_resolution,
            ),
        )

    def append_export_manifest(
        self,
        *,
        run_id: str,
        export_id: str,
        artifact_kind: str,
        content_sha256: str,
        artifact_reference: str,
    ) -> None:
        self._insert(
            """
            INSERT INTO BIDPILOT_DEMO.BIDPILOT.EXPORT_ARTIFACT_MANIFESTS (
                run_id, export_id, artifact_kind, content_sha256, artifact_reference
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (
                _required_text("run_id", run_id),
                _safe_token("export_id", export_id),
                _safe_token("artifact_kind", artifact_kind),
                _sha256("content_sha256", content_sha256),
                _safe_reference("artifact_reference", artifact_reference),
            ),
        )

    def append_approved_snapshot(
        self,
        *,
        run_id: str,
        approval_id: str,
        proposal_sha256: str,
        approver_id: str,
        artifact_reference: str,
    ) -> None:
        self._insert(
            """
            INSERT INTO BIDPILOT_DEMO.BIDPILOT.APPROVED_PROPOSAL_SNAPSHOTS (
                run_id, approval_id, proposal_sha256, approver_id, artifact_reference
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (
                _required_text("run_id", run_id),
                _safe_token("approval_id", approval_id),
                _sha256("proposal_sha256", proposal_sha256),
                _required_text("approver_id", approver_id),
                _safe_reference("artifact_reference", artifact_reference),
            ),
        )

    def list_runs(self) -> list[dict[str, Any]]:
        return self._query(
            """
            SELECT *
            FROM BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_READBACK_V2
            ORDER BY created_at DESC, run_id
            """,
            (),
        )

    def load_run(self, run_id: str) -> dict[str, Any]:
        normalized_run_id = _required_text("run_id", run_id)
        queries: Sequence[tuple[str, str]] = (
            (
                "run",
                """
                SELECT * FROM BIDPILOT_DEMO.BIDPILOT.REFINEMENT_RUN_READBACK_V2 WHERE run_id = %s
                """,
            ),
            (
                "events",
                """
                SELECT * FROM BIDPILOT_DEMO.BIDPILOT.RUN_EVENTS WHERE run_id = %s
                ORDER BY event_sequence, recorded_at, event_id
                """,
            ),
            (
                "citations",
                """
                SELECT * FROM BIDPILOT_DEMO.BIDPILOT.PROPOSAL_CITATIONS WHERE run_id = %s
                ORDER BY criterion_id, claim_id, citation_id
                """,
            ),
            (
                "red_team_findings",
                """
                SELECT * FROM BIDPILOT_DEMO.BIDPILOT.RED_TEAM_FINDINGS WHERE run_id = %s
                ORDER BY severity DESC, finding_id
                """,
            ),
            (
                "exports",
                """
                SELECT * FROM BIDPILOT_DEMO.BIDPILOT.EXPORT_ARTIFACT_MANIFESTS WHERE run_id = %s
                ORDER BY created_at, export_id
                """,
            ),
            (
                "approved_snapshots",
                """
                SELECT * FROM BIDPILOT_DEMO.BIDPILOT.APPROVED_PROPOSAL_SNAPSHOTS WHERE run_id = %s
                ORDER BY approved_at, approval_id
                """,
            ),
        )
        result: dict[str, Any] = {}
        for key, sql in queries:
            rows = self._query(sql, (normalized_run_id,))
            result[key] = rows[0] if key == "run" and rows else (None if key == "run" else rows)
        if result["run"] is None:
            raise KeyError(normalized_run_id)
        return result
