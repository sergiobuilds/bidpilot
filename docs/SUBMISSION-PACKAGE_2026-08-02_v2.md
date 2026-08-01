---
doc_kind: project-material
status: canonical
version: 2026-08-02_v2
canonical_path: /home/elite/projects/personal/products/bidpilot/docs/SUBMISSION-PACKAGE_2026-08-02_v2.md
---

# BidPilot submission package

This is the paste-ready English submission source and the recording contract for the final BidPilot entry.

## Submission copy

### Title

BidPilot — Turn tender scoring into a proposal-winning Bid Room

### One-line description

BidPilot combines a public tender's evaluation matrix with supplier operating memory to decide whether to pursue, choose a proof-backed Win Position, draft the proposal, red-team it, and persist the work as one replayable Snowflake run.

### Problem

Small B2G teams lose weeks in two places: they pursue opportunities they cannot credibly win, and they begin writing without connecting the buyer's scoring model to their own delivery evidence. Qualification, strategy, drafting, review, and task ownership live in separate files and meetings. Generic AI can summarize the notice or produce fluent prose, but it does not maintain an accountable chain from official evaluation weights to supplier evidence and an executable bid plan.

### Solution

BidPilot creates a Bid Room around one tender and supplier profile. It computes a transparent `PURSUE`, `REVIEW`, or `NO-GO` decision; proposal generation remains locked unless the decision is `PURSUE`. The official score map then drives selectable Win Positions. Every criterion becomes a response plan with its weight, claim, supplier asset, owner, and evidence gap. Cortex Code writes eight proposal areas, red-teams the score-bearing sections, creates owned gap-closing work, and saves the complete result under one `run_id`.

### Why Snowflake and CoCo

This workflow requires more than a chat transcript. Snowflake holds the versioned Opportunity Graph that joins external tender requirements and evaluation criteria with internal credentials, availability, people, past delivery, and prior proposal assets. Snowpark evaluates the same policy next to the governed data. Cortex Code queries that graph and persists strategy, sections, tasks, and execution provenance under the same run. Streamlit then reloads the run through a least-privilege reader role. That shared, replayable state is the product's organizational memory.

### What is working

- An authenticated Snowpark 2×2 matrix across two tenders and two supplier profiles.
- A complete evidence-safe run, `bidpilot-v2-dq-northstar`, with one decision, one selected strategy, four response plans, eight sections, eleven tasks, and Cortex session/query provenance.
- A proposal gate that rejects raw, locked, `REVIEW`, and `NO-GO` inputs.
- Score-weighted proposal depth and criterion-specific supplier assets.
- A red-team that detects missing assets and empty validation or buyer-outcome content in the top-weighted response.
- An authenticated Streamlit Bid Room with editable/downloadable Markdown and no fixture fallback.
- Thirty-three passing tests and authenticated app renders with no horizontal overflow at 1440, 768, and 390 CSS pixels.

### Business value

The first buyer is a small B2G proposal team. BidPilot reduces wasted pursuit effort before drafting, makes the buyer's score allocation visible to every author, and preserves reusable delivery proof and lessons across bids. The commercial path is a team subscription with governed supplier memory, plus usage-based agent runs for intake, strategy, drafting, and review.

### Project description, 200 words

Bid teams lose time before proposal writing even begins. They pursue opportunities they cannot credibly win, then draft generic responses without connecting the buyer's scoring model to their own delivery evidence. BidPilot turns that fragmented process into one Snowflake-native Bid Room.

The workflow combines a versioned public tender with supplier credentials, capacity, people, and past delivery records in a Snowflake Opportunity Graph. Snowpark evaluates transparent eligibility, capacity, and comparable-delivery rules to return PURSUE, REVIEW, or NO-GO. Proposal generation remains locked unless the result is PURSUE. For a viable opportunity, Cortex Code reads the same governed records, selects a proof-backed Win Position, and creates a weighted response plan. Each evaluation criterion is bound to a claim, supplier asset, owner, and evidence gap before eight editable proposal areas are written.

The verified run persists its decision, selected strategy, four weighted plans, eight proposal sections, eleven owned tasks, and Cortex session and query provenance under one run ID. Streamlit reloads that run through a least-privilege reader role without silently falling back to fixtures. Missing personnel, pricing, or metrics are never invented; they become explicit pursuit tasks.

BidPilot is not another tender summarizer. It shows a team whether to bid, where the points are, what it can credibly say now, and what must be closed next.

## Ninety-second demo script

| Time | Screen and action | Voice-over |
|---:|---|---|
| 0–8 s | Open the authenticated Bid Room and point to the `PURSUE` verdict and run strip. | “Proposal tools start after the bid decision. BidPilot keeps the decision, strategy, proposal, and work in one Snowflake Bid Room.” |
| 8–20 s | Focus the 40-point Technical approach row: weight, supplier asset, and claim. | “The buyer's official score map is the control plane. This 40-point criterion is connected to recorded delivery evidence, not a generic prompt.” |
| 20–30 s | Show the decision dimensions and the two-supplier matrix result. | “Snowpark checks eligibility, capacity, and comparable delivery. The same tender is `PURSUE` for one supplier and `NO-GO` for another, which locks proposal generation.” |
| 30–43 s | Show the selected Win Position and four response-plan rows. | “Cortex Code turns the strongest evidence into a Win Position, then binds every weighted response to a claim, an asset, and an owner.” |
| 43–58 s | Scroll the editable eight-section proposal. | “The output is not a form fill. It is an editable strategy-led proposal covering the requirement, technical approach, comparable delivery, team, plan, risk, and commercial response.” |
| 58–70 s | Show review status and open tasks for people, pricing, and missing metrics. | “Missing personnel and pricing data are not invented. They become owned work, and the top-weighted section must carry validation and a buyer outcome.” |
| 70–82 s | Open execution provenance and show session ID plus query IDs. | “Snowpark and Cortex Code wrote one complete run. The provider, policy version, session, query IDs, sections, and tasks are reloadable from Snowflake.” |
| 82–90 s | Return to the 40-point row and proposal download. | “BidPilot turns the question ‘Should we bid?’ into ‘Here is how we win, what we can write now, and what the team must close next.’” |

## Pitch deck copy

### Slide 1 — The proposal starts too late

**Headline:** Teams waste the bid before they write it.

**Copy:** Qualification, win strategy, evidence, drafting, review, and ownership are separated across meetings and files. Generic AI can summarize a tender, but it cannot tell a team what it can credibly win with its current operating memory.

### Slide 2 — One visible decision chain

**Headline:** Should we bid, and if so, how do we win the score?

**Copy:** BidPilot connects the buyer's evaluation matrix to supplier credentials, capacity, people, and comparable delivery. It returns PURSUE, REVIEW, or NO-GO, then exposes the exact weighted criteria that control the proposal.

### Slide 3 — The 40-point moment

**Headline:** Official weight becomes writing priority.

**Copy:** The highest-value criterion shows its readiness, selected supplier proof, unresolved gap, planned claim, and owner before a paragraph is generated. Changing the supplier or Win Position changes the decision and response plan.

### Slide 4 — Why Snowflake is required

**Headline:** A Bid Room needs governed memory, not a chat transcript.

**Copy:** The Opportunity Graph joins versioned external tenders with internal operating records. Snowpark executes the pursuit policy next to the data. Streamlit reloads durable artifacts through a least-privilege role.

### Slide 5 — What Cortex Code does

**Headline:** One agent run turns evidence into owned work.

**Copy:** Cortex Code queries the graph, selects a Win Position, writes four weighted response plans and eight proposal areas, identifies missing evidence, creates eleven tasks, and stores session and query provenance under one run ID.

### Slide 6 — Failure is a product state

**Headline:** REVIEW and NO-GO do not get fluent fiction.

**Copy:** Proposal generation is locked when eligibility, capacity, or comparable-delivery gates fail. Missing people, pricing, and quantitative outcomes stay visible as gaps and tasks rather than invented claims.

### Slide 7 — Verified prototype

**Headline:** Authenticated end to end.

**Copy:** Two tenders by two suppliers produce PURSUE, NO-GO, PURSUE, and REVIEW. The complete run contains one decision, one strategy, four plans, eight sections, eleven tasks, and reproducible Snowflake and Cortex provenance. Thirty-three tests pass.

### Slide 8 — From one bid to operating memory

**Headline:** Every pursuit makes the next one smarter.

**Copy:** The first buyer is a small B2G bid team. BidPilot reduces wasted pursuits, focuses authors on score-bearing evidence, and accumulates reusable delivery proof and proposal learning in a governed team workspace.

## Expected judge questions

| Question | Answer |
|---|---|
| Why is this different from pasting the tender into a general LLM? | A general LLM has no governed supplier memory, deterministic pursuit gate, official-weight control plane, durable run contract, or owned evidence-gap workflow. BidPilot proves each link in that chain. |
| Why does Snowflake need to be in the core path? | Snowflake joins versioned external requirements with controlled internal evidence, executes Snowpark policy next to those records, and stores every downstream artifact and query provenance under one replayable run ID. Removing it removes the shared operating memory. |
| What exactly did Cortex Code do? | The recorded CLI session queried ten Snowflake object families, created the selected strategy and four response plans, wrote eight proposal sections and eleven tasks, and persisted its session and query IDs in the run trace. |
| How do you prevent hallucinated business facts? | The verified fixture deliberately has zero people and prior proposals and no pricing table. The resulting proposal names those gaps and creates tasks; it does not invent names, rates, prices, or outcome metrics. Tests cover the generation gates and weak high-weight content. |
| Is this only a qualification checker? | No. Qualification is the permission boundary. The visible product value is the next chain: weighted score map, Win Position, criterion-level blueprint, editable proposal, red-team, and owned work. |
| Does changing input change the output meaningfully? | Yes. The authenticated 2×2 matrix changes status across PURSUE, REVIEW, and NO-GO. Supplier projects, credentials, people, availability, official weights, and the selected Win Position change the claims, assets, owners, and response depth. |
| Can the system submit a bid automatically? | No. A human owns source review, supplier evidence, pricing, final editing, and submission. BidPilot prepares and governs the work; it does not transmit a legal bid. |
| What becomes the paid product after the hackathon? | A team Bid Room subscription with governed supplier memory and usage-based agent runs for intake, strategy, proposal drafting, review, and evidence-gap closure. |

## Reproduction

```bash
uv sync --group dev
uv run pytest -q
export BIDPILOT_SNOWFLAKE_CONNECTION=bidpilot-reader
uv run streamlit run app.py
```

The authenticated account must contain the objects defined in `snowflake/sql/01_schema.sql` and the fixture in `02_seed_fixture.sql`. The exact Snowpark and Cortex Code commands are recorded in `snowflake/COCO_RUNBOOK.md`.

## Technical architecture

| Layer | Responsibility | Verified implementation |
|---|---|---|
| Tender intake | Hash and review untrusted URL, PDF, or text input | Python intake contract and historical public-notice fixture |
| Opportunity Graph | Join opportunity versions, evaluation criteria, requirements, and supplier operating memory | `BIDPILOT_DEMO.BIDPILOT` Snowflake schema |
| Pursuit policy | Compute eligibility, capacity gap, comparable delivery, and status | Matching Python and authenticated Snowpark vectors |
| Agent execution | Query the graph and create strategy, response plans, sections, and tasks | Cortex Code CLI complete run with session and query IDs |
| Bid Room | Reload one complete run, expose the score map, edit proposal text, and download | Streamlit through `BIDPILOT_READER`, without fixture fallback |
| Verification | Exercise gates, content variation, persistence, and responsive UI | 33 tests, authenticated AppTest, 1440/768/390 captures |

## Data, safety, and license disclosure

| Asset | Status and permitted claim |
|---|---|
| Two tender replays and two supplier profiles | Synthetic contest fixtures created for this repository. No customer or confidential company data. |
| G2B case `R26BK01490484` | Closed historical public notice used for intake and qualification testing. Source URL, retrieval date, page count, and SHA-256 are recorded in code. It is not presented as currently open. |
| Snowflake run artifacts | Generated from the synthetic fixture through authenticated Snowpark and Cortex Code execution. |
| Generated proposal | Demo output only; named people, rates, prices, and quantitative outcomes absent from source tables are not asserted. |
| Source code | MIT License, except third-party dependencies under their own licenses. |

No final bid is submitted by the product. A human owns source review, company evidence, pricing, and the final submission.

## Final submission checklist

- Replace the repository placeholder with the judge-accessible GitHub URL and verified commit SHA.
- Record the 90-second video from authenticated mode and verify audio, text size, and URL permissions from a signed-out browser.
- Paste the title, one-line description, problem, solution, Snowflake explanation, and business value without adding unsupported claims.
- Confirm the repository, video, and any live demo remain accessible for the judging window.
- Sergio performs the external final-submit click after reviewing the rendered form.

## Official contest status verified on 2 August 2026

- Korea is explicitly eligible under Japan & Korea, and the event is marked Global and online.
- Registration closes on 2 August 2026.
- Prototype submissions close on 6 August 2026.
- The selected problem statement is Intelligent Workflow Automation Agent.
- The published rubric is Real-World Relevance 30%, Technical Execution 40%, and Solution Completeness 30%.
- Official event page: `https://hack2skill.com/event/cococlihack/`.
