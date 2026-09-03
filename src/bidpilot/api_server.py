"""Anonymous read-only HTTP surface: REST, OpenAPI, ChatGPT manifest, MCP at /mcp."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel, Field

from bidpilot import agent_core
from bidpilot.agent_core import AgentCoreError
from bidpilot.mcp_server import server as mcp
from bidpilot.snowflake_store import configured_connection_name

VERSION = "0.1.0"
_STATUS = {
    "tender_not_found": 404,
    "run_not_found": 404,
    "supplier_not_found": 404,
    "proposal_locked": 423,
    "notice_closed": 423,
    "snowflake_not_configured": 503,
    "snowflake_error": 502,
}

# Cloud Run terminates TLS and forwards an arbitrary public host, so the
# transport's localhost DNS-rebinding allow-list must not apply here.  The
# surface is anonymous and read-only; sessions are stateless so any instance
# can answer any request.
mcp_app = mcp.streamable_http_app(
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    host="0.0.0.0",  # the container listens on every interface
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with mcp_app.router.lifespan_context(mcp_app):
        yield


app = FastAPI(
    title="BidPilot pursuit API",
    version=VERSION,
    description=(
        "Evidence-first B2G pursuit decisions over the public G2B catalogue, "
        "proposal drafting behind the PURSUE gate (POST /proposal, synthetic demo "
        "supplier, nothing persisted), plus read-only replay of completed Cortex "
        "analyses. Anonymous and read-only; the same policy the BidPilot app applies."
    ),
    lifespan=lifespan,
)


class DecideRequest(BaseModel):
    notice_number: str = Field(..., examples=["R26BK01680611-000"])
    supplier_evidence: dict[str, bool] | None = Field(
        default=None,
        description=(
            "Evidence the supplier actually holds: keys are the zero-based requirement "
            "index as a string or the exact requirement text; values true/false."
        ),
        examples=[{"0": True, "1": True}],
    )


class ProposalRequest(DecideRequest):
    supplier_id: str = Field(
        default=agent_core.DEFAULT_SUPPLIER_ID,
        description="A synthetic fixture supplier profile id; never a real company.",
    )
    position_index: int = Field(default=0, ge=0, description="Win Position to bind.")
    historical_exercise: bool = Field(
        default=False,
        description="Allow drafting for a closed notice as a labelled historical exercise.",
    )


@app.exception_handler(AgentCoreError)
async def _core_error(_: Request, error: AgentCoreError) -> JSONResponse:
    return JSONResponse(
        status_code=_STATUS.get(error.code, 400), content=error.to_dict()
    )


def _health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": VERSION,
        "snowflake_configured": configured_connection_name() is not None,
        "mcp": "/mcp",
        "openapi": "/openapi.json",
    }


# Google Front End answers /healthz itself with a 404 before Cloud Run sees it,
# so the same payload is also served at / and /health.
@app.get("/healthz", tags=["meta"])
def healthz() -> dict[str, Any]:
    return _health()


@app.get("/health", tags=["meta"], include_in_schema=False)
def health() -> dict[str, Any]:
    return _health()


@app.get("/", tags=["meta"], include_in_schema=False)
def root() -> dict[str, Any]:
    return _health()


@app.get("/tenders", tags=["tenders"], operation_id="list_tenders")
def list_tenders() -> list[dict[str, Any]]:
    """List the public G2B tender catalogue with each deadline judged open or closed."""
    return agent_core.list_tenders()


@app.get("/tenders/{notice_number}", tags=["tenders"], operation_id="get_tender")
def get_tender(notice_number: str) -> dict[str, Any]:
    """Return one catalogue row; the reviewed notice carries requirements and provenance."""
    return agent_core.get_tender(notice_number)


@app.post("/decide", tags=["decision"], operation_id="decide")
def decide(request: DecideRequest) -> dict[str, Any]:
    """Apply the pursuit policy without inventing evidence."""
    return agent_core.decide(request.notice_number, request.supplier_evidence)


@app.post(
    "/proposal",
    tags=["proposal"],
    operation_id="draft_proposal",
    responses={
        423: {
            "description": "proposal_locked (REVIEW/NO-GO with gaps) or notice_closed"
        },
        404: {"description": "tender_not_found or supplier_not_found"},
    },
)
def draft_proposal(request: ProposalRequest) -> dict[str, Any]:
    """Draft a proposal only when the pursuit decision is PURSUE; 423 with the decision payload otherwise. The supplier is a synthetic demo profile and nothing is persisted."""
    return agent_core.draft_proposal(
        request.notice_number,
        request.supplier_evidence,
        supplier_id=request.supplier_id,
        position_index=request.position_index,
        historical_exercise=request.historical_exercise,
    )


@app.get("/runs", tags=["runs"], operation_id="list_runs")
def list_runs() -> list[dict[str, Any]]:
    """List completed Cortex analyses via BIDPILOT_READER; 503 when not configured."""
    return agent_core.list_runs()


@app.get("/runs/{run_id}", tags=["runs"], operation_id="replay")
def replay(run_id: str) -> dict[str, Any]:
    """Replay one completed analysis with its Cortex provenance."""
    return agent_core.replay(run_id)


@app.get("/.well-known/ai-plugin.json", tags=["meta"], include_in_schema=False)
def ai_plugin(request: Request) -> dict[str, Any]:
    base = str(request.base_url).rstrip("/")
    return {
        "schema_version": "v1",
        "name_for_human": "BidPilot",
        "name_for_model": "bidpilot",
        "description_for_human": "Evidence-first B2G tender pursuit decisions.",
        "description_for_model": (
            "Read the public tender catalogue, apply the evidence-first pursuit policy "
            "with evidence the user supplies (never invent it), draft a proposal with "
            "POST /proposal only when the decision is PURSUE (synthetic demo supplier; "
            "423 proposal_locked lists the gaps otherwise), and replay completed "
            "Cortex analyses. REVIEW or NO-GO means no proposal is drafted."
        ),
        "auth": {"type": "none"},
        "api": {"type": "openapi", "url": f"{base}/openapi.json"},
        "mcp": {"url": f"{base}/mcp", "transport": "streamable-http"},
        "logo_url": f"{base}/healthz",
        "contact_email": "noreply@example.invalid",
        "legal_info_url": f"{base}/healthz",
    }


# Register the transport route at exactly /mcp: a Starlette mount would answer
# /mcp with a 307 to /mcp/, which reverse proxies rewrite to plain http.
app.router.routes.extend(mcp_app.routes)
