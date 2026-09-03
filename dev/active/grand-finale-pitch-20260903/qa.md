# BidPilot Grand Finale Q&A

This table provides concise English answers for a three-minute judge Q&A.

**Contents**: 1 Core questions · 2 Delivery rule · 3 Change history

## 1 Core questions

| Question | 20–30 second answer |
|---|---|
| Why not use a general LLM? | A general LLM can summarize a tender and draft prose. BidPilot adds a deterministic pursuit gate, governed supplier evidence, official-weight control, owned evidence gaps, and a durable run record. The value is the accountable chain from eligibility and scoring to strategy, proposal content, review, and action. |
| Why is Snowflake necessary? | Snowflake joins versioned tender requirements with controlled supplier evidence, executes the Snowpark decision beside that data, and stores every downstream artifact under one run identity. It also separates runner and reader permissions. Without that shared state, the workflow becomes disconnected files and chat transcripts. |
| What exactly did Cortex Code CLI do? | In the recorded historical run, Cortex Code queried the opportunity and supplier evidence, compared three Win Positions, created four weighted response plans, wrote eight proposal sections, created twelve tasks, and persisted its session and Snowflake query references under the same run ID. |
| Is the tender data real? | The Suwon notice is a real public G2B tender source. We use it to prove source handling and the decision boundary, and we do not represent it as a currently open opportunity. Its `REVIEW` result is separate from the full historical replay. |
| Is the supplier data real? | No. The public demo labels the supplier profile as synthetic demo data. We do not use customer records or confidential company data, and we do not claim real customer outcomes, award results, or commercial performance. |
| Why does the real tender show REVIEW? | Four supplier evidence requirements remain unresolved. BidPilot therefore refuses to approve the pursuit, create a run, or draft a proposal. That is expected behavior. `REVIEW` shows the system preserves uncertainty instead of converting missing evidence into confident text. |
| Is this an automated legal bid submission tool? | No. BidPilot prepares and governs pursuit work. A human reviews the source, confirms supplier evidence, owns pricing, edits and approves the proposal, and performs the legal submission. The product creates accountable internal work and does not transmit a bid. |
| How do you prevent hallucinated credentials or project results? | Claims are bound to recorded supplier assets. Missing people, pricing, prior proposals, or outcome metrics stay visible as gaps and tasks. The proposal gate blocks unsupported states, and the red team checks score-bearing sections before the work is presented as ready. |
| What happens when evidence is missing? | The decision can remain `REVIEW`, proposal generation stays locked, and each missing item becomes owned remediation work. In a supported replay, any remaining proposal-level gap is carried into review and task ownership instead of being hidden in fluent prose. |
| What is already built versus future work? | Built today are the decision policy, weighted strategy, proposal and red-team flow, owned tasks, least-privilege Snowflake persistence, same-run replay, and public Streamlit experience. Production hardening would add tenant authentication, private data connectors, supervised run operations, and approved external work-system integrations. |
| Who is the buyer and what is the business model? | The first buyer is a small B2G proposal team that must decide quickly and coordinate evidence across authors. The commercial path is a team subscription for governed supplier memory, plus usage-based runs for intake, decision, strategy, drafting, and review. |
| How would this work with a company’s private operating data? | The same Opportunity Graph would connect the tender to approved credentials, people, availability, delivery history, and prior proposal assets inside the company’s governed Snowflake environment. The public demo uses synthetic supplier data, while a private deployment would apply tenant access and evidence approval controls. |
| How do reader and runner permissions differ? | The runner is the execution role. It reads approved inputs and writes run artifacts. The reader is the presentation role. It can reload only complete results needed by the app and cannot create a run. The app also verifies the active role and fails closed on mismatch or connection error. |
| Can judges reproduce or inspect the run? | Judges can inspect the public repository, the runbook, the public app, and the signed-out backup video. The runbook names the policy, role split, verified run ID, artifact counts, Cortex session, and completeness query. Account-level replay requires authorized Snowflake access. |
| What is the strongest measurable proof today? | The strongest proof is the complete historical run: one decision, three strategies, four weighted plans, eight proposal sections, twelve tasks, and Cortex plus Snowflake provenance under one replayable run ID. We do not substitute unverified customer or win-rate claims for that evidence. |

## 2 Delivery rule

Answer the first sentence directly, give one proof, and stop. If three minutes expire, prioritize the general LLM, Snowflake, data-boundary, and strongest-proof questions. The fifteen answers were rendered individually and measure between 23.475 and 23.513 seconds.

## 3 Change history

- 2026-09-03 v1: Prepared fifteen evidence-bound answers for the finale Q&A.
- 2026-09-03 v2: Recorded the 23.475–23.513 second TTS range.
