# BidPilot agent surface — two-track plan (2026-09-03, finale day)

Goal: BidPilot is a pursuit capability any agent can mount, not a dashboard. Two tracks run in parallel in separate worktrees and merge into `main` before 15:00 KST. The public Streamlit app (`bidpilot-demo`, revision 00012-vvg) is never touched.

## Shared core contract (Track A builds it; Track B codes against it)

Module `src/bidpilot/agent_core.py`, pure Python over existing modules (`tender_catalog`, `refinement_app.curated_tender_view`, `public_tender.assess_public_tender`-style logic, `snowflake_store.SnowflakeBidRoomStore`). No Streamlit import. Every function returns JSON-serialisable dicts.

| Function | Input | Output (keys) |
|---|---|---|
| `list_tenders(now=None)` | aware datetime optional | `[{notice_number, title, issuer, deadline, deadline_state: open/closed, evidence_level, status, official_url, contract_value_krw, technical_weight, price_weight}]` |
| `get_tender(notice_number)` | str | row above + for the reviewed notice: `eligibility_requirements: [str]`, `source_url`, `source_sha256`, `retrieved_at`, `delivery_term`, `supplier_boundary` |
| `decide(notice_number, supplier_evidence=None)` | evidence = `{requirement_index(int as str) or exact requirement text: true/false}` | `{notice_number, decision: PURSUE/REVIEW/NO-GO, reason, checks: [{requirement, status: PASS/FAIL/EVIDENCE REQUIRED}], evidence_gaps: int, weights: {technical, price}, proposal_gate: OPEN/LOCKED, next_actions: [str], provider: "LOCAL_PYTHON_POLICY", persisted: false, deadline_state}` — any FAIL → NO-GO; any EVIDENCE REQUIRED → REVIEW; all PASS → PURSUE with `proposal_gate: OPEN` only if `deadline_state == open`, else `LOCKED` with reason. Never invents evidence: with no evidence map the reviewed notice returns REVIEW with 4 gaps (matches the public app). |
| `list_runs()` | — | `[{run_id, state, is_complete, opportunity_id, created_at}]` via `BIDPILOT_READER`; raises `AgentCoreError("snowflake_not_configured")` without `BIDPILOT_SNOWFLAKE_CONNECTION`; never falls back to fixtures |
| `replay(run_id)` | str | `{run_id, decision, selected_strategy, strategy_count, plan_count, section_count, task_count, sections: [{criterion, title, weight}], tasks: [{title, owner}], provenance: {cortex_session_id, query_ids…}}` from the reader; same fail-closed rule |

CLI shim for scripts (not a product surface): `python -m bidpilot.agent_core <list-tenders|get-tender NOTICE|decide NOTICE [--evidence JSON]|list-runs|replay RUN_ID>` prints one JSON document to stdout, exit 1 with `{"error": ...}` on failure.

## Track A — core + remote MCP + HTTP API + Cloud Run `bidpilot-api`
Worktree `~/projects/personal/products/.worktrees/bidpilot-agent-mcp-20260903`, branch `feat/agent-mcp-20260903`.

1. 12:10–12:40 `agent_core.py` with TDD (`tests/test_agent_core.py`). Push as soon as green — Track B rebases on it.
2. 12:40–13:20 `src/bidpilot/mcp_server.py` using `mcp>=2` (`from mcp.server.mcpserver import MCPServer`; FastMCP was renamed — do not use v1 API). Tools: `list_tenders`, `get_tender`, `decide`, `list_runs`, `replay`. Transports: stdio (for local agents) and Streamable HTTP mounted at `/mcp` in a Starlette/FastAPI app `src/bidpilot/api_server.py` that also serves REST `GET /tenders`, `GET /tenders/{id}`, `POST /decide`, `GET /runs`, `GET /runs/{id}`, `GET /openapi.json`, `GET /healthz`, and `GET /.well-known/ai-plugin.json` (ChatGPT Actions manifest pointing at the OpenAPI). Read-only, anonymous; never exposes runner.
3. Dockerfile: keep the Streamlit CMD; add `BIDPILOT_MODE=api` branch in an entrypoint that runs `uvicorn bidpilot.api_server:app --port $PORT`.
4. 13:20–13:50 Deploy a **separate** Cloud Run service `bidpilot-api` from deploy host (`ssh <deploy-host>`, `export PATH=$HOME/.local/bin:$PATH`, project `project-236b096e-5b41-4315-a01`, region `us-central1`): `gcloud run deploy bidpilot-api --region us-central1 --source . --allow-unauthenticated --set-env-vars BIDPILOT_MODE=api,BIDPILOT_SNOWFLAKE_CONNECTION=bidpilot-reader --set-secrets /secrets/bidpilot-reader-key.p8=bidpilot-snowflake-reader-key:latest`. Use an deploy host worktree at the branch commit; never touch `~/projects/personal/products/bidpilot` there. Verify: `/healthz`, `/tenders`, `/decide`, `/runs/cortex-final-20260802-a` returns decision PURSUE with 3/4/8/12, and an MCP `initialize` + `tools/list` + `tools/call` over `/mcp` from dev host with a Python MCP client.
5. Deliver: URL, commit, evidence JSON under `dev/active/grand-finale-product-20260903/evidence/agent-surface/` (raw HTTP responses, MCP session transcript), README section stub text for Track B.

## Track B — Cortex Code skill + agent mounts
Worktree `~/projects/personal/products/.worktrees/bidpilot-coco-skill-20260903`, branch `feat/coco-skill-20260903`.

1. 12:10–12:30 Find the Cortex Code CLI (`cortex` on deploy host or dev host; `~/.snowflake/cortex/skills/` is the user skill dir on dev host). Read one existing skill there for the exact SKILL.md frontmatter Cortex Code accepts. Do not run any runner/Cortex workload that writes to Snowflake.
2. 12:30–13:20 Build `skills/bidpilot/SKILL.md` (+ `scripts/`): triggers on "tender / bid / pursue / 공고 / 입찰"; workflow = list tenders → get tender → decide with evidence the user supplies → if PURSUE explain Win Position via replay of a completed run; hard rules copied from the product (no proposal on REVIEW/NO-GO, no invented evidence, closed notices are historical). Scripts call the core CLI shim (`uv run python -m bidpilot.agent_core …`) and, when `BIDPILOT_API_URL` is set, the remote REST/MCP instead, so the skill works with or without a local checkout.
3. 13:20–13:50 Agent mounts under `integrations/`: `claude-code/.mcp.json` (remote `https://bidpilot-api-…run.app/mcp` and local stdio), `cursor/mcp.json`, `chatgpt/README.md` (Custom GPT Action import of `/openapi.json`, plus MCP connector URL), `cortex-code/README.md` (copy skill into `~/.snowflake/cortex/skills/bidpilot`, plus MCP server config if Cortex Code supports it — verify from its docs, do not guess). Add a README section "Mount BidPilot in your agent".
4. 13:50–14:20 Real verification: install the skill into `~/.snowflake/cortex/skills/bidpilot` on the host that has Cortex Code and run one read-only prompt ("list tenders and decide R26BK01680611-000"); run Claude Code with the local stdio MCP (`claude mcp add` in a scratch dir) and call one tool. Save transcripts under `dev/active/grand-finale-product-20260903/evidence/agent-surface/`.
5. Rebase on Track A's core commit as soon as it lands (`git fetch && git rebase origin/feat/agent-mcp-20260903` or cherry-pick); tests must pass together.

## Rules for both
- TDD, `uv run pytest tests/ -q` from the worktree root only, ruff on changed files, commit small, push immediately.
- Do not modify `src/bidpilot/ui.py`, `workspace_ui.py`, `refinement_app.py`, or the deployed `bidpilot-demo` service.
- No secrets in code or evidence. Reader only. No new Cortex runs, no Snowflake writes.
- 14:30 KST hard stop: whatever is verified gets merged; unverified pieces are reported as not done.
