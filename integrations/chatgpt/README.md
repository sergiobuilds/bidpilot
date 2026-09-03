# BidPilot in ChatGPT

Two mounts, both read-only and anonymous. Replace `bidpilot-api-164282963747.us-central1.run.app` with the
hosted `bidpilot-api` host.

## 1 Custom GPT Action (OpenAPI import)

1. ChatGPT → Explore GPTs → Create → Configure → Actions → Create new action.
2. Choose "Import from URL" and paste `https://bidpilot-api-164282963747.us-central1.run.app/openapi.json`.
3. Authentication: None.
4. Paste the instructions below into the GPT's Instructions.

The manifest at `https://bidpilot-api-164282963747.us-central1.run.app/.well-known/ai-plugin.json` points at
the same OpenAPI document.

Endpoints imported: `GET /tenders`, `GET /tenders/{notice_number}`,
`POST /decide` (`{"notice_number": "...", "supplier_evidence": {"0": true}}`),
`GET /runs`, `GET /runs/{run_id}`.

## 2 MCP connector

In ChatGPT settings → Connectors → add a custom MCP connector with the URL
`https://bidpilot-api-164282963747.us-central1.run.app/mcp` (Streamable HTTP, no authentication). Tools:
`list_tenders`, `get_tender`, `decide`, `list_runs`, `replay`.

## Instructions to paste

```
You are a B2G pursuit assistant backed by BidPilot.
- Only discuss a proposal or Win Position when decide returns decision PURSUE and proposal_gate OPEN.
- Never invent evidence. Ask the user per requirement; unknown requirements stay EVIDENCE REQUIRED.
- If deadline_state is closed, say the notice is historical before anything else.
- You are a reader. Never claim to start a run or write to Snowflake.
- Every fact about a tender comes from the API response, never from memory.
```
