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
- 2026-08-01 [product]: BidPilot을 독립 BID/NO-BID 서비스가 아니라 B2G 공고 qualification layer로 확정했습니다. 열린 공고와 닫힌 회사 증거가 확인될 때만 Proposal Start Packet을 통해 Grant Proposal Engine의 제안서 작성 단계로 넘깁니다.
- 2026-08-01 [evidence]: 공개 G2B 공고 R26BK01490484의 원문 URL, 9쪽 원문 SHA-256, 자격·평가·과업 추출을 실제 사례로 추가했습니다. 이 공고는 마감된 과거 사례이므로 현재 투찰 가능성을 주장하지 않습니다.
- 2026-08-01 [direction]: BidPilot의 headline을 qualification이나 문서 형식 보존이 아니라 Snowflake-native B2G Revenue Agent로 확정했습니다. 외부 공고와 내부 운영 데이터를 결합해 pursuit decision, win strategy, editable proposal draft, proposal work plan을 만듭니다.
- 2026-08-01 [strategy]: 심사 시연의 magic moment는 실제 공고가 기술평가 승리 전략과 제안서 초안으로 변하는 장면으로 고정했습니다. 공고 조건과 회사 데이터 대조는 신뢰성 계층으로 유지하되 발표의 전면에는 두지 않습니다.
- 2026-08-01 [direction]: 독립 제품·구매자·심사·구조 QA를 반영해 BidPilot을 B2G Pursuit Agent의 Bid Room으로 재정의했습니다. 제품의 단위는 공고 요약이나 bid/no-bid 답이 아니라, 평가 논리와 회사 운영 메모리에서 선택한 Win Position을 전략 주도 제안서·red-team·소유 작업으로 연결한 하나의 persisted run입니다.
- 2026-08-01 [scope]: 기존 합성 hard-gate 데모, 단일 마감 공고 fixture, 고정 Markdown writer, 실행되지 않은 Snowflake 스케치는 초기 prototype으로 격하했습니다. 최종 제출 주장은 실제 Snowflake query·write, Snowpark parity, CoCo trace, 두 공고와 두 공급사 프로필의 변화 검증이 있는 경우에만 허용합니다.
- 2026-08-02 [implementation]: URL/PDF/text intake, source snapshot hash, injection-like content isolation, two-tender/two-supplier matrix, selected Win Position, strategy-led proposal, red-team, local SQLite Bid Room persistence, append-safe Opportunity Graph SQL을 구현했습니다. 이는 local evidence이며 Snowflake·CoCo run은 주장하지 않습니다.
- 2026-08-02 [blocker]: Snowflake AI Data Cloud와 CoCo 전용 가입을 각각 최종 제출까지 시도했으나 모두 계정 생성 일반 오류로 실패했습니다. 대회 공식 페이지는 CoCo CLI 기반 build를 요구하며 Geographic Eligibility 본문에는 India만 적혀 있어, account access와 참가 자격은 공식 지원의 명시 답변이 필요합니다.
