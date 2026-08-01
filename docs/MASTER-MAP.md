---
doc_kind: project-map
status: canonical
version: 2026-08-01_v1
canonical_path: /home/elite/projects/personal/products/bidpilot/docs/MASTER-MAP.md
authority_model: v2
---

# BidPilot 프로젝트 지도

기업의 RFP 참여 판단과 제안 업무 착수를 Snowflake 안에서 처리하는 해커톤 프로젝트의 정본입니다.

**목차**: 1 Project Charter · 2 Current Map · 3 Confirmed Scope · 4 Work Tree · 5 Open / Unconfirmed · 6 Canonical Documents · 7 Status · 8 변경 이력

## 1 Project Charter

### 1.1 목적

BidPilot은 RFP 문서와 회사의 역량, 인력, 단가, 일정을 함께 분석해 입찰 참여 여부를 판단하고, 승인된 건의 제안 업무를 실제 작업 단위로 생성합니다.

### 1.2 최종 산출물

1. Snowflake에 적재된 RFP와 회사 운영 데이터
2. CoCo CLI를 사용한 데이터 및 애플리케이션 작업 증거
3. 참여 여부, 예상 마진, 수행 위험을 보여주는 Python 기반 판단 흐름
4. 입력부터 작업 생성까지 실행되는 Streamlit 프로토타입
5. 영어 발표자료, 소스코드, 재현 절차, 시연 영상

### 1.3 성공 조건

| 공식 심사 항목 | 목표 증거 |
|---|---|
| 현실 적합성 30% | 실제 입찰 담당자, 검토 시간, 저수익 수주와 마감 누락 비용을 명시합니다. |
| 기술 실행 40% | CoCo CLI, Snowflake, Python, Snowpark를 핵심 처리 경로에서 사용합니다. |
| 솔루션 완성도 30% | RFP 입력, 판단, 승인, 작업 생성까지 한 번에 시연합니다. |

### 1.4 가드레일

1. 내부 마감은 2026년 8월 2일로 고정합니다.
2. 실제 고객 자료, 감사 자료, 비공개 업무자료를 사용하지 않습니다.
3. 합성 데이터 또는 공개 사용이 허용된 자료만 사용합니다.
4. 데이터 검증, 출처 추적, 범용 대시보드를 제품 주제로 삼지 않습니다.
5. CoCo CLI와 Snowflake가 핵심 가치 경로에서 실제로 작동해야 합니다.

### 1.5 명시적 비목표

1. 여러 산업을 동시에 지원하는 범용 업무 플랫폼
2. 회계감사 또는 보조금 정산 제품
3. RFP 전체 답변을 무검토로 자동 제출하는 기능
4. 2026년 8월 2일 이후에야 시연 가능한 대규모 구현

## 2 Current Map

| 축 | 현재 상태 | 정본 포인터 |
|---|---|---|
| 제품 | RFP 참여 판단 및 제안 업무 실행 Agent로 확정 | [CHRONICLE.md](CHRONICLE.md) |
| 대회 | Snowflake CoCo CLI Hackathon 2026 | [CHRONICLE.md](CHRONICLE.md) |
| 문제 영역 | Intelligent Workflow Automation Agent | [CHRONICLE.md](CHRONICLE.md) |
| 저장소 | 비공개 GitHub 저장소 생성 | `sergiobuilds/bidpilot` |
| 구현 | 미착수 | 이 문서의 Work Tree |
| 제출 | 미착수 | 내부 마감 2026-08-02 |

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
| 2 | L2 | root | todo | Snowflake 계정과 CoCo CLI 실행 경로 확인 | 연결 확인, SQL 실행, 세션 기록 | 계정 또는 역할 접근 불가 | 데이터 모델 구축 | 필수 기술요건을 검증합니다. |
| 3 | L3 | root | todo | RFP와 회사 운영 데이터 모델 구축 | DDL, 합성 데이터, 적재 테스트 | 핵심 입력을 표현하지 못함 | 판단 엔진 구현 | 판단에 필요한 데이터를 제공합니다. |
| 4 | L4 | root | todo | 참여 판단 엔진 구현 | Python 테스트, Snowpark 실행, 고정 사례 결과 | 결정이 재현되지 않음 | 사용자 흐름 구현 | 핵심 판단 가치를 만듭니다. |
| 5 | L5 | root | todo | Streamlit 사용자 흐름 구현 | 입력부터 판단까지 라이브 시연 | 설명 없이 흐름 완주 불가 | 작업 생성 연동 | 제품 가치를 화면에 연결합니다. |
| 6 | L6 | root | todo | 승인 후 제안 업무 생성 | 실제 작업 생성과 Snowflake 상태 기록 | 외부 행동 또는 상태 변경 없음 | 평가와 실패복구 | 판단을 실행으로 전환합니다. |
| 7 | L7 | root | todo | 평가와 실패복구 검증 | 전체 테스트, 시간 비교, 데모 반복 성공 | 반복 시연 실패 | 제출물 제작 | 심사 증거를 확정합니다. |
| 8 | L8 | root | todo | 제출물 제작과 제출 | 영어 자료, 코드, 영상, 제출 확인 | 2026-08-02 안에 제출 불가 | 완료 | 대회 참가를 마감합니다. |

## 5 Open / Unconfirmed

1. Snowflake 계정의 CoCo CLI 사용 권한과 지역별 모델 가용성
2. Hack2Skill 제출 화면에서 요구하는 파일 형식과 업로드 필드
3. 승인 후 작업 생성 대상을 GitHub Issues로 할지 내부 작업 원장으로 할지 여부
4. 시연용 RFP의 공개 출처 또는 합성 문서 구성

## 6 Canonical Documents

| 문서 | 역할 | 비고 |
|---|---|---|
| [MASTER-MAP.md](MASTER-MAP.md) | project-map | 목적, 범위, Work Tree, 상태의 유일한 정본 |
| [CHRONICLE.md](CHRONICLE.md) | project-decision | append-only 결정 기록 |
| [../PASSDOWN.md](../PASSDOWN.md) | 인계 | 현재 복귀 지점과 금지사항 |
| [../README.md](../README.md) | 소개 | 저장소 진입점 |

## 7 Status

- 마지막 확인 신호: 2026-08-01 17:47 KST에 비공개 GitHub 저장소를 생성했습니다.
- 진행상황: L1 완료, 제품 구현 미착수
- 현재 주장 가능 범위: 제품 방향, 대회 문제 영역, 내부 마감, 정본 구조가 확정됐습니다.
- 다음 복귀 지점: L2에서 Snowflake 계정과 CoCo CLI의 실제 연결을 확인합니다.

## 8 변경 이력

- 2026-08-01 v1: BidPilot을 해커톤 출품 프로젝트로 승격하고 Charter, Work Tree, 상태를 기록했습니다.
