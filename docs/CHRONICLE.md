---
doc_kind: project-decision
status: canonical
version: 2026-08-01_v1
canonical_path: /home/elite/projects/personal/products/bidpilot/docs/CHRONICLE.md
---

# BidPilot 결정 기록

이 문서는 무엇을 왜 정했는지 보존하는 append-only 기록이며, 문서 자체가 변경 이력 역할을 합니다.

- 2026-08-01 [direction]: Snowflake CoCo CLI Hackathon 2026 출품 아이템을 BidPilot으로 확정했습니다. 공개 경쟁 후보에서 공급망, 금융, 제조, 보안 Agent가 붐볐고 RFP 참여 판단과 제안 업무 실행은 직접 경쟁이 적었습니다.
- 2026-08-01 [direction]: 공식 문제 영역은 Intelligent Workflow Automation Agent로 선택했습니다. RFP 입력부터 판단, 승인, 작업 생성까지 한 흐름으로 시연할 수 있습니다.
- 2026-08-01 [deadline]: 행사 페이지와 Terms의 일정 충돌과 무관하게 내부 마감은 2026년 8월 2일로 고정했습니다. Sergio가 해당 날짜를 기준으로 제작하기로 확정했습니다.
- 2026-08-01 [scope]: Snowflake, CoCo CLI, Python을 필수 핵심 경로로 사용하고 Snowpark와 Streamlit을 제품 흐름에 포함하기로 했습니다.
- 2026-08-01 [boundary]: 실제 고객 자료, 감사 자료, 비공개 업무자료를 제외하고 합성 데이터 또는 공개 사용 허용 자료만 사용하기로 했습니다.
- 2026-08-01 [boundary]: 데이터 검증, 출처 추적, 범용 대시보드를 제품 주제로 삼지 않기로 했습니다.
- 2026-08-01 [validation]: 내부 IDEA blind league의 4개 후보 중 BidPilot이 가장 높은 측정 신호를 얻었고, 제조 정비 후보와의 제시 순서 양방향 결선에서도 일관되게 우세했습니다. 이는 공개 경쟁자 전체 순위가 아닌 동일 정보량의 내부 후보군 판정입니다.
- 2026-08-01 [implementation]: 높은 매출 RFP가 자격·용량·마진 hard gate로 NO-BID가 되고 다음 RFP의 내부 제안 업무가 생성되는 단일 시연 장면을 구현 범위로 고정했습니다.
- 2026-08-01 [evidence]: 로컬 Python 엔진, Streamlit 사용자 흐름, Snowflake DDL·seed·Snowpark 실행 경로를 만들었습니다. Snowflake 연결 프로필이 없어 실제 SQL, Snowpark, CoCo 세션 증거는 아직 주장하지 않습니다.
- 2026-08-01 [implementation]: 심사자 화면을 hard gate별 정책·관측값·통과 여부가 보이는 decision-to-action workbench로 확장했습니다. 긍정 판단은 owner·기한·workstream·expected outcome을 가진 내부 proposal work plan으로 전환합니다.
- 2026-08-01 [submission]: 영어 제출 설명, 90초 시연 순서, 로컬 재현 명령, 증거 경계를 제출 패키지에 고정했습니다. 실제 Snowflake 및 CoCo 세션 증거는 여전히 미완료입니다.
