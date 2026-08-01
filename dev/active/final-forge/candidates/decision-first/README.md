# BidPilot pursuit workbench — reference screen

Standalone reference for the BidPilot information architecture and interactions. It defines
layout and behaviour only; the product logic and data contract are unchanged.

**Contents** — 1 Files · 2 Data contract · 3 Interactions · 4 Derived-on-screen values · 5 Verification

## 1 Files

| File | Role |
|---|---|
| `index.html` | Document structure and semantics |
| `ledger.css` | Layout layer above the design tokens |
| `ledger.js` | Port of the product decision logic and the render loop |
| `tokens.css` | Design-system tokens and component recipes, copied verbatim |

Open `index.html` directly. No build step, no network requests, no external fonts.

## 2 Data contract

`ledger.js` reproduces the product modules exactly:

| Product module | Port |
|---|---|
| `policy.pursue_status` | `pursueStatus` |
| `pursuit.build_pursuit_brief` | `buildPursuitBrief` |
| `pursuit.select_win_position` | `selectWinPosition` |
| `pursuit._position`, `_proof_cards`, `_blueprint` | `makePosition`, `proofCards`, `buildBlueprint` |
| `proposal_writer.write_strategy_proposal` | `strategyMarkdown` |
| `proposal_writer.red_team_proposal` | `redTeam` |
| `bid_room.BidRoomStore.save` | `persistRun` |

Two deviations, both deliberate and both inside the existing contract:

1. **Three Win Positions.** `build_pursuit_brief` returns two. The third is a further
   `_position(...)` call seeded from the next criterion in the rotated score map, which uses the
   same generator and the same inputs. No new field or behaviour.
2. **Header composition.** The pursuit brief carries no deadline, contract value, or source
   snapshot; those live on the reviewed-intake tender that `build_pursuit_tender` emits. The
   header joins the two, which is what a reviewed Bid Room holds.

Both records are replay fixtures, so their header facts are fixture facts:

| Field | Basis |
|---|---|
| Snapshot sha256 | `sha256("<id>\|<title>\|<delivery_hours>\|<criterion>:<weight>,…")` over the shipped record. Reproducible from the screen, and not the digest of any redistributed document. |
| Bid close | Set in the future so a PURSUE outcome and an open notice do not contradict each other. |
| Source origin, pages, contract value | Fixture values in the shape the intake snapshot records. |

## 3 Interactions

- **Opportunity** and **Supplier profile** selectors drive the real decision. The four decision
  outcomes are reachable: `Information-system DB quality × Northstar` → PURSUE,
  `Municipal analytics × Atlas` → REVIEW, `Information-system DB quality × Atlas` → NO-GO.
- **Surface state** switches Loaded / Loading / Empty.
- **Win Position** is a keyboard-operable radio group (arrow keys, roving tabindex). Selecting a
  position re-binds every blueprint claim, the score-map claim column, the readiness derivation,
  the draft, the red-team pass, and the run key — not just a highlight.
- **Build proposal from selected strategy** persists a run; it is `disabled` with explicit gate
  text for REVIEW and NO-GO, matching `can_generate_proposal`.
- **Replay run** reloads the persisted run. **Download draft** emits the real markdown.
- Deep links for review: `?tender=1&supplier=1`, `?view=loading`, `?view=empty`, `?position=2`.

## 4 Derived-on-screen values

Readiness and blueprint status are not engine fields. They are derived from the selected position
and the supplier profile by a rule stated in the score-map footnote: **Ready** (targeted and
asset-backed), **Partial** (asset-backed, not targeted), **Input required** (no profile asset
addresses the criterion — Price). Blueprint status maps from the same rule.

## 5 Verification

`ds-shot` at 1440 / 768 / 390, `overflow=false` at every width, in the loaded, loading, empty,
REVIEW and NO-GO states. Screenshots are in `.dsshot/`.

Mobile order is decision → next actions → primary action → win positions → selected proof →
score map → blueprint → draft → red team → run. Tables reflow into stacked records; nothing
scrolls horizontally.
