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
- Thirty-three passing tests and responsive Seed reference renders at 1440, 768, and 390 CSS pixels.

### Business value

The first buyer is a small B2G proposal team. BidPilot reduces wasted pursuit effort before drafting, makes the buyer's score allocation visible to every author, and preserves reusable delivery proof and lessons across bids. The commercial path is a team subscription with governed supplier memory, plus usage-based agent runs for intake, strategy, drafting, and review.

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

## Reproduction

```bash
uv sync --group dev
uv run pytest -q
export BIDPILOT_SNOWFLAKE_CONNECTION=bidpilot-reader
uv run streamlit run app.py
```

The authenticated account must contain the objects defined in `snowflake/sql/01_schema.sql` and the fixture in `02_seed_fixture.sql`. The exact Snowpark and Cortex Code commands are recorded in `snowflake/COCO_RUNBOOK.md`.

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
