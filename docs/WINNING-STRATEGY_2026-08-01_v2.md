---
doc_kind: project-material
status: canonical
version: 2026-08-01_v2
canonical_path: /home/elite/projects/personal/products/bidpilot/docs/WINNING-STRATEGY_2026-08-01_v2.md
---

# BidPilot 우승 전략과 구현 기준

BidPilot을 Snowflake CoCo CLI Hackathon에서 실제 B2G 입찰팀의 의사결정과 제안서 작업을 끝까지 연결하는 제출물로 만드는 기준입니다.

**목차**: 1 결론 · 2 심사 기준의 현실 · 3 제품 계약 · 4 사용자 경험 · 5 Snowflake와 CoCo의 필수성 · 6 데이터와 실행 계약 · 7 제안서 생성 계약 · 8 시연 설계 · 9 구현 순서와 합격 기준 · 10 제출 기준 · 11 이력

## 1 결론

### 1.1 제출 한 문장

**BidPilot turns a tender into a Bid Room: it finds the evaluation logic, retrieves the supplier's winning operating memory, selects a win position, and builds a proposal around it.**

### 1.2 사용자에게 파는 결과

B2G 사업자는 공고를 읽은 뒤 며칠 안에 투입할 입찰 인력과 방향을 정해야 합니다. BidPilot의 결과물은 단순한 `BID/NO-BID` 답이 아닙니다. 입찰팀이 바로 시작할 수 있는 Pursuit Brief와 전략 주도 제안서 초안입니다.

| 사용자 질문 | BidPilot의 답 |
|---|---|
| 이 공고에 사람을 투입할 가치가 있는가 | `PURSUE`, `REVIEW`, `NO-GO`와 그 이유 |
| 기술평가에서 무엇으로 이길 수 있는가 | 한 문장의 Win Position과 평가항목별 공략 순서 |
| 그 말을 뒷받침할 회사의 무엇이 있는가 | 과거 수행, 자격, 가용 인력, 제안 자산의 연결 카드 |
| 오늘 무엇을 써야 하는가 | 평가항목별 제안서 구조, 초안, 담당 작업 |

### 1.3 제품의 중심 장면

심사자가 봐야 할 장면은 공고 PDF 요약도, 일반 대화창도 아닙니다. 기술평가 항목 하나가 회사의 과거 수행과 가용 팀에 연결되고, 그 연결이 선택된 Win Position과 제안서 한 섹션을 즉시 바꾸는 장면입니다.

## 2 심사 기준의 현실

### 2.1 현재 구현의 판정

현재 저장소에는 합성 replay fixture와 마감된 공개 공고 한 건을 분리한 local mode, authenticated Snowflake Opportunity Graph, Python–Snowpark 2×2 parity, runner-only Cortex Code 산출물, 같은 run ID로 재조회되는 공개 Bid Room이 있습니다. 새 verified run `cortex-final-20260802-a`는 세 전략 비교, 네 weighted plan, 여덟 proposal section, 열두 task와 execution provenance를 가집니다.

| 심사 축 | 현재 판정 | 1위권에 필요한 전이 |
|---|---|---|
| 현실 적합성 30 | timestamped replay와 증거 공백을 화면에 명시함 | 실제 입찰팀 검증과 열린 공고 증거가 추가로 필요함 |
| 기술 실행 40 | 최소권한 Snowflake, runner-only 2×2 Snowpark, Cortex query provenance와 complete replay를 확인함 | live demo에서 role, lifecycle, query provenance를 짧게 증명해야 함 |
| 완성도 30 | 공개 score-map Bid Room, 세 전략, proposal, adversarial review, owned tasks, 3–5분 영상과 PDF 덱이 구현됨 | signed-out 링크 검증과 포털 최종 제출이 필요함 |

### 2.2 버리는 주장

다음은 최종 제출물의 headline이나 시연 주인공으로 사용하지 않습니다.

1. 용량과 마진 hard gate만 보여주는 합성 BID/NO-BID 데모.
2. 사용자가 Yes/No를 직접 선택해야 하는 자격 판정.
3. 공고와 회사 데이터에 따라 바뀌지 않는 고정 제안서 템플릿.
4. 실행 증거 없이 쓰는 Snowflake-native 또는 CoCo Agent 주장.
5. Grant Proposal Engine의 HWPX 편집 기능.

### 2.3 남기는 자산

결정 정책, 공고 원문 추출 경험, 회사 자료를 구조화하는 방식, 제안서 품질 검토 흐름은 남깁니다. 다만 이들은 Win Position을 만들기 위한 내부 실행 기반이며, 제품의 전면 메시지는 아닙니다.

## 3 제품 계약

### 3.1 대상 사용자와 사용 순간

대상은 20명에서 300명 규모의 기술·서비스 공급사에서 공공 입찰을 맡는 제안 리드 또는 사업개발 책임자입니다. 사용 순간은 새 공고를 발견한 뒤, 48시간에서 72시간 안에 입찰팀의 시간을 걸지 결정해야 할 때입니다.

### 3.2 입력과 결과

| 구분 | 입력 또는 결과 | 필수 내용 |
|---|---|---|
| 공고 | G2B 공고 URL 또는 공고 PDF | 공고 식별자, 원문 버전, 마감, 과업, 자격, 평가표 |
| 공급사 | 선택된 회사 프로필 | 자격, 사람, 가용성, 과거 수행, 제안 자산, 가격 가정 |
| Pursuit Brief | 입찰 판단과 승리 논리 | buyer objective, score map, win position, 강점 3개, 약점과 보완 |
| Proposal Blueprint | 제안서 작성 지도 | 평가항목, 주장, 사용할 회사 자산, 섹션, 담당자, 완료 기준 |
| Bid Room | 실행 상태 | 결정, 전략, 섹션 초안, 리뷰, 작업, Agent run |

### 3.3 Pursuit Brief 출력 계약

`Pursuit Brief`는 모델의 자유 서술이 아니라 아래 필드를 갖는 저장 가능한 결과입니다.

| 필드 | 의미 | 화면에서의 역할 |
|---|---|---|
| buyer_objective | 발주처가 실제로 해결하려는 운영 문제 | 제안서 첫 문단의 문제 정의 |
| score_map | 평가항목, 배점, 우선순위 | 어디에 입찰 시간을 쓸지 결정 |
| pursuit_status | `PURSUE`, `REVIEW`, `NO-GO` | 팀 투입 여부 |
| win_positions | 서로 다른 2개 또는 3개의 승리 가설 | 사용자가 전략을 선택 |
| selected_position | 선택한 한 문장 포지션 | 제안서 전체의 중심 |
| proof_cards | 회사 운영 메모리에서 찾은 관련 항목 | 각 주장의 재료 |
| weakness_and_action | 약점과 해소 작업 | 무리한 자동 작성 방지 |
| proposal_blueprint | 항목별 주장·자산·섹션·담당자 | 작성과 검토의 계약 |

### 3.4 Win Position의 형식

Win Position은 추상적인 칭찬 문구가 아닙니다. `발주처의 평가 우선순위 + 공급사의 고유 자산 + 약속할 실행 결과`를 한 문장으로 결합합니다.

| 요소 | 예시 형식 |
|---|---|
| 평가 우선순위 | "데이터 정확도와 서비스 연속성" |
| 공급사 자산 | "유사 공공 데이터 운영 3건과 즉시 투입 가능한 전담팀" |
| 실행 결과 | "180일 안에 오류를 줄이고 OpenAPI 운영 신뢰도를 높이는 운영 전환" |

선택된 포지션은 평가표, 실행 접근법, 팀 소개, 첫 요약, red-team 검토 질문에서 같은 방식으로 소비되어야 합니다.

## 4 사용자 경험

### 4.1 공고 수집

사용자는 URL 또는 PDF를 넣고 공급사 프로필 하나를 고릅니다. 시스템은 원문과 추출본을 별도 버전으로 보관하고, 과업·자격·평가표·제출물을 화면에서 수정 가능한 구조로 제시합니다.

### 4.2 전략 선택

BidPilot은 단일 답을 강요하지 않습니다. 두세 개의 Win Position을 제시하고, 각 포지션마다 어떤 평가점수를 노리는지, 어떤 과거 수행을 쓰는지, 어떤 약점이 남는지를 보여줍니다. 사용자가 하나를 선택하면 그 선택이 Bid Room의 기준 버전이 됩니다.

### 4.3 제안서 작성

`Build proposal`은 통짜 문서를 바로 배출하는 버튼이 아닙니다. 먼저 Proposal Blueprint를 만들고, 그 지도에 따라 평가항목별 섹션을 생성합니다. 각 섹션은 `buyer need`, `claim`, `company asset`, `approach`, `outcome`, `owner`를 함께 보입니다.

### 4.4 Red-team과 실행

Red-team은 같은 평가표를 다시 읽어 점수 손실 가능성이 큰 섹션만 지적하고 재작성합니다. 통과한 결과에는 자격 확인, 인력 확정, 가격 검토, 제안서 편집 작업이 Bid Room에 저장됩니다.

## 5 Snowflake와 CoCo의 필수성

### 5.1 일반 GPT만으로 부족한 이유

일반 GPT는 공고를 요약하고 문장을 쓸 수 있습니다. 그러나 입찰의 승패는 공고 텍스트 밖에 있는 과거 수행, 자격, 인력 가용성, 진행 중인 프로젝트, 이전 제안 자산을 같은 기회 버전 안에서 찾아 결합하는 데 있습니다. 이 연결이 없으면 제안서는 어느 회사에도 적용되는 문장으로 수렴합니다.

### 5.2 Snowflake의 역할

Snowflake는 채팅의 뒤에 붙는 저장소가 아니라, 매 공고마다 공급사의 운영 메모리를 다시 조합하는 Opportunity Graph입니다. 공고 원문과 회사 운영 자료가 같은 opportunity version과 supplier profile 아래에서 조회·연결·저장되므로, 전략과 제안서가 어떤 입력으로 만들어졌는지 재현할 수 있습니다.

### 5.3 CoCo의 역할

CoCo는 다음 단계를 하나의 실행으로 연결합니다.

1. 공고 문서에서 과업, 자격, 평가표, 제출물을 구조화합니다.
2. Snowflake SQL로 관련 과거 수행, 자격, 사람, 가용성, 제안 자산을 찾습니다.
3. Snowpark 결과를 포함해 pursuit status와 여러 Win Position을 만듭니다.
4. 선택된 Win Position으로 Proposal Blueprint와 평가항목별 초안을 만듭니다.
5. 같은 평가표로 red-team을 실행하고 약한 섹션만 보완합니다.
6. run, 결과, 작업을 Snowflake에 기록합니다.

### 5.4 심사자가 볼 기술 증거

| 증거 | 보여줄 사실 | 합격 기준 |
|---|---|---|
| Snowflake query | 공고와 공급사 운영 메모리를 함께 조회함 | 실제 account에서 실행된 query 결과 |
| Snowpark policy | 자격·가용성·상업 조건을 같은 규칙으로 계산함 | Python과 Snowpark parity test |
| CoCo run | 추출부터 전략·초안·작업 생성까지 단계가 이어짐 | 입력, SQL, 출력, 실패가 남은 run trace |
| persisted Bid Room | 결과가 브라우저 상태에만 있지 않음 | decision, strategy, sections, tasks가 테이블에 저장됨 |

## 6 데이터와 실행 계약

### 6.1 최소 데이터 모델

| 영역 | 테이블 | 책임 |
|---|---|---|
| 공고 | `OPPORTUNITIES`, `OPPORTUNITY_DOCUMENTS`, `DOCUMENT_CHUNKS` | 공고 원문, 첨부, 버전, 추출 원문 위치 |
| 공고 해석 | `REQUIREMENTS`, `EVALUATION_CRITERIA`, `SUBMISSION_ITEMS` | 자격, 과업, 배점, 제출물 |
| 공급사 메모리 | `SUPPLIER_PROFILES`, `CREDENTIALS`, `PEOPLE`, `AVAILABILITY`, `PAST_PROJECTS`, `PAST_PROPOSALS`, `RATE_CARDS` | 회사가 실제로 가진 수행 가능 자산 |
| 판단과 전략 | `REQUIREMENT_MATCHES`, `PURSUIT_DECISIONS`, `WIN_STRATEGIES`, `RUBRIC_RESPONSE_PLAN` | 입찰 판단, 포지션, 평가항목별 작성 지도 |
| 실행 | `PROPOSAL_SECTIONS`, `PROPOSAL_CITATIONS`, `PURSUIT_TASKS`, `AGENT_RUNS` | 초안, 사용 입력, 작업, 재현 기록 |

### 6.2 식별과 버전 규칙

모든 판단과 생성 결과는 `tenant_id`, `supplier_profile_id`, `opportunity_id`, `opportunity_version`, `run_id`, `policy_version`을 가집니다. 같은 공고라도 첨부가 바뀌거나 공급사 프로필이 달라지면 이전 초안을 재사용하지 않고 새 run으로 만듭니다.

### 6.3 안전한 처리 규칙

공고 원문과 과거 제안서에는 지시문처럼 보이는 문장이 섞일 수 있습니다. 문서 내용은 데이터로만 취급하고, 시스템 명령이나 실행 지시로 사용하지 않습니다. 최대 파일 크기, 형식, 추출 실패, 필수 평가표 누락을 intake 단계에서 명시적으로 처리합니다.

### 6.4 실제 사례 규칙

데모에는 제출 시점에 열려 있는 공개 공고를 우선 사용합니다. 여의치 않으면 공고 원문 URL, 취득 시각, SHA-256, 마감 상태를 함께 보이는 timestamped replay로 명시합니다. 이미 마감된 공고를 현재 입찰 가능한 사례로 제시하지 않습니다.

## 7 제안서 생성 계약

### 7.1 섹션 입력

각 제안서 섹션은 최소한 하나의 평가항목과 하나의 선택된 Win Position에 연결됩니다. 섹션 작성기는 일반 템플릿이 아니라 아래 입력을 받아야 합니다.

| 입력 | 목적 |
|---|---|
| evaluation criterion and weight | 점수에 맞는 분량과 우선순위 |
| buyer objective | 발주처 언어로 문제를 정의 |
| selected win position | 모든 섹션의 메시지를 일관되게 유지 |
| company assets | 과거 수행, 자격, 인력, 가용성의 선택 재료 |
| delivery constraints | 일정, 팀, 범위, 제외 사항 |
| red-team findings | 약한 주장만 다시 쓰기 |

### 7.2 섹션 출력

섹션은 `why this matters`, `our claim`, `how we deliver`, `what the buyer gets`, `owner and next action` 구조를 가집니다. 생성문은 편집 가능하지만, 어떤 평가항목과 회사 자산에서 왔는지는 Bid Room에서 계속 보입니다.

### 7.3 변화 검증

최소 두 개 공고와 두 개 공급사 프로필의 2×2 실행에서 다음이 달라져야 합니다.

1. pursuit status 또는 weakness action.
2. 선택 가능한 Win Position.
3. 각 포지션에 연결된 회사 자산.
4. Proposal Blueprint의 평가항목별 우선순위.
5. 제안서의 summary와 최소 두 개 섹션.

문장 일부만 바뀌는 결과는 불합격입니다.

## 8 시연 설계

### 8.1 3–5분 시연 구조

| 시간 | 화면 | 한 가지 전달 사실 |
|---|---|---|
| 0:00–0:37 | 문제와 제품 질문 | 제안서 작성 전의 pursuit 손실을 정의함 |
| 0:37–1:09 | Tender intake | URL/PDF와 reviewed source boundary를 보여줌 |
| 1:09–2:13 | Pursuit verdict와 score map | 작성 권한과 공식 배점 우선순위를 연결함 |
| 2:13–3:04 | 세 Win Position과 proposal | 비교·선택된 전략이 실제 섹션을 통제함 |
| 3:04–3:44 | Adversarial review와 owned work | 다운로드 gate와 열두 task를 보여줌 |
| 3:44–4:38 | Snowflake architecture와 provenance | role, lifecycle, session, query, 비용 경계를 증명함 |

### 8.2 비교 장면

영상 또는 스크린샷 하나에는 같은 공고에 대해 공급사 프로필을 바꾼 결과를 짧게 보여줍니다. 목표는 모델이 공고를 요약하는 것이 아니라, 공급사마다 다른 전략을 찾는다는 것을 증명하는 것입니다.

### 8.3 금지되는 시연 편집

화면을 따로 녹화해 이어 붙여 하나의 run처럼 보이게 하지 않습니다. Snowflake 조회, CoCo trace, 전략, 제안서, 저장 결과는 같은 `run_id`를 공유해야 합니다.

## 9 구현 순서와 합격 기준

### 9.1 P0. 신뢰 가능한 입력과 공급사 fixture

| 작업 | 완료 정의 | 실패 시 조치 |
|---|---|---|
| 공개 공고 intake | 원문, 취득 시각, hash, 추출 평가표가 저장됨 | timestamped replay로 격하하고 표기를 고침 |
| 공급사 fixture | 최소 2개 프로필, 3개 과거 수행, 2개 자격, 가용 인력, 2개 제안 자산 | 빈 필드를 모델 서술로 보충하지 않음 |
| 입력 검증 | 형식·크기·필수 평가표·문서 지시문 격리 테스트 | 해당 입력을 run 시작 전에 거절 |

### 9.2 P1. Snowflake Opportunity Graph

기존 demo DDL을 append-safe 모델로 교체하고, 공고·공급사·결정·전략·섹션·작업·run을 관계로 저장합니다. `CREATE OR REPLACE`로 history를 지우는 초기화 스크립트는 개발 fixture에만 한정합니다.

**합격 기준**: Snowflake account에서 한 공고와 두 공급사 프로필을 조회하고, 두 개 이상의 `run_id`를 저장·재조회합니다.

### 9.3 P2. 정책 parity와 Win Position Engine

자격·가용성·상업 조건은 Snowpark와 Python이 같은 결과를 내야 합니다. 그 위에서 Win Position Engine은 `score_map + supplier assets + constraints`를 입력으로 여러 전략과 weakness action을 만듭니다.

**합격 기준**: parity test, 2×2 변화 검증, `NO-GO`에서 proposal generation 차단이 모두 통과합니다.

### 9.4 P3. 전략 주도 Proposal Builder

고정 f-string writer를 평가항목별 section generator로 교체합니다. Proposal Blueprint를 먼저 저장하고, 선택된 포지션과 연결된 회사 자산을 바꿀 때 summary와 적어도 두 섹션이 달라지는 회귀 테스트를 둡니다.

**합격 기준**: `PURSUE` run만 초안을 만들고, `REVIEW`는 보완 작업을, `NO-GO`는 차단 이유를 남깁니다.

### 9.5 P4. CoCo orchestration과 Bid Room

CoCo 실행은 intake, retrieval, strategy, proposal, red-team, task creation의 단계별 input·output·SQL·상태를 `AGENT_RUNS`에 기록합니다. Streamlit은 이 저장 결과를 읽는 Bid Room이 됩니다.

**합격 기준**: 화면 새로고침 뒤에도 같은 run과 작업을 복원하고, 실패 단계와 재시도 대상을 확인할 수 있습니다.

### 9.6 P5. 제출 패키지

영어 제출문, 100초 영상, 기술 증거 스크린샷, clean-clone 실행 절차는 실제 run 하나에만 근거해 만듭니다. 제출문은 로컬 prototype과 authenticated Snowflake run을 구분해 서술합니다.

## 10 제출 기준

### 10.1 출품 가능한 최소선

아래 여섯 가지가 같은 run에서 확인되어야 합니다.

1. 공개 공고의 원문과 평가표가 Snowflake에 적재됩니다.
2. 회사 운영 fixture를 Snowflake에서 조회합니다.
3. Snowpark가 입찰 판단의 기계적 조건을 계산합니다.
4. CoCo가 Win Position과 Proposal Blueprint를 만듭니다.
5. 전략에 따라 달라지는 제안서 섹션과 red-team 보완이 생성됩니다.
6. decision, sections, tasks, trace가 Bid Room에 저장됩니다.

### 10.2 1위권 방어선

| 공격 질문 | 제출물이 보여줄 답 |
|---|---|
| "GPT로도 되는 것 아닌가" | 공고만 바꾸거나 공급사 프로필만 바꿔도 retrieval, 전략, 제안서, 작업이 함께 달라지는 2×2 run |
| "Snowflake가 왜 필요한가" | 문서와 운영 메모리의 조인, Snowpark 계산, 실행 trace와 persistent Bid Room |
| "실제 사용 흐름인가" | 72시간 안에 사람이 내릴 pursuit 결정과 그 뒤의 제안서 작업을 하나의 화면과 run으로 제시 |
| "정말 끝까지 되는가" | intake부터 red-team, 저장된 작업까지 같은 run_id로 재현 |

### 10.3 현재 즉시 행동

지금의 첫 작업은 화면 문구나 템플릿 문장을 더 다듬는 일이 아닙니다. P0 fixture와 P1 Snowflake Opportunity Graph를 먼저 만들고, 그 위에서 P2부터 P4를 같은 run으로 연결해야 합니다. Snowflake 계정 또는 CoCo 권한이 막히면 계정 생성 실패 화면을 반복하지 않고, 정확한 권한 오류와 필요한 계정 상태만 기록해 제출 범위를 조정합니다.

## 11 이력

- 2026-08-02 v3: authenticated 실행 현실, historical bootstrap run 경계, runner-only lifecycle과 failure-safe 재실증 과제를 반영했습니다.
- 2026-08-02 v4: runner-only Cortex 완주, 공개 앱, 3–5분 데모, PDF 덱과 제출 직전 외부 게이트를 반영했습니다.
- 2026-08-01 v2: 독립 QA의 제품·구매자·심사·구조 지적을 반영해 고정 hard-gate 데모를 기준안에서 제외하고, Bid Room·Win Position·전략 주도 제안서·Snowflake run trace를 최종 구현 계약으로 고정했습니다.
