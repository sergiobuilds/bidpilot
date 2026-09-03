DEPLOYED AND VERIFIED — production readback passed 2026-09-03 13:58 KST; bidpilot-demo-00024-fim and bidpilot-api-00005-suv both built from main 1955d4b, 100% traffic, min-instances 1

# Demo click path (three screens, one tab)

Presenter keeps one browser tab. Every step is a query-parameter route, so Back and reload return to the same state.

0. **Landing** `/` — the site opens on the landing page: the claim, the live pipeline, then Problem, How it works, Proof (the real notice's score sheet and the completed run's counts), Agents. Click `Open the workspace` (top right or hero).
1. **Dashboard** `?view=opportunities` — Say: six official G2B notices, separated by evidence level. Point at the two KPI tiles. The second tile reads `Open deadlines 1 · 5 closed · next 2026.09.03 · 16:00 KST` until 16:00 KST today, and `Open deadlines 0 · All deadlines passed · historical public sources` afterwards. Every row carries an `Open` or `Closed` tag next to a KST deadline. The blue `Open verified PURSUE replay →` button sits beside the filters, above the table.
2. **Real tender detail** — click `Review →` on `R26BK01680611-000`. Say: decision is `REVIEW`, eligibility gaps `4`, run `Not created`. Under the decision summary the candidate build explains: REVIEW is the correct outcome because the synthetic supplier profile has no evidence for four eligibility requirements, so no strategy or proposal is generated. This is evidence discipline, not a product failure.
2b. **Draft it live (45 seconds)** — scroll to `Run the decision and draft a proposal` at the end of the tender detail. Click `Run decision and draft` with nothing ticked: REVIEW, four gaps, no draft. Tick the four evidence boxes, click again: PURSUE, Win Position, fourteen proposal sections, red-team result, owned work, `Download proposal draft`. Say: the gate is evidence, the supplier is a disclosed synthetic profile, and every agent gets the same draft through `draft_proposal`. After 16:00 KST the same draft carries a HISTORICAL EXERCISE banner because the notice has closed.
3. **Verified replay** — click `Verified replay` in the detail top bar (first viewport on all three sizes on the candidate build; on the live main build the only link sits at the end of the page). Say: separate synthetic fixture, run `cortex-final-20260802-a`, decision `PURSUE`, highest weight 40 points, 3 strategies compared and 1 selected, 4 response plans, 8 proposal sections, red-team retained, 12 tasks, Snowflake and Cortex provenance. Loading captions on the candidate build name the Snowflake `BIDPILOT_READER` step being waited on.
4. **Return** — click the `BidPilot` brand in the replay top bar to get back to `/`.

What not to do on stage:
- Do not describe the closed notices as biddable. The catalogue is a historical public source snapshot retrieved 2026-08-24.
- Do not combine the real notice and the replay into one run; they are separate evidence.
- Do not click the evaluator workspace links unless asked; `Tender intake` and `Synthetic decision simulation` are supporting surfaces.
- Do not open the replay first on a cold instance; open the dashboard first (no Snowflake), then the replay.

5. **Agent surface (optional, 30 seconds)** — in a terminal on the presenter laptop, `cortex` with the `bidpilot` skill: type `List the open tenders and decide R26BK01680611-000` and show the REVIEW / 4 gaps answer. Or open `https://bidpilot-api-164282963747.us-central1.run.app/openapi.json` to show the same engine as an API any agent can mount. Say: the dashboard is one window; the product is the judgement engine plus the Snowflake record, mounted into whatever agent the bid team already uses.
