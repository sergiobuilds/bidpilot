# Proposal draft evidence (agent surface, 2026-09-03)

Branch `feat/proposal-draft-20260903`. `draft_proposal` in `src/bidpilot/agent_core.py`, exposed as CLI `draft-proposal`, MCP tool `draft_proposal`, REST `POST /proposal`, and `skills/bidpilot/scripts/bidpilot.sh draft-proposal`.

## local/ (dev host, uv run, clock in clock.txt)

| file | case | result |
|---|---|---|
| cli-draft-R26BK01680611-000-pursue.json | real notice, full evidence | PURSUE, gate OPEN, 14 sections, criteria Technical/Price |
| cli-draft-G2B-REPLAY-DATA-QUALITY-pursue.json | fixture tender | PURSUE, 14 sections, 4 criteria |
| cli-draft-R26BK01680611-000-review-locked.json | real notice, no evidence | error proposal_locked, decision REVIEW, 4 gaps |
| cli-draft-R26BK01680611-000-closed.json | real notice, `--now 2026-09-03T08:00:00+00:00` | error notice_closed |
| cli-draft-R26BK01680611-000-historical.json | same with `--historical` | PURSUE, gate HISTORICAL EXERCISE, banner first line |
| skill-draft-G2B-REPLAY-ANALYTICS-position1.json | skill script local mode | PURSUE, Operational continuity |

## cloud-run/ (bidpilot-api revision bidpilot-api-00003-l4q, commit d4ff190)

| file | case | result |
|---|---|---|
| deploy-deploy-host.log | gcloud run deploy from deploy host worktree | Service URL https://bidpilot-api-164282963747.us-central1.run.app |
| proposal-R26BK01680611-000-pursue.json | POST /proposal full evidence | HTTP 200, PURSUE, sections + markdown |
| proposal-R26BK01680611-000-locked.json | POST /proposal no evidence | HTTP 423 proposal_locked, REVIEW, 4 gaps |
| proposal-G2B-REPLAY-DATA-QUALITY.json | POST /proposal fixture | HTTP 200, 4 criteria |
| openapi.json | GET /openapi.json | lists /proposal, operationId draft_proposal |
| ai-plugin.json | GET /.well-known/ai-plugin.json | description mentions POST /proposal |
| skill-rest-draft-G2B-REPLAY-ANALYTICS.json | bidpilot.sh with BIDPILOT_API_URL | PURSUE |
| mcp-session-draft-proposal.json | mcp 2.1 Python client over /mcp (mcp_probe.py) | tools/list has draft_proposal; tools/call PURSUE, 14 sections |

No secrets are stored; the surface is anonymous and read-only.
