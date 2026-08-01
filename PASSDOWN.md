# BidPilot 인계

BidPilot 구현을 재개할 때 읽는 현재 작업 진입점입니다.

**목차** — 1 어디서 끊겼나 · 2 무엇부터 하고 무엇을 건드리지 마나 · 3 정본 링크 · 4 변경 이력

## 1 어디서 끊겼나

- 비공개 GitHub 저장소 `sergiobuilds/bidpilot`을 생성했습니다.
- RFP 참여 판단과 제안 업무 실행 Agent로 제품 방향을 확정했습니다.
- 프로젝트 지도와 결정 기록을 작성했습니다.
- CoCo CLI v1.1.52와 Snowflake CLI v3.23.0을 설치했습니다.
- Snowflake 연결 프로필은 아직 없으므로 SQL 적재, Snowpark 실행, CoCo 세션 증거는 미완료입니다.
- 합성 RFP fixture, 결정 엔진, inspectable policy trace, Streamlit workbench, 실제 공개 G2B qualification, Proposal Start Packet, in-session 작업 계획을 구현했습니다.
- 로컬 정책 테스트 4건, 린트, Streamlit health endpoint를 확인했습니다.
- 영어 제출 설명과 90초 시연 대본은 [제출 패키지](docs/SUBMISSION-PACKAGE_2026-08-01_v1.md)에 있습니다.
- 내부 제출 마감은 2026년 8월 2일입니다.

## 2 무엇부터 하고 무엇을 건드리지 마나

1. Snowflake 연결 프로필을 만든 뒤 CoCo CLI에서 계정, 역할, Cortex 모델 접근을 실제 확인합니다.
2. `snowflake/sql/01_schema.sql`과 `02_seed_fixture.sql`을 적재하고 `snowflake/snowpark_decision.py`의 결과를 기록합니다.
3. 실제 G2B 공고와 확인된 회사 증거로 Proposal Start Packet을 생성한 뒤, Grant Proposal Engine consumer를 별도 변경으로 연결합니다.
4. [제출 패키지](docs/SUBMISSION-PACKAGE_2026-08-01_v1.md)를 기준으로 영상을 녹화하고 대회 제출 필드를 확인합니다.
4. 실제 고객 자료, 감사 자료, 비공개 업무자료를 넣지 않습니다.
5. 데이터 검증, 출처 추적, 범용 대시보드 방향으로 바꾸지 않습니다.
6. 제품 범위나 Work Tree를 바꿀 때는 [CHRONICLE.md](docs/CHRONICLE.md)에 방향 결정을 먼저 기록합니다.

## 3 정본 링크

- 프로젝트 지도: [docs/MASTER-MAP.md](docs/MASTER-MAP.md)
- 결정 기록: [docs/CHRONICLE.md](docs/CHRONICLE.md)
- 저장소 소개: [README.md](README.md)
- 원격 저장소: https://github.com/sergiobuilds/bidpilot

## 4 변경 이력

- 2026-08-01 v3: 고도화된 workbench, 제출 패키지, 현재 검증 결과를 기록했습니다.
- 2026-08-01 v4: 실제 G2B 공고 qualification과 Proposal Start Packet 경계를 기록했습니다.
- 2026-08-01 v2: 로컬 구현과 검증 결과, Snowflake 연결 전 남은 하드 게이트를 기록했습니다.
- 2026-08-01 v1: 프로젝트 승격 직후 L2 복귀 지점과 금지사항을 기록했습니다.
