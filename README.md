# BidPilot

BidPilot is an evidence-aware B2G Pursuit Agent built for the Snowflake CoCo CLI Hackathon 2026. It turns a public tender and a supplier profile into a pursuit decision, a score-weighted Win Position, an editable proposal, owned gap-closing work, and one replayable Bid Room run.

## The product

Most proposal tools begin after a team has already decided to bid. BidPilot starts earlier and keeps the decision connected to the writing:

1. Capture or replay a tender and its official evaluation weights.
2. Compare eligibility, delivery capacity, and comparable work with a supplier profile.
3. Return `PURSUE`, `REVIEW`, or `NO-GO`; only `PURSUE` can generate a proposal.
4. Select a Win Position and bind each weighted criterion to a claim, supplier asset, and owner.
5. Generate eight proposal areas, red-team the score-bearing sections, and create gap-closing tasks.
6. Reload the decision, strategy, sections, tasks, and execution provenance from one Snowflake `run_id`.

The differentiator is not tender summarization. It is the visible causal chain from the buyer's 40-point criterion to supplier evidence, strategy, proposal content, review, and owned work.

The authenticated product presents that chain as four screens: `Opportunities`, `Bid Decision`, `Win Plan`, and `Proposal Room`. Snowflake and Cortex provenance stays available inside `Run proof` instead of interrupting the bid workflow.

## Why Snowflake

Snowflake is the operating memory, not a decorative database. The Opportunity Graph joins external tender versions with internal credentials, availability, people, and delivery records. Snowpark executes the pursuit policy next to that data. Cortex Code reads the same graph and persists the selected strategy, rubric response plan, proposal sections, tasks, and trace under one run identifier.

The current verified run is `cortex-final-20260802-a`. It contains one decision, three materially different strategies with one selected, four weighted plans, eight proposal sections, twelve owned and adversarial tasks, and Cortex session/query provenance. Cortex Code created it through `BIDPILOT_RUNNER`; the public app reloads it through `BIDPILOT_READER`.

## Run and verify

```bash
uv sync --group dev
uv run pytest -q
uv run streamlit run app.py
```

Authenticated mode uses a named Snowflake CLI connection and never falls back to fixtures:

```bash
export BIDPILOT_SNOWFLAKE_CONNECTION=bidpilot-reader
uv run streamlit run app.py
```

Load the schema and fixture, then run the Snowpark matrix with the commands in [COCO_RUNBOOK.md](snowflake/COCO_RUNBOOK.md). No LLM API key is required; Cortex Code uses the authenticated CLI session.

The matrix runner persists `RUNNING`, `FAILED`, and `COMPLETED` states, requires exactly one decision per run, and supports idempotent retry. The role setup narrows table grants and configures a five-credit monthly resource monitor, 300-second statement timeout, 60-second queue timeout, and 60-second warehouse auto-suspend.

## Evidence and boundaries

| Surface | Verified state |
|---|---|
| Python proposal, policy, store, and four-screen UI suite | 59 tests pass |
| Snowpark matrix | Four runner-only tender/supplier combinations match the Python policy and complete their persisted lifecycle |
| Complete Cortex run | One decision, three strategies, four plans, eight sections, twelve tasks, and trace share one `run_id` |
| Streamlit authenticated mode | Complete run reloads through `BIDPILOT_READER` with editable/downloadable Markdown |
| Public deployment | `https://bidpilot-demo-tbauoylpra-uc.a.run.app` renders the authenticated run |
| Responsive authenticated app | Actual Snowflake-backed renders at 1440, 768, and 390 CSS pixels report no horizontal overflow |

The submitted Cloud Run deployment remains the attempt 1 baseline. The WDS four-screen redesign is verified locally against the authenticated reader connection and is waiting for VivoBook visual sign-off before deployment.

Verified public captures are stored under `dev/active/final-forge/public-app-verified/`, `public-app-768/`, and `public-app-390/`. The portal-ready 278.136-second narrated demo is `dev/active/final-forge/BidPilot-Final-Demo.mp4`. A separate 90-second English pitch with burned subtitles is `dev/active/final-forge/BidPilot-90s-Pitch.mp4`; application scenes can be regenerated with `capture-demo.mjs`.

The replay records are synthetic contest fixtures. The included public G2B notice is a closed historical example used only to test intake and qualification; it is not presented as an open opportunity. `PEOPLE`, prior-proposal, and pricing evidence absent from the Snowflake run remain explicit tasks and are not invented in the proposal.

## Submission and project records

- [Submission package and final demo contract](docs/SUBMISSION-PACKAGE_2026-08-02_v2.md)
- [Project map](docs/MASTER-MAP.md)
- [Decision record](docs/CHRONICLE.md)
- [Current handoff](PASSDOWN.md)
- [MIT License](LICENSE)

## Change history

- 2026-08-02: Applied runner lifecycle, least-privilege roles, bounded compute, a new Cortex Code run, responsive public deployment, criterion-grouped persisted drafting, and 48-test verification.
- 2026-08-02: Rebuilt the authenticated UI through Design Forge and the Wanted Design System as a four-screen workflow, then verified 59 tests and no horizontal overflow at 1440, 768, and 390 CSS pixels.
