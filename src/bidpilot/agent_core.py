"""Agent-facing pursuit core: the same policy the public app applies, as JSON.

Every function returns JSON-serialisable dicts and never imports Streamlit, so
an MCP server, an HTTP API, or a shell script can mount BidPilot as a
capability.  Persisted analyses are read through ``BIDPILOT_READER`` only and
fail closed when no Snowflake connection is configured; nothing here writes.

Evidence keys for :func:`decide` are either the zero-based position of a
requirement in ``eligibility_requirements`` written as a string (``"0"``) or
the exact requirement text.  Missing evidence is reported, never assumed.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from bidpilot.g2b_source import load_public_source
from bidpilot.snowflake_store import (
    SnowflakeBidRoomError,
    SnowflakeBidRoomStore,
    configured_connection_name,
)
from bidpilot.tender_catalog import load_public_tender_catalog
from bidpilot.workspace_ui import deadline_state

PROVIDER = "LOCAL_PYTHON_POLICY"
PASS = "PASS"
FAIL = "FAIL"
EVIDENCE_REQUIRED = "EVIDENCE REQUIRED"

_CATALOG_KEYS = (
    "notice_number",
    "title",
    "issuer",
    "deadline",
    "deadline_state",
    "evidence_level",
    "status",
    "official_url",
    "contract_value_krw",
    "technical_weight",
    "price_weight",
)


class AgentCoreError(ValueError):
    """Raised with a stable machine-readable code when a call fails closed."""

    def __init__(self, code: str, detail: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        payload = {"error": self.code}
        if self.detail:
            payload["detail"] = self.detail
        return payload


def _now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(UTC)
    if now.tzinfo is None:
        raise AgentCoreError("naive_clock", "The clock must be timezone-aware.")
    return now


def _plain(value: Any) -> Any:
    """Coerce store values into JSON-serialisable primitives."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_plain(item) for item in value]
    return str(value)


def _catalog_row(row: Mapping[str, Any], now: datetime) -> dict[str, Any]:
    shaped = {
        key: _plain(row.get(key)) for key in _CATALOG_KEYS if key != "deadline_state"
    }
    shaped["deadline_state"] = deadline_state(row.get("deadline"), now)
    return shaped


def list_tenders(now: datetime | None = None) -> list[dict[str, Any]]:
    """Return the public catalogue with each deadline judged against the clock."""
    clock = _now(now)
    return [_catalog_row(row, clock) for row in load_public_tender_catalog()]


def _reviewed_detail() -> dict[str, Any]:
    source = load_public_source()
    projection = source["public_projection"]
    facts = {item["field"]: item["value"] for item in projection["source_facts"]}
    labels = {item["field"]: item["value"] for item in projection["public_labels"]}
    notice = next(
        item for item in source["artifacts"] if item["artifact_id"] == "notice-pdf"
    )
    return {
        "eligibility_requirements": [
            str(item) for item in facts["eligibility_requirements"]
        ],
        "source_url": str(notice["official_url"]),
        "source_sha256": str(notice["sha256"]),
        "retrieved_at": str(notice["retrieved_at"]),
        "delivery_term": str(facts["delivery_term"]),
        "supplier_boundary": str(labels["supplier_profile_boundary"]),
    }


def get_tender(notice_number: str, now: datetime | None = None) -> dict[str, Any]:
    """Return one catalogue row, with source provenance for the reviewed notice."""
    clock = _now(now)
    wanted = str(notice_number or "").strip()
    for row in load_public_tender_catalog():
        if row["notice_number"] != wanted:
            continue
        shaped = _catalog_row(row, clock)
        if row.get("evidence_level") == "source-reviewed":
            shaped.update(_reviewed_detail())
        return shaped
    raise AgentCoreError("tender_not_found", f"No catalogue row for {wanted!r}.")


def _evidence_for(
    requirements: list[str], supplier_evidence: Mapping[str, Any] | None
) -> list[bool | None]:
    verdicts: list[bool | None] = [None] * len(requirements)
    for key, value in (supplier_evidence or {}).items():
        label = str(key).strip()
        if label.isdigit() and int(label) < len(requirements):
            index = int(label)
        elif label in requirements:
            index = requirements.index(label)
        else:
            raise AgentCoreError(
                "unknown_requirement", f"No requirement matches {label!r}."
            )
        if not isinstance(value, bool):
            raise AgentCoreError(
                "invalid_evidence", f"Evidence for {label!r} must be true or false."
            )
        verdicts[index] = value
    return verdicts


def decide(
    notice_number: str,
    supplier_evidence: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Apply the evidence-first pursuit policy without inventing any evidence."""
    tender = get_tender(notice_number, now=now)
    requirements = list(tender.get("eligibility_requirements") or [])
    verdicts = _evidence_for(requirements, supplier_evidence)
    checks = [
        {
            "requirement": requirement,
            "status": PASS
            if verdict is True
            else FAIL
            if verdict is False
            else EVIDENCE_REQUIRED,
        }
        for requirement, verdict in zip(requirements, verdicts, strict=True)
    ]
    failed = [check["requirement"] for check in checks if check["status"] == FAIL]
    gaps = [
        check["requirement"] for check in checks if check["status"] == EVIDENCE_REQUIRED
    ]
    state = tender["deadline_state"]
    gate = "LOCKED"
    next_actions: list[str]

    if not requirements:
        decision = "REVIEW"
        reason = (
            "This notice is source-found only; its eligibility requirements have not "
            "been reviewed, so no pursuit decision can be made from it."
        )
        next_actions = ["Review the official notice attachment before any decision."]
    elif failed:
        decision = "NO-GO"
        reason = f"{len(failed)} mandatory requirement(s) failed: " + "; ".join(failed)
        next_actions = [
            "Do not draft a proposal.",
            "Record the failed requirement(s) for the pursuit log.",
        ]
    elif gaps:
        decision = "REVIEW"
        reason = f"{len(gaps)} of {len(requirements)} eligibility requirements still need supplier evidence."
        next_actions = [f"Supply evidence for: {gap}" for gap in gaps]
    else:
        decision = "PURSUE"
        if state == "open":
            gate = "OPEN"
            reason = "Every eligibility requirement is evidenced and the notice is still open."
            next_actions = [
                "Open the proposal gate and plan the technical response against the 90/10 weights."
            ]
        else:
            reason = (
                "Every eligibility requirement is evidenced, but the notice is closed; "
                "the proposal gate stays locked and the result is historical."
            )
            next_actions = [
                "Treat this notice as a historical reference; no submission is possible."
            ]

    return {
        "notice_number": tender["notice_number"],
        "decision": decision,
        "reason": reason,
        "checks": checks,
        "evidence_gaps": len(gaps),
        "weights": {
            "technical": tender["technical_weight"],
            "price": tender["price_weight"],
        },
        "proposal_gate": gate,
        "next_actions": next_actions,
        "provider": PROVIDER,
        "persisted": False,
        "deadline_state": state,
    }


def _store() -> SnowflakeBidRoomStore:
    connection = configured_connection_name()
    if not connection:
        raise AgentCoreError(
            "snowflake_not_configured",
            "Set BIDPILOT_SNOWFLAKE_CONNECTION to a BIDPILOT_READER connection; no fixture fallback.",
        )
    return SnowflakeBidRoomStore(connection)


def list_runs() -> list[dict[str, Any]]:
    """List persisted analyses through the reader role, or fail closed."""
    store = _store()
    try:
        rows = store.list_runs()
    except SnowflakeBidRoomError as error:
        raise AgentCoreError("snowflake_error", str(error)) from error
    return [
        {
            "run_id": str(row.get("run_id")),
            "state": _plain(row.get("state")),
            "is_complete": bool(row.get("is_complete")),
            "opportunity_id": _plain(row.get("opportunity_id")),
            "created_at": str(row.get("created_at")),
        }
        for row in rows
    ]


def _first_heading(markdown: object, fallback: str) -> str:
    for line in str(markdown or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def _as_int(value: object) -> int | float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def replay(run_id: str) -> dict[str, Any]:
    """Shape one complete persisted run for an agent, or fail closed."""
    store = _store()
    wanted = str(run_id or "").strip()
    try:
        result = store.load_run(wanted)
    except KeyError as error:
        raise AgentCoreError("run_not_found", f"No complete run {wanted!r}.") from error
    except SnowflakeBidRoomError as error:
        raise AgentCoreError("snowflake_error", str(error)) from error

    run = result.get("run") or {}
    trace = run.get("trace") if isinstance(run.get("trace"), dict) else {}
    opportunity = result.get("opportunity") or {}
    supplier = result.get("supplier") or {}
    decision = result.get("decision") or {}
    strategies = list(result.get("strategies") or [])
    blueprint = list(result.get("blueprint") or [])
    sections = list(result.get("sections") or [])
    tasks = list(result.get("tasks") or [])
    selected = next((item for item in strategies if item.get("selected")), None)
    weights = {
        str(item.get("criterion_name") or "").strip(): _as_int(item.get("weight"))
        for item in blueprint
    }
    provenance = (
        trace.get("execution_provenance")
        if isinstance(trace.get("execution_provenance"), dict)
        else {}
    )

    return {
        "run_id": wanted,
        "opportunity_id": _plain(run.get("opportunity_id")),
        "title": _plain(opportunity.get("title")),
        "supplier_name": _plain(supplier.get("supplier_name")),
        "decision": _plain(decision.get("status")),
        "selected_strategy": _plain(selected.get("title")) if selected else None,
        "strategy_count": len(strategies),
        "plan_count": len(blueprint),
        "section_count": len(sections),
        "task_count": len(tasks),
        "sections": [
            {
                "criterion": str(item.get("criterion_name") or "").strip(),
                "title": _first_heading(
                    item.get("section_markdown"),
                    str(item.get("criterion_name") or "").strip(),
                ),
                "weight": weights.get(str(item.get("criterion_name") or "").strip()),
            }
            for item in sections
        ],
        "tasks": [
            {"title": _plain(item.get("task_name")), "owner": _plain(item.get("owner"))}
            for item in tasks
        ],
        "completed_at": _plain(trace.get("completed_at")),
        "provenance": {
            "cortex_session_id": _plain(provenance.get("cortex_session_id")),
            "query_ids": _plain(provenance.get("cortex_write_query_ids") or []),
            "provider": _plain(run.get("provider")),
            "policy_version": _plain(run.get("policy_version")),
        },
    }


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bidpilot.agent_core")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list-tenders")
    commands.add_parser("get-tender").add_argument("notice_number")
    decide_parser = commands.add_parser("decide")
    decide_parser.add_argument("notice_number")
    decide_parser.add_argument(
        "--evidence", default=None, help="JSON object of evidence"
    )
    commands.add_parser("list-runs")
    commands.add_parser("replay").add_argument("run_id")
    args = parser.parse_args(argv)

    try:
        if args.command == "list-tenders":
            payload: Any = list_tenders()
        elif args.command == "get-tender":
            payload = get_tender(args.notice_number)
        elif args.command == "decide":
            evidence = json.loads(args.evidence) if args.evidence else None
            if evidence is not None and not isinstance(evidence, dict):
                raise AgentCoreError(
                    "invalid_evidence", "--evidence must be a JSON object."
                )
            payload = decide(args.notice_number, evidence)
        elif args.command == "list-runs":
            payload = list_runs()
        else:
            payload = replay(args.run_id)
    except AgentCoreError as error:
        print(json.dumps(error.to_dict(), ensure_ascii=False))
        return 1
    except json.JSONDecodeError as error:
        print(json.dumps({"error": "invalid_evidence", "detail": str(error)}))
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
