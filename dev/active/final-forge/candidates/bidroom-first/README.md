# Bid Room reference screen — bidroom-first

A standalone reference screen for BidPilot's saved Bid Room. It defines information
architecture and interactions only; the product logic and data contract are unchanged.

## Files

| File | Role |
|---|---|
| `index.html` | The screen |
| `styles.css` | Composition layer over the supplied design tokens and component classes |
| `app.js` | Win Position selection, stage navigator, companion tabs, state specimens |
| `tokens.css` | The supplied design-system tokens and component classes, verbatim |
| `.dsshot/` | Verification renders at 1440 / 768 / 390 |

Open `index.html` directly. Two deep links help review: `#pos=0|1|2` preselects a Win
Position, `#state=ready|loading|empty|review|nogo` preselects a state specimen.

## Data fidelity

Every value on the screen is what the existing code produces for
`G2B-REPLAY-DATA-QUALITY × supplier-northstar`, verified by running the modules:

- `pursue_status(0, 0, 2)` → `PURSUE`; next actions are the two the policy records.
- Proof cards are `_proof_cards` output: two matched past projects, then one credential.
- Blueprint rows are `_blueprint` output — criterion, weight, claim, assets, owner. Each
  claim is prefixed with the selected Win Position title, so selecting a different
  position rewrites the entire blueprint, the draft, and the saved-run match.
- The draft preview is the markdown `write_strategy_proposal` emits, including the
  lowercase `api` in `promised_outcome` and the doubled period after the evidence
  sentence. Both are what the writer produces; the screen does not clean them up.
- **Red-team findings are 0.** For this pairing `red_team_proposal` returns an empty
  tuple: every section carries a selected supplier asset and both 30+ point sections
  carry `Validation:` and `Buyer outcome:`. The screen shows the count as zero and
  names the four checks that passed rather than inventing findings.
- Owned tasks are the four `Develop {criterion} response` tasks the app creates from the
  blueprint, all `OPEN`.
- The run trace is the `agent_run` contract: `local-development-adapter`, state
  `not-executed-in-snowflake-or-coco`, five steps. The companion region says so in
  plain text and does not present local events as authenticated Snowflake or CoCo events.
- `opportunity_version` is `fixture:G2B-REPLAY-DATA-QUALITY:v1`, the value
  `tender.get("source_snapshot", {}).get("sha256", f"fixture:{id}:v1")` falls back to.

### Two deliberate deviations

1. **Three Win Positions.** The generator returns two for this tender
   (`Technical approach`, `Operational continuity`). The third, `Delivery team`, is
   extended by the same criterion-rotation rule the generator uses. This is stated in
   visible copy under the selector.
2. **Commercial fit reads "Not evaluated."** The margin gate lives in `engine.py` over
   `RFPS`/`COMPANY`; `TENDERS` records carry no contract value, so no margin policy runs
   for this pairing. The gate says that explicitly instead of showing a fabricated
   percentage.

### State specimens

Each is a real pairing, not a mock:

| State | Pairing | Source |
|---|---|---|
| Ready | data-quality × northstar | the run on this page |
| Loading | — | the five `agent_run` steps in progress |
| Empty | any unsaved position | `BidRoomStore.latest()` keys on the selected position statement |
| REVIEW | analytics × atlas | 1 comparable project → `position.mitigation` |
| NO-GO | data-quality × atlas | 1 missing credential + 160 h gap → `build_gap_closure_plan` |

### Switching position rolls the run back

`BidRoomStore.latest()` matches on opportunity, supplier, version, and the **selected
position statement**. So a position with no persisted run has not been drafted, reviewed,
or assigned — and the screen says so everywhere at once rather than leaving the previous
run's numbers on display:

| Region | Run matched | No run for this position |
|---|---|---|
| Execution strip | 4 / 4 sections · 0 open · 4 tasks | Not built · Not reviewed · Not assigned |
| Stage rail | Draft, Review complete | Draft, Review, Assign pending |
| Run trace | proposal, red-team, task-plan recorded | "Not run for this Win Position" |
| Task ownership | 4 owned tasks | empty-state message |
| Stage summary | 4 of 6 complete | 2 of 6 complete |
| Draft preview | `bidpilot-strategy-proposal.md` | same file, labelled "preview, not persisted" |
| Primary action | Rebuild proposal | Build proposal |
| Replay | enabled | disabled |

Selecting position 1 restores the whole chain. That reversible rollback is the
contract-true demonstration that one run threads every stage.

Replay announces the run id, opportunity version, and position through a `role="status"`
line beside the saved-run card, and is disabled when no run matches.

## Composition

A ledger spine runs the width of the page: one 2px rule segmented by stage state — dark
for complete, brand for the active stage, hairline for pending. Each stage carries its
state as literal text, never colour alone. Below it a four-cell execution strip carries
the run's live numbers, then a two-column workbench (decision, position, score map ·
companion activity), then a full-width output band (blueprint, draft + review, state
specimens). Brand colour appears only on the active stage, the selected position, targeted
criteria, and the primary action.

## Responsive

- **1440** — 1320px contained grid, sticky companion column.
- **768** — single column; the stage spine survives with its trailing detail dropped
  below 1080px; the primary action moves to a fixed bottom dock.
- **390** — the stage navigator becomes a compact progress control (previous / next,
  "Stage 3 of 6 · Active", a progress meter); the blueprint table becomes labelled cards;
  the primary action stays reachable in the dock, with page padding reserved for it.

`ds-shot` reports `overflow=false` at all three widths.

## Accessibility

- One `h1`, section `h2`s, `aria-labelledby` on every region.
- Stage navigator is an `<ol>` of buttons with `aria-current="step"` and left/right arrow
  keys; state is in the text, not the colour.
- Win Positions are a `radiogroup` with arrow, Home, and End keys.
- Companion views are a real `tablist`/`tabpanel` pair; state specimens are a `radiogroup`.
- Visible focus ring on every interactive element, from the design system's focus token.
- Body text uses the muted foreground token (≈6.4:1 on the default surface) rather than
  the subtle one (≈3.3:1), including for the unchecked segmented-control label.
- Live regions announce the selected position and the active stage.
- `prefers-reduced-motion` disables the load-in and meter animations.
