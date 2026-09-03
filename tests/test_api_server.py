"""The remote agent surface: REST, OpenAPI, ChatGPT manifest, and MCP over HTTP."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from test_app import RUN_ID, FakeConnection, product_responses

from bidpilot import mcp_server
from bidpilot.api_server import app

REVIEWED = "R26BK01680611-000"
MCP_HEADERS = {"Accept": "application/json, text/event-stream"}


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_healthz_reports_the_surface_without_a_snowflake_connection(
    client, monkeypatch
) -> None:
    monkeypatch.delenv("BIDPILOT_SNOWFLAKE_CONNECTION", raising=False)
    for path in ("/healthz", "/health", "/"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.json()["status"] == "ok"
        assert response.json()["snowflake_configured"] is False


def test_tenders_endpoints_serve_the_catalogue(client) -> None:
    listed = client.get("/tenders").json()
    assert listed[0]["notice_number"] == REVIEWED
    assert len(listed) == 6

    detail = client.get(f"/tenders/{REVIEWED}").json()
    assert len(detail["eligibility_requirements"]) == 4

    missing = client.get("/tenders/R99BK00000000-000")
    assert missing.status_code == 404
    assert missing.json()["error"] == "tender_not_found"


def test_decide_endpoint_never_invents_evidence(client) -> None:
    response = client.post("/decide", json={"notice_number": REVIEWED})
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "REVIEW"
    assert body["evidence_gaps"] == 4

    evidenced = client.post(
        "/decide",
        json={
            "notice_number": REVIEWED,
            "supplier_evidence": {"0": True, "1": True, "2": True, "3": True},
        },
    ).json()
    assert evidenced["decision"] == "PURSUE"

    bad = client.post(
        "/decide", json={"notice_number": REVIEWED, "supplier_evidence": {"9": True}}
    )
    assert bad.status_code == 400
    assert bad.json()["error"] == "unknown_requirement"


def test_runs_endpoints_fail_closed_without_a_connection(client, monkeypatch) -> None:
    monkeypatch.delenv("BIDPILOT_SNOWFLAKE_CONNECTION", raising=False)
    listed = client.get("/runs")
    assert listed.status_code == 503
    assert listed.json()["error"] == "snowflake_not_configured"
    replayed = client.get(f"/runs/{RUN_ID}")
    assert replayed.status_code == 503


def test_runs_endpoints_read_the_reader_store(client, monkeypatch) -> None:
    monkeypatch.setenv("BIDPILOT_SNOWFLAKE_CONNECTION", "contest")
    with patch("bidpilot.snowflake_store.snowflake.connector.connect") as connect:
        connect.return_value = FakeConnection(product_responses())
        listed = client.get("/runs").json()
        replayed = client.get(f"/runs/{RUN_ID}").json()
    assert listed[0]["run_id"] == RUN_ID
    assert replayed["decision"] == "PURSUE"
    assert replayed["strategy_count"] == 3


def test_openapi_and_chatgpt_manifest_are_served(client) -> None:
    spec = client.get("/openapi.json").json()
    assert set(spec["paths"]) >= {
        "/tenders",
        "/tenders/{notice_number}",
        "/decide",
        "/runs",
        "/runs/{run_id}",
    }
    manifest = client.get("/.well-known/ai-plugin.json").json()
    assert manifest["api"]["type"] == "openapi"
    assert manifest["api"]["url"].endswith("/openapi.json")
    assert manifest["auth"]["type"] == "none"


def test_no_route_reaches_the_runner_or_writes(client) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert all(set(methods) <= {"get", "post"} for methods in paths.values())
    assert not any("run" in path and "runs" not in path for path in paths)


def test_mcp_server_exposes_the_six_read_only_tools() -> None:
    import asyncio

    tools = asyncio.run(mcp_server.server.list_tools())
    assert {tool.name for tool in tools} == {
        "list_tenders",
        "get_tender",
        "decide",
        "list_runs",
        "replay",
        "draft_proposal",
    }
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in tools)

    result = asyncio.run(
        mcp_server.server.call_tool("decide", {"notice_number": REVIEWED})
    )
    payload = result.structured_content or json.loads(result.content[0].text)
    assert payload["decision"] == "REVIEW"


def test_mcp_tools_fail_closed_as_tool_errors(client, monkeypatch) -> None:
    monkeypatch.delenv("BIDPILOT_SNOWFLAKE_CONNECTION", raising=False)
    called = _rpc(
        client, "tools/call", {"name": "list_runs", "arguments": {}}, request_id=9
    )
    assert called.status_code == 200, called.text
    payload = called.json()["result"]
    assert payload["isError"] is True
    assert "snowflake_not_configured" in payload["content"][0]["text"]


def _rpc(
    client: TestClient, method: str, params: dict | None = None, request_id: int = 1
):
    body = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params or {},
    }
    # No redirect is tolerated: a 307 to /mcp/ becomes plain http behind a proxy.
    return client.post("/mcp", json=body, headers=MCP_HEADERS, follow_redirects=False)


def test_mcp_streamable_http_is_mounted_at_mcp(client) -> None:
    initialised = _rpc(
        client,
        "initialize",
        {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0"},
        },
    )
    assert initialised.status_code == 200, initialised.text
    assert initialised.json()["result"]["serverInfo"]["name"] == "bidpilot"

    listed = _rpc(client, "tools/list", request_id=2)
    assert listed.status_code == 200, listed.text
    names = {tool["name"] for tool in listed.json()["result"]["tools"]}
    assert "list_tenders" in names

    called = _rpc(
        client, "tools/call", {"name": "list_tenders", "arguments": {}}, request_id=3
    )
    assert called.status_code == 200, called.text
    payload = called.json()["result"]
    assert payload.get("isError") is not True
    rows = payload["structuredContent"]["result"]
    assert rows[0]["notice_number"] == REVIEWED


FULL_EVIDENCE = {"0": True, "1": True, "2": True, "3": True}


def test_proposal_endpoint_drafts_only_behind_the_pursue_gate(client) -> None:
    drafted = client.post(
        "/proposal",
        json={"notice_number": REVIEWED, "supplier_evidence": FULL_EVIDENCE},
    )
    if drafted.status_code == 200:
        payload = drafted.json()
        assert payload["decision"] == "PURSUE"
        assert payload["proposal_gate"] == "OPEN"
        assert payload["sections"] and payload["markdown"].startswith("# ")
        assert payload["supplier"]["synthetic"] is True
    else:
        # After the real deadline the notice is closed: the gate refuses.
        assert drafted.status_code == 423
        assert drafted.json()["error"] == "notice_closed"

    locked = client.post("/proposal", json={"notice_number": REVIEWED})
    assert locked.status_code == 423
    body = locked.json()
    assert body["error"] == "proposal_locked"
    assert body["detail"]["decision"] == "REVIEW"
    assert len(body["detail"]["gaps"]) == 4

    fixture = client.post(
        "/proposal",
        json={"notice_number": "G2B-REPLAY-DATA-QUALITY", "position_index": 1},
    )
    assert fixture.status_code == 200, fixture.text
    assert fixture.json()["selected_position"]["title"] == "Operational continuity"

    unknown = client.post(
        "/proposal",
        json={"notice_number": "G2B-REPLAY-DATA-QUALITY", "supplier_id": "real-co"},
    )
    assert unknown.status_code == 404
    assert unknown.json()["error"] == "supplier_not_found"


def test_openapi_and_manifest_advertise_proposal_drafting(client) -> None:
    schema = client.get("/openapi.json").json()
    assert "/proposal" in schema["paths"]
    assert schema["paths"]["/proposal"]["post"]["operationId"] == "draft_proposal"
    assert "proposal" in schema["info"]["description"].lower()
    manifest = client.get("/.well-known/ai-plugin.json").json()
    assert "draft" in manifest["description_for_model"].lower()


def test_mcp_draft_proposal_tool_returns_sections_and_locks_as_a_tool_error(
    client,
) -> None:
    called = _rpc(
        client,
        "tools/call",
        {
            "name": "draft_proposal",
            "arguments": {"notice_number": "G2B-REPLAY-DATA-QUALITY"},
        },
        request_id=11,
    )
    assert called.status_code == 200, called.text
    result = called.json()["result"]
    assert not result.get("isError")
    payload = result.get("structuredContent") or json.loads(
        result["content"][0]["text"]
    )
    assert payload["decision"] == "PURSUE"
    assert [s["criterion"] for s in payload["sections"] if s["criterion"]] == [
        "Technical approach",
        "Comparable delivery",
        "Delivery team",
        "Price",
    ]

    locked = _rpc(
        client,
        "tools/call",
        {"name": "draft_proposal", "arguments": {"notice_number": REVIEWED}},
        request_id=12,
    )
    result = locked.json()["result"]
    assert result["isError"] is True
    assert "proposal_locked" in result["content"][0]["text"]
    assert (
        "EVIDENCE REQUIRED" in result["content"][0]["text"]
        or "gaps" in result["content"][0]["text"]
    )
