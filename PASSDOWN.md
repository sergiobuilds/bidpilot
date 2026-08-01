# BidPilot 인계

BidPilot 구현을 재개할 때 읽는 현재 작업 진입점입니다.

**목차** — 1 어디서 끊겼나 · 2 무엇부터 하고 무엇을 건드리지 마나 · 3 정본 링크 · 4 변경 이력

## 1 어디서 끊겼나

- 비공개 GitHub 저장소 `sergiobuilds/bidpilot`을 생성했습니다.
- 제품 방향은 B2G Pursuit Agent의 Bid Room으로 확정했습니다. 공고의 평가 논리와 회사 운영 메모리에서 Win Position을 고르고, 그 전략으로 제안서와 작업을 만듭니다.
- 프로젝트 지도와 결정 기록을 작성했습니다.
- Snowflake CLI v3.23.0은 설치됐습니다. 현재 환경에서 `coco` 독립 실행 명령은 확인되지 않았습니다.
- Snowflake 가입은 AI Data Cloud와 CoCo 전용 경로에서 모두 마지막 생성 요청이 일반 오류로 실패했습니다. SQL 적재, Snowpark 실행, CoCo 세션 증거는 미완료입니다.
- URL/PDF/text intake, source hash, 지시문형 텍스트 격리, 2×2 supplier/tender fixture, Win Position, strategy-led draft, red-team, SQLite Bid Room persistence를 구현했습니다.
- Snowflake Opportunity Graph SQL과 Snowpark 정책은 account-ready이며 실행 증거는 없습니다.
- 현재 [제출 패키지 v2](docs/SUBMISSION-PACKAGE_2026-08-02_v2.md)는 local evidence와 account gate를 구분합니다.
- 내부 제출 마감은 2026년 8월 2일입니다.

## 2 무엇부터 하고 무엇을 건드리지 마나

1. 현재 open public tender를 source snapshot으로 intake하고 reviewed Bid Room까지 실행합니다.
2. Snowflake 연결 프로필을 만들 수 있는 정상 계정이 확보되면 schema와 seed를 적재하고 Snowpark parity를 실제 실행합니다.
3. CoCo가 intake, retrieval, strategy, proposal, red-team, task creation을 수행한 trace를 `AGENT_RUNS`에 저장합니다.
4. 실제 run 뒤에만 제출 패키지와 영상을 최종화합니다.
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
- 2026-08-02 v6: local intake와 persistent Bid Room 구현, Snowflake 가입 외부 게이트, 다음 실증 순서를 반영했습니다.
- 2026-08-01 v2: 로컬 구현과 검증 결과, Snowflake 연결 전 남은 하드 게이트를 기록했습니다.
- 2026-08-01 v1: 프로젝트 승격 직후 L2 복귀 지점과 금지사항을 기록했습니다.
