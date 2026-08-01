# BidPilot authenticated execution runbook

This runbook reproduces the Snowflake Opportunity Graph, Snowpark decision matrix, Cortex Code execution, and least-privilege Bid Room read path.

## Connections and roles

The verified environment uses three named Snowflake CLI connections:

| Connection | Purpose | Primary role |
|---|---|---|
| `bidpilot` | Bootstrap and account administration | `ACCOUNTADMIN` |
| `bidpilot-runner` | Snowpark and Cortex artifact writes | `BIDPILOT_RUNNER` |
| `bidpilot-reader` | Streamlit authenticated reads | `BIDPILOT_READER` |

Apply grants with an administrator, then grant the reader and runner roles to the intended Snowflake user:

```bash
snow sql -c bidpilot -f snowflake/sql/03_roles.sql
```

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

The verified policy version is `2026-08-02.v1`. Expected vectors are:

| Opportunity | Supplier | Expected status |
|---|---|---|
| Data quality | Northstar | `PURSUE` |
| Data quality | Atlas | `NO-GO` |
| Analytics | Northstar | `PURSUE` |
| Analytics | Atlas | `REVIEW` |

## Run Cortex Code

Start Cortex Code from the repository with the authenticated bootstrap connection:

```bash
cortex -c bidpilot -w "$PWD" --bypass --effort high --session-name bidpilot-authenticated-run
```

The agent must query the opportunity, requirements, evaluation criteria, credentials, effective availability, past projects, people, and past proposals. It may write strategy and proposal artifacts only for a persisted `PURSUE` decision. Every write uses the same run ID.

The verified run is `bidpilot-v2-dq-northstar` and the verified Cortex session is `2d68fa00-3379-4147-8433-87b6ccddcd75` on CLI version `1.1.52+200734.789ffffc1c9e`.

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
WHERE a.run_id = 'bidpilot-v2-dq-northstar'
GROUP BY a.run_id, a.policy_version, a.provider, a.state;
```

Expected counts are `1, 1, 4, 8, 11`. The trace must contain the Cortex session, CLI version, Snowpark decision query ID, Cortex write query IDs, completion audit query ID, and recovered preflight failures.

## Run the product

```bash
export BIDPILOT_SNOWFLAKE_CONNECTION=bidpilot-reader
uv run streamlit run app.py
```

Authenticated mode lists only `COMPLETED` runs that have decision, strategy, sections, tasks, and the current policy version. A connection or query error remains visible and never triggers fixture fallback.
