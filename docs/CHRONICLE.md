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
- 2026-08-02 [evidence]: `snow connection list`는 connection profile이 없다고 반환했고, Snowflake CLI 3.23.0만 확인됐습니다. 현재 환경의 `coco` 독립 실행 명령은 확인되지 않았습니다.
- 2026-08-02 [evidence]: Snowflake 가입과 JWT 연결을 완료하고 `BIDPILOT_DEMO.BIDPILOT` schema와 fixture를 적재했습니다. Snowpark 2×2 결과는 data-quality×northstar `PURSUE`, data-quality×atlas `NO-GO`, analytics×northstar `PURSUE`, analytics×atlas `REVIEW`로 Python 정책과 일치했습니다.
- 2026-08-02 [evidence]: Cortex Code CLI session `2d68fa00-3379-4147-8433-87b6ccddcd75`가 `bidpilot-v2-dq-northstar` run에 decision 1, strategy 1, response plan 4, proposal section 8, task 11과 query provenance를 저장했습니다. 사람, 과거 제안, 가격 데이터가 없는 사실은 문장으로 보충하지 않고 gap task로 보존했습니다.
- 2026-08-02 [security]: 앱 읽기와 실행 권한을 `BIDPILOT_READER`, `BIDPILOT_RUNNER`로 분리하고 secondary role을 비활성화했습니다. authenticated mode는 local fixture로 fallback하지 않습니다.
- 2026-08-02 [validation]: 제안서 엔진의 packet gate, 배점별 내용 변화, canonical 8영역, criterion-specific asset, 상대 최고배점 red-team 반례를 독립 재감사했고 5개 항목 모두 통과했습니다. 전체 테스트는 33개입니다.
- 2026-08-02 [design]: Seed design system으로 decision-first, scoremap-first, bidroom-first 세 후보를 만들고 동일 정보량의 ARTIFACT blind league를 실행했습니다. 절대점수는 decision-first가 75점으로 높았지만, 세 lane의 양방향 finalist pairwise는 모두 scoremap-first를 선택해 최종 화면을 score map 중심 하이브리드로 확정했습니다.
- 2026-08-02 [submission]: 공식 Hack2Skill 페이지에서 한국이 Japan & Korea 권역으로 참가 가능하고 행사는 Global·Online이며, 등록 마감은 8월 2일, prototype 제출 마감은 8월 6일임을 재확인했습니다. 공개 rubric은 Relevance 30, Technical 40, Completeness 30입니다.
- 2026-08-02 [evidence]: runner-only 최종 run `cortex-final-20260802-a`를 만들고 decision 1, strategy 3 중 selected 1, response plan 4, proposal section 8, task 12, Cortex session과 six write query IDs를 reader 역할로 재조회했습니다. 5-credit resource monitor와 query timeout을 실계정에 적용했습니다.
- 2026-08-02 [validation]: 현재 artifact 6개를 후보별 독립 3회가 되도록 균형 재실행했습니다. BidPilot은 corrected median 91, source-locked 99로 1위였고 VF Logistics와의 AB 2회·BA 2회 결선을 4대 0으로 이겼습니다. 이는 동결 모집단의 측정 승률이며 우승 보장은 아닙니다.
- 2026-08-02 [correction]: 공개 앱에서 persisted proposal fragment가 criterion heading 없이 합쳐져 false missing-section 경고를 내던 문제를 수정했습니다. 네 score-bearing criterion 아래 여덟 fragment를 조합하고 live red-team 통과와 download 활성화를 signed-out 브라우저에서 확인했습니다.
- 2026-08-02 [submission]: 실제 포털의 3–5분 요건에는 4분 38초 영문 영상을 사용합니다. Goal의 90초 구조도 별도 companion pitch로 보존하되 포털 필수 영상과 혼동하지 않습니다.
- 2026-08-02 [gate]: 최종 적대 QA는 0.97 PASS입니다. GitHub public 전환과 Hack2Skill final Submit은 Sergio의 명시 승인 전까지 외부 게이트로 남깁니다.
- 2026-08-02 [submission]: Sergio가 final submission까지 명시 승인했습니다. Hack2Skill 계정의 OTP 인증 후 저장소를 public으로 전환하고 signed-out 접근을 확인했습니다. GitHub/Deployed Link와 Prototype/MVP의 attempt 1을 각각 최종 평가 확인창에서 제출했으며, 하드 리로드 뒤 challenge, URL, 878자 brief, 영상 URL과 PDF명이 서버에서 복원됐습니다.
- 2026-08-02 [design]: 제출 후 UI를 Design Forge의 `wanted-design-system` pack으로 다시 만들었습니다. 공개 제품의 주 흐름을 Opportunities, Bid Decision, Win Plan, Proposal Room 네 화면으로 제한하고 provenance는 Proposal Room의 Run proof로 내렸습니다. 실제 reader run과 59 tests, 1440/768/390 네 화면의 overflow 0을 확인했으며, 기존 Cloud Run은 VivoBook sign-off 전까지 유지합니다.
- 2026-08-02 [security]: 공개 저장소의 현재 문서에서 제출 계정 이메일을 제거했습니다. 제출 완료 증거에는 계정 주소가 필요하지 않습니다.
- 2026-08-02 [deployment]: WDS 네 화면을 Cloud Run revision `bidpilot-demo-00004-9fd`로 배포하고 트래픽 100%와 기존 공개 URL의 HTTP 200을 확인했습니다. signed-out 1440, 768, 390 검증에서 네 화면 모두 horizontal overflow가 없었습니다.
- 2026-08-02 [submission]: GitHub/Deployed Link와 Prototype/MVP를 각각 attempt 2로 최종 제출했습니다. Prototype brief를 네 화면과 59 tests를 반영한 1022자로 갱신했고 기존 4분 38초 영상과 8쪽 PDF를 유지했습니다. 강제 재로드 후 challenge, 두 URL, brief, 영상 URL과 PDF명이 서버에서 복원됐습니다.
- 2026-08-03 [correction]: complete run 판정을 provider, policy, supplier profile version, 단일 PURSUE decision, 전략 선택 수, 100점 plan, section과 task, Cortex provenance까지 fail-closed로 강화했습니다. live migration은 기존 supplier 하위 레코드와 agent run에 profile version을 backfill했고 final run의 3 strategies, 4 plans, 8 sections, 12 tasks를 reader 역할로 재확인했습니다.
- 2026-08-03 [direction]: Sergio의 지시에 따라 기존 프론트의 시각 구조를 폐기하고 Design Forge의 `wanted-design-system` pack으로 Opportunities, Bid decision, Win plan, Proposal room을 blank-slate 재구축했습니다. 저장된 run은 불변 비교 기록으로 유지하고 proposal draft만 편집 가능하게 했습니다.
- 2026-08-03 [security]: Snowflake 연결 실패 시 connector 원문과 로컬 profile 목록이 화면에 노출되던 경로를 닫았습니다. 사용자 화면은 복구 지침만 제공하고 상세 예외는 서버 로그에 남기며 Streamlit 상세 오류 표시를 비활성화했습니다.
- 2026-08-03 [gate]: 새 source는 Ruff, compileall, 83 tests, 실제 reader run과 1440/768/390 화면 검증을 통과했습니다. 기존 Cloud Run revision은 유지하며 새 화면은 Sergio가 VivoBook에서 확인하기 전 배포하지 않습니다.
- 2026-08-03 [deployment]: Sergio의 시각 승인 후 blank-slate WDS source를 Cloud Run revision `bidpilot-demo-00005-fc2`로 배포했습니다. reader 연결, secret mount와 service account를 보존했고 새 revision이 100% 트래픽을 받습니다. 공개 Stage 1·4는 1440과 390에서 재렌더됐으며 가로 overflow가 없습니다.
