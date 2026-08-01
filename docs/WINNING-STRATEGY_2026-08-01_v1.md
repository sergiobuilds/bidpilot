---
doc_kind: project-material
status: canonical
version: 2026-08-01_v1
canonical_path: /home/elite/projects/personal/products/bidpilot/docs/WINNING-STRATEGY_2026-08-01_v1.md
---

# BidPilot Winning Strategy

BidPilot을 Snowflake CoCo CLI Hackathon의 B2G Revenue Agent로 출품하기 위한 제품, 시연, 기술 실행, 제출 기준을 고정합니다.

**목차** — 1 Winning thesis · 2 Product experience · 3 Snowflake necessity · 4 Rubric strategy · 5 Demo script · 6 Submission assets · 7 Execution gates · 8 Change history

## 1 Winning thesis

### 1.1 Product statement

**BidPilot turns a public tender into a winnable bid strategy and an editable proposal draft.**

### 1.2 Buyer outcome

B2G 사업자는 공고를 찾은 뒤 두 가지를 즉시 해결해야 합니다.

1. 이 공고를 실제로 잡을 수 있는지 판단합니다.
2. 잡을 수 있다면 기술평가에서 이길 제안서를 바로 시작합니다.

### 1.3 Product boundary

BidPilot은 단순 공고 요약기나 범용 문서 생성기가 아닙니다. 외부 공고와 내부 회사 운영 데이터를 결합해 pursuit decision, win strategy, proposal draft, proposal work plan을 한 흐름으로 만듭니다.

## 2 Product experience

### 2.1 Primary user journey

| 단계 | 사용자 행동 | BidPilot 결과 |
|---|---|---|
| Tender intake | 나라장터 공고번호 또는 RFP PDF를 넣음 | 공고 과업, 참가 조건, 평가 구조, 마감 추출 |
| Pursuit decision | 회사 프로필과 운영 데이터를 선택함 | `PURSUE`, `DO NOT PURSUE`, `RESOLVE GAP` |
| Win strategy | 결과를 확인함 | 발주처의 핵심 문제, 차별 포지션, 기술평가 우선순위 |
| Proposal drafting | Generate Bid를 선택함 | Executive Summary, Technical Approach, Delivery Plan, Team Positioning, Submission Checklist |
| Execution | 작업 계획을 확인함 | 제안 리드, 기술 리드, 가격 검토, 최종 리뷰의 소유 작업 |

### 2.2 Demo magic moment

실제 공고를 넣은 뒤 BidPilot이 다음 문장을 만듭니다.

> Do not sell database maintenance. Sell operational trust in public data services.

그 전략은 기술평가 항목, 180일 실행계획, 제안서 초안에 즉시 반영됩니다. 심사자가 보는 결과는 공고 요약이 아니라 입찰팀이 바로 이어서 편집할 수 있는 winning bid입니다.

### 2.3 Invisible reliability layer

공고 조건, 회사 프로필, 과거 프로젝트, 인력 가용성, 원가, 일정은 Snowflake 안에서 결합합니다. 이 계층은 제품의 신뢰성을 만들지만, 발표의 주인공은 pursuit decision과 winning proposal입니다.

## 3 Snowflake necessity

### 3.1 Why a generic chat product is insufficient

한 공고의 승부는 RFP 텍스트 하나로 결정되지 않습니다. 과거 수행, 유사 제안서, 현재 가용 인력, 단가, 자격, 프로젝트 일정이 함께 필요합니다. 이 자료는 문서와 표로 흩어져 있고, 매 입찰마다 다시 결합돼야 합니다.

### 3.2 Snowflake-native workflow

| Snowflake layer | BidPilot responsibility | Judge-visible proof |
|---|---|---|
| Structured tables | supplier profile, capability, capacity, cost, past project | qualified pursuit decision |
| Unstructured documents | tender PDF, RFP, prior proposal | requirement and evaluation understanding |
| CoCo agent | query, synthesis, win-strategy and draft orchestration | execution trace and generated bid workspace |
| Snowpark | deterministic commercial and capacity calculation | reproducible margin and availability result |
| Streamlit | decision and proposal workspace | complete user journey |

### 3.3 Technical claim boundary

The local prototype proves the policy and product flow. The final submission may claim Snowflake-native execution only after the same flow runs against an authenticated account and produces a CoCo trace.

## 4 Rubric strategy

| Rubric | Weight | Winning proof |
|---|---:|---|
| Real-world relevance | 30 | Public B2G tender, time-sensitive qualification, technical-evaluation strategy, proposal-team workflow |
| Technical execution | 40 | Public RFP document plus Snowflake operational data, CoCo multi-step run, Snowpark calculation, persisted decision and work plan |
| Solution completeness | 30 | Tender intake to pursuit decision to win strategy to editable proposal draft and owned work plan |

### 4.1 Relevance score thesis

The product targets an expensive B2G failure mode: teams spend proposal capacity on tenders they cannot win or cannot deliver. BidPilot converts that early ambiguity into a concrete win position and a usable proposal.

### 4.2 Technical score thesis

Snowflake is not used as passive storage. It is the operating memory that lets CoCo join public tender content with company delivery data, identify the bid angle, and trigger proposal work.

### 4.3 Completeness score thesis

The demo ends with an editable proposal and named internal actions. It does not stop at a recommendation or a chat response.

## 5 Demo script

### 5.1 Opening: 0–15 seconds

Open an actual public tender. State the buyer, scope, duration, technical evaluation emphasis, and the commercial opportunity.

### 5.2 Pursuit decision: 15–35 seconds

Select the company profile. Show `PURSUE` or `RESOLVE GAP` and state the operational implication in one sentence.

### 5.3 Win strategy: 35–55 seconds

Show the single strategic position. Connect it to the tender’s technical evaluation and the company’s relevant delivery strength.

### 5.4 Proposal generation: 55–85 seconds

Select **Generate Bid**. Show the executive summary, technical approach, and phased delivery plan already organized around the win strategy.

### 5.5 Action: 85–100 seconds

Show the proposal work plan and the persisted Snowflake decision record. End with: “From live tender to winning bid, in one workspace.”

## 6 Submission assets

| Asset | Required content | Acceptance check |
|---|---|---|
| Repository | runnable app, Snowflake SQL, Snowpark, CoCo instructions | clean clone instructions work |
| Video | 100-second end-to-end story | no setup screens or manual explanation gap |
| Screenshots | tender intake, win strategy, proposal draft, Snowflake trace | each screen supports one rubric claim |
| Submission text | problem, solution, Snowflake architecture, links | matches video and source reality |
| Public tender case | source URL and extracted facts | no invented tender facts |

## 7 Execution gates

### 7.1 Required before final submission

1. An authenticated Snowflake account runs the schema, public tender case, company fixture, Snowpark calculation, and persisted work plan.
2. CoCo performs or records the multi-step tender-to-proposal workflow.
3. The demo generates a proposal draft from the same public tender shown in the video.
4. The video and screenshots show one coherent run rather than disconnected feature screens.

### 7.2 Stop conditions

Do not claim technical execution until the Snowflake run exists. Do not present HWPX editing, source validation, or generic chat as the product’s headline moment.

## 8 Change history

- 2026-08-01 v1: Fixed BidPilot as a Snowflake-native B2G Revenue Agent and defined the winning thesis, rubric proof, demo, assets, and execution gates.
