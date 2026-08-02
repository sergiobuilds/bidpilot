---
doc_kind: work-evidence
status: pass
version: 2026-08-02_v1
---

# BidPilot final adversarial QA

## Verdict

| Measure | Result |
|---|---:|
| QAScore | 0.97 |
| Verdict | PASS |
| Critical artifact blockers | 0 |
| Official-axis measured median | 27 / 30 relevance, 38 / 40 technical, 29 / 30 completeness |
| Corrected artifact-league median | 91 / 100 |
| Source-locked sensitivity | 99 / 100 |

The result means BidPilot has the highest measured win signal in the frozen artifact population. It is not a guarantee of first place.

## Hard gates

| Gate | Evidence | Result |
|---|---|---|
| Source and remote freeze | `HEAD == origin/main` | PASS |
| Policy and proposal tests | 48 tests | PASS |
| Public product | Signed-out run `cortex-final-20260802-a` loads | PASS |
| Proposal readiness | Four criterion headings, live red-team pass, download enabled | PASS |
| Snowflake lifecycle | `COMPLETED`, reader reload, no fixture fallback | PASS |
| Run cardinality | 1 decision, 3 strategies, 4 plans, 8 sections, 12 tasks | PASS |
| Cortex and query provenance | Session ID, six write query IDs, `snow-v3.23.0` in stored trace | PASS |
| Submission PDF | 8 pages, 391,203 bytes, 12 tasks split 5/4/3 | PASS |
| Portal video | 278.136 seconds, H.264/AAC, public HTTP 206 | PASS |
| Companion pitch | 90.000 seconds, H.264/AAC, English narration and burned subtitles | PASS |
| Responsive captures | 1440, 768, and 390 CSS pixels | PASS |
| Current artifact blind league | Balanced 3-lane v2, sealed before reveal, 4–0 pairwise | PASS |

The reproducible command is:

```bash
uv run python dev/active/final-forge/verify-final.py
```

## Problems found and corrected

1. Runner privileges and lifecycle were too broad. Grants, timeouts, a monthly resource monitor, and runner-only execution were applied and reloaded.
2. The first public run did not satisfy the app's persisted trace contract. Cortex Code updated the same run with the required execution provenance.
3. The first deck said eleven owned tasks while the run held twelve mixed-purpose tasks. The deck now states twelve verified tasks: five owned, four red-team, and three provenance.
4. Persisted proposal fragments used subsection names while the live red-team expected criterion headings. The app now groups eight fragments under four score-bearing criteria, passes the live check, and enables download.
5. The first artifact-league assignment repeated candidates inside a lane. The v2 league gives each candidate exactly one measurement from each of three judges and preserves the earlier failed run as audit history.
6. Candidate revision and identity mapping diverged. Both now point to the product revision, and the reveal embeds the sealed aggregate SHA-256.

## Residual risks

- There is no paid-customer result or outcome from an open tender submission.
- Competition judges may reward a different domain or presentation style than the frozen population did.
- The public prototype uses synthetic supplier fixtures and a closed historical public notice, disclosed in the submission.
- GitHub remains private and the portal remains unfilled until the owner-controlled gates are approved.
