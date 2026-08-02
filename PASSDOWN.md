# BidPilot 최종 제출 기록

BidPilot 최종 제출 완료 상태의 복귀 지점입니다.

## 1 현재 사실

- 제품은 공고 평가표와 공급사 운영 메모리를 연결하는 B2G Pursuit Agent의 Bid Room입니다.
- Snowflake 실계정에 `BIDPILOT_READER`와 `BIDPILOT_RUNNER`의 세분화 grant, 5-credit 월간 resource monitor, warehouse/query timeout을 적용했습니다.
- runner-only Snowpark 2×2 결과는 `PURSUE`, `NO-GO`, `PURSUE`, `REVIEW`이며 Python 정책과 같습니다.
- Cortex Code session `7d9dc75b-3fd9-4ab0-9d8f-4d0c0e2c18f1`이 complete run `cortex-final-20260802-a`를 만들었습니다.
- complete run은 decision 1, strategy 3 중 selected 1, response plan 4, proposal section 8, task 12와 query provenance를 가집니다.
- 제안서 엔진의 raw/locked/REVIEW/NO-GO 차단, 배점별 내용 변화, 필수 8영역, 항목별 자산, 고배점 red-team 반례를 독립 재감사했고 모두 통과했습니다.
- 세 Seed 후보를 동일 정보량으로 블라인드 평가했습니다. 절대점수는 decision-first가 높았지만, 세 레인의 양방향 결선은 모두 scoremap-first를 선택했습니다. 최종 앱은 score map 중심 하이브리드입니다.
- 전체 테스트는 83개 통과합니다. 새 source는 Design Forge와 WDS로 blank-slate 재구축한 `Opportunities → Bid Decision → Win Plan → Proposal Room` 네 화면을 제공합니다.
- 후보마다 서로 다른 세 심사자가 한 번씩 보도록 균형 재실행한 내부 artifact blind league에서 BidPilot은 parity 91점, source-locked 99점으로 모두 1위였습니다. 2위 VF Logistics와의 새 좌우 반전 결선도 4대 0으로 이겼습니다. 제출문에는 경쟁 우위의 내부 방향성 자료로만 사용합니다.
- 공개 영상은 `https://storage.googleapis.com/bidpilot-demo-164282963747/BidPilot-Final-Demo.mp4`이며 signed-out HTTP range 요청이 206으로 통과합니다.
- `uv run python dev/active/final-forge/verify-final.py` 한 번으로 git, tests, live DOM, PDF, 영상, Snowflake trace와 blind-league chain을 재검증할 수 있습니다.
- 포털용 4분 38초 영상과 별도로 Goal 구조를 만족하는 정확히 90초 영문 자막 pitch `dev/active/final-forge/BidPilot-90s-Pitch.mp4`를 만들었습니다.
- GitHub 저장소를 public으로 전환하고 signed-out `git ls-remote`로 `main`을 확인했습니다.
- Hack2Skill의 GitHub/Deployed Link와 Prototype/MVP attempt 2를 모두 최종 확인창까지 제출했습니다. 하드 리로드 후 challenge, URL, 1022자 brief, 영상 URL과 PDF명이 서버에서 복원됐습니다.
- 새 WDS 후보는 reader 연결에서 실제 네 화면을 순서대로 통과했습니다. 1440, 768, 390의 모든 화면은 horizontal overflow가 없고, Opportunities의 primary action은 각 첫 viewport 안에 있습니다.
- Cloud Run revision `bidpilot-demo-00005-fc2`가 트래픽 100%를 받고 있으며 공개 URL은 새 WDS source를 제공합니다.
- 공개 source는 strict complete-run 계약, supplier profile version binding, 안전한 연결 오류 화면을 포함합니다. `bidpilot-reader`로 final run의 strategy 3, plan 4, section 8, task 12를 재확인했습니다.
- Sergio의 시각 승인 후 공개 Stage 1·4를 1440과 390에서 다시 열어 가로 overflow가 없음을 확인했습니다. 첫 cold start는 Snowflake JWT 연결 때문에 지연될 수 있습니다.

## 2 제출 후 유지

1. 심사 기간 동안 공개 저장소, 앱, 영상의 signed-out 접근을 유지합니다.
2. 포털을 다시 수정할 때는 attempt 1과 attempt 2를 보존하고 새 attempt의 변경점을 먼저 확인합니다.
3. 합성 fixture와 닫힌 역사 공고라는 disclosure를 유지합니다.
4. 공개 URL은 새 revision을 이미 제공하므로 심사 중에는 runtime 접근성과 reader 연결만 점검합니다.

## 3 금지 경계

- 합성 fixture를 실제 고객 데이터로 소개하지 않습니다.
- 닫힌 G2B 사례를 현재 투찰 가능한 공고라고 말하지 않습니다.
- 없는 사람, 가격, 실적 수치를 제안서에 추가하지 않습니다.
- authenticated mode 실패 시 local fixture로 조용히 대체하지 않습니다.
- 완료된 Snowflake/Cortex 프로세스를 증거 없이 재실행하거나 기존 run을 삭제하지 않습니다.

## 4 정본

- [프로젝트 지도](docs/MASTER-MAP.md)
- [결정 기록](docs/CHRONICLE.md)
- [영어 제출 패키지](docs/SUBMISSION-PACKAGE_2026-08-02_v2.md)
- [실행 절차](snowflake/COCO_RUNBOOK.md)

## 5 변경 이력

- 2026-08-03: strict data contract, supplier version migration, blank-slate WDS source, 83 tests와 배포 전 시각 승인 게이트를 반영했습니다.
- 2026-08-03: Sergio 승인 후 Cloud Run `bidpilot-demo-00005-fc2`를 배포하고 공개 Stage 1·4의 desktop/mobile readback을 반영했습니다.
- 2026-08-02: WDS 공개 배포, Cloud Run revision, Hack2Skill attempt 2와 서버 재로드 검증을 반영했습니다.
