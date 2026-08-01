# BidPilot 인계

BidPilot 구현을 재개할 때 읽는 현재 작업 진입점입니다.

**목차** — 1 어디서 끊겼나 · 2 무엇부터 하고 무엇을 건드리지 마나 · 3 정본 링크 · 4 변경 이력

## 1 어디서 끊겼나

- 비공개 GitHub 저장소 `sergiobuilds/bidpilot`을 생성했습니다.
- 제품 방향은 B2G Pursuit Agent의 Bid Room으로 확정했습니다. 공고의 평가 논리와 회사 운영 메모리에서 Win Position을 고르고, 그 전략으로 제안서와 작업을 만듭니다.
- 프로젝트 지도와 결정 기록을 작성했습니다.
- CoCo CLI v1.1.52와 Snowflake CLI v3.23.0을 설치했습니다.
- Snowflake 연결 프로필은 아직 없으므로 SQL 적재, Snowpark 실행, CoCo 세션 증거는 미완료입니다.
- 합성 RFP fixture, 결정 엔진, inspectable policy trace, Streamlit workbench, 과거 공개 G2B fixture, 고정 proposal template, in-session 작업 계획이 있습니다.
- 로컬 정책 테스트와 린트는 초기 prototype 범위만 확인합니다.
- 기존 [제출 패키지](docs/SUBMISSION-PACKAGE_2026-08-01_v1.md)는 초기 hard-gate 방향으로, 최종 사용 전에 교체해야 합니다.
- 내부 제출 마감은 2026년 8월 2일입니다.

## 2 무엇부터 하고 무엇을 건드리지 마나

1. [Winning Strategy v2](docs/WINNING-STRATEGY_2026-08-01_v2.md)의 L2를 실행합니다. 공개 공고 원문·취득 시각·hash·평가표와 최소 두 공급사 fixture를 고정합니다.
2. Snowflake 연결 프로필을 만든 뒤 CoCo CLI에서 계정, 역할, 모델 접근을 실제 확인합니다.
3. Opportunity Graph schema를 구현해 공고, 공급사, strategy, sections, tasks, run을 관계로 저장합니다.
4. Snowpark parity와 Win Position Engine을 구현하고 2×2 변화 검증을 통과시킵니다.
5. 고정 writer를 평가항목별 strategy-led section generator로 교체하고 CoCo run trace와 persistent Bid Room을 연결합니다.
6. 실제 run 뒤에만 제출 패키지와 영상을 새로 만듭니다.
7. 실제 고객 자료, 감사 자료, 비공개 업무자료를 넣지 않습니다.
8. 데이터 검증, 출처 추적, 범용 대시보드 방향으로 바꾸지 않습니다.
9. 제품 범위나 Work Tree를 바꿀 때는 [CHRONICLE.md](docs/CHRONICLE.md)에 방향 결정을 먼저 기록합니다.

## 3 정본 링크

- 프로젝트 지도: [docs/MASTER-MAP.md](docs/MASTER-MAP.md)
- 결정 기록: [docs/CHRONICLE.md](docs/CHRONICLE.md)
- 저장소 소개: [README.md](README.md)
- 원격 저장소: https://github.com/sergiobuilds/bidpilot

## 4 변경 이력

- 2026-08-01 v3: 고도화된 workbench, 제출 패키지, 현재 검증 결과를 기록했습니다.
- 2026-08-01 v4: 실제 G2B 공고 qualification과 Proposal Start Packet 경계를 기록했습니다.
- 2026-08-01 v5: 독립 QA 후 Bid Room 전략과 실제 구현 순서를 정본으로 교체했습니다.
- 2026-08-01 v2: 로컬 구현과 검증 결과, Snowflake 연결 전 남은 하드 게이트를 기록했습니다.
- 2026-08-01 v1: 프로젝트 승격 직후 L2 복귀 지점과 금지사항을 기록했습니다.
