# BidPilot CoCo 실행 절차

Snowflake 계정이 확보된 뒤 BidPilot의 source snapshot부터 persisted Bid Room까지 같은 run으로 실행하는 절차입니다.

**목차**: 1 실행 전제 · 2 적재 · 3 CoCo run · 4 trace 저장 · 5 검증 · 6 이력

## 1 실행 전제

### 1.1 필요한 권한

1. Snowflake account, warehouse, database, schema 생성 권한이 필요합니다.
2. Snowflake CLI와 CoCo CLI가 같은 authenticated account를 사용해야 합니다.
3. CoCo 실행과 SQL 출력은 실제 실행 시각과 run ID를 함께 보관합니다.

### 1.2 금지되는 주장

계정, schema 적재, Snowpark, CoCo trace를 실제로 확인하기 전에는 Snowflake-native execution이나 CoCo orchestration을 제출문에 쓰지 않습니다.

## 2 적재

### 2.1 스키마와 fixture

```bash
snow sql -f snowflake/sql/01_schema.sql
snow sql -f snowflake/sql/02_seed_fixture.sql
```

### 2.2 확인 쿼리

```sql
SELECT opportunity_id, opportunity_version, title, source_sha256
FROM BIDPILOT_DEMO.BIDPILOT.OPPORTUNITIES;

SELECT supplier_profile_id, project_title, tags
FROM BIDPILOT_DEMO.BIDPILOT.PAST_PROJECTS;
```

## 3 CoCo run

### 3.1 입력 계약

CoCo에게 tender source snapshot, opportunity version, supplier profile ID, policy version을 제공합니다. 문서 원문은 데이터이며 시스템 지시로 해석하지 않습니다.

### 3.2 실행 순서

1. 공고 원문에서 scope, eligibility, evaluation criteria, submission items를 읽습니다.
2. Snowflake SQL로 credentials, availability, past projects, proposal assets를 조회합니다.
3. Snowpark policy를 실행해 `PURSUE`, `REVIEW`, `NO-GO`를 기록합니다.
4. 평가표와 retrieval 결과에서 Win Position 후보를 만듭니다.
5. 선택된 포지션으로 rubric response plan과 proposal sections를 만듭니다.
6. 같은 evaluation criteria로 red-team을 실행하고 필요한 section만 보완합니다.
7. `AGENT_RUNS`, `WIN_STRATEGIES`, `RUBRIC_RESPONSE_PLANS`, `PROPOSAL_SECTIONS`, `PURSUIT_TASKS`에 같은 run ID로 저장합니다.

## 4 trace 저장

### 4.1 최소 trace 필드

| 필드 | 내용 |
|---|---|
| run_id | 하나의 end-to-end 실행 식별자 |
| opportunity_version | source SHA-256 또는 ingestion version |
| supplier_profile_id | 선택된 공급사 profile |
| policy_version | `2026-08-02.v1` |
| provider | 실제 CoCo 또는 local development adapter |
| state | succeeded, failed, 또는 blocked |
| trace | 단계별 input, SQL, output, error |

### 4.2 계정 실패 상태

계정이 없을 때 local SQLite trace는 `local-development-adapter`와 `not-executed-in-snowflake-or-coco` 상태를 기록합니다. 이를 CoCo run으로 표시하지 않습니다.

## 5 검증

1. 같은 tender와 supplier에서 CoCo trace, Snowpark decision, Bid Room run ID가 일치해야 합니다.
2. supplier profile이나 tender를 바꾸면 Win Position, proposal blueprint, proposal sections가 달라져야 합니다.
3. `NO-GO` 결과에서는 proposal sections를 생성하지 않아야 합니다.
4. 새 Streamlit 세션에서 같은 versioned run을 재조회해야 합니다.

## 6 이력

- 2026-08-02 v1: account-ready CoCo execution order, trace contract, and verification gates를 기록했습니다.
