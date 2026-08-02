# BidPilot 인계

BidPilot 최종 제출 직전 상태의 복귀 지점입니다.

## 현재 사실

- 제품은 공고 평가표와 공급사 운영 메모리를 연결하는 B2G Pursuit Agent의 Bid Room입니다.
- Snowflake 실계정에 `BIDPILOT_READER`와 `BIDPILOT_RUNNER`의 세분화 grant, 5-credit 월간 resource monitor, warehouse/query timeout을 적용했습니다.
- runner-only Snowpark 2×2 결과는 `PURSUE`, `NO-GO`, `PURSUE`, `REVIEW`이며 Python 정책과 같습니다.
- Cortex Code session `7d9dc75b-3fd9-4ab0-9d8f-4d0c0e2c18f1`이 complete run `cortex-final-20260802-a`를 만들었습니다.
- complete run은 decision 1, strategy 3 중 selected 1, response plan 4, proposal section 8, task 12와 query provenance를 가집니다.
- 제안서 엔진의 raw/locked/REVIEW/NO-GO 차단, 배점별 내용 변화, 필수 8영역, 항목별 자산, 고배점 red-team 반례를 독립 재감사했고 모두 통과했습니다.
- 세 Seed 후보를 동일 정보량으로 블라인드 평가했습니다. 절대점수는 decision-first가 높았지만, 세 레인의 양방향 결선은 모두 scoremap-first를 선택했습니다. 최종 앱은 score map 중심 하이브리드입니다.
- 전체 테스트는 47개 통과합니다. authenticated AppTest에서 complete run, 9,202자 편집 초안, provenance 화면을 확인했습니다.
- 후보마다 서로 다른 세 심사자가 한 번씩 보도록 균형 재실행한 내부 artifact blind league에서 BidPilot은 parity 91점, source-locked 99점으로 모두 1위였습니다. 2위 VF Logistics와의 새 좌우 반전 결선도 4대 0으로 이겼습니다. 제출문에는 경쟁 우위의 내부 방향성 자료로만 사용합니다.
- 공개 영상은 `https://storage.googleapis.com/bidpilot-demo-164282963747/BidPilot-Final-Demo.mp4`이며 signed-out HTTP range 요청이 206으로 통과합니다.

## 다음 작업

1. CDP 9222에 실제 Chrome이 열리면 포털 초안을 채웁니다. 현재 원격 9222는 Chrome이 아니라 `svchost`가 점유해 응답이 없습니다.
2. Sergio 승인 후 저장소를 public으로 전환하고 signed-out clone을 검증합니다.
3. 최종 제출 버튼은 Sergio 승인 후에만 누릅니다.

## 금지 경계

- 합성 fixture를 실제 고객 데이터로 소개하지 않습니다.
- 닫힌 G2B 사례를 현재 투찰 가능한 공고라고 말하지 않습니다.
- 없는 사람, 가격, 실적 수치를 제안서에 추가하지 않습니다.
- authenticated mode 실패 시 local fixture로 조용히 대체하지 않습니다.
- 완료된 Snowflake/Cortex 프로세스를 증거 없이 재실행하거나 기존 run을 삭제하지 않습니다.

## 정본

- [프로젝트 지도](docs/MASTER-MAP.md)
- [결정 기록](docs/CHRONICLE.md)
- [영어 제출 패키지](docs/SUBMISSION-PACKAGE_2026-08-02_v2.md)
- [실행 절차](snowflake/COCO_RUNBOOK.md)
