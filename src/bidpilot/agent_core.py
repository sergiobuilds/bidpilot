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
import re
import sys
from collections.abc import Mapping
from dataclasses import asdict
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from bidpilot import fixtures
from bidpilot.g2b_source import load_public_source
from bidpilot.proposal_writer import (
    build_gap_closure_plan,
    red_team_proposal,
    red_team_tasks,
    write_strategy_proposal,
)
from bidpilot.pursuit import PursuitInputError, build_pursuit_brief, select_win_position
from bidpilot.snowflake_store import (
    SnowflakeBidRoomError,
    SnowflakeBidRoomStore,
    configured_connection_name,
)
from bidpilot.tender_catalog import load_public_tender_catalog
from bidpilot.workspace_ui import deadline_state

PROVIDER = "LOCAL_PYTHON_POLICY"
DISCLOSURE = "Synthetic demo supplier profile; nothing here is a real company claim."
DEFAULT_SUPPLIER_ID = "supplier-northstar"
# The public notice states a delivery term, not an effort figure.  The pursuit
# policy needs planned hours to judge capacity, so this planning constant is
# declared in every draft's ``assumptions`` rather than presented as a fact.
ASSUMED_DELIVERY_HOURS = 800
KST = timezone(timedelta(hours=9))
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

    def __init__(
        self, code: str, detail: str | Mapping[str, Any] | None = None
    ) -> None:
        super().__init__(code)
        self.code = code
        self.detail: str | dict[str, Any] | None = (
            dict(detail) if isinstance(detail, Mapping) else detail
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"error": self.code}
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


def _supplier(supplier_id: str) -> dict[str, Any]:
    wanted = str(supplier_id or "").strip()
    for profile in fixtures.SUPPLIER_PROFILES:
        if profile["id"] == wanted:
            return json.loads(json.dumps(profile))
    raise AgentCoreError(
        "supplier_not_found",
        f"No synthetic supplier profile {wanted!r}; only fixtures.SUPPLIER_PROFILES ids are accepted.",
    )


def _fixture_tender(notice_number: str) -> dict[str, Any] | None:
    for tender in fixtures.TENDERS:
        if tender["id"] == notice_number:
            return json.loads(json.dumps(tender))
    return None


def _title_tags(title: str) -> list[str]:
    return [word for word in re.split(r"\s+", str(title).lower()) if word]


def _catalogue_tender(row: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Shape the writer's tender from source facts only, naming every assumption."""
    title = str(row["title"])
    delivery_term = str(row.get("delivery_term") or "")
    tags = _title_tags(title)
    assumptions = [
        (
            f"delivery_hours={ASSUMED_DELIVERY_HOURS} is a planning constant, not a source fact; "
            f"the notice states the delivery term {delivery_term!r} and no effort figure."
        ),
        (
            "buyer_objective and promised_outcome quote the notice title and delivery term "
            "verbatim; no deliverable beyond the source facts is asserted."
        ),
        (
            "tags are the lowercase words of the notice title, plus 'public-sector' because "
            f"the issuer is a public body ({row.get('issuer')})."
        ),
    ]
    tags.append("public-sector")
    tender = {
        "id": str(row["notice_number"]),
        "title": title,
        "buyer_objective": f'the procurement of "{title}" (notice title), delivered within the term "{delivery_term}".',
        "promised_outcome": f'the service described by the notice title "{title}", within the delivery term "{delivery_term}"',
        "tags": tags,
        "eligibility_requirements": [
            str(item) for item in row.get("eligibility_requirements") or []
        ],
        "delivery_hours": ASSUMED_DELIVERY_HOURS,
        "evaluation_criteria": [
            {"name": "Technical", "weight": int(row["technical_weight"])},
            {"name": "Price", "weight": int(row["price_weight"])},
        ],
    }
    return tender, assumptions


def _deadline_kst(deadline: object) -> str:
    parsed = datetime.fromisoformat(str(deadline))
    return parsed.astimezone(KST).strftime("%Y-%m-%d %H:%M KST")


def _sections(markdown: str, criteria: list[str]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    heading: str | None = None
    body: list[str] = []
    lookup = {name.casefold(): name for name in criteria}

    def flush() -> None:
        if heading is None:
            return
        bare = re.sub(r"\s*\(\d+ points\)\s*$", "", heading)
        sections.append(
            {
                "criterion": lookup.get(bare.casefold()),
                "heading": heading,
                "markdown": ("\n".join([f"## {heading}", *body])).strip(),
            }
        )

    for line in markdown.splitlines():
        if line.startswith("## "):
            flush()
            heading = line[3:].strip()
            body = []
        elif heading is not None:
            body.append(line)
    flush()
    return sections


def _position_dict(position: Any, index: int) -> dict[str, Any]:
    shaped = asdict(position)
    shaped["summary"] = position.statement
    shaped["index"] = index
    return shaped


def draft_proposal(
    notice_number: str,
    supplier_evidence: Mapping[str, Any] | None = None,
    supplier_id: str = DEFAULT_SUPPLIER_ID,
    position_index: int = 0,
    historical_exercise: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Draft a proposal only behind an open PURSUE gate, from a synthetic supplier.

    The supplier is always one of ``fixtures.SUPPLIER_PROFILES``; its
    credentials gain a catalogue requirement only when the caller evidences that
    requirement as true.  Nothing is persisted and no Cortex run is started.
    """
    wanted = str(notice_number or "").strip()
    supplier = _supplier(supplier_id)
    assumptions: list[str] = []
    fixture = _fixture_tender(wanted)

    if fixture is not None:
        tender = fixture
        requirements = list(tender["eligibility_requirements"])
        verdicts = _evidence_for(requirements, supplier_evidence)
        state = "open"
        gate = "OPEN"
        decision_payload: dict[str, Any] = {"decision": None, "next_actions": []}
        deadline = None
    else:
        decision_payload = decide(wanted, supplier_evidence, now=now)
        row = get_tender(wanted, now=now)
        tender, assumptions = _catalogue_tender(row)
        requirements = list(tender["eligibility_requirements"])
        verdicts = _evidence_for(requirements, supplier_evidence)
        state = decision_payload["deadline_state"]
        deadline = row.get("deadline")
        if decision_payload["decision"] != "PURSUE":
            raise AgentCoreError(
                "proposal_locked",
                {
                    "decision": decision_payload["decision"],
                    "reason": decision_payload["reason"],
                    "proposal_gate": "LOCKED",
                    "gaps": [
                        check["requirement"]
                        for check in decision_payload["checks"]
                        if check["status"] != PASS
                    ],
                    "checks": decision_payload["checks"],
                    "next_actions": decision_payload["next_actions"],
                    "deadline_state": state,
                },
            )
        if state == "closed" and not historical_exercise:
            raise AgentCoreError(
                "notice_closed",
                {
                    "decision": decision_payload["decision"],
                    "proposal_gate": "LOCKED",
                    "deadline": deadline,
                    "deadline_state": state,
                    "next_actions": [
                        (
                            "No submission is possible; pass historical_exercise=true to draft "
                            "a clearly labelled historical exercise."
                        )
                    ],
                },
            )
        gate = "HISTORICAL EXERCISE" if state == "closed" else "OPEN"

    for requirement, verdict in zip(requirements, verdicts, strict=True):
        if verdict is True and requirement not in supplier["credentials"]:
            supplier["credentials"].append(requirement)
        if verdict is False and requirement in supplier["credentials"]:
            supplier["credentials"].remove(requirement)

    try:
        brief = build_pursuit_brief(tender, supplier)
    except PursuitInputError as error:
        raise AgentCoreError("invalid_pursuit_input", str(error)) from error
    if brief.status != "PURSUE":
        gaps = list(brief.missing_eligibility)
        if brief.capacity_gap_hours:
            gaps.append(f"{brief.capacity_gap_hours} delivery hours of capacity")
        if brief.status == "REVIEW":
            gaps.append("Comparable delivery evidence")
        raise AgentCoreError(
            "proposal_locked",
            {
                "decision": brief.status,
                "reason": f"The pursuit policy returned {brief.status} for {supplier['name']}.",
                "proposal_gate": "LOCKED",
                "gaps": gaps,
                "next_actions": list(brief.next_actions),
                "gap_closure_plan": [
                    dict(item) for item in build_gap_closure_plan(brief)
                ],
                "deadline_state": state,
            },
        )
    if position_index < 0 or position_index >= len(brief.win_positions):
        raise AgentCoreError(
            "invalid_position",
            f"position_index must be between 0 and {len(brief.win_positions) - 1}.",
        )
    brief = select_win_position(brief, tender, supplier, position_index)
    markdown = write_strategy_proposal(tender, supplier, brief)
    if gate == "HISTORICAL EXERCISE":
        markdown = (
            f"> HISTORICAL EXERCISE — notice {wanted} closed on {_deadline_kst(deadline)}; "
            "this draft is a qualification exercise on a past notice, not a submission.\n\n"
            + markdown
        )
    criteria = [str(row["name"]) for row in brief.score_map]
    findings = red_team_proposal(brief, markdown)
    tasks = [
        {"title": task["action"], **task} for task in red_team_tasks(brief, markdown)
    ]
    selected = brief.win_positions[brief.selected_position_index]

    return {
        "notice_number": wanted,
        "decision": "PURSUE",
        "proposal_gate": gate,
        "deadline_state": state,
        "deadline": deadline,
        "supplier": {"id": supplier["id"], "name": supplier["name"], "synthetic": True},
        "score_map": [
            {"name": str(row["name"]), "weight": int(row["weight"])}
            for row in brief.score_map
        ],
        "win_positions": [
            _position_dict(position, index)
            for index, position in enumerate(brief.win_positions)
        ],
        "selected_position": _position_dict(selected, brief.selected_position_index),
        "sections": _sections(markdown, criteria),
        "markdown": markdown,
        "red_team": list(findings),
        "tasks": tasks,
        "gap_closure_plan": [dict(item) for item in build_gap_closure_plan(brief)],
        "tender": tender,
        "assumptions": assumptions,
        "provider": PROVIDER,
        "persisted": False,
        "disclosure": DISCLOSURE,
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
    draft_parser = commands.add_parser("draft-proposal")
    draft_parser.add_argument("notice_number")
    draft_parser.add_argument(
        "--evidence", default=None, help="JSON object of evidence"
    )
    draft_parser.add_argument("--supplier", default=DEFAULT_SUPPLIER_ID)
    draft_parser.add_argument("--position", type=int, default=0)
    draft_parser.add_argument("--historical", action="store_true")
    draft_parser.add_argument(
        "--now",
        default=None,
        help="Aware ISO-8601 clock for deadline judgement (tests)",
    )
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
        elif args.command == "draft-proposal":
            evidence = json.loads(args.evidence) if args.evidence else None
            if evidence is not None and not isinstance(evidence, dict):
                raise AgentCoreError(
                    "invalid_evidence", "--evidence must be a JSON object."
                )
            clock = datetime.fromisoformat(args.now) if args.now else None
            payload = draft_proposal(
                args.notice_number,
                evidence,
                supplier_id=args.supplier,
                position_index=args.position,
                historical_exercise=args.historical,
                now=clock,
            )
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
