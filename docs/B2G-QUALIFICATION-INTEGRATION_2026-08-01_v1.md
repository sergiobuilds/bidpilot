---
doc_kind: project-material
status: canonical
version: 2026-08-01_v1
canonical_path: /home/elite/projects/personal/products/bidpilot/docs/B2G-QUALIFICATION-INTEGRATION_2026-08-01_v1.md
---

# B2G Qualification Integration

BidPilot을 B2G 공고의 qualification layer로 두고 Grant Proposal Engine에 안전한 작성 시작 패킷을 넘기는 경계를 정의합니다.

**목차** — 1 Product role · 2 Workflow · 3 Packet contract · 4 Reuse boundary · 5 Delivery order · 6 Change history

## 1 Product role

BidPilot의 판매 단위는 적합성 판정이 아닙니다. B2G 사업자가 실제로 사는 결과는 제출 가능한 제안서입니다. BidPilot은 제안서를 쓰기 전에 공고 요건과 회사 근거를 닫아, 쓸 수 없는 공고에는 문서 생성을 막고 가능한 공고만 Proposal Engine으로 보냅니다.

## 2 Workflow

1. 공개 공고문과 첨부 원문을 가져옵니다.
2. 자격, 제출 방식, 평가 기준, 일정, 과업을 원문 위치와 함께 추출합니다.
3. 회사 증거와 대조해 `PASS`, `FAIL`, `EVIDENCE REQUIRED`를 만듭니다.
4. 결과를 `NO-BID — INELIGIBLE`, `HOLD — EVIDENCE REQUIRED`, `ELIGIBLE — COMMERCIAL REVIEW REQUIRED`로 고정합니다.
5. 열려 있고 증거가 닫힌 공고만 Proposal Start Packet을 통해 제안서 작성으로 보냅니다.

## 3 Packet contract

| 필드 | 의미 | Proposal Engine의 사용 방식 |
|---|---|---|
| `opportunity` | 공고 식별자, 발주기관, 과업, 금액, 기간, 마감 | 문서의 공고 기본정보와 작성 범위 |
| `source` | 원문 URL, SHA-256, 수집일, 페이지 수 | 모든 추출 사실의 검증 기준 |
| `qualification` | 요건별 상태, 실패 요건, 누락 증거 질문 | 자격 미충족이면 작성 차단, 누락이면 질문 생성 |
| `proposal_strategy` | 평가 방식과 writing gate | 평가항목 구조와 문서 생성 가능 여부 |

## 4 Reuse boundary

| BidPilot | Grant Proposal Engine |
|---|---|
| 공고 적합성, 자격 요건, 공급자 증거 확인 | 회사 근거 조립, 평가항목별 초안, 원본 양식 편집 |
| `Proposal Start Packet` 생성 | 패킷을 입력으로 받아 질문·작성·검증 실행 |
| 공고가 열려 있고 증거가 닫힐 때만 writing gate 개방 | `SUPPORTED/MISSING/CONFLICT`와 연결해 근거 없는 문장 차단 |

Grant Proposal Engine의 현재 작업 트리는 변경하지 않습니다. 해당 저장소에 미완료 변경이 있어, 이 저장소에서 패킷 계약과 실제 공고 사례를 먼저 검증한 뒤 소비자 어댑터를 별도 변경으로 넣습니다.

## 5 Delivery order

1. 나라장터와 지원사업 공고를 각각 하나씩 실제 공개 원문으로 검증합니다.
2. 각 원문에서 packet을 생성하고 누락 회사 증거 질문을 확인합니다.
3. Grant Proposal Engine에 packet consumer를 추가합니다.
4. 열려 있는 공고와 확인된 회사 근거로 제안서 생성까지 한 번 완주합니다.
5. Snowflake에 공고, 증거 상태, handoff 기록을 적재해 CoCo 실행 증거를 만듭니다.

## 6 Change history

- 2026-08-01 v1: BidPilot을 B2G qualification layer로 정하고 Proposal Start Packet 계약과 Grant Proposal Engine 경계를 기록했습니다.
