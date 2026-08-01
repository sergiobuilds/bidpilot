---
doc_kind: project-map
status: canonical
version: 2026-08-01_v1
canonical_path: /home/elite/projects/personal/products/bidpilot/docs/MASTER-MAP.md
authority_model: v2
---

# BidPilot 프로젝트 지도

Snowflake 안에서 B2G 공고를 winning bid strategy와 제안서 초안으로 전환하는 해커톤 프로젝트의 정본입니다.

**목차**: 1 Project Charter · 2 Current Map · 3 Confirmed Scope · 4 Work Tree · 5 Open / Unconfirmed · 6 Canonical Documents · 7 Status · 8 변경 이력

## 1 Project Charter

### 1.1 목적

BidPilot은 외부 B2G 공고의 평가 논리와 회사의 운영 메모리를 결합해 Bid Room을 만듭니다. 결과는 pursuit decision, win position, 평가항목별 proposal blueprint와 draft, red-team review, owned pursuit work입니다.

### 1.2 최종 산출물

1. Snowflake에 적재된 B2G 공고, 평가표, 회사 운영 메모리
2. CoCo CLI가 공고 해석, retrieval, win position, proposal drafting, red-team을 연결한 작업 증거
3. pursuit decision과 Win Position을 만드는 Python·Snowpark 흐름
4. 공고 입력부터 Bid Room, editable proposal draft와 작업 생성까지 실행되는 Streamlit 프로토타입
5. 영어 발표자료, 소스코드, 재현 절차, 시연 영상

### 1.3 성공 조건

| 공식 심사 항목 | 목표 증거 |
|---|---|
| 현실 적합성 30% | 실제 B2G 공고에서 pursuit decision과 기술평가별 승리 포지션을 만듭니다. |
| 기술 실행 40% | CoCo CLI, Snowflake, Python, Snowpark가 공고와 회사 운영 메모리를 결합하고 run trace를 남깁니다. |
| 솔루션 완성도 30% | 공고 입력, strategy 선택, proposal draft, red-team, 저장된 작업까지 한 번에 시연합니다. |

### 1.4 가드레일

1. 내부 마감은 2026년 8월 2일로 고정합니다.
2. 실제 고객 자료, 감사 자료, 비공개 업무자료를 사용하지 않습니다.
3. 합성 데이터 또는 공개 사용이 허용된 자료만 사용합니다.
4. 공고 검증과 데이터 결합은 내부 신뢰성 계층으로 두고 제품의 headline으로 삼지 않습니다.
5. CoCo CLI와 Snowflake가 핵심 가치 경로에서 실제로 작동해야 합니다.

### 1.5 명시적 비목표

1. 여러 산업을 동시에 지원하는 범용 업무 플랫폼
2. 회계감사 또는 보조금 정산 제품
3. RFP 전체 답변을 무검토로 자동 제출하는 기능
4. 2026년 8월 2일 이후에야 시연 가능한 대규모 구현

## 2 Current Map

| 축 | 현재 상태 | 정본 포인터 |
|---|---|---|
| 제품 | B2G Pursuit Agent와 Bid Room으로 확정 | [CHRONICLE.md](CHRONICLE.md) |
| 대회 | Snowflake CoCo CLI Hackathon 2026 | [CHRONICLE.md](CHRONICLE.md) |
| 문제 영역 | Intelligent Workflow Automation Agent | [CHRONICLE.md](CHRONICLE.md) |
| 저장소 | 비공개 GitHub 저장소 생성 | `sergiobuilds/bidpilot` |
| 구현 | local intake, strategy-led generation, persistent Bid Room 구현. Snowflake·CoCo 실제 run은 미실행 | 이 문서의 Work Tree |
| 제출 | in_progress | v2 제출 패키지는 local evidence와 account gate를 분리합니다. |

## 3 Confirmed Scope

### 3.1 사용자 확정 요구

1. Snowflake CoCo CLI Hackathon 출품 프로젝트로 승격합니다.
2. 공식 일정 충돌과 무관하게 2026년 8월 2일을 마감으로 간주합니다.
3. 프로젝트 정본과 인계 문서를 먼저 고정합니다.

### 3.2 제품 입력과 결과

| 구분 | 내용 |
|---|---|
| 입력 | RFP 문서, 회사 역량, 인력 가용성, 단가, 일정, 과거 수행정보 |
| 판단 | 자격·가용성·상업 조건, 기술평가 우선순위, pursuit decision, Win Position |
| 승인 후 결과 | 평가항목별 proposal blueprint, 섹션 초안, red-team 결과, 담당 작업 |
| 시연 표면 | Streamlit |
| 핵심 기반 | Snowflake, CoCo CLI, Python, Snowpark |

## 4 Work Tree

| 번호 | leaf ID | parent | 상태 | 한 가지 책임 | 완료 증거 | 실패 조건 | 다음 전이 | 기여 |
|---|---|---|---|---|---|---|---|---|
| 1 | L1 | root | done | 프로젝트 정본과 저장소 생성 | 이 지도, 결정 로그, 인계 문서, GitHub 저장소 | 정본 검사 또는 push 실패 | Snowflake 연결 확인 | 구현 범위를 고정합니다. |
| 2 | L2 | root | done | 공개 공고와 공급사 fixture를 신뢰 가능한 입력으로 고정 | source hash, input validation, 두 tender·두 supplier profile | 마감 공고를 현재 공고로 제시하거나 빈 데이터를 생성문으로 보충함 | Opportunity Graph 적재 | URL/PDF/text intake와 fixture contract를 local test로 확인했습니다. |
| 3 | L3 | root | in_progress | Snowflake Opportunity Graph 구축 | append-safe schema, 두 profile run, 재조회 | 공고·회사·run 버전 관계를 표현하지 못함 | policy와 retrieval 구현 | schema와 idempotent seed는 구현됐고 authenticated 적재를 대기합니다. |
| 4 | L4 | root | done | pursuit policy와 Win Position Engine 구현 | policy vectors, 2×2 전략 변화 | 고정 사례나 고정 전략이 나옴 | proposal blueprint 구현 | Python policy와 strategy contract를 local test로 확인했습니다. |
| 5 | L5 | root | done | 전략 주도 Proposal Builder 구현 | 평가항목별 section, profile별 출력 변화, NO-GO 차단 | 고정 템플릿 또는 NO-GO 생성 | CoCo orchestration | selected Win Position과 Blueprint를 연결한 local generator를 구현했습니다. |
| 6 | L6 | root | in_progress | CoCo run과 persistent Bid Room 구현 | 단계별 trace, sections, tasks 재조회 | 브라우저 state에만 남음 | evaluation과 submission | local SQLite Bid Room은 구현됐고 CoCo/Snowflake persistence는 미실행입니다. |
| 7 | L7 | root | in_progress | 실제 run 검증 | input validation, injection isolation, 2×2, replay | 같은 run을 재현하지 못함 | 제출물 제작 | local test는 intake·matrix·NO-GO·persistence·policy vectors를 다루며 authenticated run은 남았습니다. |
| 8 | L8 | root | in_progress | 제출물 제작과 제출 | 실제 run 기반 영어 자료, 영상, 제출 확인 | 2026-08-02 안에 제출 불가 | 완료 | 기존 제출 패키지는 초기 hard-gate 데모 기준입니다. |

## 5 Open / Unconfirmed

1. Snowflake 계정의 CoCo CLI 사용 권한과 지역별 모델 가용성
2. Hack2Skill 제출 화면에서 요구하는 파일 형식과 업로드 필드
3. 대회 사이트의 Global 표기와 India-only 본문 표기 중 실제 참가 자격

## 6 Canonical Documents

| 문서 | 역할 | 비고 |
|---|---|---|
| [MASTER-MAP.md](MASTER-MAP.md) | project-map | 목적, 범위, Work Tree, 상태의 유일한 정본 |
| [CHRONICLE.md](CHRONICLE.md) | project-decision | append-only 결정 기록 |
| [WINNING-STRATEGY_2026-08-01_v2.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/WINNING-STRATEGY_2026-08-01_v2.md) | project-material | 현재 제품 계약, Snowflake necessity, run trace, demo, implementation gates |
| [WINNING-STRATEGY_2026-08-01_v1.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/WINNING-STRATEGY_2026-08-01_v1.md) | project-material | deprecated 초기 전략안 |
| [B2G-QUALIFICATION-INTEGRATION_2026-08-01_v1.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/B2G-QUALIFICATION-INTEGRATION_2026-08-01_v1.md) | project-material | B2G qualification layer와 Proposal Start Packet 경계 |
| [SUBMISSION-PACKAGE_2026-08-02_v2.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/SUBMISSION-PACKAGE_2026-08-02_v2.md) | project-material | 현재 local demo, account evidence gate, submission boundary |
| [SUBMISSION-PACKAGE_2026-08-01_v1.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/SUBMISSION-PACKAGE_2026-08-01_v1.md) | project-material | deprecated hard-gate 초기 제출안 |
| [../PASSDOWN.md](../PASSDOWN.md) | 인계 | 현재 복귀 지점과 금지사항 |
| [../README.md](../README.md) | 소개 | 저장소 진입점 |

## 7 Status

- 마지막 확인 신호: 2026-08-02 KST에 21개 local tests, compile, Streamlit intake·Bid Room smoke test를 확인했습니다.
- 진행상황: L1, L2, L4, L5 완료. L3와 L6--L8은 authenticated Snowflake account와 CoCo trace가 필요합니다.
- 현재 주장 가능 범위: local intake, 두 tender·두 supplier fixture, Win Position, strategy-led draft, red-team, SQLite persistent Bid Room, append-safe Snowflake schema와 account-ready Snowpark policy가 있습니다. Snowflake 실행과 CoCo 세션 증거는 없습니다.
- 외부 게이트: Snowflake AI Data Cloud와 CoCo 가입의 계정 생성이 모두 일반 오류로 실패했습니다. 공식 대회 본문의 India-only 자격도 확인이 필요합니다.
- 다음 복귀 지점: 정상 Snowflake account에서 schema·seed·Snowpark·CoCo run을 실행하고 실제 `AGENT_RUNS` 증거를 기록합니다.

## 8 변경 이력

- 2026-08-01 v1: BidPilot을 해커톤 출품 프로젝트로 승격하고 Charter, Work Tree, 상태를 기록했습니다.
- 2026-08-01 v2: 로컬 프로토타입, 합성 데이터와 Snowflake 실행 경로의 실제 상태를 반영했습니다.
- 2026-08-01 v3: 판단 근거를 화면에 노출하는 workbench와 제출 패키지의 실제 상태를 반영했습니다.
- 2026-08-01 v4: BidPilot을 B2G qualification layer로 확장하고 실제 G2B 공고와 Proposal Start Packet 경계를 반영했습니다.
- 2026-08-01 v5: BidPilot을 Snowflake-native B2G Revenue Agent로 정본화하고 winning strategy와 rubric proof를 반영했습니다.
- 2026-08-01 v6: 독립 QA 결과를 반영해 BidPilot을 B2G Pursuit Agent의 Bid Room으로 재정의하고, 하드코드 공고·고정 writer·미실행 Snowflake 주장과 실제 구현 목표를 분리했습니다.
- 2026-08-02 v7: local tender intake, strategy-led generation, persistent Bid Room, account-ready Opportunity Graph를 반영하고 Snowflake 가입·대회 자격 외부 게이트를 기록했습니다.
