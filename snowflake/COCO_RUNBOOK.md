# BidPilot authenticated execution runbook

This runbook reproduces the Snowflake Opportunity Graph, Snowpark decision matrix, Cortex Code execution, and least-privilege Bid Room read path.

## Connections and roles

The verified environment uses three named Snowflake CLI connections:

| Connection | Purpose | Primary role |
|---|---|---|
| `bidpilot` | Schema, role, and cost-control administration only | `ACCOUNTADMIN` |
| `bidpilot-runner` | Snowpark lifecycle and Cortex artifact writes | `BIDPILOT_RUNNER` |
| `bidpilot-reader` | Streamlit authenticated reads | `BIDPILOT_READER` |

Apply grants with an administrator, then grant the reader and runner roles to the intended Snowflake user:

```bash
snow sql -c bidpilot -f snowflake/sql/03_roles.sql
```

The role script removes the former schema-wide grants. The reader can select
only the eight tables rendered by the app. The runner can only read source
tables, append derived artifacts, and update `AGENT_RUNS` lifecycle state.
It also attaches a five-credit monthly resource monitor, preserves the X-Small
warehouse's 60-second auto-suspend, and applies 300-second statement and
60-second queue timeouts.

## Load the Opportunity Graph

```bash
snow sql -c bidpilot -f snowflake/sql/01_schema.sql
snow sql -c bidpilot -f snowflake/sql/02_seed_fixture.sql
```

The fixture is synthetic and contains two opportunities and two supplier profiles. Do not replace missing people, past proposals, rates, or prices with generated facts.

## Execute the Snowpark matrix

```bash
.venv/bin/python snowflake/run_matrix.py \
  --connection bidpilot-runner \
  --run-prefix snowpark-matrix-$(date +%Y%m%d%H%M%S)
```

Each matrix cell creates an `AGENT_RUNS` row in `RUNNING`, requires exactly one
persisted decision, and moves to `COMPLETED` only after that check. An exception
moves the run to `FAILED`. Reusing a prefix is an idempotent retry: a valid
completed cell is not written again, while a failed or interrupted cell resumes
without duplicating its decision. The runner refuses to write unless
`CURRENT_ROLE()` is exactly `BIDPILOT_RUNNER` and tags the session with its run
prefix.

The verified policy version is `2026-08-02.v1`. Expected vectors are:

| Opportunity | Supplier | Expected status |
|---|---|---|
| Data quality | Northstar | `PURSUE` |
| Data quality | Atlas | `NO-GO` |
| Analytics | Northstar | `PURSUE` |
| Analytics | Atlas | `REVIEW` |

## Run Cortex Code

Start new Cortex Code executions from the repository with the runner connection:

```bash
cortex -c bidpilot-runner -w "$PWD" --bypass --effort high --session-name bidpilot-authenticated-run
```

The agent must query the opportunity, requirements, evaluation criteria, credentials, effective availability, past projects, people, and past proposals. It may write strategy and proposal artifacts only for a persisted `PURSUE` decision. Every write uses the same run ID.

The current verified runner-only run is `cortex-final-20260802-a`. Cortex Code
session evidence is `7d9dc75b-3fd9-4ab0-9d8f-4d0c0e2c18f1`. The persisted
trace records Snowflake CLI `snow-v3.23.0`. The run contains one decision,
three strategies with one selected, four
weighted plans, eight proposal sections, and twelve tasks. The historical
bootstrap run `bidpilot-v2-dq-northstar` remains replay evidence.

## Verify completeness

```sql
SELECT
  a.run_id,
  a.policy_version,
  a.provider,
  a.state,
  COUNT(DISTINCT d.run_id) AS decisions,
  COUNT(DISTINCT w.strategy_id) AS strategies,
  COUNT(DISTINCT p.criterion_name) AS plans,
  COUNT(DISTINCT s.section_id) AS sections,
  COUNT(DISTINCT t.task_id) AS tasks
FROM BIDPILOT_DEMO.BIDPILOT.AGENT_RUNS a
LEFT JOIN BIDPILOT_DEMO.BIDPILOT.PURSUIT_DECISIONS d USING (run_id)
LEFT JOIN BIDPILOT_DEMO.BIDPILOT.WIN_STRATEGIES w USING (run_id)
LEFT JOIN BIDPILOT_DEMO.BIDPILOT.RUBRIC_RESPONSE_PLANS p USING (run_id)
LEFT JOIN BIDPILOT_DEMO.BIDPILOT.PROPOSAL_SECTIONS s USING (run_id)
LEFT JOIN BIDPILOT_DEMO.BIDPILOT.PURSUIT_TASKS t USING (run_id)
WHERE a.run_id = 'cortex-final-20260802-a'
GROUP BY a.run_id, a.policy_version, a.provider, a.state;
```

Expected counts are `1, 3, 4, 8, 12`. The trace must contain the Cortex session,
CLI version, Snowpark decision query ID, Cortex write query IDs, and completion
audit query ID. Reader completeness also requires `COMPLETED`, current policy,
provider `CORTEX_CODE_CLI`, exactly one agent row, exactly one decision, exactly
one selected strategy, and non-empty plans, sections, and tasks.

## Run the product

```bash
export BIDPILOT_SNOWFLAKE_CONNECTION=bidpilot-reader
uv run streamlit run app.py
```

Authenticated mode lists only `COMPLETED` runs that have decision, strategy, sections, tasks, and the current policy version. A connection or query error remains visible and never triggers fixture fallback.

The reader refuses any connection whose `CURRENT_ROLE()` is not exactly
`BIDPILOT_READER`; pointing the app at the bootstrap profile therefore fails
closed.

## Change history

- 2026-08-02: Added runner-only lifecycle, exact decision cardinality, idempotent retry, narrowed grants, and warehouse cost boundaries.
- 2026-08-02: Applied the role and cost boundaries and completed a runner-only Cortex Code run that passes the reader contract.
