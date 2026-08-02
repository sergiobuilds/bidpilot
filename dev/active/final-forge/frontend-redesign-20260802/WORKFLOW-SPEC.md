---
doc_kind: project-work
status: working
version: 2026-08-02_v2
canonical_path: self
---

# BidPilot 심사자 화면 워크플로 명세

Snowflake에 저장된 한 건의 Bid Room을 입찰 판단부터 제안서와 후속 작업까지 읽고 실행하는 화면 계약입니다.

**목차** — 1 사용자 목표 · 2 소비자 흐름 · 3 화면 구조 · 4 요소 계약 · 5 상태 계약 · 6 검증 게이트 · 7 검증 결과 · 8 변경 이력

## 1 사용자 목표

### 1.1 핵심 사용자

마감이 임박한 B2G 입찰 책임자는 한 공고에 조직 역량을 투입할지 빠르게 결정해야 합니다. 투입한다면 공식 배점에서 이길 전략을 선택하고 제안서를 작성한 뒤 남은 약점을 담당자에게 넘겨야 합니다.

### 1.2 심사자 이해 목표

심사자는 첫 화면에서 다음 문장을 재구성할 수 있어야 합니다.

> BidPilot decides whether to bid, shows how to win the official score, turns the selected strategy into a proposal, and assigns the remaining gaps under one Snowflake run.

### 1.3 소비자 범위

| 소비자 | 주요 질문 | 성공 결과 |
|---|---|---|
| 입찰 책임자 | 이 공고에 들어가야 하는가 | PURSUE, REVIEW, NO-GO와 결정 사유를 확인합니다. |
| 제안서 책임자 | 어느 배점에서 무엇으로 이길 것인가 | 평가항목, 배점, 공급사 자산, 계획 주장을 연결합니다. |
| 작성자 | 선택 전략이 실제 문안에 반영됐는가 | 평가항목별 초안을 편집하고 검토 상태를 확인합니다. |
| 경영자 | 남은 위험과 담당자는 누구인가 | red-team finding과 owned work를 확인합니다. |
| 해커톤 심사자 | 왜 Snowflake여야 하는가 | 동일 run ID의 decision, strategy, proposal, task, provenance를 확인합니다. |
| 자동 검증기 | 화면이 계약대로 렌더되는가 | landmark, heading, 상태 문구, overflow 수치를 파싱합니다. |

## 2 소비자 흐름

### 2.1 기본 흐름

| 단계 | 사용자 질문 | 화면의 답 | 다음 행동 |
|---:|---|---|---|
| 1 | Should we bid | 결정, 자격 누락, 가용시간 차이 | PURSUE일 때 score map으로 이동합니다. |
| 2 | Where do we win the score | 공식 배점, 증거 커버리지, 계획 주장 | 가장 중요한 평가항목과 빈 증거를 확인합니다. |
| 3 | What is our Win Position | 선택 전략, proof card, 약점과 완화책 | 선택 전략이 초안에 반영됐는지 확인합니다. |
| 4 | What do we submit | 평가항목별 proposal draft | 편집하고 red-team 결과를 재확인합니다. |
| 5 | What remains before submission | finding, closure action, owner, status | 담당 작업을 실행하거나 전달합니다. |
| 6 | Can this run be trusted and replayed | Snowflake state, Cortex session, query provenance | 전체 trace를 필요할 때만 엽니다. |

### 2.2 재방문 흐름

1. 사용자는 persisted run selector에서 다른 run을 선택합니다.
2. 화면은 선택된 run의 decision부터 provenance까지 같은 순서로 다시 그립니다.
3. 편집 중인 초안은 run ID별 session key로 분리합니다.
4. run 변경 뒤 제목과 모든 downstream 영역이 같은 run ID를 가리켜야 합니다.

### 2.3 제품과 개발 표면의 경계

1. Snowflake 연결이 있으면 공개 화면은 authenticated Bid Room으로 바로 진입합니다.
2. 공개 화면의 sidebar에 replay, intake, synthetic simulation 선택지를 노출하지 않습니다.
3. Snowflake 연결이 없는 로컬 환경에서만 기존 개발용 workflow selector를 유지합니다.
4. 합성 fixture와 로컬 replay는 제품의 첫 화면과 시각적 위계를 공유하지 않습니다.

## 3 화면 구조

### 3.1 첫 화면

| 영역 | 필수 정보 | 역할 |
|---|---|---|
| 제품 sidebar | BidPilot 이름, live Snowflake 상태, persisted run selector, 6단계 흐름 | 현재 위치와 전체 업무 흐름을 설명합니다. |
| opportunity header | 공고명, buyer objective, opportunity ID, supplier | 분석 대상을 확정합니다. |
| decision panel | PURSUE, REVIEW, NO-GO, 결정 사유 | 첫 번째 가치인 입찰 여부를 즉시 답합니다. |
| score opportunity panel | lead score target, covered points, open points | 두 번째 가치인 승리 경로를 바로 연결합니다. |
| selected strategy panel | Win Position 이름과 한 문장 | proposal이 어떤 전략에서 시작하는지 보여줍니다. |
| primary action | Open score map 또는 Open proposal | 사용자를 다음 핵심 단계로 이동시킵니다. |

### 3.2 본문 순서

1. Decision brief
2. Official score map
3. Selected Win Position
4. Proposal workspace
5. Red-team and owned work
6. Execution provenance

### 3.3 정보 위계

1. decision과 score map은 첫 viewport에서 함께 보여야 합니다.
2. Snowflake 실행 메타데이터는 확인 가능해야 하지만 제품 판단보다 앞에 나오지 않습니다.
3. technical table name은 보조 설명으로만 사용합니다.
4. provenance의 전체 JSON은 접힌 상태로 둡니다.

## 4 요소 계약

### 4.1 Sidebar

| 요소 | 작동 | 표현 | 연결 | WDS 계약 |
|---|---|---|---|---|
| 제품 이름 | 홈 의미를 제공합니다. | 고정 기록입니다. | 현재 Bid Room 전체에 연결됩니다. | typography token을 사용합니다. |
| connection status | 실제 연결 이름을 표시합니다. | settled status입니다. | authenticated store와 연결됩니다. | status badge를 사용합니다. |
| run selector | completed run을 전환합니다. | form control입니다. | 모든 downstream 섹션을 다시 로드합니다. | select field를 사용합니다. |
| workflow steps | anchor 이동을 제공합니다. | navigation입니다. | 여섯 본문 landmark와 연결됩니다. | list와 active indicator를 사용합니다. |
| data boundary | 데이터 범위를 설명합니다. | settled note입니다. | fixture disclosure와 연결됩니다. | subdued surface를 사용합니다. |

### 4.2 Main content

| 요소 | 작동 | 표현 | 연결 | WDS 계약 |
|---|---|---|---|---|
| opportunity header | 현재 run의 공고와 공급사를 표시합니다. | settled record입니다. | selected run과 연결됩니다. | page header를 사용합니다. |
| verdict badge | decision status를 표시합니다. | settled status입니다. | decision row와 연결됩니다. | semantic badge를 사용합니다. |
| decision facts | eligibility와 capacity를 표시합니다. | settled record입니다. | pursuit decision과 연결됩니다. | stat card를 사용합니다. |
| score summary | lead target과 evidence coverage를 표시합니다. | settled record입니다. | score map으로 이동합니다. | progress와 stat을 사용합니다. |
| score map | criterion별 weight, asset, claim, owner를 표시합니다. | settled table입니다. | proposal blueprint와 연결됩니다. | responsive table을 사용합니다. |
| strategy panel | 선택 전략과 proof card를 표시합니다. | selected record입니다. | proposal sections와 연결됩니다. | selected card를 사용합니다. |
| alternate strategies | 미선택 후보를 표시합니다. | comparison record입니다. | selected strategy와 구분됩니다. | subdued list를 사용합니다. |
| proposal editor | 초안을 편집합니다. | open form입니다. | red-team 검사와 download에 연결됩니다. | textarea를 사용합니다. |
| review status | 편집 초안의 통과 여부를 표시합니다. | live status입니다. | download enabled state와 연결됩니다. | alert를 사용합니다. |
| download button | 현재 편집본을 내려받습니다. | action입니다. | review pass일 때만 활성화됩니다. | primary button을 사용합니다. |
| red-team table | finding과 closure action을 표시합니다. | settled record입니다. | owned work에 연결됩니다. | responsive table을 사용합니다. |
| task table | task, owner, status를 표시합니다. | settled record입니다. | 동일 run ID에 연결됩니다. | responsive table과 status badge를 사용합니다. |
| provenance summary | provider, state, session, queries를 표시합니다. | settled record입니다. | full trace와 연결됩니다. | metadata list를 사용합니다. |
| full trace expander | 저장된 JSON을 엽니다. | disclosure control입니다. | AGENT_RUNS.trace와 연결됩니다. | accordion을 사용합니다. |

## 5 상태 계약

| 상태 | 화면 반응 | 복구 경로 |
|---|---|---|
| loading | run selector와 본문 대신 진행 상태를 표시합니다. | 로드 완료 후 같은 run을 표시합니다. |
| permission denied | 연결·role 오류를 표시합니다. | reader role과 connection 설정을 확인합니다. |
| no completed run | complete run이 없음을 표시합니다. | available run 목록을 진단용으로 보여줍니다. |
| incomplete run | 빠진 decision, strategy, section, task를 명시합니다. | 다른 completed run을 선택합니다. |
| missing field | 값을 만들지 않고 Not recorded를 표시합니다. | provenance에서 원본 run을 확인합니다. |
| proposal review fail | criterion별 finding을 표시합니다. | 초안을 수정하면 다시 검사합니다. |
| proposal review pass | download를 활성화합니다. | 현재 편집본을 내려받습니다. |
| narrow viewport | table을 labelled card로 전환합니다. | 수평 스크롤 없이 같은 정보를 읽습니다. |

## 6 검증 게이트

### 6.1 기능

1. persisted run 변경이 모든 섹션에 반영됩니다.
2. proposal 수정이 red-team 상태와 download payload에 반영됩니다.
3. missing field에 합성값을 넣지 않습니다.
4. authenticated failure가 fixture fallback으로 전환되지 않습니다.

### 6.2 접근성

1. keyboard-only 사용자가 run selector, anchor navigation, proposal editor, download, expander에 도달합니다.
2. focus-visible 표시가 모든 interactive element에 나타납니다.
3. status 의미는 색상과 텍스트를 함께 사용합니다.
4. score coverage는 accessible name을 가집니다.
5. heading 순서와 main, navigation landmark가 유지됩니다.

### 6.3 반응형

| viewport | 성공 조건 |
|---:|---|
| 1440 | decision, score opportunity, selected strategy가 첫 화면에서 하나의 흐름으로 보입니다. |
| 768 | sidebar와 본문이 겹치지 않고 핵심 작업을 순서대로 읽습니다. |
| 390 | horizontal overflow가 없고 table 정보가 labelled card로 바뀝니다. |

### 6.4 완료 판정

1. 전체 요소의 Works, Reads right, Connects, Conforms가 확인됩니다.
2. empty, error, permission, retry, edit-fail, edit-pass 상태가 확인됩니다.
3. 마지막 두 UX 감사에서 새로운 S1 또는 S2 finding이 없어야 합니다.
4. 최종 sign-off는 VivoBook의 실제 화면에서 Sergio가 판단합니다.

## 7 검증 결과

### 7.1 기능 검증

| 항목 | 결과 |
|---|---|
| 전체 테스트 | 59 passed |
| 실제 reader 연결 | complete run을 네 화면에서 재조회했습니다. |
| 화면 전환 | Opportunities, Bid Decision, Win Plan, Proposal Room 순서로 통과했습니다. |
| proposal 상태 | 편집, red-team, download enabled 상태를 유지했습니다. |

### 7.2 반응형 검증

| viewport | 네 화면 overflow | Opportunities action y | Proposal editor y |
|---:|---|---:|---:|
| 1440×900 | false | 624 | 505 |
| 768×900 | false | 667 | 873 |
| 390×844 | false | 773 | 890 |

최종 캡처와 기계 측정값은 `four-screen-final-verified-1440`, `four-screen-final-verified-768`, `four-screen-final-verified-390`에 있습니다.

## 8 변경 이력

- 2026-08-02 v1: authenticated Bid Room의 decision-to-proposal 흐름, 요소, 상태, 반응형 검증 계약을 작성했습니다.
- 2026-08-02 v2: WDS 네 화면 이식, 실제 reader 전환, 59 tests와 세 viewport의 overflow·action·editor 측정값을 반영했습니다.
