---
doc_kind: project-material
status: canonical
version: 2026-08-01_v1
canonical_path: ~/projects/personal/products/bidpilot/docs/SUBMISSION-PACKAGE_2026-08-01_v1.md
---

# BidPilot 제출 패키지

해커톤 제출 설명, 90초 데모, 재현 명령을 한 곳에 둡니다.

**목차** — 1 Submission narrative · 2 90-second demonstration · 3 Reproduction · 4 Evidence boundary · 5 Change history

## 1 Submission narrative

### 1.1 Title

**BidPilot — Protect delivery capacity before the proposal starts.**

### 1.2 One-line description

BidPilot evaluates an RFP against mandatory qualifications, delivery capacity, and a margin floor, then converts a viable bid into owned proposal work.

### 1.3 Problem

Proposal teams often spend scarce time pursuing large contracts that cannot meet a mandatory requirement, fit the delivery calendar, or clear the commercial floor. A late rejection wastes proposal effort and leaves the next viable opportunity unattended.

### 1.4 Solution

BidPilot makes the participation decision inspectable. Every hard gate is shown with its policy, observed value, and pass or fail state. A failed gate produces NO-BID and preserves capacity. A viable bid produces an internal proposal plan with owner, due date, workstream, and expected outcome.

### 1.5 Technical execution

| Component | Implementation | Judge-visible purpose |
|---|---|---|
| Decision policy | Python deterministic engine | Reproducible qualification, capacity, and margin gates |
| Application | Streamlit decision-to-action workbench | RFP selection, decision trace, and work-plan creation |
| Data model | Snowflake SQL DDL and synthetic seed fixture | RFP, capabilities, capacity, decision, and task records |
| Cloud execution path | Snowpark decision script | Runs the same hard-gate logic against Snowflake tables |
| Developer workflow | CoCo CLI and Snowflake CLI setup | Prepared local execution route for an authenticated account |

## 2 90-second demonstration

### 2.1 Opening: RFP-ORBIT

1. Open BidPilot with `RFP-ORBIT` selected.
2. State that contract value alone does not decide whether to bid.
3. Point to the NO-BID decision and the three failed hard gates.

### 2.2 Evidence: policy trace

1. Read the capability failure: the required public-sector clearance is absent.
2. Read the capacity failure: the team is 70 hours short.
3. Read the margin failure: expected margin is below the 22% policy floor.
4. Point out that deadline and incumbent risks remain visible but do not obscure the hard-gate result.

### 2.3 Action: RFP-NORTHSTAR

1. Select `RFP-NORTHSTAR` in the opportunity queue.
2. Show that all three hard gates pass and the recommendation switches to BID.
3. Select **Create internal proposal work plan**.
4. Show the four owned tasks, their outcomes, owners, and deadlines.

### 2.4 Closing

BidPilot does not automate an external proposal submission. It makes the decision accountable, prevents wasteful pursuit, and turns an approved opportunity into bounded internal work.

## 3 Reproduction

### 3.1 Local demo

```bash
uv sync --group dev
uv run pytest -q
uv run streamlit run app.py
```

### 3.2 Expected checks

| Check | Expected result |
|---|---|
| `RFP-ORBIT` | NO-BID with three failed hard gates |
| `RFP-NORTHSTAR` | BID with four proposal tasks after the button is selected |
| Test suite | Four passing policy and import tests |

### 3.3 Snowflake execution route

1. Create an authenticated Snowflake connection profile.
2. Run `snowflake/sql/01_schema.sql` and `snowflake/sql/02_seed_fixture.sql`.
3. Execute `snowflake/snowpark_decision.py` from an authenticated Snowpark environment.
4. Record the resulting `BID_DECISIONS` table output and CoCo CLI session for the final submission.

## 4 Evidence boundary

The local application uses synthetic RFP and company fixtures. The repository contains Snowflake DDL, seed data, and a Snowpark execution path for the same policy. No live Snowflake account, customer record, persistent task store, or CoCo execution trace is claimed in the current build.

## 5 Change history

- 2026-08-01 v1: Created the English submission narrative, 90-second demonstration, local reproduction, and evidence boundary.
