---
doc_kind: work-evidence
status: complete
date: 2026-08-02
---

# Current artifact blind league

## Verdict

BidPilot ranks first in both the parity-reconstructed and source-locked views of the six scoreable CoCo CLI Hackathon artifacts. The corrected v2 assignment gives every candidate exactly one measurement from each of three independent judges. Four new top-two judgments also select BidPilot over VF Logistics after the left/right order is reversed.

| View | BidPilot | Runner-up | Margin |
|---|---:|---:|---:|
| Parity-reconstructed median | 91 | VF Logistics 85 | +6 |
| Source-locked median | 99 | VF Logistics 83 | +16 |

## Protocol

- Six candidate cards were frozen before scoring and identified only by random blind IDs.
- Three independent lanes scored the official rubric: relevance 30, technical execution 40, and completeness 30. Every lane contained all six candidates exactly once.
- Low, mid, and high anchors calibrated each lane before the aggregate was sealed.
- Every candidate received three measurements. Identity mapping was opened only after `sealed-aggregate.json` existed.
- The top two then received four fresh pairwise judgments: two in each left/right orientation.

## Revealed ranking

| Rank | Candidate | Parity | Source-locked |
|---:|---|---:|---:|
| 1 | BidPilot | 91 | 99 |
| 2 | VF Logistics | 85 | 83 |
| 3 | Cortex SupplyGuard | 74 | 68 |
| 4 | SALAY | 69 | 65 |
| 5 | Contract Risk and Obligation Auditor | 67 | 63 |
| 6 | Trading Agent App OS | 67 | 62 |

The top two do not change between views. Contract Risk and Trading Agent tie on the reconstructed view and separate under source lock.

## Top-two final

| Orientation | BidPilot | VF Logistics | Winner |
|---|---:|---:|---|
| BidPilot left, judge 1 | 97 | 88 | BidPilot |
| BidPilot left, judge 2 | 91 | 87 | BidPilot |
| BidPilot right, judge 1 | 96 | 87 | BidPilot |
| BidPilot right, judge 2 | 95 | 91 | BidPilot |

BidPilot wins 4–0. The left item wins two of four non-ties, so observed position bias is 50%, below the 65% warning threshold. All four judgments identify the same decisive advantage: authenticated, persisted, replayable end-to-end execution evidence rather than implementation claims alone.

## Residual risks

- There is no paid-customer outcome or result from a live tender submission.
- The GitHub repository is still private pending owner approval, although the public app and video are reachable signed out.
- The competition portal has not received its final submit action.
- Competitor cards are reconstructed from the accessible artifacts frozen for this run; inaccessible private evidence cannot receive credit.

## Evidence index

- Frozen v2 inputs and hashes: `run-v2/protocol/freeze-manifest.json`
- Balanced v2 assignments: `run-v2/protocol/assignments.json`
- Judge provenance: `run-v2/protocol/judge-provenance.json`
- Three lane results: `run-v2/judge/lane-1-results.json`, `lane-2-results.json`, `lane-3-results.json`
- Sealed pre-reveal aggregate: `run-v2/sealed-aggregate.json`
- Post-seal identity reveal: `run-v2/revealed-ranking.json`
- Top-two judgments: `run-v2/judge/pair-ab-1.json`, `pair-ab-2.json`, `pair-ba-1.json`, `pair-ba-2.json`

The earlier `run/` directory is retained as superseded audit history. Its assignment plan was not one-candidate-per-lane balanced and must not be used for the final result.
