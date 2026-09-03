# BidPilot Grand Finale Demo Runbook

This runbook defines the live demo path, spoken lines, timed transitions, and failure fallbacks.

**Contents**: 1 Prepared state · 2 Timed path · 3 Failure branches · 4 Verification · 5 Change history

## 1 Prepared state

1. Open `https://bidpilot-demo-tbauoylpra-uc.a.run.app/?tender=R26BK01680611-000` before 15:15 KST and wait for the tender detail to render.
2. Open `https://bidpilot-demo-tbauoylpra-uc.a.run.app/?walkthrough=1` in a second tab and wait for the verified replay to render.
3. Keep the walkthrough at the top and preconfirm that the Snowflake proof expander is reachable.
4. Open `assets/BidPilot-Top16-Refinement-Demo.mp4` locally as the video fallback.
5. Keep slides 4 through 6 available as the no-network fallback.
6. Do not create, rerun, change, or delete a Snowflake run.

## 2 Timed path

| Time | Screen and action | Spoken proof |
|---:|---|---|
| 0:00–0:15 | Real-tender tab, no click | “This is a real public G2B tender source from Suwon City.” |
| 0:15–0:32 | Point to source evidence and supplier label | “The notice facts are source-reviewed. The supplier profile is synthetic demo data.” |
| 0:32–0:58 | Point to `REVIEW`, four gaps, and locked proposal | “Four evidence requirements remain unresolved, so no run, strategy, or proposal is created.” |
| 0:58–1:05 | Switch to walkthrough tab | “Now I’m moving to a separate synthetic historical replay.” |
| 1:05–1:35 | Point to `PURSUE`, 40 points, Win Position | “Here, the stored policy supports PURSUE. The 40-point criterion leads the selected position.” |
| 1:35–2:12 | Scroll through four plans and eight sections | “Official weight controls the plan and the proposal content.” |
| 2:12–2:35 | Point to green review result | “The persisted red-team result checks the score-bearing claims.” |
| 2:35–3:10 | Scroll through twelve tasks | “Unresolved evidence becomes owned delivery, review, and provenance work.” |
| 3:10–3:34 | Open Snowflake proof | “The reader returns the same completed run with Cortex session and Snowflake query provenance.” |
| 3:34–3:42 | Return to slide 7 | “No new run was created during this demo.” |

## 3 Failure branches

| Failure | Immediate action | Spoken line |
|---|---|---|
| Tender tab is blank or reconnecting | Return to slide 4 | “I’ll use the release-bound capture of the same public screen.” |
| Walkthrough tab is blank or reconnecting | Play local Top 16 video from 0:00 | “This is the signed-out backup recording of the released application.” |
| Delay exceeds five seconds | Stop waiting and use the next backup surface | “I’ll continue with the recorded evidence path.” |
| Internet is unavailable | Use slides 4–8 only | “The backup slides preserve the same source, run, and artifact boundaries.” |
| Snowflake proof expander does not open | Keep the current screen and move to slide 7 | “The release manifest and runbook record the same run identity and provenance.” |

## 4 Verification

1. The measured spoken demo plus twelve seconds of transition pauses is 194.652 seconds, or 3 minutes 14.652 seconds.
2. The primary path contains no dashboard landing page.
3. The real public tender and historical replay are named as separate evidence.
4. The real-tender `REVIEW` is explained as a reliability result.
5. The run ID remains `cortex-final-20260802-a` throughout the replay.

## 5 Change history

- 2026-09-03 v1: Defined the 3:42 stage ceiling, live tabs, and deterministic fallback branches.
- 2026-09-03 v2: Recorded the measured demo duration of 194.652 seconds.
