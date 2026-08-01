# BidPilot

BidPilot is an RFP bid/no-bid decision prototype for the Snowflake CoCo CLI Hackathon 2026. The local demo connects a proposed engagement to delivery capability, capacity, economics, and deadlines, then creates an in-session proposal work plan.

**Contents** — 1 Demo flow · 2 Run locally · 3 Snowflake proof path · 4 Canonical project records · Change history

## 1 Demo flow

1. Select `RFP-ORBIT` to see a high-value opportunity rejected because mandatory qualification, capacity, and margin gates fail.
2. Select `RFP-NORTHSTAR` to see the next viable bid.
3. Create its proposal work plan and inspect the owned internal tasks.

All records are synthetic. The fixture includes no customer, audit, or confidential bid data.

## 2 Run locally

```bash
uv sync --group dev
uv run pytest -q
uv run streamlit run app.py
```

## 3 Snowflake proof path

| Layer | Evidence prepared in this repository | Current runtime state |
|---|---|---|
| Data model | `snowflake/sql/01_schema.sql` and `02_seed_fixture.sql` | Prepared, not yet loaded to an account |
| Decision policy | `snowflake/snowpark_decision.py` | Prepared, awaits authenticated Snowpark execution |
| CoCo CLI | CoCo CLI v1.1.52 and Snowflake CLI v3.23.0 installed locally | No Snowflake connection profile yet |
| User flow | Streamlit decision and in-session work-plan prototype | Local browser flow verified; no persistent store is active |

## 4 Canonical project records

- Project map: [docs/MASTER-MAP.md](docs/MASTER-MAP.md)
- Decision record: [docs/CHRONICLE.md](docs/CHRONICLE.md)
- Current handoff: [PASSDOWN.md](PASSDOWN.md)

## Change history

- 2026-08-01 v2: Added the synthetic decision prototype, Snowflake schema and Snowpark execution path, local verification commands, and current proof boundary.
- 2026-08-01 v1: Created the repository and canonical document entry points.
