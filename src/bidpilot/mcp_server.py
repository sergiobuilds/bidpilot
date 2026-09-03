"""MCP server over the agent core: six read-only tools, stdio or Streamable HTTP.

Run ``python -m bidpilot.mcp_server`` for a stdio server (local agents such as
Claude Code, Cursor, or Cortex Code).  The HTTP transport is mounted at ``/mcp``
by :mod:`bidpilot.api_server`.  Nothing here writes to Snowflake or starts a
Cortex run.
"""

from __future__ import annotations

import functools
import json
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from bidpilot import agent_core
from bidpilot.agent_core import AgentCoreError

SERVER_NAME = "bidpilot"
INSTRUCTIONS = (
    "BidPilot is an evidence-first B2G pursuit capability. Use list_tenders and "
    "get_tender to read the public catalogue, decide to apply the pursuit policy "
    "with supplier evidence you actually hold (never invent evidence), and "
    "list_runs/replay to read completed Cortex analyses. draft_proposal writes a "
    "proposal draft only when decide would return PURSUE, from a synthetic demo "
    "supplier profile; a REVIEW or NO-GO decision means no proposal is drafted "
    "and the tool reports the gaps instead. Closed notices are historical and "
    "draft only as a labelled historical exercise."
)

READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, openWorldHint=False
)

server = MCPServer(
    SERVER_NAME,
    title="BidPilot pursuit capability",
    instructions=INSTRUCTIONS,
    version="0.1.0",
)


def _tool(function):
    """Convert core failures into MCP tool errors instead of transport errors."""

    @functools.wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except AgentCoreError as error:
            detail = error.detail
            if isinstance(detail, dict):
                detail = json.dumps(detail, ensure_ascii=False)
            suffix = f" — {detail}" if detail else ""
            raise ToolError(f"{error.code}{suffix}") from error

    return wrapper


@server.tool(annotations=READ_ONLY)
@_tool
def list_tenders() -> list[dict[str, Any]]:
    """List the public G2B tender catalogue with each deadline judged open or closed."""
    return agent_core.list_tenders()


@server.tool(annotations=READ_ONLY)
@_tool
def get_tender(notice_number: str) -> dict[str, Any]:
    """Return one catalogue row; the reviewed notice carries eligibility requirements and source provenance."""
    return agent_core.get_tender(notice_number)


@server.tool(annotations=READ_ONLY)
@_tool
def decide(
    notice_number: str, supplier_evidence: dict[str, bool] | None = None
) -> dict[str, Any]:
    """Apply the pursuit policy. Evidence keys are the zero-based requirement index as a string or the exact requirement text; values are true/false. Missing evidence yields REVIEW, any false yields NO-GO."""
    return agent_core.decide(notice_number, supplier_evidence)


@server.tool(annotations=READ_ONLY)
@_tool
def list_runs() -> list[dict[str, Any]]:
    """List completed Cortex analyses through the BIDPILOT_READER role; fails closed without a configured connection."""
    return agent_core.list_runs()


@server.tool(annotations=READ_ONLY)
@_tool
def replay(run_id: str) -> dict[str, Any]:
    """Replay one completed analysis: decision, selected strategy, rubric plan, proposal sections, tasks, and Cortex provenance."""
    return agent_core.replay(run_id)


@server.tool(annotations=READ_ONLY)
@_tool
def draft_proposal(
    notice_number: str,
    supplier_evidence: dict[str, bool] | None = None,
    supplier_id: str = agent_core.DEFAULT_SUPPLIER_ID,
    position_index: int = 0,
    historical_exercise: bool = False,
) -> dict[str, Any]:
    """Draft a proposal for a catalogue notice or a fixture tender id, only when decide would return PURSUE. Returns score_map, win_positions, sections, markdown, red_team findings and tasks from a synthetic demo supplier (never a real company). Errors: proposal_locked (REVIEW/NO-GO, with gaps and next_actions), notice_closed (pass historical_exercise=true only after asking the user). Persists nothing."""
    return agent_core.draft_proposal(
        notice_number,
        supplier_evidence,
        supplier_id=supplier_id,
        position_index=position_index,
        historical_exercise=historical_exercise,
    )


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
