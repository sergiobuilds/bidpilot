# BidPilot Grand Finale Pitch Script

This is the English presentation script for the fifteen-slide Grand Finale deck and live demonstration.

**Contents**: 1 Delivery contract · 2 Timed script · 3 Measurement · 4 Change history

## 1 Delivery contract

1. Deliver slides 1 through 9 in 3 minutes 40 seconds.
2. Keep the slide 10 live demonstration at or below 3 minutes 15 seconds.
3. Deliver slides 11 through 15 in 2 minutes 40 seconds.
4. Reserve the final twenty seconds for the conclusion and memory line.
5. Use the corresponding backup slide when a live screen waits longer than five seconds.

## 2 Timed script

### 2.1 Slide 1 · 0:00–0:25

Quick case. You find a public tender worth two hundred fifty million Korean won. Technical quality carries ninety points. Price carries ten. Would you bid? Pursue, or no-go? Most teams feel pressure to decide immediately. But the score is not the missing answer.

### 2.2 Slide 2 · 0:25–0:50

The missing answer is REVIEW. Four supplier requirements remain unsupported. The tender is a real public G2B notice. The supplier profile is explicitly synthetic demo data. BidPilot refuses to approve the pursuit until the company can support its eligibility and delivery claims.

### 2.3 Slide 3 · 0:50–1:20

I’m Sergio Lee, a Washington State CPA specializing in government grants, public-program accounting, and government-support applications. Working through an accounting firm exposed the same breakpoints in every pursuit: verify eligibility before committing resources, separate source facts from assumptions, bind score-bearing claims to evidence, and assign every unresolved gap to an owner. That discipline became BidPilot.

### 2.4 Slide 4 · 1:20–1:55

The accounting firm repeatedly interprets notices, requests documents, reconciles gaps, and works against a fixed deadline. The company must find the opportunity, prove eligibility, locate credentials and people, understand the score, choose a position, and assign unresolved work. These six decisions usually live across email, files, and meetings. Writing begins while the decision chain is still broken.

### 2.5 Slide 5 · 1:55–2:25

This pattern is global. OECD public procurement represented 12.9 percent of GDP across OECD countries in 2021. The European Union’s TED service publishes over three thousand notices each weekday. Korea G2B, US SAM.gov, and EU TED have different legal rules, but they share an operating pattern: public notice, eligibility rules, scored evaluation, private supplier evidence, and a fixed submission boundary.

### 2.6 Slide 6 · 2:25–2:50

A defensible decision needs three things. Verification establishes what the notice says and what the supplier can prove. Context connects credentials, people, availability, and delivery history. Strategy converts official weights into a competitive position and owned work. If any stream is incomplete, the correct result may be REVIEW or NO-GO.

### 2.7 Slide 7 · 2:50–3:00

Fluency is not evidence. A proposal can sound excellent and still be indefensible.

### 2.8 Slide 8 · 3:00–3:25

BidPilot connects one accountable path: tender, decision, Win Position, proposal, and owner. The same run identity persists every stage in Snowflake. A general LLM returns prose. BidPilot turns governed evidence into a pursuit decision, a score-weighted strategy, and executable proposal work.

### 2.9 Slide 9 · 3:25–3:40

The demo keeps two evidence paths separate. The real public tender proves source handling and the decision boundary. A separate synthetic historical replay proves the full workflow and Snowflake execution. I will not create or change a run today.

### 2.10 Slide 10 and live demo · 3:40–6:50

[Open the preloaded real-tender tab. Pause 2 seconds.]

This is a real public G2B tender source from Suwon City. We use it strictly as a fixed demonstration case, not as a live bid recommendation. The published evaluation is technical ninety and price ten. The notice facts are source-reviewed, while the supplier profile is labeled synthetic demo data.

BidPilot identifies four unresolved supplier evidence requirements. The result is REVIEW, and the run count is zero. Strategy and proposal work remain closed. This is a successful control outcome. Missing eligibility or delivery evidence stays visible instead of becoming a confident proposal claim.

[Switch to the preloaded walkthrough tab. Pause 2 seconds.]

Now I’m moving to a separate synthetic historical replay. This is not the Suwon decision. Here, the recorded policy supports PURSUE. The official score profile is forty, thirty, twenty, and ten. The forty-point criterion leads the response.

BidPilot compared three Win Positions and selected Proven Data Quality Operations. The selection remains connected to recorded supplier evidence, the planned claim, and an accountable owner.

[Scroll through the weighted plan and proposal. Pause 2 seconds.]

That position controls four weighted response plans and eight proposal sections. Each score-bearing section follows the official weight and recorded evidence. The persisted red-team result checks the highest-value claims.

[Scroll through owned work and Snowflake proof. Pause 2 seconds.]

Twelve tasks assign delivery, review, and provenance work. The same screen returns historical run `cortex-final-20260802-a` through the least-privilege reader with Cortex session and Snowflake query provenance. No new execution occurred during this demo.

[Return to slide 11. Pause 2 seconds.]

### 2.11 Slide 11 · 6:50–7:20

The mechanism is the score spine. Forty points receive the strongest strategic and writing emphasis. That weight controls the selected Win Position, supporting evidence, proposal section, red-team check, and owner. The other criteria remain covered, but they do not receive equal attention. Four plans become eight sections and twelve owned or review tasks.

### 2.12 Slide 12 · 7:20–8:00

Why Snowflake? The product needs governed enterprise context and durable organizational memory. The Opportunity Graph joins versioned tender requirements with controlled credentials, people, availability, and delivery history. Snowpark executes policy beside that data. The runner writes approved execution artifacts. The reader reloads only complete results. Every decision, strategy, plan, section, task, session, and query reference stays attached to one run identity. An authenticated read failure fails closed.

### 2.13 Slide 13 · 8:00–8:40

Why CoCo CLI? The work is an execution sequence, not one model response. In the recorded session, Cortex Code queried governed Snowflake records, compared three positions, selected one, wrote four plans and eight proposal sections, challenged score-bearing claims, created twelve tasks, and persisted session and query provenance. It operated through an authenticated CLI session inside the repository workspace, with no LLM API key.

### 2.14 Slide 14 · 8:40–9:10

The verified run contains one decision, three strategies, four weighted plans, eight proposal sections, and twelve tasks. The machine path stops at internal work ready. A person still reviews the source, confirms supplier evidence, owns pricing, approves the final edit, and performs the legal submission. The first buyer is a small B2G proposal team, served through a team workspace with usage-based runs.

### 2.15 Slide 15 · 9:10–9:30

BidPilot brings verification, company context, and score strategy into one replayable Snowflake run. Teams get a defensible decision, a weighted win strategy, and owned execution work.

[Pause.]

Win the score, not the prompt.

## 3 Measurement

FFmpeg Flite rendered all spoken lines at the calibrated slow stage pace and added fourteen seconds for documented transitions. The measured presentation duration is 569.988 seconds, or 9 minutes 29.988 seconds. The live-demo segment is separately measured at 190.007 seconds, or 3 minutes 10.007 seconds.

## 4 Change history

- 2026-09-03 v1: Rebuilt the script around founder authority, global public-sector evidence, verification, context, strategy, Snowflake necessity, CoCo CLI execution, and central visual explanations.
- 2026-09-03 v2: Recorded the first rendered narration and live-demo measurements.
- 2026-09-03 v3: Expanded the script to the fifteen-slide dark show, adding the audience quiz, REVIEW reveal, breathing beat, product spine, and simplified close while preserving the verified evidence chain.
