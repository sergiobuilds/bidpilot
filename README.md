# BidPilot

BidPilot is a B2G Pursuit Agent for the Snowflake CoCo CLI Hackathon 2026. It is designed to turn a tender into a Bid Room: evaluation logic, supplier operating memory, a selected win position, a strategy-led proposal draft, and owned pursuit work.

**Contents** — 1 Product direction · 2 Current prototype boundary · 3 Run locally · 4 Snowflake proof path · 5 Canonical project records · 6 Change history

## 1 Product direction

The target flow is public tender intake → supplier retrieval → pursuit brief → win position → proposal blueprint and draft → red-team → persisted Bid Room.

The canonical implementation contract is [Winning Strategy v2](docs/WINNING-STRATEGY_2026-08-01_v2.md).

## 2 Current prototype boundary

The repository currently contains a local, account-independent implementation:

1. URL, PDF, and text tender intake with source hash, bounded download, and instruction-like-content isolation.
2. Two tender replays and two supplier profiles with projects, credentials, people, availability, and proposal assets.
3. Deterministic `PURSUE`, `REVIEW`, and `NO-GO` decisions, selectable Win Positions, strategy-led proposals, and matrix tests.
4. A local SQLite Bid Room that persists versioned strategy, draft, red-team, task, and unexecuted-agent trace data.
5. Append-safe Snowflake Opportunity Graph SQL and a Snowpark policy path that are account-ready but unexecuted.

It does not yet prove authenticated Snowflake retrieval or persistence, CoCo orchestration, or a Snowflake-backed Bid Room.

## 3 Run locally

```bash
uv sync --group dev
uv run pytest -q
uv run streamlit run app.py
```

## 4 Snowflake proof path

| Layer | Evidence prepared in this repository | Current runtime state |
|---|---|---|
| Data model | `snowflake/sql/01_schema.sql` and `02_seed_fixture.sql` | Append-safe Opportunity Graph prepared, not yet loaded to an account |
| Decision policy | `snowflake/snowpark_decision.py` | Versioned policy path prepared, awaits authenticated Snowpark execution |
| CoCo CLI | Snowflake CLI v3.23.0 is installed; a `coco` executable is not present in this environment | No Snowflake connection profile or verified CoCo execution path |
| User flow | Streamlit tender intake and persistent local Bid Room | Local browser flow verified; SQLite is a development adapter only |

The account-run procedure is in [snowflake/COCO_RUNBOOK.md](snowflake/COCO_RUNBOOK.md).

## 5 Canonical project records

- Project map: [docs/MASTER-MAP.md](docs/MASTER-MAP.md)
- Decision record: [docs/CHRONICLE.md](docs/CHRONICLE.md)
- Implementation contract: [docs/WINNING-STRATEGY_2026-08-01_v2.md](docs/WINNING-STRATEGY_2026-08-01_v2.md)
- Current handoff: [PASSDOWN.md](PASSDOWN.md)

## 6 Change history

- 2026-08-02 v4: Recorded the implemented local intake, strategy-led proposal, persistent Bid Room, and append-safe account-ready Snowflake boundary.
- 2026-08-01 v3: Replaced the prototype-first repository description with the canonical Bid Room direction and separated unproven prototype behavior from the target implementation.
- 2026-08-01 v2: Added the synthetic decision prototype, Snowflake schema and Snowpark execution path, local verification commands, and current proof boundary.
- 2026-08-01 v1: Created the repository and canonical document entry points.
