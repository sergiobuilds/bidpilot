DEPLOYED AND VERIFIED — production readback passed 2026-09-03 11:40 KST on Cloud Run revision bidpilot-demo-00012-vvg (100% traffic, min-instances 1); main = c78c40c

# Demo click path (three screens, one tab)

Presenter keeps one browser tab. Every step is a query-parameter route, so Back and reload return to the same state.

1. **Dashboard** `/` — Say: six official G2B notices, separated by evidence level. Point at the KPI band. On the candidate build the fourth tile reads `Open deadlines 1 · 5 closed · next 2026.09.03 · 16:00 KST` until 16:00 KST today, and `Open deadlines 0 · All deadlines passed · historical public sources` afterwards. Every row carries an `Open` or `Closed` tag next to a KST deadline. The `PURSUE 0` tile links to the verified replay.
2. **Real tender detail** — click `Review →` on `R26BK01680611-000`. Say: decision is `REVIEW`, eligibility gaps `4`, run `Not created`. Under the decision summary the candidate build explains: REVIEW is the correct outcome because the synthetic supplier profile has no evidence for four eligibility requirements, so no strategy or proposal is generated. This is evidence discipline, not a product failure.
3. **Verified replay** — click `Verified replay` in the detail top bar (first viewport on all three sizes on the candidate build; on the live main build the only link sits at the end of the page). Say: separate synthetic fixture, run `cortex-final-20260802-a`, decision `PURSUE`, highest weight 40 points, 3 strategies compared and 1 selected, 4 response plans, 8 proposal sections, red-team retained, 12 tasks, Snowflake and Cortex provenance. Loading captions on the candidate build name the Snowflake `BIDPILOT_READER` step being waited on.
4. **Return** — click the `BidPilot` brand in the replay top bar to get back to `/`.

What not to do on stage:
- Do not describe the closed notices as biddable. The catalogue is a historical public source snapshot retrieved 2026-08-24.
- Do not combine the real notice and the replay into one run; they are separate evidence.
- Do not click the evaluator workspace links unless asked; `Tender intake` and `Synthetic decision simulation` are supporting surfaces.
- Do not open the replay first on a cold instance; open the dashboard first (no Snowflake), then the replay.
