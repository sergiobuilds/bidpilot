---
name: bidpilot
description: "Evidence-aware B2G pursuit decisions over public tenders. Use when the user asks about a tender, bid, notice, RFP, pursue/no-go, eligibility, win position, proposal readiness, or a BidPilot run. Korean triggers: 공고, 입찰, 나라장터, 제안, 수주, 적격. Lists tenders, opens one notice, decides PURSUE / REVIEW / NO-GO from supplier evidence the user supplies, drafts a proposal only behind an open PURSUE gate, and replays a completed Bid Room run. Read-only: never starts a Cortex run or writes to Snowflake."
---

# BidPilot — pursuit decision skill

BidPilot turns a public tender and supplier evidence into a pursuit decision, a
score-weighted Win Position, and a replayable Bid Room run. This skill exposes
that capability to the agent through one script, `scripts/bidpilot.sh`, which
prints one JSON document per call.

## Hard rules (copied from the product; do not relax them)

1. A proposal or Win Position is discussed only when the decision is `PURSUE` and
   `proposal_gate` is `OPEN`. On `REVIEW` or `NO-GO`, report the gaps or the
   failing requirement and stop. Never draft proposal text on REVIEW or NO-GO;
   `draft-proposal` itself refuses with `proposal_locked` and lists the gaps.
   The draft's supplier is always a synthetic demo profile
   (`supplier-northstar` by default); repeat its `disclosure` line to the user
   and never present the draft as a real company's claim.
2. Never invent evidence. A requirement is `PASS` or `FAIL` only when the user
   states it; otherwise it stays `EVIDENCE REQUIRED`. Do not fill the evidence map
   from company names, prior chats, or assumptions. Ask the user per requirement.
3. Closed notices are historical. When `deadline_state` is `closed`, say so first;
   the decision is a qualification exercise on a past notice, not an open
   opportunity, and the proposal gate stays `LOCKED`. `draft-proposal` answers
   `notice_closed`; ask the user before re-running with `--historical`, and
   then keep the `HISTORICAL EXERCISE` banner in front of the draft.
4. This skill is reader-only. It never starts a Cortex run, never writes to
   Snowflake, and never calls the runner. Never start a Cortex run for an
   anonymous user; runs are only read back by `run_id`.
5. Do not summarise a tender from memory. Every fact about a notice comes from
   `get-tender` (`source_url`, `source_sha256`, `retrieved_at`) or `replay`.
   If the script returns `{"error": ...}`, report the error; do not substitute
   fixture or remembered data.

## Workflow

1. `list-tenders` — show `notice_number`, `title`, `issuer`, `deadline`,
   `deadline_state`, `evidence_level`. Prefer the `source-reviewed` notice for
   decisions; `source-found` rows are catalogued but not yet reviewed.
2. `get-tender NOTICE` — read `eligibility_requirements`, weights, delivery term,
   supplier boundary, provenance.
3. Ask the user which requirements they can evidence. Build the evidence map:
   `{"<requirement_index>": true|false}` (index as a string, or the exact
   requirement text). Leave unknown requirements out.
4. `decide NOTICE --evidence '<json>'` — report `decision`, each check with its
   status, `evidence_gaps`, `weights`, `proposal_gate`, `next_actions`.
   Without an evidence map the reviewed notice returns `REVIEW` with 4 gaps.
   On `REVIEW`, list every `EVIDENCE REQUIRED` requirement and ask the user
   which of them they can evidence. When they answer, run `decide` again with
   the fuller evidence map. Do not draft in between.
5. Only on `PURSUE` with `proposal_gate: OPEN`: run
   `draft-proposal NOTICE --evidence '<same json>'`. Present `selected_position`
   (title and summary), then the `sections` in order (heading, and for the
   score-bearing ones the `criterion` and its weight from `score_map`), then
   the `red_team` findings and the `tasks` with owners. Read out
   `assumptions` (planned hours are a stated constant, not a source fact) and
   the `disclosure`. `--position N` binds another Win Position;
   `--supplier ID` picks another synthetic profile. If the script returns
   `notice_closed`, ask the user whether a historical exercise is wanted before
   adding `--historical`.
6. To show how a persisted Bid Room run looks, replay a completed run
   (`list-runs`, then `replay RUN_ID`) — selected strategy, weighted sections,
   owned tasks, Cortex provenance. `list-runs`/`replay` need
   `BIDPILOT_SNOWFLAKE_CONNECTION` (reader) or `BIDPILOT_API_URL`; otherwise the
   script returns `snowflake_not_configured` and you report that instead of
   guessing.

## Running the script

```bash
scripts/bidpilot.sh list-tenders
scripts/bidpilot.sh get-tender R26BK01680611-000
scripts/bidpilot.sh decide R26BK01680611-000
scripts/bidpilot.sh decide R26BK01680611-000 --evidence '{"0": true, "1": true, "2": false}'
scripts/bidpilot.sh draft-proposal R26BK01680611-000 --evidence '{"0": true, "1": true, "2": true, "3": true}'
scripts/bidpilot.sh draft-proposal G2B-REPLAY-DATA-QUALITY --position 1
scripts/bidpilot.sh draft-proposal R26BK01680611-000 --evidence '{"0": true, "1": true, "2": true, "3": true}' --historical
scripts/bidpilot.sh list-runs
scripts/bidpilot.sh replay cortex-final-20260802-a
```

Backend: if `BIDPILOT_API_URL` is set (for example the hosted `bidpilot-api`
service) the script calls its REST endpoints; otherwise it runs
`uv run python -m bidpilot.agent_core` from the BidPilot checkout that contains
this skill (`BIDPILOT_REPO` overrides the location). Both print the same JSON.

## Worked examples

### Example 1 — "What tenders are in BidPilot right now?"

Run `list-tenders`. Answer with a table: notice number, title, deadline and
`deadline_state`, evidence level. Point out which row is `source-reviewed`
(decidable) and that `closed` rows are historical. Do not rank or recommend
until the user picks one.

Expected shape:

```json
[{"notice_number": "R26BK01680611-000", "title": "...", "issuer": "...",
  "deadline": "2026-09-03T16:00:00+09:00", "deadline_state": "open|closed",
  "evidence_level": "source-reviewed", "status": "REVIEW",
  "official_url": "https://...", "contract_value_krw": 0,
  "technical_weight": 0, "price_weight": 0}]
```

### Example 2 — "Should we pursue R26BK01680611-000?"

Run `get-tender R26BK01680611-000`, list the eligibility requirements, and ask
the user for evidence on each. If they give none, run `decide` without
`--evidence` and report `REVIEW` with `evidence_gaps: 4`, listing the four
`EVIDENCE REQUIRED` checks and `next_actions`. Do not write a proposal.

Expected shape:

```json
{"notice_number": "R26BK01680611-000", "decision": "REVIEW",
 "reason": "...", "checks": [{"requirement": "...", "status": "EVIDENCE REQUIRED"}],
 "evidence_gaps": 4, "weights": {"technical": 0, "price": 0},
 "proposal_gate": "LOCKED", "next_actions": ["..."],
 "provider": "LOCAL_PYTHON_POLICY", "persisted": false, "deadline_state": "open"}
```

### Example 3 — "We hold all four items as evidence; show the win plan."

Run `decide ... --evidence '{"0": true, "1": true, "2": true, "3": true}'`.
If `decision` is `PURSUE` and `proposal_gate` is `OPEN`, run `list-runs` then
`replay cortex-final-20260802-a` and explain the selected strategy, the weighted
sections (criterion → title → weight), the owned tasks, and the Cortex
provenance. If the notice is `closed`, `proposal_gate` is `LOCKED`: say the
decision is historical qualification only and stop at the checks.

Expected replay shape:

```json
{"run_id": "cortex-final-20260802-a", "decision": "PURSUE",
 "selected_strategy": "...", "strategy_count": 3, "plan_count": 4,
 "section_count": 8, "task_count": 12,
 "sections": [{"criterion": "...", "title": "...", "weight": 40}],
 "tasks": [{"title": "...", "owner": "..."}],
 "provenance": {"cortex_session_id": "...", "query_ids": ["..."]}}
```

### Example 4 — "We can evidence all four. Draft the proposal."

Run `decide R26BK01680611-000 --evidence '{"0": true, "1": true, "2": true, "3": true}'`.
Only if it returns `PURSUE` with `proposal_gate: OPEN`, run
`draft-proposal R26BK01680611-000 --evidence '{"0": true, "1": true, "2": true, "3": true}'`.
Present the selected Win Position, the sections (`Technical`, 90 points, and
`Price`, 10 points, are the score-bearing ones; the others frame the draft),
the `red_team` findings, the `tasks` with owners, the `assumptions`, and the
`disclosure`. If the user still lacks one item, `draft-proposal` returns
`proposal_locked` with `detail.gaps`: report the gap and stop. If the notice
has closed, it returns `notice_closed`: ask before re-running with
`--historical`, and lead with the `HISTORICAL EXERCISE` banner.

Expected shape:

```json
{"notice_number": "R26BK01680611-000", "decision": "PURSUE",
 "proposal_gate": "OPEN", "deadline_state": "open",
 "supplier": {"id": "supplier-northstar", "name": "...", "synthetic": true},
 "score_map": [{"name": "Technical", "weight": 90}, {"name": "Price", "weight": 10}],
 "win_positions": [{"title": "...", "summary": "..."}],
 "selected_position": {"index": 0, "title": "...", "summary": "..."},
 "sections": [{"criterion": "Technical", "heading": "Technical (90 points)", "markdown": "## ..."}],
 "markdown": "# ...", "red_team": ["..."], "tasks": [{"title": "...", "owner": "..."}],
 "gap_closure_plan": [], "assumptions": ["delivery_hours=800 is a planning constant, ..."],
 "provider": "LOCAL_PYTHON_POLICY", "persisted": false,
 "disclosure": "Synthetic demo supplier profile; nothing here is a real company claim."}
```

Locked shape (exit code 1 locally, HTTP 423 remotely):

```json
{"error": "proposal_locked", "detail": {"decision": "REVIEW", "proposal_gate": "LOCKED",
 "gaps": ["..."], "checks": [{"requirement": "...", "status": "EVIDENCE REQUIRED"}],
 "next_actions": ["Supply evidence for: ..."]}}
```

## Reporting style

Lead with the decision and the gate, then the checks, then next actions. Keep
provenance (source URL, hash, retrieval time, run id) at the end so it is
available without interrupting the pursuit answer.
