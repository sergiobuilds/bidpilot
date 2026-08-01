# BidPilot

BidPilot is a B2G Pursuit Agent for the Snowflake CoCo CLI Hackathon 2026. It is designed to turn a tender into a Bid Room: evaluation logic, supplier operating memory, a selected win position, a strategy-led proposal draft, and owned pursuit work.

**Contents** — 1 Product direction · 2 Current prototype boundary · 3 Run locally · 4 Snowflake proof path · 5 Canonical project records · 6 Change history

## 1 Product direction

The target flow is public tender intake → supplier retrieval → pursuit brief → win position → proposal blueprint and draft → red-team → persisted Bid Room.

The canonical implementation contract is [Winning Strategy v2](docs/WINNING-STRATEGY_2026-08-01_v2.md).

## 2 Current prototype boundary

The repository currently contains an early local prototype:

1. Two synthetic RFP hard-gate scenarios.
2. One historical public G2B tender fixture.
3. A fixed Markdown proposal template.
4. Prepared Snowflake SQL and Snowpark sketches without an authenticated run.

It does not yet prove public tender intake, Snowflake retrieval or persistence, CoCo orchestration, strategy-driven proposal generation, or a persistent Bid Room.

## 3 Run locally

```bash
uv sync --group dev
uv run pytest -q
uv run streamlit run app.py
```

## 4 Snowflake proof path

| Layer | Evidence prepared in this repository | Current runtime state |
|---|---|---|
| Data model | `snowflake/sql/01_schema.sql` and `02_seed_fixture.sql` | Prepared, not yet loaded to an account |
| Decision policy | `snowflake/snowpark_decision.py` | Prepared, awaits authenticated Snowpark execution |
| CoCo CLI | CoCo CLI v1.1.52 and Snowflake CLI v3.23.0 installed locally | No Snowflake connection profile yet |
| User flow | Streamlit decision and in-session work-plan prototype | Local browser flow verified; no persistent store is active |

## 5 Canonical project records

- Project map: [docs/MASTER-MAP.md](docs/MASTER-MAP.md)
- Decision record: [docs/CHRONICLE.md](docs/CHRONICLE.md)
- Implementation contract: [docs/WINNING-STRATEGY_2026-08-01_v2.md](docs/WINNING-STRATEGY_2026-08-01_v2.md)
- Current handoff: [PASSDOWN.md](PASSDOWN.md)

## 6 Change history

- 2026-08-01 v3: Replaced the prototype-first repository description with the canonical Bid Room direction and separated unproven prototype behavior from the target implementation.
- 2026-08-01 v2: Added the synthetic decision prototype, Snowflake schema and Snowpark execution path, local verification commands, and current proof boundary.
- 2026-08-01 v1: Created the repository and canonical document entry points.
