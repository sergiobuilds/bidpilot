---
doc_kind: project-material
status: canonical
version: 2026-08-02_v2
canonical_path: /home/elite/projects/personal/products/bidpilot/docs/SUBMISSION-PACKAGE_2026-08-02_v2.md
---

# BidPilot 제출 패키지

BidPilot의 현재 구현과 Snowflake·CoCo 실증 게이트를 구분하는 제출 기준입니다.

**목차**: 1 제출 명제 · 2 현재 시연 · 3 계정 실증 후 시연 · 4 재현 · 5 주장 경계 · 6 이력

## 1 제출 명제

### 1.1 제목

**BidPilot — From tender evaluation to a strategy-led Bid Room.**

### 1.2 한 문장

BidPilot captures a tender, connects its evaluation matrix to supplier operating memory, selects a Win Position, builds score-bearing proposal sections, red-teams them, and persists the work as a Bid Room.

## 2 현재 시연

### 2.1 구현된 장면

| 순서 | 화면 | 확인할 결과 |
|---|---|---|
| 1 | Tender intake | URL/PDF/text source hash, 추출 구조, 지시문형 텍스트 격리 |
| 2 | Bid Room | tender와 supplier profile에 따라 달라지는 `PURSUE`, `REVIEW`, `NO-GO` |
| 3 | Win Position | 평가표, 과거 수행, 자격, 가용성을 연결한 선택 가능한 전략 |
| 4 | Proposal Blueprint | 평가항목별 claim, asset, owner |
| 5 | Build and Red-team | 선택 전략을 쓴 draft, section review, SQLite persisted run과 task |

### 2.2 재현 명령

```bash
uv sync --group dev
uv run pytest -q
uv run streamlit run app.py
```

## 3 계정 실증 후 시연

### 3.1 Snowflake 실행

1. `snowflake/sql/01_schema.sql`과 `02_seed_fixture.sql`을 authenticated account에 실행합니다.
2. 공고 source snapshot, supplier profile, strategy, sections, tasks, `AGENT_RUNS`를 조회합니다.
3. Snowpark policy를 실행해 Python policy와 같은 결과를 저장합니다.

### 3.2 CoCo 실행

CoCo trace는 intake, Snowflake retrieval, Win Position, proposal section, red-team, task creation의 단계별 입력·SQL·출력을 같은 `run_id`로 남겨야 합니다.

## 4 주장 경계

| 주장 | 현재 상태 |
|---|---|
| Tender intake, strategy-led proposal, red-team, persistent local Bid Room | 구현 및 local test 확인 |
| Snowflake Opportunity Graph SQL과 Snowpark policy | account-ready 코드만 존재 |
| Snowflake SQL·Snowpark 실행, CoCo trace, Snowflake persistence | 미실행 |
| Snowflake-native end-to-end submission | 실제 account run 전에는 주장 불가 |

## 5 대회 외부 게이트

Snowflake 가입은 AI Data Cloud와 CoCo 전용 경로에서 모두 계정 생성 일반 오류로 실패했습니다. 공식 대회 페이지는 CoCo CLI 기반 구현을 요구하며 Geographic Eligibility 본문에는 India만 적혀 있습니다. 계정 실증과 참가 자격은 공식 지원의 명시 답변이 있어야 해결됩니다.

## 6 이력

- 2026-08-02 v2: Bid Room local implementation, account-ready Snowflake path, CoCo evidence gate, 가입·자격 외부 리스크를 반영했습니다.
