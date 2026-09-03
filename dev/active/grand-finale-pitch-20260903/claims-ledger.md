# BidPilot Grand Finale Claims Ledger

This ledger fixes the evidence, wording, and data boundaries for the 3 September 2026 presentation.

**Contents**: 1 Release identity · 2 Permitted claims · 3 Data boundaries · 4 Evaluation proof · 5 Excluded claims · 6 Sources · 7 Change history

## 1 Release identity

| Field | Verified value |
|---|---|
| Source commit | `bf7fd4d56f95220677f86358d0004905b497872a` |
| Public repository | `https://github.com/sergiobuilds/bidpilot` |
| Public app | `https://bidpilot-demo-tbauoylpra-uc.a.run.app` |
| Real-tender route | `/?tender=R26BK01680611-000` |
| Verified replay route | `/?walkthrough=1` |
| Historical run | `cortex-final-20260802-a` |
| Cortex session | `7d9dc75b-3fd9-4ab0-9d8f-4d0c0e2c18f1` |
| Public app capture | 3 September 2026 KST |

## 2 Permitted claims

| Claim | Evidence | Presentation wording |
|---|---|---|
| Product definition | README, MASTER-MAP, Top 16 plan | “BidPilot is a pursuit decision and execution workspace for B2G proposal teams.” |
| End-to-end chain | Public replay and persisted run | “Tender and supplier evidence become a decision, weighted strategy, proposal, review, owned work, and same-run readback.” |
| Runtime | Repository and runbook | Python, Streamlit, Snowflake, Snowpark, Cortex Code CLI. |
| Completed replay | Runbook and public replay | One decision, three strategies with one selected, four weighted plans, eight proposal sections, and twelve tasks. |
| Least privilege | Role SQL, runbook, README | Runner writes execution artifacts. Reader reloads complete runs. |
| Fail closed | Store contract and public wording | Authenticated reader errors do not silently switch to fixtures. |
| Founder fit | Sergio Lee biography supplied for the finale | Washington State CPA, government grants and public-program accounting specialist, three-time AI hackathon winner. |
| Finalist status | Event contract supplied for the finale | Global Top 16 finalist. No total applicant count is stated. |

## 3 Data boundaries

| Surface | Data status | Required wording |
|---|---|---|
| Suwon G2B notice `R26BK01680611-000` | Real public notice used as a source case | “Real public tender source. It is not represented as a currently open opportunity.” |
| Supplier profile on the real-tender screen | Synthetic demo data | “Synthetic demo supplier profile.” |
| Real-tender result | `REVIEW` with four evidence gaps | “REVIEW is the trusted answer when supplier evidence is insufficient.” |
| Verified replay | Separate synthetic historical fixture | “Separate historical replay used to prove the complete product and Snowflake execution.” |
| Verified replay result | `PURSUE` | Never describe it as the result for the Suwon notice. |
| Customer outcomes | No verified customer evidence | Do not claim customers, wins, revenue, time savings, or award results. |

## 4 Evaluation proof

| Official criterion | Weight | Direct proof in the presentation |
|---|---:|---|
| Real-World Relevance | 30% | Real public G2B notice, pre-writing pursuit decision, four evidence gaps, proposal-team buyer. |
| Technical Execution | 40% | Snowpark policy, runner and reader role separation, Cortex session and query provenance, same-run Snowflake replay, fail-closed reader. |
| Solution Completeness | 30% | Decision, selected Win Position, four weighted plans, eight sections, red-team result, twelve owned and review tasks, replayable run. |

## 5 Excluded claims

1. BidPilot is not described as a general RFP summarizer, chatbot, audit product, grant-settlement product, or automated legal submission tool.
2. The real G2B case is not described as the same execution as the historical verified replay.
3. Internal blind evaluations are not presented as official rankings or win probabilities.
4. Test counts are excluded because the finale deck does not rerun the complete suite at this commit.
5. Product changes outside `origin/main` and the public deployment are excluded.
6. Unverified market size, time-saving percentages, customer counts, revenue, and win-rate claims are excluded.

## 6 Sources

1. `git:refs/heads/main:docs/MASTER-MAP.md`, returned by the project authority router.
2. `PASSDOWN.md`, `docs/CHRONICLE.md`, `README.md`, and `snowflake/COCO_RUNBOOK.md` at the source commit.
3. `docs/SUBMISSION-PACKAGE_2026-08-02_v2.md`.
4. Public app captures in `assets/live/`, captured from the two finale URLs.
5. Public GitHub `refs/heads/main`, verified against the local `origin/main` SHA.
6. The 78-second Top 16 refinement video downloaded from the supplied public URL.

## 7 Change history

- 2026-09-03 v1: Fixed the finale evidence baseline, permitted wording, and data boundaries.
