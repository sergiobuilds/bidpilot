DEPLOYED AND VERIFIED — production readback passed 2026-09-03 12:46 KST on Cloud Run revision bidpilot-demo-00020-rat (lean dashboard, 100% traffic, min-instances 1); agent API bidpilot-api live; main = f72a056

# Verified claims (what the PPT may state, with the evidence that backs each line)

Verified on 2026-09-03 KST on dev host against branch `fix/grand-finale-product-20260903` (local preview and container) and the live public app (main). Anything marked *candidate* is true only after Sergio approves deployment and production readback passes.

| Claim | Evidence | Scope |
|---|---|---|
| 168 tests pass, 0 failed | `test-results.txt` | candidate branch |
| The one failing test on main asserted a stale CSS literal; the layout contract (tender table before funnel and recent activity) held and is now asserted by DOM position | commit 8d544f4, `tests/test_workspace_ui.py` | candidate |
| No notice with a passed deadline is shown as due soon; each row carries Open/Closed judged against an aware clock; deadlines are shown in KST | commit cbb46ab, `test_dashboard_never_lists_a_passed_deadline_as_due_soon`, screenshots `candidate-local-dashboard-*.png` | candidate |
| Notice `R26BK01680611-000` remains `REVIEW` with 4 eligibility gaps and no run | `candidate-local-detail-*.dom.txt`, live `live-current-detail-*.png` | both |
| Verified replay shows `PURSUE`, 40-point top criterion, 3 strategies compared and 1 selected, 4 response plans, 8 proposal sections, 12 tasks, run `cortex-final-20260802-a`, header `Verified capability replay · separate synthetic fixture` | `screenshots/live-current-replay-1440x900-r0.dom.txt` | live (unchanged data path) |
| No horizontal overflow, document scroll works, no nested full-height scroller on dashboard, detail and replay at 1440, 768 and 390 | `browser-results.json` (`horizontalOverflow=false`, `pageScrollable=true`) | both |
| Verified replay CTA is in the first viewport of the dashboard (top nav) at all three widths | `browser-results.json` ctas | both |
| Verified replay CTA is in the first viewport of the tender detail (top bar) at all three widths | `browser-results.json` ctas, commit f7928c0 | candidate only (live: link at y≈2175 / 3008 / 3451 px) |
| Keyboard Tab reaches brand, Opportunities, Verified replay, then evaluator links in order | `browser-results.json` keyboard_focus_path | both |
| Row actions are 44 px tall on mobile | `browser-results.json` ctas height | both |
| Warm public loads: dashboard 2.5–3.4 s, detail 2.6–3.6 s, replay 2.7–3.1 s to content (n=3 at 1440 for each) | `browser-results.json` live section | live |
| First touch after 18 min idle: dashboard 17.4 s (9.0 s Cloud Run instance start, then Streamlit boot); replay right after 10.8 s (first reader connection); warm loads 2.7–3.5 s | `cold-start.md`, `cold-start-results.json` | live + container |
| No fixture fallback in authenticated mode; connection failure shows a visible error with a working retry | `tests/test_app.py::test_connection_failure_stays_visible_and_offers_a_working_retry` | both |
| No tracked secret; the reader key is a Cloud Run secret mount referenced by path only | `test-results.txt` | both |
| Container image builds from the candidate branch and serves the dashboard 3.4 s after `docker run` (HTTP 200 at 1.6 s) | `release-candidate-manifest.json` | candidate |

Do not claim: a live PURSUE on the real notice, currently biddable tenders, any customer, price, credential or past performance that is not in the fixture, or a new Cortex run.

## Added 2026-09-03 after 12:00 KST (all live)

| Claim | Evidence |
|---|---|
| Dashboard is now two KPIs (Needs review, Open deadlines), the tender table and one `Open verified PURSUE replay` button; funnel, recent activity and causal strip are gone; evaluator workspaces are footer links | `screenshots/production-lean-dashboard-*.png`, `browser-results.json` production_readback_lean_revision_00020_rat |
| Tender detail folds processing history and source evidence under the decision summary | `screenshots/production-lean-detail-1440x900-r0.dom.txt` |
| 204 tests pass | `test-results.txt` header + commit f72a056 |
| The same judgement engine is exposed as a remote MCP server and REST/OpenAPI at `https://bidpilot-api-164282963747.us-central1.run.app` (`/mcp`, `/tenders`, `/decide`, `/runs/{id}`, `/openapi.json`, `/.well-known/ai-plugin.json`), reader-only, no anonymous runner | `agent-surface/cloud-run/*.json`, `agent-surface/skill-script-rest-remote-dev-host.txt` |
| Claude Code mounts the remote MCP over HTTP and calls list_tenders, decide (REVIEW, 4 gaps) and replay (PURSUE 3/4/8/12) | `agent-surface/remote-mcp-claude-code-dev-host.txt` |
| A Cortex Code skill `bidpilot` is installed on a real Cortex Code CLI (v1.1.78), auto-loads on a tender prompt and answers REVIEW / 4 gaps / proposal LOCKED; the remote MCP is registered with `cortex mcp add` | `agent-surface/cortex-code-interactive-deploy-host.txt`, `agent-surface/cortex-code-mcp-add-deploy-host.txt` |
| Cursor, Gemini CLI and ChatGPT (Custom GPT Actions via OpenAPI, MCP connector) mount files exist | `integrations/` — ChatGPT import itself was not exercised |

Do not claim: `cortex exec` non-interactive runs (blocked on subscription accounts), a ChatGPT session that was actually connected, or any write path through the agent surface.
