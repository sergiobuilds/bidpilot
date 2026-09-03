# Agent surface evidence — bidpilot-api (2026-09-03)

Service: `https://bidpilot-api-164282963747.us-central1.run.app` (Cloud Run, us-central1, separate from `bidpilot-demo`).
Revision: `bidpilot-api-00002-bdf`, built from branch `feat/agent-mcp-20260903` commit `023a15f`.
Verified from dev host at 12:30 KST with curl and the Python `mcp` 2.x client; raw responses in this directory, no secrets.

| Check | Result | File |
|---|---|---|
| `GET /`, `GET /health` | 200, `snowflake_configured: true` | `cloud-run/root.json`, `cloud-run/health.json` |
| `GET /healthz` | 404 from Google Front End (GFE answers this path itself); use `/health` | `cloud-run/healthz-gfe.txt` |
| `GET /tenders` | 200, 6 rows, reviewed notice first | `cloud-run/tenders.json` |
| `GET /tenders/R26BK01680611-000` | 200, 4 eligibility requirements, source sha256 | `cloud-run/tender-R26BK01680611-000.json` |
| `POST /decide {"notice_number":"R26BK01680611-000"}` | REVIEW, 4 gaps, gate LOCKED, deadline open | `cloud-run/decide.json` |
| `GET /runs` | 200, 12 runs via BIDPILOT_READER | `cloud-run/runs.json` |
| `GET /runs/cortex-final-20260802-a` | PURSUE, strategies 3, plans 4, sections 8, tasks 12, Cortex provenance | `cloud-run/run-cortex-final-20260802-a.json` |
| `GET /openapi.json`, `/.well-known/ai-plugin.json` | 200, https URLs | `cloud-run/openapi.json`, `cloud-run/ai-plugin.json` |
| MCP over `/mcp`: initialize, tools/list (5 tools), tools/call replay | PURSUE 3/4/8/12, `is_error: false` | `cloud-run/mcp-session-replay.json` |
| Local image `BIDPILOT_MODE=api` | same REST + MCP session without Snowflake (503 / tool error fail-closed) | `local-container/` |
| Local image default mode | Streamlit `/_stcore/health` OK | (console only) |

Contract: `src/bidpilot/agent_core.py`; MCP tools in `src/bidpilot/mcp_server.py` (stdio: `python -m bidpilot.mcp_server`); HTTP in `src/bidpilot/api_server.py`.
