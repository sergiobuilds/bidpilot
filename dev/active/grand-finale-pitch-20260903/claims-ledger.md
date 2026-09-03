# BidPilot Grand Finale Claims Ledger

This ledger fixes the authoritative facts, global evidence, product boundaries, and excluded claims for the rebuilt presentation.

**Contents**: 1 Release identity · 2 Founder authority · 3 Global evidence · 4 Product evidence · 5 Data boundaries · 6 Evaluation proof · 7 Excluded claims · 8 Change history

## 1 Release identity

| Field | Verified value |
|---|---|
| Current `origin/main` | `f72a0565c6d804b26b77f00febbecbdd6908c5a2` |
| Public-app source | `c78c40c` · Cloud Run revision `bidpilot-demo-00012-vvg` |
| Public repository | `https://github.com/sergiobuilds/bidpilot` |
| Public application | `https://bidpilot-demo-tbauoylpra-uc.a.run.app` |
| Real-tender route | `/?tender=R26BK01680611-000` |
| Verified replay route | `/?walkthrough=1` |
| Historical run | `cortex-final-20260802-a` |
| Cortex session | `7d9dc75b-3fd9-4ab0-9d8f-4d0c0e2c18f1` |

## 2 Founder authority

| Claim | Authority | Permitted wording |
|---|---|---|
| Washington State CPA | Sergio-provided biography | `Washington State CPA` or `USCPA` |
| Government grants and public-program accounting | Sergio-provided biography | `Government grants and public-program accounting specialist` |
| Government-support application work | Sergio-provided professional experience | `Government-support application specialist` |
| Three AI hackathon wins | Sergio-provided biography | `Three-time AI hackathon winner` |
| Accounting-firm friction | Founder observation | Present as repeated professional observation, not measured market research. |

The founder experience explains the product discipline. It does not classify BidPilot as an audit, accounting-opinion, or grant-settlement product.

## 3 Global evidence

| Claim | Official source | Verified wording |
|---|---|---|
| OECD public procurement scale | `https://www.oecd.org/en/topics/public-procurement.html` | Public procurement expenditure increased to 12.9% of GDP across the OECD in 2021. |
| EU notice volume | `https://ted.europa.eu/en/about-ted` | TED publishes over 3,000 public procurement notices each weekday. |
| US federal opportunity structure | `https://sam.gov/content/opportunities` | SAM.gov contract opportunities are procurement notices from federal contracting offices and are publicly searchable. |
| Korea source structure | Current public G2B notice and BidPilot source record | The public notice provides official requirements, dates, and evaluation structure. |

The global claim is structural: public notice, eligibility rules, scored evaluation, private supplier evidence, and a fixed submission boundary recur across systems. The deck does not claim that legal rules are identical across countries.

## 4 Product evidence

| Claim | Verified evidence |
|---|---|
| Runtime | Python, Streamlit, Snowflake, Snowpark, Cortex Code CLI |
| Decision outcomes | `PURSUE`, `REVIEW`, `NO-GO` |
| Historical run | One decision, three strategies with one selected, four plans, eight sections, twelve tasks |
| Role boundary | `BIDPILOT_RUNNER` writes execution artifacts; `BIDPILOT_READER` reloads complete runs |
| Failure boundary | Authenticated reader failure does not silently switch to a fixture |
| Snowflake purpose | Governed join, policy execution, least privilege, durable same-run memory |
| CoCo CLI purpose | Query, compare, select, write, challenge, and persist with session and query provenance |

## 5 Data boundaries

| Evidence path | Data status | Required presentation boundary |
|---|---|---|
| Suwon G2B notice `R26BK01680611-000` | Real public source | Source and decision-boundary proof; not represented as a currently open opportunity |
| Supplier profile on the real-tender screen | Synthetic demo data | Labeled on the slide, in narration, and in Q&A |
| Real-tender result | `REVIEW`, four evidence gaps, no run | Reliability proof |
| Verified replay | Separate synthetic historical fixture | Full product and Snowflake execution proof |
| Verified replay result | `PURSUE` | Never attributed to the Suwon notice |

## 6 Evaluation proof

| Criterion | Weight | Direct evidence |
|---|---:|---|
| Real-World Relevance | 30% | Founder authority, accounting-firm and enterprise friction, global public-sector structure, real G2B source |
| Technical Execution | 40% | Snowpark policy, CoCo CLI execution, reader and runner roles, session and query provenance, same-run replay |
| Solution Completeness | 30% | Decision, weighted strategy, proposal, red-team, owned work, human approval boundary |

## 7 Excluded claims

1. No customer count, revenue, market share, time-saving percentage, bid win rate, or award result.
2. No official ranking or winning probability derived from internal blind evaluation.
3. No test count in the main presentation.
4. No claim that the real tender and historical replay are one execution.
5. No claim that BidPilot automatically submits a legal bid.
6. No claim that national procurement laws or procedures are identical.
7. No product screen from an unmerged or undeployed branch.

## 8 Change history

- 2026-09-03 v1: Added founder authority, accounting-firm friction, official OECD, TED, and SAM.gov evidence, Snowflake necessity, CoCo CLI necessity, and data-boundary controls.
- 2026-09-03 v2: Synchronized the source identity and screenshots to the deployed finale product after production readback.
- 2026-09-03 v3: Advanced the repository source identity after the reader-only agent surface and simplified dashboard reached `origin/main`; the public-app source remains separately identified.
