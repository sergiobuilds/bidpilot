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

BidPilot은 외부 B2G 공고와 회사의 자격, 역량, 인력, 단가, 일정, 과거 수행을 결합합니다. 결과는 pursuit decision, win strategy, editable proposal draft, proposal work plan입니다.

### 1.2 최종 산출물

1. Snowflake에 적재된 B2G 공고와 회사 운영 데이터
2. CoCo CLI가 공고와 운영 데이터를 결합한 작업 증거
3. pursuit decision과 win strategy를 만드는 Python·Snowpark 흐름
4. 공고 입력부터 editable proposal draft와 작업 생성까지 실행되는 Streamlit 프로토타입
5. 영어 발표자료, 소스코드, 재현 절차, 시연 영상

### 1.3 성공 조건

| 공식 심사 항목 | 목표 증거 |
|---|---|
| 현실 적합성 30% | 실제 B2G 공고에서 pursuit decision과 기술평가 승리 전략을 만듭니다. |
| 기술 실행 40% | CoCo CLI, Snowflake, Python, Snowpark가 공고와 회사 운영 데이터를 결합합니다. |
| 솔루션 완성도 30% | 공고 입력, pursuit decision, win strategy, proposal draft, 작업 생성까지 한 번에 시연합니다. |

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
| 제품 | Snowflake-native B2G Revenue Agent로 확정 | [CHRONICLE.md](CHRONICLE.md) |
| 대회 | Snowflake CoCo CLI Hackathon 2026 | [CHRONICLE.md](CHRONICLE.md) |
| 문제 영역 | Intelligent Workflow Automation Agent | [CHRONICLE.md](CHRONICLE.md) |
| 저장소 | 비공개 GitHub 저장소 생성 | `sergiobuilds/bidpilot` |
| 구현 | 로컬 프로토타입과 Snowflake 실행 경로 준비 완료. 계정 연결 대기 | 이 문서의 Work Tree |
| 제출 | in_progress | 영어 제출 설명, 90초 데모 대본, 재현 절차 준비 완료. 영상과 실제 Snowflake 실행 증거가 남았습니다. |

## 3 Confirmed Scope

### 3.1 사용자 확정 요구

1. Snowflake CoCo CLI Hackathon 출품 프로젝트로 승격합니다.
2. 공식 일정 충돌과 무관하게 2026년 8월 2일을 마감으로 간주합니다.
3. 프로젝트 정본과 인계 문서를 먼저 고정합니다.

### 3.2 제품 입력과 결과

| 구분 | 내용 |
|---|---|
| 입력 | RFP 문서, 회사 역량, 인력 가용성, 단가, 일정, 과거 수행정보 |
| 판단 | 필수조건 충족 여부, 예상 마진, 수행 위험, 참여 또는 포기 |
| 승인 후 결과 | 제안 목차, 담당 업무, 마감 일정, 작업 상태 |
| 시연 표면 | Streamlit |
| 핵심 기반 | Snowflake, CoCo CLI, Python, Snowpark |

## 4 Work Tree

| 번호 | leaf ID | parent | 상태 | 한 가지 책임 | 완료 증거 | 실패 조건 | 다음 전이 | 기여 |
|---|---|---|---|---|---|---|---|---|
| 1 | L1 | root | done | 프로젝트 정본과 저장소 생성 | 이 지도, 결정 로그, 인계 문서, GitHub 저장소 | 정본 검사 또는 push 실패 | Snowflake 연결 확인 | 구현 범위를 고정합니다. |
| 2 | L2 | root | in_progress | Snowflake 계정과 CoCo CLI 실행 경로 확인 | 연결 확인, SQL 실행, 세션 기록 | 계정 또는 역할 접근 불가 | 데이터 모델 구축 | CoCo CLI v1.1.52와 Snowflake CLI v3.23.0은 설치됐으나 연결 프로필이 없습니다. |
| 3 | L3 | root | in_progress | RFP와 회사 운영 데이터 모델 구축 | DDL, 합성 데이터, 적재 테스트 | 핵심 입력을 표현하지 못함 | 판단 엔진 구현 | 스키마와 합성 fixture는 준비됐고 계정 적재를 대기합니다. |
| 4 | L4 | root | in_progress | 참여 판단 엔진 구현 | Python 테스트, Snowpark 실행, 고정 사례 결과 | 결정이 재현되지 않음 | 사용자 흐름 구현 | 로컬 Python 판단은 두 고정 사례로 검증됐고 Snowpark 실행이 남았습니다. |
| 5 | L5 | root | in_progress | Streamlit 사용자 흐름 구현 | 입력부터 판단까지 라이브 시연 | 설명 없이 흐름 완주 불가 | 작업 생성 연동 | 로컬 브라우저에서 NO-BID 반전과 BID 흐름을 검증했습니다. |
| 6 | L6 | root | in_progress | 승인 후 제안 업무 생성 | 실제 작업 생성과 Snowflake 상태 기록 | 외부 행동 또는 상태 변경 없음 | 평가와 실패복구 | 로컬 in-session 작업 계획은 구현됐고 영속 Snowflake 상태 기록을 대기합니다. |
| 7 | L7 | root | in_progress | 평가와 실패복구 검증 | 전체 테스트, 시간 비교, 데모 반복 성공 | 반복 시연 실패 | 제출물 제작 | 로컬 정책 테스트 4건과 Streamlit health 확인을 마쳤습니다. |
| 8 | L8 | root | in_progress | 제출물 제작과 제출 | 영어 자료, 코드, 영상, 제출 확인 | 2026-08-02 안에 제출 불가 | 완료 | 제출 설명과 90초 대본은 준비됐고 영상과 제출 화면 확인이 남았습니다. |

## 5 Open / Unconfirmed

1. Snowflake 계정의 CoCo CLI 사용 권한과 지역별 모델 가용성
2. Hack2Skill 제출 화면에서 요구하는 파일 형식과 업로드 필드
3. 대회 사이트의 Global 표기와 India-only 본문 표기 중 실제 참가 자격

## 6 Canonical Documents

| 문서 | 역할 | 비고 |
|---|---|---|
| [MASTER-MAP.md](MASTER-MAP.md) | project-map | 목적, 범위, Work Tree, 상태의 유일한 정본 |
| [CHRONICLE.md](CHRONICLE.md) | project-decision | append-only 결정 기록 |
| [WINNING-STRATEGY_2026-08-01_v1.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/WINNING-STRATEGY_2026-08-01_v1.md) | project-material | winning thesis, Snowflake necessity, rubric proof, demo, submission gates |
| [B2G-QUALIFICATION-INTEGRATION_2026-08-01_v1.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/B2G-QUALIFICATION-INTEGRATION_2026-08-01_v1.md) | project-material | B2G qualification layer와 Proposal Start Packet 경계 |
| [SUBMISSION-PACKAGE_2026-08-01_v1.md](https://docs.svvys.com/projects/personal/products/bidpilot/docs/SUBMISSION-PACKAGE_2026-08-01_v1.md) | project-material | 영어 제출 설명, 90초 데모, 재현 절차 |
| [../PASSDOWN.md](../PASSDOWN.md) | 인계 | 현재 복귀 지점과 금지사항 |
| [../README.md](../README.md) | 소개 | 저장소 진입점 |

## 7 Status

- 마지막 확인 신호: 2026-08-01 KST에 로컬 정책 테스트 4건, 린트, Streamlit health endpoint를 확인했습니다.
- 진행상황: L1 완료. L2--L6은 계정 연결 전 로컬 구현까지 진행됐고, 공개 G2B 공고에서 pursuit decision과 editable proposal draft를 만드는 흐름을 추가 중입니다. L7--L8은 winning demo와 제출 패키지 제작 단계입니다.
- 현재 주장 가능 범위: 로컬 Streamlit, 합성 fixture, 실제 공개 G2B 공고 기반 qualification, proposal draft, in-session work-plan behavior, SQL과 Snowpark 실행 경로가 준비됐습니다. Snowflake 실행과 CoCo 세션 증거는 아직 없습니다.
- 다음 복귀 지점: Snowflake 연결 프로필을 만들고 `snow sql`로 스키마·fixture를 적재한 뒤 CoCo CLI 세션과 Snowpark 결과를 기록합니다.

## 8 변경 이력

- 2026-08-01 v1: BidPilot을 해커톤 출품 프로젝트로 승격하고 Charter, Work Tree, 상태를 기록했습니다.
- 2026-08-01 v2: 로컬 프로토타입, 합성 데이터와 Snowflake 실행 경로의 실제 상태를 반영했습니다.
- 2026-08-01 v3: 판단 근거를 화면에 노출하는 workbench와 제출 패키지의 실제 상태를 반영했습니다.
- 2026-08-01 v4: BidPilot을 B2G qualification layer로 확장하고 실제 G2B 공고와 Proposal Start Packet 경계를 반영했습니다.
- 2026-08-01 v5: BidPilot을 Snowflake-native B2G Revenue Agent로 정본화하고 winning strategy와 rubric proof를 반영했습니다.
