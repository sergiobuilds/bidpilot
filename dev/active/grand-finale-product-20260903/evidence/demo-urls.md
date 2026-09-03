NOT DEPLOYED: DO NOT PRESENT AS THE CURRENT PUBLIC APP

# Demo URLs

The public URLs below currently serve `origin/main` (bf7fd4d, Cloud Run revision `bidpilot-demo-00010-fjt`). The deadline and CTA fixes on branch `fix/grand-finale-product-20260903` are only in the local preview until Sergio approves deployment.

| Surface | URL | Serves today |
|---|---|---|
| Dashboard | https://bidpilot-demo-tbauoylpra-uc.a.run.app | main (still says `Due soon 6` / `After 24 Aug 2026`) |
| Real tender detail | https://bidpilot-demo-tbauoylpra-uc.a.run.app/?tender=R26BK01680611-000 | main (replay link only at page end) |
| Verified Replay | https://bidpilot-demo-tbauoylpra-uc.a.run.app/?walkthrough=1 | main (unchanged by this branch except loading captions) |
| Repository | https://github.com/sergiobuilds/bidpilot | branch pushed |
| Candidate branch | https://github.com/sergiobuilds/bidpilot/tree/fix/grand-finale-product-20260903 | 4 commits over main |

All three public routes were loaded signed-out from a fresh Playwright context at 1440×900, 768×900 and 390×844. Direct URL entry and reload reproduce the same state because every route is a query parameter, not session state.
