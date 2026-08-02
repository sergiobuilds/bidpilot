---
doc_kind: work-checklist
status: waiting-owner
version: 2026-08-02_v1
---

# Hack2Skill portal checklist

## Paste-ready fields

| Portal field | Exact value or artifact | State |
|---|---|---|
| Challenge | Intelligent Workflow Automation Agent | Ready |
| GitHub public repository | `https://github.com/sergiobuilds/bidpilot` | Waiting for public-transition approval |
| Deployed prototype | `https://bidpilot-demo-tbauoylpra-uc.a.run.app` | Signed-out HTTP 200 |
| Brief | `docs/SUBMISSION-PACKAGE_2026-08-02_v2.md`, Portal brief section, 878 characters | Ready |
| Demo video | `https://storage.googleapis.com/bidpilot-demo-164282963747/BidPilot-Final-Demo.mp4` | Signed-out HTTP 206, 4:38 |
| PDF deck | `dev/active/final-forge/submission-deck/BidPilot-Submission-Deck.pdf` | Ready, 8 pages, under 5 MB |

## Browser state

- laptop CDP 9222 is not serving Chrome; the local tunnel reaches a Windows `svchost` listener and times out.
- laptop CDP 9447 is active and displays the Hack2Skill login page.
- The 9447 browser profile is not authenticated to Hack2Skill.
- No portal field has been entered in this final freeze, and no final Submit action has occurred.

## Required final sequence

1. Sergio logs in to Hack2Skill on the visible 9447 tab.
2. Change the GitHub repository from private to public only after Sergio approves.
3. Verify a signed-out clone resolves to the final `origin/main` SHA.
4. Enter the challenge, repository, deployed prototype, brief, public video, and PDF.
5. Re-read the rendered values and links, save the draft if the portal supports it, and stop before Submit.
6. Report every rendered field to Sergio.
7. Click final Submit only after Sergio gives a separate explicit approval.
