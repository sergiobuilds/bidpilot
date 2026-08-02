---
doc_kind: work-evidence
status: complete
date: 2026-08-02
---

# Current artifact blind league

## Verdict

BidPilot ranks first in both the parity-reconstructed and source-locked views of the six scoreable CoCo CLI Hackathon artifacts. Four independent top-two judgments also select BidPilot over VF Logistics after the left/right order is reversed.

| View | BidPilot | Runner-up | Margin |
|---|---:|---:|---:|
| Parity-reconstructed median | 90 | VF Logistics 80 | +10 |
| Source-locked median | 94 | VF Logistics 78 | +16 |

## Protocol

- Six candidate cards were frozen before scoring and identified only by random blind IDs.
- Three independent lanes scored the official rubric: relevance 30, technical execution 40, and completeness 30.
- Low, mid, and high anchors calibrated each lane before the aggregate was sealed.
- Every candidate received three measurements. Identity mapping was opened only after `sealed-aggregate.json` existed.
- The top two then received four fresh pairwise judgments: two in each left/right orientation.

## Revealed ranking

| Rank | Candidate | Parity | Source-locked |
|---:|---|---:|---:|
| 1 | BidPilot | 90 | 94 |
| 2 | VF Logistics | 80 | 78 |
| 3 | Cortex SupplyGuard | 76 | 71 |
| 4 | Trading Agent App OS | 70 | 65 |
| 5 | SALAY | 66 | 66 |
| 6 | Contract Risk and Obligation Auditor | 64 | 64 |

SALAY and Trading Agent App OS reverse order between the two views. The top two do not change.

## Top-two final

| Orientation | BidPilot | VF Logistics | Winner |
|---|---:|---:|---|
| BidPilot left, judge 1 | 97 | 90 | BidPilot |
| BidPilot left, judge 2 | 96 | 92 | BidPilot |
| BidPilot right, judge 1 | 96 | 90 | BidPilot |
| BidPilot right, judge 2 | 93 | 90 | BidPilot |

BidPilot wins 4–0. The left item wins two of four non-ties, so observed position bias is 50%, below the 65% warning threshold. All four judgments identify the same decisive advantage: authenticated, persisted, replayable end-to-end execution evidence rather than implementation claims alone.

## Residual risks

- There is no paid-customer outcome or result from a live tender submission.
- The GitHub repository is still private pending owner approval, although the public app and video are reachable signed out.
- The competition portal has not received its final submit action.
- Competitor cards are reconstructed from the accessible artifacts frozen for this run; inaccessible private evidence cannot receive credit.

## Evidence index

- Frozen inputs and hashes: `run/protocol/freeze-manifest.json`
- Balanced assignments: `run/protocol/assignments.json`
- Three lane results: `run/judge/lane-1-results.json`, `lane-2-results.json`, `lane-3-results.json`
- Sealed pre-reveal aggregate: `run/sealed-aggregate.json`
- Post-seal identity reveal: `run/revealed-ranking.json`
- Top-two judgments: `run/judge/pair-ab-1.json`, `pair-ab-2.json`, `pair-ba-1.json`, `pair-ba-2.json`
