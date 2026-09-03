DEPLOYED AND VERIFIED — production readback passed 2026-09-03 12:46 KST on Cloud Run revision bidpilot-demo-00020-rat (lean dashboard, 100% traffic, min-instances 1); agent API bidpilot-api live; main = f72a056

# Demo URLs

All public URLs serve `c78c40c` on Cloud Run revision `bidpilot-demo-00012-vvg` with one instance kept warm. The PPT may present these screens as the current public app.

| Surface | URL | Serves today |
|---|---|---|
| Dashboard | https://bidpilot-demo-tbauoylpra-uc.a.run.app | c78c40c (Open/Closed tags, KST, Open deadlines tile) |
| Real tender detail | https://bidpilot-demo-tbauoylpra-uc.a.run.app/?tender=R26BK01680611-000 | c78c40c (Verified replay in top bar, REVIEW explanation) |
| Verified Replay | https://bidpilot-demo-tbauoylpra-uc.a.run.app/?walkthrough=1 | c78c40c (named Snowflake loading steps) |
| Repository | https://github.com/sergiobuilds/bidpilot | branch pushed |
| Candidate branch | https://github.com/sergiobuilds/bidpilot/tree/fix/grand-finale-product-20260903 | 4 commits over main |

All three public routes were loaded signed-out from a fresh Playwright context at 1440×900, 768×900 and 390×844. Direct URL entry and reload reproduce the same state because every route is a query parameter, not session state.

| Agent API + MCP | https://bidpilot-api-164282963747.us-central1.run.app (`/mcp`, `/openapi.json`, `/tenders`, `/decide`, `/runs/cortex-final-20260802-a`) | separate Cloud Run service `bidpilot-api`, reader-only |
