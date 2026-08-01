/* BidPilot pursuit workbench — reference screen.
   The decision, win positions, blueprint, draft and red-team logic below are a
   faithful port of the product modules (policy / pursuit / proposal_writer /
   bid_room). No new product capability is introduced here. */

'use strict';

/* ── Reviewed opportunity records ─────────────────────────────────── */

const TENDERS = [
  {
    id: 'G2B-R26BK01490484',
    title: 'Information-system DB quality diagnosis and consulting service',
    buyer_objective: 'Improve public-data reliability while keeping citizen-facing APIs stable.',
    promised_outcome: 'a measured data-quality improvement and a maintained API operating model',
    tags: ['public-data', 'data-quality', 'api-operations'],
    eligibility_requirements: ['SME confirmation', 'Information-system maintenance certificate'],
    delivery_hours: 720,
    evaluation_criteria: [
      { name: 'Technical approach', weight: 40 },
      { name: 'Comparable delivery', weight: 30 },
      { name: 'Delivery team', weight: 20 },
      { name: 'Price', weight: 10 }
    ],
    source_snapshot: {
      origin: 'g2b.go.kr · Notice 2026-936',
      sha256: 'b5c052a56ed10caac786ddf6d90dd2186eec91338b560974a715a9bb59bd9ca3',
      retrieved_at: '2026-08-01',
      pages: 9
    },
    bid_close: '2026-08-19 10:00 KST',
    contract_value: 'KRW 70,000,000'
  },
  {
    id: 'G2B-R26MU00871220',
    title: 'Municipal analytics governance service',
    buyer_objective: 'Give policy teams governed analytics they can operate after handoff.',
    promised_outcome: 'a governed analytics service with a practical operating handoff',
    tags: ['analytics', 'governance', 'public-sector'],
    eligibility_requirements: ['SME confirmation'],
    delivery_hours: 520,
    evaluation_criteria: [
      { name: 'Comparable delivery', weight: 45 },
      { name: 'Team capability', weight: 25 },
      { name: 'Operating handoff', weight: 20 },
      { name: 'Price', weight: 10 }
    ],
    source_snapshot: {
      origin: 'g2b.go.kr · Notice 2026-1104',
      sha256: '4bd04123c2fb5b39f9599b82c62b11428e1c0164e89a32c47c58656d370fdee2',
      retrieved_at: '2026-08-01',
      pages: 6
    },
    bid_close: '2026-09-02 10:00 KST',
    contract_value: 'KRW 48,000,000'
  }
];

const SUPPLIERS = [
  {
    id: 'supplier-northstar',
    name: 'Northstar Systems',
    credentials: ['SME confirmation', 'Information-system maintenance certificate'],
    available_hours: 900,
    people: [
      { name: 'Mina Lee', role: 'Public data delivery lead' },
      { name: 'Jun Park', role: 'API operations architect' }
    ],
    past_projects: [
      { title: 'City Open Data Reliability Program', tags: ['public-data', 'data-quality', 'api-operations'], outcome: 'Reduced recurring data defects and introduced API change control.' },
      { title: 'Regional Analytics Governance Rollout', tags: ['analytics', 'governance', 'public-sector'], outcome: 'Handed governed dashboards to policy teams with an operating playbook.' },
      { title: 'Citizen API Service Transition', tags: ['api-operations', 'public-sector'], outcome: 'Transferred API support without a public-service interruption.' }
    ]
  },
  {
    id: 'supplier-atlas',
    name: 'Atlas Advisory',
    credentials: ['SME confirmation'],
    available_hours: 560,
    people: [{ name: 'Dana Cho', role: 'Analytics strategy lead' }],
    past_projects: [
      { title: 'Commercial Analytics Modernization', tags: ['analytics', 'governance'], outcome: 'Established a commercial analytics governance model.' }
    ]
  }
];

const POLICY_VERSION = '2026-08-02.v1';

/* ── Engine port ──────────────────────────────────────────────────── */

function pursueStatus(missingCount, capacityGap, comparableCount) {
  if (missingCount || capacityGap) return 'NO-GO';
  if (comparableCount < 2) return 'REVIEW';
  return 'PURSUE';
}

function matchedProjects(tender, supplier) {
  const tags = new Set(tender.tags);
  return supplier.past_projects.filter((p) => p.tags.some((t) => tags.has(t)));
}

function proofCards(supplier, projects) {
  const cards = projects.slice(0, 2).map((p) => ({ label: p.title, kind: 'Past project', detail: p.outcome }));
  supplier.credentials.slice(0, 3 - cards.length).forEach((c) =>
    cards.push({ label: c, kind: 'Credential', detail: 'Available in the selected supplier profile' }));
  supplier.people.slice(0, 3 - cards.length).forEach((p) =>
    cards.push({ label: p.name, kind: 'Delivery lead', detail: p.role }));
  return cards.slice(0, 3);
}

function makePosition(title, tender, supplier, projects, criteria) {
  const cards = proofCards(supplier, projects);
  const target = criteria.slice(0, 2).map((c) => c.name);
  const proofNames = cards.slice(0, 2).map((c) => c.label).join(', ') || 'the selected delivery team';
  const statement = `Win ${title.toLowerCase()} with ${proofNames}: ${supplier.name} will deliver ${tender.promised_outcome}.`;
  let weakness = null;
  let mitigation = null;
  if (projects.length < 2) {
    weakness = 'Limited directly comparable delivery history';
    mitigation = 'Confirm an additional reference and assign an executive delivery reviewer before pursuing.';
  }
  return { title, statement, target_criteria: target, proof_cards: cards, weakness, mitigation };
}

function buildBlueprint(tender, supplier, position, projects) {
  const assets = projects.slice(0, 2).map((p) => p.title);
  const assetNames = assets.length ? assets : position.proof_cards.map((c) => c.label);
  return tender.evaluation_criteria
    .slice()
    .sort((a, b) => b.weight - a.weight)
    .map((criterion) => ({
      criterion: criterion.name,
      weight: criterion.weight,
      section: `${criterion.name} (${criterion.weight} points)`,
      claim: `${position.title}: ${supplier.name} will address ${criterion.name.toLowerCase()} through ${tender.promised_outcome}.`,
      assets: assetNames,
      owner: criterion.weight >= 30 ? 'Solution lead' : 'Bid manager'
    }));
}

function buildPursuitBrief(tender, supplier) {
  const held = new Set(supplier.credentials);
  const missing = tender.eligibility_requirements.filter((r) => !held.has(r)).sort();
  const capacityGap = Math.max(0, tender.delivery_hours - supplier.available_hours);
  const projects = matchedProjects(tender, supplier);
  const scoreMap = tender.evaluation_criteria.slice().sort((a, b) => b.weight - a.weight);

  const rotate = (n) => scoreMap.slice(n).concat(scoreMap.slice(0, n));
  const positions = [
    makePosition(scoreMap[0].name, tender, supplier, projects, rotate(0)),
    makePosition('Operational continuity', tender, supplier, projects, rotate(1)),
    makePosition(scoreMap[1].name, tender, supplier, projects, rotate(2))
  ];

  const status = pursueStatus(missing.length, capacityGap, projects.length);
  let nextActions;
  if (status === 'NO-GO') {
    nextActions = ['Do not generate a proposal.', 'Resolve eligibility or delivery capacity before reopening this opportunity.'];
  } else if (status === 'REVIEW') {
    nextActions = ['Validate the comparable-project gap.', 'Add a delivery reference before authoring a proposal.'];
  } else {
    nextActions = ['Select a Win Position.', 'Assign the proposal blueprint owners.'];
  }

  return {
    opportunity_id: tender.id,
    supplier_profile_id: supplier.id,
    status,
    buyer_objective: tender.buyer_objective,
    missing_eligibility: missing,
    capacity_gap_hours: capacityGap,
    matched_projects: projects,
    score_map: scoreMap,
    win_positions: positions,
    proposal_blueprint: buildBlueprint(tender, supplier, positions[0], projects),
    next_actions: nextActions,
    selected_position_index: 0,
    can_generate_proposal: status === 'PURSUE'
  };
}

function selectWinPosition(brief, tender, supplier, index) {
  const projects = matchedProjects(tender, supplier);
  return Object.assign({}, brief, {
    selected_position_index: index,
    proposal_blueprint: buildBlueprint(tender, supplier, brief.win_positions[index], projects)
  });
}

function strategyMarkdown(tender, supplier, brief) {
  const position = brief.win_positions[brief.selected_position_index];
  const proofList = position.proof_cards.map((c) => `- **${c.label}** — ${c.detail}`).join('\n');
  const sections = brief.proposal_blueprint
    .map((s) => `## ${s.section}\n\n${s.claim}\n\nDelivery assets: ${s.assets.join(', ')}.\n\nProposal owner: ${s.owner}.`)
    .join('\n\n');
  const outcome = tender.promised_outcome.charAt(0).toUpperCase() + tender.promised_outcome.slice(1);
  return `# ${tender.title}\n\n## Win Position\n\n${position.statement}\n\n## Buyer Objective\n\n${brief.buyer_objective}\n\n## Selected Delivery Assets\n\n${proofList}\n\n${sections}\n\n## Delivery Action\n\n${outcome} is delivered within the planned effort of ${tender.delivery_hours} hours.\n`;
}

/* Mirrors red_team_proposal: every score-bearing section must be present in the
   draft and connected to a selected supplier asset. */
function redTeam(brief, draft) {
  const checks = [];
  const findings = [];
  brief.proposal_blueprint.forEach((s) => {
    const hasSection = draft.indexOf(s.criterion) !== -1;
    const hasAsset = s.assets.some((a) => draft.indexOf(a) !== -1);
    checks.push({ text: `<b>${s.criterion}</b> section present in the draft`, ok: hasSection });
    checks.push({ text: `<b>${s.criterion}</b> connected to a selected supplier asset`, ok: hasAsset });
    if (!hasSection) findings.push(`Add an explicit ${s.criterion} section before review.`);
    if (!hasAsset) findings.push(`Connect ${s.criterion} to a selected supplier asset.`);
  });
  const position = brief.win_positions[brief.selected_position_index];
  if (position.weakness) findings.push(position.mitigation || position.weakness);
  return { checks, findings };
}

/* ── Readiness derivation (presentation rule, stated on screen) ────── */

function readinessFor(criterion, brief) {
  const position = brief.win_positions[brief.selected_position_index];
  const backed = brief.matched_projects.length > 0 && criterion.name !== 'Price';
  if (!backed) return { label: 'Input required', tone: 'warning' };
  if (position.target_criteria.indexOf(criterion.name) !== -1) return { label: 'Ready', tone: 'positive' };
  return { label: 'Partial', tone: 'informative' };
}

const BLUEPRINT_STATUS = {
  Ready: { label: 'Drafted', tone: 'positive' },
  Partial: { label: 'Drafted · review', tone: 'informative' },
  'Input required': { label: 'Awaiting input', tone: 'warning' }
};

/* ── Rendering helpers ────────────────────────────────────────────── */

const $ = (id) => document.getElementById(id);

function esc(value) {
  return String(value).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

function badge(label, tone, size) {
  const s = size || 'medium';
  return `<span class="seed-badge__root seed-badge__root--size_${s} seed-badge__root--variant_weak seed-badge__root--tone_${tone}-variant_weak"><span class="seed-badge__label">${esc(label)}</span></span>`;
}

function banner(variant, title, description) {
  return `<div class="seed-inline-banner__root seed-inline-banner__root--variant_${variant}" style="border-radius:var(--seed-radius-r2_5)">
    <div class="seed-inline-banner__content">
      <span class="seed-inline-banner__title seed-inline-banner__title--variant_${variant}">${esc(title)}</span>
      <span class="seed-inline-banner__description seed-inline-banner__description--variant_${variant}">${esc(description)}</span>
    </div>
  </div>`;
}

const STATUS_TONE = { PURSUE: 'positive', REVIEW: 'warning', 'NO-GO': 'critical' };
const STATUS_ACCENT = {
  PURSUE: 'var(--seed-color-bg-brand-solid)',
  REVIEW: 'var(--seed-color-palette-yellow-700)',
  'NO-GO': 'var(--seed-color-bg-critical-solid)'
};
const VERDICT_COLOR = {
  PURSUE: 'var(--seed-color-fg-brand-contrast)',
  REVIEW: 'var(--seed-color-fg-warning-contrast)',
  'NO-GO': 'var(--seed-color-fg-critical-contrast)'
};

/* ── State ────────────────────────────────────────────────────────── */

const params = new URLSearchParams(window.location.search);
const state = {
  tenderIndex: Number(params.get('tender') || 0),
  supplierIndex: Number(params.get('supplier') || 0),
  positionIndex: Number(params.get('position') || 0),
  view: params.get('view') || 'live'
};
const savedRuns = {};
let current = null;

function runKey(tender, supplier, brief) {
  return `${tender.id}:${supplier.id}:${brief.selected_position_index}:${tender.source_snapshot.sha256}`;
}

/* Deterministic identifiers so a replay shows the same persisted run. */
function runId(seed) {
  let h = 0x811c9dc5;
  for (let i = 0; i < seed.length; i += 1) { h ^= seed.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
  const hex = [];
  for (let i = 0; i < 8; i += 1) { h = Math.imul(h ^ (h >>> 13), 0x01000193) >>> 0; hex.push(h.toString(16).padStart(8, '0')); }
  const s = hex.join('').slice(0, 32);
  return `${s.slice(0, 8)}-${s.slice(8, 12)}-4${s.slice(13, 16)}-a${s.slice(17, 20)}-${s.slice(20, 32)}`;
}

/* ── Renderers ────────────────────────────────────────────────────── */

const EMPTY_DASH = '—';

function renderEmptyHeader() {
  ['factSource', 'factOpp', 'factCaptured', 'factSupplier', 'factDeadline', 'factValue'].forEach((id) => {
    $(id).textContent = EMPTY_DASH;
  });
  const hash = $('factHash');
  hash.textContent = EMPTY_DASH;
  hash.removeAttribute('title');
  $('mastEyebrow').textContent = 'No source snapshot';
  $('tenderTitle').textContent = 'No tender captured';
  $('tenderObjective').textContent = 'A buyer objective appears after a source snapshot is reviewed.';
  $('factNext').textContent = 'Capture a tender source';
  const b = $('mastStatusBadge');
  b.className = 'seed-badge__root seed-badge__root--size_large seed-badge__root--variant_weak seed-badge__root--tone_neutral-variant_weak';
  b.firstElementChild.textContent = 'NOT STARTED';
}

function renderHeader(tender, supplier, brief) {
  if (state.view === 'empty') { renderEmptyHeader(); return; }
  const snap = tender.source_snapshot;
  $('mastEyebrow').textContent = 'Captured tender · reviewed intake';
  $('factSource').textContent = snap.origin;
  $('factOpp').textContent = tender.id;
  const hash = $('factHash');
  hash.textContent = `${snap.sha256.slice(0, 12)}…${snap.sha256.slice(-6)}`;
  hash.title = `sha256 ${snap.sha256}`;
  $('factCaptured').textContent = `${snap.retrieved_at} · ${snap.pages} pages`;

  $('tenderTitle').textContent = tender.title;
  $('tenderObjective').textContent = tender.buyer_objective;
  $('factSupplier').textContent = `${supplier.name} · ${supplier.available_hours} h available`;
  $('factDeadline').textContent = tender.bid_close;
  $('factValue').textContent = tender.contract_value;
  const evaluating = state.view === 'loading';
  $('factNext').textContent = evaluating ? 'Evaluating against the supplier profile' : brief.next_actions[0];

  const b = $('mastStatusBadge');
  if (evaluating) {
    b.className = 'seed-badge__root seed-badge__root--size_large seed-badge__root--variant_weak seed-badge__root--tone_neutral-variant_weak';
    b.firstElementChild.textContent = 'EVALUATING';
  } else {
    b.className = `seed-badge__root seed-badge__root--size_large seed-badge__root--variant_solid seed-badge__root--tone_${STATUS_TONE[brief.status]}-variant_solid`;
    b.firstElementChild.textContent = brief.status;
  }
}

function renderDecision(tender, supplier, brief) {
  const plate = $('decisionPlate');
  plate.style.setProperty('--bp-plate-accent', STATUS_ACCENT[brief.status]);
  const verdict = $('verdictWord');
  verdict.textContent = brief.status;
  verdict.parentElement.style.color = VERDICT_COLOR[brief.status];

  const missing = brief.missing_eligibility;
  let because;
  if (brief.status === 'PURSUE') {
    because = `Every eligibility requirement is held, delivery capacity covers the tender, and ${brief.matched_projects.length} comparable public-sector deliveries are on the supplier profile.`;
  } else if (brief.status === 'REVIEW') {
    because = `Eligibility and capacity gates pass, but only ${brief.matched_projects.length} comparable delivery matches the tender scope. The policy threshold is 2.`;
  } else {
    const reasons = [];
    if (missing.length) reasons.push(`missing eligibility: ${missing.join(', ')}`);
    if (brief.capacity_gap_hours) reasons.push(`delivery capacity ${brief.capacity_gap_hours} h short`);
    because = `A non-negotiable gate failed — ${reasons.join('; ')}. Proposal generation stays closed.`;
  }
  $('verdictBecause').textContent = because;

  $('verdictActions').innerHTML = brief.next_actions.map((a) => `<li>${esc(a)}</li>`).join('');

  const btn = $('buildBtn');
  btn.disabled = !brief.can_generate_proposal;
  const gate = $('buildGate');
  if (brief.can_generate_proposal) {
    gate.className = 'bp-plate__gate';
    gate.textContent = `Writing gate OPEN · policy ${POLICY_VERSION} · selected position: ${brief.win_positions[brief.selected_position_index].title}`;
  } else {
    gate.className = 'bp-plate__gate bp-plate__gate--blocked';
    gate.textContent = `Writing gate LOCKED · proposal generation is blocked for ${brief.status} opportunities.`;
  }
}

function renderDimensions(tender, supplier, brief) {
  const eligibilityHeld = tender.eligibility_requirements.length - brief.missing_eligibility.length;
  const nonPrice = tender.evaluation_criteria.filter((c) => c.name !== 'Price').reduce((s, c) => s + c.weight, 0);
  const priceWeight = 100 - nonPrice;

  const dims = [
    {
      name: 'Eligibility',
      value: brief.missing_eligibility.length ? 'Not met' : 'Met',
      tone: brief.missing_eligibility.length ? 'critical' : 'positive',
      flag: brief.missing_eligibility.length ? 'FAIL' : 'PASS',
      evidence: brief.missing_eligibility.length
        ? `Missing ${brief.missing_eligibility.join(', ')}.`
        : `${eligibilityHeld} of ${tender.eligibility_requirements.length} declared requirements held on the supplier profile.`,
      rule: 'Gate — every declared requirement must be held'
    },
    {
      name: 'Delivery capacity',
      value: brief.capacity_gap_hours ? `${brief.capacity_gap_hours} h short` : `${supplier.available_hours - tender.delivery_hours} h headroom`,
      tone: brief.capacity_gap_hours ? 'critical' : 'positive',
      flag: brief.capacity_gap_hours ? 'FAIL' : 'PASS',
      evidence: `${supplier.available_hours} h available against ${tender.delivery_hours} h of planned delivery effort.`,
      rule: 'Gate — available hours must cover delivery effort'
    },
    {
      name: 'Commercial fit',
      value: `${nonPrice} of 100`,
      tone: 'positive',
      flag: 'FAVOURABLE',
      evidence: `${nonPrice} points are awarded on non-price criteria; price carries ${priceWeight}. The evaluation rewards delivery credibility over unit rate.`,
      rule: 'Signal — from the published evaluation weights'
    },
    {
      name: 'Evidence strength',
      value: `${brief.matched_projects.length} comparable`,
      tone: brief.matched_projects.length >= 2 ? 'positive' : 'warning',
      flag: brief.matched_projects.length >= 2 ? 'PASS' : 'REVIEW',
      evidence: brief.matched_projects.length
        ? `Tag overlap with ${brief.matched_projects.map((p) => p.title).join(' and ')}.`
        : 'No profile project overlaps the tender scope tags.',
      rule: 'Gate — 2 comparable deliveries required for PURSUE'
    }
  ];

  $('dimensions').innerHTML = dims.map((d) => `
    <article class="bp-dim">
      <div class="bp-dim__top">
        <h3 class="bp-dim__name">${esc(d.name)}</h3>
        ${badge(d.flag, d.tone)}
      </div>
      <p class="bp-dim__value" style="color:var(--seed-color-fg-${d.tone}-contrast)">${esc(d.value)}</p>
      <p class="bp-dim__evidence">${esc(d.evidence)}</p>
      <p class="bp-dim__rule">${esc(d.rule)}</p>
    </article>`).join('');
}

function renderPositions(brief) {
  $('positions').innerHTML = brief.win_positions.map((p, i) => `
    <button type="button" class="bp-option" role="radio" aria-checked="${i === brief.selected_position_index}" data-position="${i}" tabindex="${i === brief.selected_position_index ? 0 : -1}">
      <span class="bp-option__mark" aria-hidden="true"></span>
      <span class="bp-option__title">${esc(p.title)}<span class="bp-option__targets">targets ${esc(p.target_criteria.join(' · '))}</span></span>
      <span class="bp-option__statement">${esc(p.statement)}</span>
    </button>`).join('');

  const position = brief.win_positions[brief.selected_position_index];
  const weaknessOpen = Boolean(position.weakness);
  const weakness = position.weakness || 'Not raised by the pursuit engine for this position. The comparable-delivery threshold is met with 2 matched deliveries.';
  const mitigation = position.mitigation || 'Standing control — the red-team pass below re-checks every score-bearing section against the selected assets.';

  $('positionDetail').innerHTML = `
    <div class="bp-reveal__head">
      <h3 class="bp-reveal__title">Proof behind “${esc(position.title)}”</h3>
      <p class="bp-panel__note">${position.proof_cards.length} selected delivery assets</p>
    </div>
    <div class="bp-proofs">
      ${position.proof_cards.map((c) => `
        <article class="bp-proof">
          <p class="bp-proof__kind">${esc(c.kind)}</p>
          <h4 class="bp-proof__label">${esc(c.label)}</h4>
          <p class="bp-proof__detail">${esc(c.detail)}</p>
        </article>`).join('')}
    </div>
    <div class="bp-risk${weaknessOpen ? ' bp-risk--open' : ''}">
      <div class="bp-risk__row"><span class="bp-risk__key">Weakness</span><span class="bp-risk__val">${esc(weakness)}</span></div>
      <div class="bp-risk__row"><span class="bp-risk__key">Mitigation</span><span class="bp-risk__val">${esc(mitigation)}</span></div>
    </div>`;
}

function renderScoreMap(brief) {
  const position = brief.win_positions[brief.selected_position_index];
  const prefix = `${position.title}: `;
  const blueprintByCriterion = {};
  brief.proposal_blueprint.forEach((s) => { blueprintByCriterion[s.criterion] = s; });

  $('scoreBound').innerHTML = `Every claim below is bound to <b>${esc(position.title)}</b>`;

  $('scoreBody').innerHTML = brief.score_map.map((c) => {
    const r = readinessFor(c, brief);
    const section = blueprintByCriterion[c.name];
    const claim = section ? section.claim.replace(prefix, '') : '';
    return `<tr>
      <td data-label="Criterion" class="bp-criterion">${esc(c.name)}</td>
      <td data-label="Weight" class="bp-num">${c.weight}</td>
      <td data-label="Readiness">${badge(r.label, r.tone)}</td>
      <td data-label="Proposal claim" class="bp-claim">${esc(claim)}</td>
    </tr>`;
  }).join('');
}

function renderBlueprint(brief) {
  const position = brief.win_positions[brief.selected_position_index];
  const prefix = `${position.title}: `;
  $('blueprintNote').innerHTML = `${brief.proposal_blueprint.length} sections bound to <b>${esc(position.title)}</b>`;
  $('blueprintBody').innerHTML = brief.proposal_blueprint.map((s) => {
    const readiness = readinessFor({ name: s.criterion }, brief);
    const status = BLUEPRINT_STATUS[readiness.label];
    return `<tr>
      <td data-label="Criterion" class="bp-criterion">${esc(s.criterion)}</td>
      <td data-label="Section">${esc(s.section)}</td>
      <td data-label="Claim" class="bp-claim">${esc(s.claim.replace(prefix, ''))}</td>
      <td data-label="Supplier asset" class="bp-claim">${esc(s.assets.join(', '))}</td>
      <td data-label="Owner">${esc(s.owner)}</td>
      <td data-label="Status">${badge(status.label, status.tone)}</td>
    </tr>`;
  }).join('');
}

function markdownToHtml(md) {
  return md.split('\n\n').map((block) => {
    const b = block.trim();
    if (!b) return '';
    if (b.startsWith('# ')) return `<h3>${esc(b.slice(2))}</h3>`;
    if (b.startsWith('## ')) return `<h4>${esc(b.slice(3))}</h4>`;
    if (b.startsWith('- ')) {
      return `<ul>${b.split('\n').map((line) => `<li>${esc(line.replace(/^-\s*/, '')).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')}</li>`).join('')}</ul>`;
    }
    return `<p>${esc(b).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')}</p>`;
  }).join('');
}

function renderOutputs(tender, supplier, brief) {
  const blocked = !brief.can_generate_proposal;
  const draftEl = $('draftPreview');
  const downloadBtn = $('downloadBtn');

  if (blocked) {
    draftEl.innerHTML = banner(
      'criticalWeak',
      'No draft exists.',
      `write_strategy_proposal refuses ${brief.status} opportunities. Resolve the failed gate, then rebuild from the selected strategy.`
    );
    downloadBtn.disabled = true;
    current.draft = '';
    $('draftNote').textContent = '';
    $('redteam').innerHTML = banner('neutralWeak', 'Red team not run.', 'The red-team pass reviews a generated draft. Nothing has been generated for this opportunity.');
    return;
  }

  const draft = strategyMarkdown(tender, supplier, brief);
  current.draft = draft;
  draftEl.innerHTML = markdownToHtml(draft);
  downloadBtn.disabled = false;
  $('draftNote').textContent = `Preview scrolls. The draft carries ${brief.proposal_blueprint.length} score-bearing sections plus the Win Position, buyer objective, selected assets, and delivery action.`;

  const review = redTeam(brief, draft);
  const passed = review.checks.filter((c) => c.ok).length;
  const findingsHtml = review.findings.length
    ? `<div class="bp-findings">${review.findings.map((f) => banner('warningWeak', 'Finding', f)).join('')}</div>`
    : `<div class="bp-findings">${banner('positiveWeak', `0 blocking findings.`, `${passed} of ${review.checks.length} score-bearing checks passed. Every criterion has a section and a selected supplier asset.`)}</div>`;

  $('redteam').innerHTML = findingsHtml + `<div class="bp-checks">${review.checks.map((c) => `
    <div class="bp-check">
      <p class="bp-check__text">${c.text}</p>
      ${badge(c.ok ? 'PASS' : 'FAIL', c.ok ? 'positive' : 'critical')}
    </div>`).join('')}</div>`;
}

function renderRun(tender, supplier, brief) {
  const key = runKey(tender, supplier, brief);
  const saved = savedRuns[key];
  const body = $('runBody');
  $('replayBtn').disabled = !saved;

  if (!saved) {
    body.innerHTML = banner(
      'neutralWeak',
      'No saved run for this input.',
      brief.can_generate_proposal
        ? 'Build the proposal from the selected strategy to persist a versioned Bid Room run.'
        : `Runs are only persisted for PURSUE opportunities. This opportunity is ${brief.status}.`
    );
    return;
  }

  body.innerHTML = `
    <div class="bp-run__grid">
      <dl class="bp-run__facts">
        <div class="bp-fact"><dt>Run ID</dt><dd>${esc(saved.run_id)}</dd></div>
        <div class="bp-fact"><dt>Opportunity version</dt><dd class="bp-hash" title="sha256 ${esc(saved.opportunity_version)}">${esc(saved.opportunity_version.slice(0, 12))}…${esc(saved.opportunity_version.slice(-6))}</dd></div>
        <div class="bp-fact"><dt>Selected position</dt><dd>${esc(saved.selected_position_title)}</dd></div>
        <div class="bp-fact"><dt>Saved</dt><dd>${esc(saved.created_at)}</dd></div>
        <div class="bp-fact"><dt>Agent trace</dt><dd>${esc(saved.agent_run.provider)} · ${esc(saved.agent_run.state)}</dd></div>
        <div class="bp-fact"><dt>Recorded steps</dt><dd>${esc(saved.agent_run.steps.join(' → '))}</dd></div>
      </dl>
      <div>
        <p class="bp-eyebrow" style="margin-bottom:var(--seed-dimension-x3)">Pursuit tasks · ${saved.tasks.length} open</p>
        <div class="bp-tasks">
          ${saved.tasks.map((t) => `
            <article class="bp-task">
              <h3 class="bp-task__name">${esc(t.task)}</h3>
              <p class="bp-task__owner">${esc(t.owner)}</p>
              ${badge(t.status, 'informative')}
            </article>`).join('')}
        </div>
      </div>
    </div>`;
}

/* ── Compose ──────────────────────────────────────────────────────── */

function render() {
  const tender = TENDERS[state.tenderIndex];
  const supplier = SUPPLIERS[state.supplierIndex];
  let brief = buildPursuitBrief(tender, supplier);
  const index = Math.min(state.positionIndex, brief.win_positions.length - 1);
  brief = selectWinPosition(brief, tender, supplier, index);
  current = { tender, supplier, brief, draft: '' };

  $('liveState').hidden = state.view !== 'live';
  $('loadingState').hidden = state.view !== 'loading';
  $('emptyState').hidden = state.view !== 'empty';

  renderHeader(tender, supplier, brief);
  if (state.view !== 'live') return;

  renderDecision(tender, supplier, brief);
  renderDimensions(tender, supplier, brief);
  renderPositions(brief);
  renderScoreMap(brief);
  renderBlueprint(brief);
  renderOutputs(tender, supplier, brief);
  renderRun(tender, supplier, brief);
}

function persistRun() {
  const { tender, supplier, brief, draft } = current;
  if (!brief.can_generate_proposal) return;
  const key = runKey(tender, supplier, brief);
  savedRuns[key] = {
    run_id: runId(key),
    opportunity_version: tender.source_snapshot.sha256,
    selected_position_title: brief.win_positions[brief.selected_position_index].title,
    created_at: '2026-08-02 09:41 KST',
    proposal_markdown: draft,
    tasks: brief.proposal_blueprint.map((s) => ({ task: `Develop ${s.criterion} response`, owner: s.owner, status: 'OPEN' })),
    agent_run: {
      provider: 'local-development-adapter',
      state: 'not-executed-in-snowflake-or-coco',
      steps: ['pursuit', 'strategy', 'proposal', 'red-team', 'task-plan']
    }
  };
  renderRun(tender, supplier, brief);
}

/* ── Wiring ───────────────────────────────────────────────────────── */

function initSelects() {
  const t = $('tenderSelect');
  t.innerHTML = TENDERS.map((x, i) => `<option value="${i}">${esc(x.title)}</option>`).join('');
  t.value = String(state.tenderIndex);
  t.addEventListener('change', (e) => { state.tenderIndex = Number(e.target.value); state.positionIndex = 0; render(); });

  const s = $('supplierSelect');
  s.innerHTML = SUPPLIERS.map((x, i) => `<option value="${i}">${esc(x.name)}</option>`).join('');
  s.value = String(state.supplierIndex);
  s.addEventListener('change', (e) => { state.supplierIndex = Number(e.target.value); state.positionIndex = 0; render(); });
}

function initViewSwitch() {
  const root = $('viewSwitch');
  const items = Array.prototype.slice.call(root.querySelectorAll('[data-view]'));
  const apply = (view) => {
    state.view = view;
    items.forEach((item, i) => {
      const on = item.dataset.view === view;
      item.setAttribute('aria-checked', String(on));
      if (on) { item.setAttribute('data-checked', ''); $('viewIndicator').style.setProperty('--segment-index', i); }
      else item.removeAttribute('data-checked');
      item.tabIndex = on ? 0 : -1;
    });
    render();
  };
  items.forEach((item, i) => {
    item.addEventListener('click', () => apply(item.dataset.view));
    item.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault();
      const next = items[(i + (e.key === 'ArrowRight' ? 1 : items.length - 1)) % items.length];
      apply(next.dataset.view);
      next.focus();
    });
  });
  if (state.view !== 'live') apply(state.view);
}

function initPositionChoice() {
  const list = $('positions');
  list.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-position]');
    if (!btn) return;
    state.positionIndex = Number(btn.dataset.position);
    render();
    const focused = list.querySelector('[aria-checked="true"]');
    if (focused) focused.focus();
  });
  list.addEventListener('keydown', (e) => {
    if (['ArrowDown', 'ArrowUp', 'ArrowRight', 'ArrowLeft'].indexOf(e.key) === -1) return;
    e.preventDefault();
    const total = current.brief.win_positions.length;
    const step = (e.key === 'ArrowDown' || e.key === 'ArrowRight') ? 1 : total - 1;
    state.positionIndex = (state.positionIndex + step) % total;
    render();
    const focused = list.querySelector('[aria-checked="true"]');
    if (focused) focused.focus();
  });
}

function initActions() {
  $('buildBtn').addEventListener('click', persistRun);

  $('replayBtn').addEventListener('click', () => {
    const { tender, supplier, brief } = current;
    renderRun(tender, supplier, brief);
    $('runBody').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });

  $('downloadBtn').addEventListener('click', () => {
    if (!current.draft) return;
    const blob = new Blob([current.draft], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'bidpilot-strategy-proposal.md';
    a.click();
    URL.revokeObjectURL(a.href);
  });
}

initSelects();
initViewSwitch();
initPositionChoice();
initActions();
render();
/* Seed the persisted run so the saved Bid Room is visible on first load. */
persistRun();
