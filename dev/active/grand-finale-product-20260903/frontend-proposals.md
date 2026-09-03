# BidPilot 프론트 개선안 (2026-09-03)

전제: 대시보드는 누구나 만들 수 있으니 화면의 역할은 "제품을 설명하는 창"으로 줄이고, 본체는 판단 엔진과 Snowflake 기록, 그리고 에이전트 표면(Cortex Code 스킬·원격 MCP)이다. 아래 세 안은 서로 배타적이지 않으며 1안은 오늘 30분 안에, 2안은 행사 후 하루, 3안은 다음 라운드용이다.

## 현재 화면의 문제

| 위치 | 요소 | 판정 |
|---|---|---|
| 대시보드 상단 | 6단계 인과관계 띠 + 평가자 workspace 링크 3개 | 설명은 좋으나 첫 화면에서 두 번째로 큰 덩어리다. 발표자가 말로 하는 내용과 중복된다. |
| KPI 4개 | Public sources · Needs review · PURSUE · Open deadlines | PURSUE 0은 솔직하지만 첫 인상으로 약하다. 두 개면 충분하다. |
| 공고표 | 6행 × 7열 | 핵심. 유지. |
| 하단 | Pursuit funnel + Recent activity | 표와 같은 숫자를 다시 그린다. 정보량 0. |
| 공고 상세 | 8개 섹션 | Processing history와 Source evidence는 접어도 된다. Decision summary와 Owned work가 본체다. |
| Verified replay | 한 페이지 결과 | 이미 잘 정리돼 있다. 손대지 않는다. |

## 1안 — 덜어내기 (오늘 가능, 코드 삭제만)

대시보드를 세 덩어리로 줄인다. 제목과 한 줄 설명, KPI 2개(Needs review 1 · Open deadlines 1), 공고표, 그리고 표 위에 버튼 하나 `Open verified PURSUE replay →`. 인과관계 띠·workspace 링크·funnel·recent activity는 제거하고 workspace 링크는 footer 텍스트 링크로 내린다. 공고 상세는 Processing history와 Source evidence를 `details` 접힘으로 바꾼다. 테스트 3~4개만 조정하면 되고 데이터 경로는 그대로다. 심사위원이 보는 순서가 표 → REVIEW 이유 → replay로 고정된다.

## 2안 — "에이전트가 먼저" 화면 (행사 후 하루)

첫 화면을 대시보드가 아니라 "이 능력을 당신의 에이전트에 붙이세요" 페이지로 바꾼다. 위쪽에 탭 네 개(Cortex Code · Claude Code · Cursor · ChatGPT)와 각 탭에 복사 가능한 설정 한 덩어리, 그 아래 live 예시 하나: `decide R26BK01680611-000` 호출 결과(REVIEW, 4 gaps)를 JSON과 사람 문장으로 나란히 보여 준다. 공고표와 replay는 두 번째·세 번째 메뉴로 내린다. 이 안이 "대시보드는 누구나 만든다"는 문제에 정면으로 답한다. 구현은 Streamlit 한 페이지 추가와 Track A의 REST 호출뿐이다.

## 3안 — Bid Room을 대화형으로 (다음 라운드)

화면 오른쪽에 채팅 패널을 붙이고, 사용자가 "이 공고 증거 이거 이거 있음"이라고 말하면 같은 MCP 도구를 호출해 판단이 바뀌는 것을 보여 준다. 왼쪽은 결과(Decision → Win Position → 섹션 → 작업)가 채워지는 Bid Room이다. 화면이 채팅의 결과를 반영하므로 "에이전트가 일하고 화면은 기록"이라는 제품 정의와 일치한다. 인증된 runner가 필요하므로 공개 데모에는 넣지 않고 심사위원 계정으로만 연다.

## 오늘 추천

1안만 적용하되 두 트랙(스킬·MCP)이 14:00 전에 안정되면 그때 30분을 쓴다. 트랙이 늦으면 화면은 현재 배포본을 그대로 쓰고 발표에서 말로 덜어낸다. 어느 경우든 replay 화면은 손대지 않는다.
