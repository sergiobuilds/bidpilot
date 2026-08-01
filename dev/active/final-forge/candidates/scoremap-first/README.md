# BidPilot — score-map-first Bid Room reference screen

Standalone reference for the BidPilot pursuit workbench. It defines information
architecture and interactions only; the product logic and data contract are
unchanged.

**목차** — 1 실행 · 2 화면 구조 · 3 상태 · 4 데이터 출처 · 5 접근성 · 6 반응형 검증

## 1 실행

`index.html`을 브라우저로 엽니다. 빌드 단계가 없고 외부 요청도 없습니다.

| 파일 | 내용 |
|---|---|
| `index.html` | 화면 구조 |
| `app.css` | 레이아웃·리듬·데이터 마크. 색·간격·타입은 전부 디자인 토큰 참조 |
| `app.js` | 상호작용. 라디오 입력 기반 선택, 상태 전이, 초안 재생성 |
| `data.js` | 기존 fixture와 결정 함수 출력에서 가져온 레코드 |
| `tokens.css` | 디자인 시스템 토큰과 컴포넌트 정의 |

## 2 화면 구조

2.1 첫 화면(1440 기준 상단)에 공고, 발주 목적, 평가항목과 배점, 공급자 준비도, 갭, PURSUE 판정, 네 가지 결정 차원이 모두 들어갑니다.

2.2 Zone A는 평가 score map과 Win Position을 좌측에, 상시 side region(pursuit status·결정 차원·source snapshot·공급자 프로필)을 우측에 둡니다.

2.3 Zone B는 전체 폭을 씁니다. 03 blueprint와 04 초안 미리보기, 05 red-team과 06 owners·tasks를 각각 나란히 배치하고 07 Bid Room run은 전폭입니다.

2.4 matrix에서 행을 선택하면 그 항목의 제안서 섹션 blueprint와 필요한 증빙이 열립니다.

2.5 Win Position을 바꾸면 matrix의 planned claim, blueprint, 초안, red-team, 저장 run의 selected position이 함께 바뀝니다.

## 3 상태

상단 segmented control로 전환하며, `#pursue` `#review` `#nogo` `#loading` 해시로 직접 열 수도 있습니다.

| 상태 | 조합 | 화면 |
|---|---|---|
| PURSUE | Northstar Systems × G2B-REPLAY-DATA-QUALITY | 전체 산출물과 기존 저장 run |
| REVIEW | Atlas Advisory × G2B-REPLAY-ANALYTICS | 생성 차단, gap closure plan |
| NO-GO | Atlas Advisory × G2B-REPLAY-DATA-QUALITY | 생성 차단, 자격·용량 gap 작업 |
| Loading | 주 동작 실행 중 | skeleton과 진행 상태 문구 |

## 4 데이터 출처

4.1 모든 값은 `fixtures.TENDERS`·`fixtures.SUPPLIER_PROFILES`와 `policy.pursue_status`, `pursuit.build_pursuit_brief`, `proposal_writer` 함수들의 실제 출력에서 가져왔습니다. 세 상태는 실제 정책 함수로 재현을 확인했습니다.

4.2 계약금액과 제출 마감은 tender 계약에 없는 필드라 제품의 기존 문구("Requires review from the source document.")로 표시합니다. 무관한 시뮬레이션 레코드 값을 끌어오지 않습니다.

4.3 Win Position은 3안입니다. 현재 `pursuit.py`는 2안을 만들며, 3안째는 같은 `_position()` 형태를 다음 평가항목 순서에 적용한 것입니다.

4.4 criterion별 readiness는 UI 계층 파생입니다. 태그가 일치하는 과거 사업, 지정된 인력, 자격 중 그 항목에 묶인 자산이 있는지로 Covered·Partial·Open을 정합니다.

## 5 접근성

5.1 criterion 선택과 Win Position 선택은 실제 `input[type=radio]`라 키보드로 조작되고 그룹으로 읽힙니다.

5.2 포커스 링은 컴포넌트 정의의 `:focus-visible` 규칙을 그대로 씁니다.

5.3 상태는 색이 아니라 문구로도 표시합니다(PURSUE·REVIEW·NO-GO, Met·Blocked·Not assessed).

5.4 작은 보조 텍스트에 쓰이던 `fg-neutral-subtle`(흰 배경 3.42:1)과 `fg-brand`(2.94:1)는 AA 미달이라 각각 `fg-neutral-muted`(6.62:1)와 carrot-800(5.76:1)으로 올렸습니다. 컴포넌트 내부 색 조합은 손대지 않았습니다.

## 6 반응형 검증

`ds-shot`으로 1440·768·390을 촬영해 네 상태 모두 가로 overflow 없음을 확인했습니다.

- 1120px 이하: side region이 본문 위아래로 펼쳐지고, matrix에서 planned claim 열은 상세 패널이 이미 전문을 담고 있어 숨깁니다.
- 720px 이하: matrix가 criterion 카드로 바뀌며 배점과 갭을 그대로 유지합니다.
