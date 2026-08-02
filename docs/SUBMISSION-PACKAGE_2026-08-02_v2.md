---
doc_kind: project-material
status: canonical
version: 2026-08-02_v4
canonical_path: ~/projects/personal/products/bidpilot/docs/SUBMISSION-PACKAGE_2026-08-02_v2.md
---

# BidPilot submission package

This is the paste-ready English submission source and the recording contract for the final BidPilot entry.

## Submission copy

### Title

BidPilot — Turn tender scoring into a proposal-winning Bid Room

### One-line description

BidPilot combines a public tender's evaluation matrix with supplier operating memory to decide whether to pursue, choose a proof-backed Win Position, draft the proposal, red-team it, and persist the work as one replayable Snowflake run.

### Portal brief, under 1,024 characters

BidPilot is a Snowflake-native Bid Room for small B2G teams. It joins a public tender's requirements and evaluation weights with governed supplier credentials, capacity, people, and delivery history. Snowpark returns PURSUE, REVIEW, or NO-GO before drafting is allowed. For a viable bid, Cortex Code compares three Win Positions, creates score-weighted response plans, drafts eight editable proposal areas, red-teams the highest-value claims, and assigns missing evidence as owned work. Every decision, strategy, section, task, Cortex session, and query reference persists under one replayable run ID. A least-privilege Streamlit app reloads that run without fixture fallback. The verified prototype includes an authenticated 2x2 decision matrix, a complete runner-only Cortex run, 48 passing tests, responsive public deployment, a 4:38 English demo, and an eight-page PDF deck.

### Portal links and file

| Field | Value |
|---|---|
| Challenge | Intelligent Workflow Automation Agent |
| GitHub public repository | `https://github.com/sergiobuilds/bidpilot` — private until Sergio approves the public transition |
| Deployed prototype | `https://bidpilot-demo-tbauoylpra-uc.a.run.app` |
| Public demo video | `https://storage.googleapis.com/bidpilot-demo-164282963747/BidPilot-Final-Demo.mp4` |
| PDF deck | `dev/active/final-forge/submission-deck/BidPilot-Submission-Deck.pdf` |

### Problem

Small B2G teams lose weeks in two places: they pursue opportunities they cannot credibly win, and they begin writing without connecting the buyer's scoring model to their own delivery evidence. Qualification, strategy, drafting, review, and task ownership live in separate files and meetings. Generic AI can summarize the notice or produce fluent prose, but it does not maintain an accountable chain from official evaluation weights to supplier evidence and an executable bid plan.

### Solution

BidPilot creates a Bid Room around one tender and supplier profile. It computes a transparent `PURSUE`, `REVIEW`, or `NO-GO` decision; proposal generation remains locked unless the decision is `PURSUE`. The official score map then drives selectable Win Positions. Every criterion becomes a response plan with its weight, claim, supplier asset, owner, and evidence gap. Cortex Code writes eight proposal areas, red-teams the score-bearing sections, creates owned gap-closing work, and saves the complete result under one `run_id`.

### Why Snowflake and CoCo

This workflow requires more than a chat transcript. Snowflake holds the versioned Opportunity Graph that joins external tender requirements and evaluation criteria with internal credentials, availability, people, past delivery, and prior proposal assets. Snowpark evaluates the same policy next to the governed data. Cortex Code queries that graph and persists strategy, sections, tasks, and execution provenance under the same run. Streamlit then reloads the run through a least-privilege reader role. That shared, replayable state is the product's organizational memory.

### What is working

- An authenticated Snowpark 2×2 matrix across two tenders and two supplier profiles.
- A complete runner-only run, `cortex-final-20260802-a`, with one decision, three strategies with one selected, four response plans, eight sections, twelve tasks, and Cortex session/query provenance.
- A proposal gate that rejects raw, locked, `REVIEW`, and `NO-GO` inputs.
- Score-weighted proposal depth and criterion-specific supplier assets.
- A red-team that detects missing assets and empty validation or buyer-outcome content in the top-weighted response.
- An authenticated Streamlit Bid Room with editable/downloadable Markdown and no fixture fallback.
- Forty-eight passing tests and public authenticated app renders at 1440, 768, and 390 CSS pixels.

### Business value

The first buyer is a small B2G proposal team. BidPilot reduces wasted pursuit effort before drafting, makes the buyer's score allocation visible to every author, and preserves reusable delivery proof and lessons across bids. The commercial path is a team subscription with governed supplier memory, plus usage-based agent runs for intake, strategy, drafting, and review.

### Project description, 200 words

Bid teams lose time before proposal writing even begins. They pursue opportunities they cannot credibly win, then draft generic responses without connecting the buyer's scoring model to their own delivery evidence. BidPilot turns that fragmented process into one Snowflake-native Bid Room.

The workflow combines a versioned public tender with supplier credentials, capacity, people, and past delivery records in a Snowflake Opportunity Graph. Snowpark evaluates transparent eligibility, capacity, and comparable-delivery rules to return PURSUE, REVIEW, or NO-GO. Proposal generation remains locked unless the result is PURSUE. For a viable opportunity, Cortex Code reads the same governed records, selects a proof-backed Win Position, and creates a weighted response plan. Each evaluation criterion is bound to a claim, supplier asset, owner, and evidence gap before eight editable proposal areas are written.

The verified run persists its decision, three strategies with one selected, four weighted plans, eight proposal sections, twelve owned and adversarial tasks, and Cortex session and query provenance under one run ID. Streamlit reloads that run through a least-privilege reader role without silently falling back to fixtures. Missing personnel, pricing, or metrics become explicit pursuit tasks.

BidPilot is not another tender summarizer. It shows a team whether to bid, where the points are, what it can credibly say now, and what must be closed next.

## Final demo contract

| Time | Screen | Purpose |
|---:|---|---|
| 0:00–0:37 | Title and problem | Establish the pre-writing loss and product question. |
| 0:37–1:09 | Public tender intake | Show URL/PDF input and reviewed source boundary. |
| 1:09–2:13 | Pursuit verdict and score map | Show permission to draft and the official weighted control plane. |
| 2:13–3:04 | Strategy and proposal | Compare three Win Positions and open the selected proposal. |
| 3:04–3:44 | Adversarial review and owned work | Show review-gated download and twelve closure tasks. |
| 3:44–4:38 | Snowflake architecture, provenance, and close | Prove runner, reader, session, query, lifecycle, and cost boundaries. |

The repository contains a 278.136-second, 1440×900 H.264/AAC final demo at `dev/active/final-forge/BidPilot-Final-Demo.mp4`. It uses the public intake, authenticated run, Snowflake architecture, and closing deck frames with English narration. The public copy returns HTTP 206 for signed-out range requests at `https://storage.googleapis.com/bidpilot-demo-164282963747/BidPilot-Final-Demo.mp4`.

The companion pitch at `dev/active/final-forge/BidPilot-90s-Pitch.mp4` is exactly 90 seconds and follows the compressed verdict → score map → Win Position → proposal → red-team → Snowflake proof sequence. It has English narration and burned subtitles. The Hack2Skill portal requires a 3–5-minute screen recording, so the 4:38 public video remains the submission artifact.

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

**Copy:** Cortex Code queries the graph, compares three Win Positions, writes four weighted response plans and eight proposal areas, identifies missing evidence, creates twelve tasks, and stores session and query provenance under one run ID.

### Slide 6 — Failure is a product state

**Headline:** REVIEW and NO-GO do not get fluent fiction.

**Copy:** Proposal generation is locked when eligibility, capacity, or comparable-delivery gates fail. Missing people, pricing, and quantitative outcomes stay visible as gaps and tasks rather than invented claims.

### Slide 7 — Verified prototype

**Headline:** Authenticated end to end.

**Copy:** Two tenders by two suppliers produce PURSUE, NO-GO, PURSUE, and REVIEW. The final Cortex run contains one decision, three strategies with one selected, four plans, eight sections, twelve tasks, and reproducible Snowflake and Cortex provenance. Forty-eight tests pass.

### Slide 8 — From one bid to operating memory

**Headline:** Every pursuit makes the next one smarter.

**Copy:** The first buyer is a small B2G bid team. BidPilot reduces wasted pursuits, focuses authors on score-bearing evidence, and accumulates reusable delivery proof and proposal learning in a governed team workspace.

## Expected judge questions

| Question | Answer |
|---|---|
| Why is this different from pasting the tender into a general LLM? | A general LLM has no governed supplier memory, deterministic pursuit gate, official-weight control plane, durable run contract, or owned evidence-gap workflow. BidPilot proves each link in that chain. |
| Why does Snowflake need to be in the core path? | Snowflake joins versioned external requirements with controlled internal evidence, executes Snowpark policy next to those records, and stores every downstream artifact and query provenance under one replayable run ID. Removing it removes the shared operating memory. |
| What exactly did Cortex Code do? | The recorded CLI session queried ten Snowflake object families, created the selected strategy and four response plans, wrote eight proposal sections and twelve tasks, and persisted its session and query IDs in the run trace. |
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
| Verification | Exercise gates, content variation, persistence, and responsive UI | 48 tests, authenticated AppTest, 1440/768/390 captures |

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
- Keep the exact 278.136-second narrated demo public and verify audio, text size, and URL permissions from a signed-out browser.
- Paste the title, one-line description, problem, solution, Snowflake explanation, and business value without adding unsupported claims.
- Confirm the repository, video, and any live demo remain accessible for the judging window.
- Sergio performs the external final-submit click after reviewing the rendered form.

## Official contest status verified on 2 August 2026

- Korea is explicitly eligible under Japan & Korea, and the event is marked Global and online.
- Registration closes on 2 August 2026.
- The authenticated dashboard shows prototype and repository-link submissions closing on 7 August 2026 at 03:29 KST.
- The selected problem statement is Intelligent Workflow Automation Agent.
- The published rubric is Real-World Relevance 30%, Technical Execution 40%, and Solution Completeness 30%.
- Official event page: `https://hack2skill.com/event/cococlihack/`.

## Change history

- 2026-08-02 v3: Updated the verified automated test count after lifecycle, least-privilege, completeness, and failure-state hardening.
- 2026-08-02 v4: Updated the package for the runner-only Cortex run, public deployment, 4 minute 38 second narrated demo, and 8-page PDF deck.
