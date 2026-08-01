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
| 구현 | authenticated Opportunity Graph, Snowpark 2×2, Cortex complete run, score-map Bid Room 구현 | 이 문서의 Work Tree |
| 제출 | finalizing | v2 제출 패키지에 실제 run과 90초 영문 스크립트를 동결했습니다. |

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
| 3 | L3 | root | done | Snowflake Opportunity Graph 구축 | authenticated schema, fixture, 역할별 재조회 | 공고·회사·run 버전 관계를 표현하지 못함 | policy와 retrieval 구현 | schema와 fixture를 적재하고 reader/runner 최소권한 역할로 재조회했습니다. |
| 4 | L4 | root | done | pursuit policy와 Win Position Engine 구현 | policy vectors, 2×2 전략 변화 | 고정 사례나 고정 전략이 나옴 | proposal blueprint 구현 | Python policy와 strategy contract를 local test로 확인했습니다. |
| 5 | L5 | root | done | 전략 주도 Proposal Builder 구현 | 평가항목별 section, profile별 출력 변화, NO-GO 차단 | 고정 템플릿 또는 NO-GO 생성 | CoCo orchestration | selected Win Position과 Blueprint를 연결한 local generator를 구현했습니다. |
| 6 | L6 | root | done | CoCo run과 persistent Bid Room 구현 | complete run의 trace, sections, tasks 재조회 | 브라우저 state에만 남음 | evaluation과 submission | Cortex Code가 동일 run ID로 strategy, plans, 8 sections, 11 tasks와 provenance를 저장했습니다. |
| 7 | L7 | root | done | 실제 run 검증 | input validation, 2×2 parity, complete replay, 33 tests | 같은 run을 재현하지 못함 | 제출물 제작 | reader 역할의 authenticated AppTest와 proposal adversarial QA를 통과했습니다. |
| 8 | L8 | root | in_progress | 제출물 제작과 제출 | 실제 run 기반 영어 자료, 영상, 제출 확인 | 제출 링크가 심사자에게 열리지 않음 | 완료 | 영문 제출문과 90초 스크립트는 완료했고 영상과 외부 최종 제출만 남았습니다. |

## 5 Open / Unconfirmed

1. Hack2Skill 제출 화면에서 요구하는 파일 형식과 업로드 필드
2. 대회 사이트의 Global 표기와 India-only 본문 표기 중 실제 참가 자격
3. 비공개 GitHub 저장소에 부여할 공식 심사 계정

## 6 Canonical Documents

| 문서 | 역할 | 비고 |
|---|---|---|
| [MASTER-MAP.md](MASTER-MAP.md) | project-map | 목적, 범위, Work Tree, 상태의 유일한 정본 |
| [CHRONICLE.md](CHRONICLE.md) | project-decision | append-only 결정 기록 |
| [WINNING-STRATEGY_2026-08-01_v2.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/WINNING-STRATEGY_2026-08-01_v2.md) | project-material | 현재 제품 계약, Snowflake necessity, run trace, demo, implementation gates |
| [WINNING-STRATEGY_2026-08-01_v1.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/WINNING-STRATEGY_2026-08-01_v1.md) | project-material | deprecated 초기 전략안 |
| [B2G-QUALIFICATION-INTEGRATION_2026-08-01_v1.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/B2G-QUALIFICATION-INTEGRATION_2026-08-01_v1.md) | project-material | B2G qualification layer와 Proposal Start Packet 경계 |
| [SUBMISSION-PACKAGE_2026-08-02_v2.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/SUBMISSION-PACKAGE_2026-08-02_v2.md) | project-material | authenticated 영어 제출문, 90초 영상 계약, 데이터·라이선스 경계 |
| [SUBMISSION-PACKAGE_2026-08-01_v1.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/SUBMISSION-PACKAGE_2026-08-01_v1.md) | project-material | deprecated hard-gate 초기 제출안 |
| [../PASSDOWN.md](../PASSDOWN.md) | 인계 | 현재 복귀 지점과 금지사항 |
| [../README.md](../README.md) | 소개 | 저장소 진입점 |

## 7 Status

- 마지막 확인 신호: 2026-08-02 KST에 33 tests, authenticated reader AppTest, Snowpark 2×2, complete Cortex run을 확인했습니다.
- 진행상황: L1--L7 완료. L8은 영상, 심사자 저장소 접근, 외부 제출 확인이 남았습니다.
- 현재 주장 가능 범위: authenticated Snowflake Opportunity Graph, Snowpark policy parity, Cortex Code complete run, evidence-safe proposal, owned tasks, replayable Streamlit Bid Room이 있습니다.
- 외부 게이트: 비공개 GitHub 저장소의 공식 심사자 접근과 제출 폼 최종 버튼은 아직 확인하지 않았습니다.
- 다음 복귀 지점: commit/push 후 별도 권한으로 clone을 검증하고 90초 영상을 녹화합니다.

## 8 변경 이력

- 2026-08-01 v1: BidPilot을 해커톤 출품 프로젝트로 승격하고 Charter, Work Tree, 상태를 기록했습니다.
- 2026-08-01 v2: 로컬 프로토타입, 합성 데이터와 Snowflake 실행 경로의 실제 상태를 반영했습니다.
- 2026-08-01 v3: 판단 근거를 화면에 노출하는 workbench와 제출 패키지의 실제 상태를 반영했습니다.
- 2026-08-01 v4: BidPilot을 B2G qualification layer로 확장하고 실제 G2B 공고와 Proposal Start Packet 경계를 반영했습니다.
- 2026-08-01 v5: BidPilot을 Snowflake-native B2G Revenue Agent로 정본화하고 winning strategy와 rubric proof를 반영했습니다.
- 2026-08-01 v6: 독립 QA 결과를 반영해 BidPilot을 B2G Pursuit Agent의 Bid Room으로 재정의하고, 하드코드 공고·고정 writer·미실행 Snowflake 주장과 실제 구현 목표를 분리했습니다.
- 2026-08-02 v7: local tender intake, strategy-led generation, persistent Bid Room, account-ready Opportunity Graph를 반영하고 Snowflake 가입·대회 자격 외부 게이트를 기록했습니다.
- 2026-08-02 v8: authenticated Snowflake, Snowpark 2×2, evidence-safe Cortex complete run, blind-selected score-map UI, 33 tests와 최종 제출 패키지를 반영했습니다.
