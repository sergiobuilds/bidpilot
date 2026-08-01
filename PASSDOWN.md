# BidPilot 인계

BidPilot 구현을 재개할 때 읽는 현재 작업 진입점입니다.

## 1 어디서 끊겼나

- 비공개 GitHub 저장소 `sergiobuilds/bidpilot`을 생성했습니다.
- RFP 참여 판단과 제안 업무 실행 Agent로 제품 방향을 확정했습니다.
- 프로젝트 지도와 결정 기록을 작성했습니다.
- 구현과 Snowflake 연결은 아직 시작하지 않았습니다.
- 내부 제출 마감은 2026년 8월 2일입니다.

## 2 무엇부터 하고 무엇을 건드리지 마나

1. Snowflake 계정에서 CoCo CLI 연결, 역할, 모델 가용성을 실제로 확인합니다.
2. 확인이 끝나면 [L3 데이터 모델](docs/MASTER-MAP.md#4-work-tree)로 이동합니다.
3. 실제 고객 자료, 감사 자료, 비공개 업무자료를 넣지 않습니다.
4. 데이터 검증, 출처 추적, 범용 대시보드 방향으로 바꾸지 않습니다.
5. 제품 범위나 Work Tree를 바꿀 때는 [CHRONICLE.md](docs/CHRONICLE.md)에 방향 결정을 먼저 기록합니다.

## 3 정본 링크

- 프로젝트 지도: [docs/MASTER-MAP.md](docs/MASTER-MAP.md)
- 결정 기록: [docs/CHRONICLE.md](docs/CHRONICLE.md)
- 저장소 소개: [README.md](README.md)
- 원격 저장소: https://github.com/sergiobuilds/bidpilot

## 변경 이력

- 2026-08-01 v1: 프로젝트 승격 직후 L2 복귀 지점과 금지사항을 기록했습니다.
