# BidPilot 인계

BidPilot 최종 제출 직전 상태의 복귀 지점입니다.

## 현재 사실

- 제품은 공고 평가표와 공급사 운영 메모리를 연결하는 B2G Pursuit Agent의 Bid Room입니다.
- Snowflake 연결 `bidpilot`로 schema와 fixture를 적재했고, 앱은 `bidpilot-reader`, 실행은 `bidpilot-runner` 최소권한 역할을 사용합니다.
- Snowpark 2×2 결과는 `PURSUE`, `NO-GO`, `PURSUE`, `REVIEW`이며 Python 정책과 같습니다.
- Cortex Code session `2d68fa00-3379-4147-8433-87b6ccddcd75`가 complete run `bidpilot-v2-dq-northstar`를 만들었습니다.
- complete run은 decision 1, strategy 1, response plan 4, proposal section 8, task 11과 query provenance를 가집니다.
- 제안서 엔진의 raw/locked/REVIEW/NO-GO 차단, 배점별 내용 변화, 필수 8영역, 항목별 자산, 고배점 red-team 반례를 독립 재감사했고 모두 통과했습니다.
- 세 Seed 후보를 동일 정보량으로 블라인드 평가했습니다. 절대점수는 decision-first가 높았지만, 세 레인의 양방향 결선은 모두 scoremap-first를 선택했습니다. 최종 앱은 score map 중심 하이브리드입니다.
- 전체 테스트는 33개 통과합니다. authenticated AppTest에서 complete run, 9,202자 편집 초안, provenance 화면을 확인했습니다.

## 다음 작업

1. 최종 변경분을 QA하고 commit 직후 main에 push합니다.
2. 비공개 저장소에 공식 심사 계정 접근을 부여하거나 대회 규정이 허용하면 public으로 전환한 뒤 별도 세션에서 clone을 검증합니다.
3. [제출 패키지](docs/SUBMISSION-PACKAGE_2026-08-02_v2.md)의 90초 순서로 영상을 녹화합니다.
4. Hack2Skill 로그인은 `jdrnd30@jdac.co.kr`로 OTP를 발송한 상태입니다. 6자리 코드를 입력한 뒤 실제 제출 필드를 확인합니다.
5. 외부 제출 폼의 최종 버튼은 Sergio가 렌더링 결과를 확인한 뒤 누릅니다.

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
