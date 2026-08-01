/* BidPilot — Bid Room reference screen behaviour.
   All values below mirror what the pursuit policy, the strategy writer, and the
   bid-room store actually produce for this tender/supplier pairing. */

(() => {
  'use strict';

  const TENDER = {
    id: 'G2B-REPLAY-DATA-QUALITY',
    title: 'Public data quality and API continuity service',
    promisedOutcome: 'a measured data-quality improvement and a maintained api operating model',
    deliveryHours: 720,
    version: 'fixture:G2B-REPLAY-DATA-QUALITY:v1'
  };
  const SUPPLIER = { name: 'Northstar Systems', id: 'supplier-northstar', hours: 900 };

  const PROOFS = [
    ['Past project', 'City Open Data Reliability Program', 'Reduced recurring data defects and introduced API change control.'],
    ['Past project', 'Citizen API Service Transition', 'Transferred API support without a public-service interruption.'],
    ['Credential', 'SME confirmation', 'Available in the selected supplier profile']
  ];

  // Blueprint rows are position-independent except for the claim prefix,
  // which is the selected Win Position title.
  const BLUEPRINT = [
    { criterion: 'Technical approach', weight: 40, evidence: 'Reduced recurring data defects and introduced API change control.', assets: ['City Open Data Reliability Program', 'Citizen API Service Transition'], owner: 'Solution lead' },
    { criterion: 'Comparable delivery', weight: 30, evidence: '2 comparable delivery record(s)', assets: ['City Open Data Reliability Program', 'Citizen API Service Transition'], owner: 'Solution lead' },
    { criterion: 'Delivery team', weight: 20, evidence: 'the named Public data delivery lead', assets: ['Mina Lee', 'Jun Park'], owner: 'Bid manager' },
    { criterion: 'Price', weight: 10, evidence: 'a delivery envelope backed by 900 available hours', assets: ['900 available hours'], owner: 'Bid manager' }
  ];

  const PROOF_NAMES = PROOFS.slice(0, 2).map(p => p[1]).join(', ');

  const POSITIONS = [
    { title: 'Technical approach', targets: ['Technical approach', 'Comparable delivery'],
      savedRun: { id: '7c41e2b9-3d0a-4f61-9b52-8e07a1c4d6f2', saved: 'Saved from this bid room', sections: 14, findings: 0, tasks: 4 } },
    { title: 'Operational continuity', targets: ['Comparable delivery', 'Delivery team'], savedRun: null },
    { title: 'Delivery team', targets: ['Delivery team', 'Price'], savedRun: null }
  ].map(p => ({
    ...p,
    statement: `Win ${p.title.toLowerCase()} with ${PROOF_NAMES}: ${SUPPLIER.name} will deliver ${TENDER.promisedOutcome}.`
  }));

  const STAGES = [
    { name: 'Intake', state: 'Complete' },
    { name: 'Qualify', state: 'Complete' },
    { name: 'Position', state: 'Active' },
    { name: 'Draft', state: 'Complete' },
    { name: 'Review', state: 'Complete' },
    { name: 'Assign', state: 'Pending' }
  ];

  const $ = sel => document.querySelector(sel);
  const $$ = sel => Array.from(document.querySelectorAll(sel));

  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  /* ───────── draft markdown, written the way the strategy writer writes it ───────── */

  function weightedDetail(weight) {
    if (weight >= 30) {
      return 'Approach: define the baseline, execute the selected delivery pattern, and assign acceptance ownership.\n\n' +
        'Validation: agree measurable acceptance checks with the buyer and record the result in the Bid Room.\n\n' +
        'Buyer outcome: A measured data-quality improvement and a maintained api operating model.';
    }
    if (weight >= 20) return 'Approach: name the accountable owner, delivery inputs, and acceptance checkpoint for this response.';
    return 'Approach: confirm the required input and reconcile it with the final submission before approval.';
  }

  function claimFor(row, position) {
    return `${position.title}: ${SUPPLIER.name} will address ${row.criterion.toLowerCase()} through ${row.evidence}. ` +
      `This ${row.weight}-point response targets ${TENDER.promisedOutcome}.`;
  }

  function draftMarkdown(position) {
    const proofList = PROOFS.map(([, label, detail]) => `- **${label}** — ${detail}`).join('\n');
    const sections = BLUEPRINT.map(row =>
      `## ${row.criterion} (${row.weight} points)\n\n` +
      `Response priority: ${row.weight >= 30 ? 'lead response' : 'supporting response'} at ${row.weight}% of the evaluation.\n\n` +
      `${claimFor(row, position)}\n\n` +
      `Delivery assets: ${row.assets.join(', ')}.\n\n` +
      `${weightedDetail(row.weight)}\n\n` +
      `Proposal owner: ${row.owner}.`
    ).join('\n\n');

    return `# ${TENDER.title}

## Executive Summary

${SUPPLIER.name} will pursue the buyer objective through the selected Win Position: ${position.statement} The response prioritizes the highest-weighted criteria and assigns each claim to an accountable proposal owner.

## Understanding of the Requirement

The buyer needs improve public-data reliability while keeping citizen-facing apis stable. The proposed response must address the weighted evaluation matrix while remaining deliverable within ${TENDER.deliveryHours} planned hours.

## Win Position

${position.statement}

## Buyer Objective

Improve public-data reliability while keeping citizen-facing APIs stable.

## Selected Delivery Assets

${proofList}

${sections}

## Implementation Plan

1. Confirm the evaluation response plan and evidence owners.
2. Develop the highest-weighted response first and attach the selected delivery assets.
3. Validate delivery capacity, operating handoff, and criterion coverage before red-team review.

## Team and Governance

The proposal owners named in the blueprint coordinate the response. Delivery evidence is anchored in ${PROOFS.map(p => p[1]).join(', ')} and the selected supplier profile has ${SUPPLIER.hours} available hours.

## Risk and Mitigation

The current pursuit policy found no blocking eligibility or capacity gap.

Mitigation: Keep criterion owners and delivery assets traceable through the saved Bid Room run.

## Commercial Response

The commercial response will be completed against the Price criterion and reconciled with the planned ${TENDER.deliveryHours} delivery hours before submission.

## Delivery Action

${TENDER.promisedOutcome.charAt(0).toUpperCase() + TENDER.promisedOutcome.slice(1)} is delivered within the planned effort of ${TENDER.deliveryHours} hours.
`;
  }

  function renderMarkdown(md) {
    // Collapse the blank lines the writer emits so <pre> spacing comes from
    // real margins rather than stacked newlines.
    return md.split('\n')
      .filter(line => line.trim() !== '')
      .map(line => {
        if (/^#\s/.test(line)) return `<span class="bp-md-h bp-md-h1">${esc(line.slice(2))}</span>`;
        if (/^##\s/.test(line)) return `<span class="bp-md-h">${esc(line.slice(3))}</span>`;
        return `<span class="bp-md-p">${esc(line).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')}</span>`;
      }).join('');
  }

  /* ───────── state ───────── */

  let selected = 0;

  function render() {
    const pos = POSITIONS[selected];

    // strip + statement
    $('#tilePosition').textContent = pos.title;
    $('#tilePositionSub').textContent = 'Targets ' + pos.targets.join(' · ');
    $('#posStatement').textContent = pos.statement;
    $('#traceStrategy').textContent = 'Win Position bound: ' + pos.title;

    // choices
    $$('#positionGroup .bp-choice').forEach((btn, i) => {
      const on = i === selected;
      btn.setAttribute('aria-checked', String(on));
      btn.tabIndex = on ? 0 : -1;
    });

    // score map coverage
    $$('#scoreMap .bp-score__row').forEach(row => {
      const covered = pos.targets.includes(row.dataset.crit);
      row.toggleAttribute('data-covered', covered);
      row.querySelector('[data-cov]').textContent = covered
        ? 'Targeted by selected position'
        : 'Answered in blueprint only';
    });

    // blueprint
    $('#blueprintTable tbody').innerHTML = BLUEPRINT.map(row => `
      <tr>
        <td class="bp-td-crit" data-label="Criterion">${esc(row.criterion)}</td>
        <td class="bp-num bp-td-w" data-label="Weight">${row.weight}</td>
        <td class="bp-td-claim" data-label="Claim"><b>${esc(pos.title)}:</b> ${esc(claimFor(row, pos).slice(pos.title.length + 2))}</td>
        <td class="bp-td-assets" data-label="Delivery assets">${row.assets.map(esc).join('<br>')}</td>
        <td class="bp-td-owner" data-label="Owner">${esc(row.owner)}</td>
      </tr>`).join('');

    // draft
    const md = draftMarkdown(pos);
    $('#draftBody').innerHTML = renderMarkdown(md);
    const headings = (md.match(/^##\s/gm) || []).length;
    $('#draftBadge').textContent = headings + ' sections';
    $('#draftLen').textContent = md.length.toLocaleString('en-US') + ' characters · read-only preview';

    renderContinuity(pos);
    renderSavedRun(pos);
    renderPrimary(pos);
  }

  /* A run is keyed by its selected position statement. When no run matches, the
     downstream stages have not happened for this position — say so everywhere
     instead of leaving the previous run's numbers on screen. */
  function renderContinuity(pos) {
    const built = Boolean(pos.savedRun);

    $('#tileDraft').innerHTML = built
      ? '4 / 4 <span class="bp-tile__u">criterion sections</span>'
      : '<span class="bp-tile__none">Not built</span>';
    $('#tileDraftSub').textContent = built
      ? 'Strategy-led draft written from the selected position'
      : 'No draft persisted for this Win Position';

    $('#tileFindings').innerHTML = built
      ? '0 <span class="bp-tile__u">open</span>'
      : '<span class="bp-tile__none">Not reviewed</span>';
    $('#tileFindingsSub').textContent = built
      ? '4 score-bearing checks passed'
      : 'Red-team runs against a built draft';

    $('#tileTasks').innerHTML = built
      ? '4 <span class="bp-tile__u">open</span>'
      : '<span class="bp-tile__none">Not assigned</span>';
    $('#tileTasksSub').textContent = built
      ? 'Solution lead 2 · Bid manager 2'
      : 'Tasks are created with the run';

    const railText = {
      3: built ? ['Complete', ' · 4 of 4 sections'] : ['Pending', ' · not built for this position'],
      4: built ? ['Complete', ' · 0 open findings'] : ['Pending', ' · needs a draft'],
      5: built ? ['Pending', ' · 4 owned tasks open'] : ['Pending', ' · no tasks yet']
    };
    Object.keys(railText).forEach(k => {
      const btn = $(`#stageList [data-stage="${k}"]`);
      const li = btn.closest('.bp-stage');
      const complete = railText[k][0] === 'Complete';
      li.dataset.state = complete ? 'complete' : 'pending';
      btn.querySelector('use').setAttribute('href', complete ? '#i-check' : '#i-hollow');
      btn.querySelector('.bp-stage__sw').textContent = railText[k][0];
      btn.querySelector('.bp-stage__sd').textContent = railText[k][1];
      STAGES[k].state = railText[k][0];
    });
    syncStage(false);

    const trace = {
      proposal: built ? 'Strategy-led markdown written for 4 weighted criteria' : 'Not run for this Win Position',
      'red-team': built ? '4 score-bearing sections reviewed, 0 findings' : 'Not run for this Win Position',
      'task-plan': built ? '4 criterion tasks created and owned' : 'Not run for this Win Position'
    };
    Object.keys(trace).forEach(k => {
      const li = $(`.bp-trace__step[data-step="${k}"]`);
      li.querySelector('.bp-trace__v').textContent = trace[k];
      li.toggleAttribute('data-pending', !built);
    });

    $('#tasksHost').hidden = !built;
    let none = $('#tasksNone');
    if (!built && !none) {
      none = document.createElement('p');
      none.id = 'tasksNone';
      none.className = 'bp-spec__v';
      $('#panel-tasks').appendChild(none);
    }
    if (none) {
      none.hidden = built;
      none.textContent = 'No tasks yet. Task ownership is written with the run, so it appears once a proposal is built from this Win Position.';
    }

    $('#draftFile').textContent = built
      ? 'bidpilot-strategy-proposal.md'
      : 'bidpilot-strategy-proposal.md · preview, not persisted';

    $('#sumComplete').textContent = built
      ? 'Intake, Qualify, Draft, Review — 4 of 6'
      : 'Intake, Qualify — 2 of 6';
    $('#sumActive').textContent = `Position — ${selected + 1} of 3 selected`;
    $('#sumPending').textContent = built
      ? 'Assign — 4 owned tasks still open'
      : 'Draft, Review, Assign — not run for this position';
  }

  function renderSavedRun(pos) {
    const host = $('#savedRun');
    if (pos.savedRun) {
      const r = pos.savedRun;
      host.innerHTML = `
        <div class="bp-saved">
          <div class="seed-badge__root seed-badge__root--size_medium seed-badge__root--variant_weak seed-badge__root--tone_positive"><span class="seed-badge__label">Run matched</span></div>
          <p class="bp-saved__id">${esc(r.id)}</p>
          <dl class="bp-saved__meta">
            <div class="bp-saved__row bp-saved__row--wide"><dt>Opportunity version</dt><dd>${esc(TENDER.version)}</dd></div>
            <div class="bp-saved__row bp-saved__row--wide"><dt>Selected position</dt><dd>${esc(pos.title)}</dd></div>
            <div class="bp-saved__row"><dt>Draft sections</dt><dd>${r.sections}</dd></div>
            <div class="bp-saved__row"><dt>Red-team findings</dt><dd>${r.findings}</dd></div>
            <div class="bp-saved__row"><dt>Owned tasks</dt><dd>${r.tasks}</dd></div>
          </dl>
          <button type="button" data-replay class="seed-action-button seed-action-button--variant_neutralOutline seed-action-button--size_small seed-action-button--size_small-layout_withText">
            <svg class="bp-i" viewBox="0 0 18 18" aria-hidden="true"><use href="#i-replay"/></svg>
            Replay this run
          </button>
          <p class="bp-footnote">The store matches a saved run on opportunity, supplier, version, and the selected position statement.</p>
        </div>`;
    } else {
      host.innerHTML = `
        <div class="bp-saved__none">
          <svg class="bp-i" viewBox="0 0 18 18" aria-hidden="true"><use href="#i-archive"/></svg>
          <p class="bp-spec__k">No saved run for this Win Position</p>
          <p class="bp-spec__v">A run is keyed by its selected position statement, so “${esc(pos.title)}” has nothing persisted yet. Build the proposal to create one.</p>
          <button type="button" class="seed-action-button seed-action-button--variant_brandOutline seed-action-button--size_small seed-action-button--size_small-layout_withText" data-primary>
            <span data-primary-label>Build proposal from selected strategy</span>
          </button>
        </div>`;
      bindPrimary();
    }
  }

  function renderPrimary(pos) {
    const matched = Boolean(pos.savedRun);
    $('#dockLabel').textContent = pos.title;
    $('#dockState').textContent = matched ? 'Saved run matched' : 'No saved run yet';
    $$('[data-primary-label]').forEach(el => {
      const compact = el.closest('.bp-dock');
      if (compact) el.textContent = matched ? 'Rebuild proposal' : 'Build proposal';
      else el.textContent = matched ? 'Rebuild proposal from selected strategy' : 'Build proposal from selected strategy';
    });

    const top = $('#replayTop');
    top.disabled = !matched;
    top.title = matched ? '' : 'No saved run matches the selected Win Position';
    $('#replayStatus').textContent = '';
    bindReplay();
  }

  function replay() {
    const pos = POSITIONS[selected];
    if (!pos.savedRun) return;
    $('#replayStatus').textContent =
      `Replaying saved run ${pos.savedRun.id} — ${pos.title}, opportunity ${TENDER.version}.`;
    $('#h-saved').scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function bindReplay() {
    $$('[data-replay], #replayTop').forEach(btn => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', replay);
    });
  }

  /* ───────── win position keyboard control ───────── */

  const choices = $$('#positionGroup .bp-choice');
  choices.forEach((btn, i) => {
    btn.addEventListener('click', () => { selected = i; render(); btn.focus(); });
    btn.addEventListener('keydown', e => {
      const keys = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
      if (keys[e.key]) {
        e.preventDefault();
        selected = (i + keys[e.key] + choices.length) % choices.length;
        render();
        choices[selected].focus();
      } else if (e.key === 'Home' || e.key === 'End') {
        e.preventDefault();
        selected = e.key === 'Home' ? 0 : choices.length - 1;
        render();
        choices[selected].focus();
      }
    });
  });

  /* ───────── stage navigator ───────── */

  let stage = 2;

  function syncStage(scroll) {
    const s = STAGES[stage];
    $('#railcIndex').textContent = `Stage ${stage + 1} of ${STAGES.length}`;
    $('#railcState').textContent = s.state;
    $('#railcName').textContent = s.name;
    $('#railcFill').style.width = ((stage + 1) / STAGES.length * 100) + '%';
    if (scroll) {
      const btn = $$('#stageList .bp-stage__btn')[stage];
      const target = btn && document.getElementById(btn.dataset.target);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  $$('#stageList .bp-stage__btn').forEach(btn => {
    btn.addEventListener('click', () => { stage = Number(btn.dataset.stage); syncStage(true); });
    btn.addEventListener('keydown', e => {
      const d = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
      if (!d) return;
      e.preventDefault();
      const list = $$('#stageList .bp-stage__btn');
      const next = (Number(btn.dataset.stage) + d + list.length) % list.length;
      list[next].focus();
      stage = next;
      syncStage(false);
    });
  });

  $('#stagePrev').addEventListener('click', () => { stage = Math.max(0, stage - 1); syncStage(true); });
  $('#stageNext').addEventListener('click', () => { stage = Math.min(STAGES.length - 1, stage + 1); syncStage(true); });

  /* ───────── companion segmented control ───────── */

  const segs = $$('#asideSeg .seed-segmented-control__item');
  function setSeg(i, focus) {
    segs.forEach((b, j) => {
      const on = i === j;
      b.setAttribute('aria-selected', String(on));
      b.tabIndex = on ? 0 : -1;
      b.toggleAttribute('data-checked', on);
      document.getElementById(b.getAttribute('aria-controls')).hidden = !on;
    });
    $('#asideSeg').style.setProperty('--segment-index', i);
    if (focus) segs[i].focus();
  }
  segs.forEach((b, i) => {
    b.addEventListener('click', () => setSeg(i, false));
    b.addEventListener('keydown', e => {
      const d = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
      if (!d) return;
      e.preventDefault();
      setSeg((i + d + segs.length) % segs.length, true);
    });
  });

  /* ───────── state specimens ───────── */

  const item = (icon, k, v) => `
    <div class="bp-spec__item">
      <svg class="bp-i" viewBox="0 0 18 18" aria-hidden="true"><use href="#${icon}"/></svg>
      <div><p class="bp-spec__k">${k}</p><p class="bp-spec__v">${v}</p></div>
    </div>`;

  const badge = (tone, label) =>
    `<span class="seed-badge__root seed-badge__root--size_large seed-badge__root--variant_weak seed-badge__root--tone_${tone}"><span class="seed-badge__label">${label}</span></span>`;

  const SPECIMENS = {
    ready: () => `
      <div class="bp-spec__head">${badge('positive', 'PURSUE')}<p class="bp-spec__title">Ready</p></div>
      <p class="bp-spec__ctx">G2B-REPLAY-DATA-QUALITY × supplier-northstar — the pairing shown on this page.</p>
      <div class="bp-spec__body"><div class="bp-spec__list">
        ${item('i-check', 'Draft written', '14 sections generated from the selected Win Position and persisted with the run.')}
        ${item('i-check', 'Review clean', '0 open findings across 4 score-bearing criteria.')}
        ${item('i-flag', 'Assign outstanding', '4 criterion tasks are owned but still open — the only pending stage.')}
      </div></div>`,

    loading: () => `
      <div class="bp-spec__head">${badge('neutral', 'Working')}<p class="bp-spec__title">Loading</p></div>
      <p class="bp-spec__ctx">Shown while the writer, the reviewer, and the store run for one build.</p>
      <div class="bp-load" style="margin-top:var(--seed-dimension-x4)">
        <span class="seed-progress-circle__root seed-progress-circle__root--size_24 seed-progress-circle__root--tone_brand" data-progress-state="indeterminate" role="progressbar" aria-label="Building proposal">
          <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
            <circle class="seed-progress-circle__track" cx="12" cy="12" r="9.5" fill="none" stroke-width="3"/>
            <circle class="seed-progress-circle__range" cx="12" cy="12" r="9.5" fill="none" stroke-width="3" stroke-dasharray="18 42" data-progress-state="indeterminate"/>
          </svg>
        </span>
        <p class="bp-load__t">Building proposal from selected strategy…</p>
      </div>
      <div class="bp-skel-stack" aria-hidden="true">
        <span class="seed-skeleton seed-skeleton--tone_neutral seed-skeleton--radius_8" style="--seed-box-width:100%;--seed-box-height:14px"></span>
        <span class="seed-skeleton seed-skeleton--tone_neutral seed-skeleton--radius_8" style="--seed-box-width:88%;--seed-box-height:14px"></span>
        <span class="seed-skeleton seed-skeleton--tone_neutral seed-skeleton--radius_8" style="--seed-box-width:64%;--seed-box-height:14px"></span>
        <span class="seed-skeleton seed-skeleton--tone_neutral seed-skeleton--radius_8" style="--seed-box-width:94%;--seed-box-height:14px"></span>
      </div>
      <p class="bp-footnote">Steps run in order: pursuit, strategy, proposal, red-team, task-plan.</p>`,

    empty: () => `
      <div class="bp-spec__head">${badge('neutral', 'No run')}<p class="bp-spec__title">Empty</p></div>
      <p class="bp-spec__ctx">A bid room with no persisted run for the current opportunity version and position.</p>
      <div class="bp-spec__empty">
        <svg class="bp-i" viewBox="0 0 18 18" aria-hidden="true"><use href="#i-archive"/></svg>
        <p class="bp-spec__k">Nothing saved for this Win Position</p>
        <p class="bp-spec__v" style="max-width:46ch">Selecting a different position changes the stored key, so the room shows no draft, no findings, and no tasks until a proposal is built.</p>
        <button type="button" class="seed-action-button seed-action-button--variant_brandSolid seed-action-button--size_small seed-action-button--size_small-layout_withText" style="margin-top:var(--seed-dimension-x2)">Build proposal from selected strategy</button>
      </div>`,

    review: () => `
      <div class="bp-spec__head">${badge('warning', 'REVIEW')}<p class="bp-spec__title">Review required</p></div>
      <p class="bp-spec__ctx">G2B-REPLAY-ANALYTICS × supplier-atlas — eligibility and capacity pass, evidence does not.</p>
      <div class="bp-spec__body">
        <div class="seed-callout__root seed-callout__root--tone_warning">
          <svg class="bp-i bp-i--20" viewBox="0 0 18 18" aria-hidden="true"><use href="#i-alert"/></svg>
          <div class="seed-callout__content">
            <span class="seed-callout__title seed-callout__title--tone_warning">Limited directly comparable delivery history.</span>
            <span class="seed-callout__description seed-callout__description--tone_warning">Confirm an additional reference and assign an executive delivery reviewer before pursuing.</span>
          </div>
        </div>
        <div class="bp-spec__list">
          ${item('i-flag', 'Validate the comparable-project gap.', 'Next action recorded by the pursuit policy.')}
          ${item('i-flag', 'Add a delivery reference before authoring a proposal.', 'Next action recorded by the pursuit policy.')}
          ${item('i-user', 'Comparable delivery evidence — Evidence owner', 'Validate another directly comparable reference and its buyer outcome.')}
        </div>
        <p class="bp-footnote">Drafting stays locked: the writer refuses any brief that is not PURSUE.</p>
      </div>`,

    nogo: () => `
      <div class="bp-spec__head">${badge('critical', 'NO-GO')}<p class="bp-spec__title">Blocked</p></div>
      <p class="bp-spec__ctx">G2B-REPLAY-DATA-QUALITY × supplier-atlas — a hard gate failed.</p>
      <div class="bp-spec__body">
        <div class="seed-callout__root seed-callout__root--tone_critical">
          <svg class="bp-i bp-i--20" viewBox="0 0 18 18" aria-hidden="true"><use href="#i-lock"/></svg>
          <div class="seed-callout__content">
            <span class="seed-callout__title seed-callout__title--tone_critical">Do not generate a proposal.</span>
            <span class="seed-callout__description seed-callout__description--tone_critical">Resolve eligibility or delivery capacity before reopening this opportunity.</span>
          </div>
        </div>
        <div class="bp-spec__list">
          ${item('i-alert', 'Missing: Information-system maintenance certificate', 'Verify or obtain Information-system maintenance certificate before reopening. — Bid manager')}
          ${item('i-alert', 'Capacity gap: 160 delivery hours', 'Secure named delivery capacity and rerun the pursuit policy. — Delivery lead')}
        </div>
        <p class="bp-footnote">The primary action is disabled in this state; the gap-closure plan replaces it.</p>
      </div>`
  };

  const stateChips = $$('#stateGroup [data-state-key]');
  function setSpecimen(i, focus) {
    stateChips.forEach((c, j) => {
      const on = i === j;
      c.setAttribute('aria-checked', String(on));
      c.tabIndex = on ? 0 : -1;
      c.toggleAttribute('data-checked', on);
    });
    $('#specimen').innerHTML = SPECIMENS[stateChips[i].dataset.stateKey]();
    if (focus) stateChips[i].focus();
  }
  stateChips.forEach((c, i) => {
    c.addEventListener('click', () => setSpecimen(i, false));
    c.addEventListener('keydown', e => {
      const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      if (!d) return;
      e.preventDefault();
      setSpecimen((i + d + stateChips.length) % stateChips.length, true);
    });
  });

  /* ───────── primary action ───────── */

  function bindPrimary() {
    $$('[data-primary]').forEach(btn => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', () => {
        const idx = stateChips.findIndex(c => c.dataset.stateKey === 'loading');
        setSpecimen(idx, false);
        $('#sec-states').scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  /* ───────── boot ───────── */

  const wantedPos = Number((location.hash.match(/pos=(\d)/) || [])[1]);
  if (Number.isInteger(wantedPos) && wantedPos >= 0 && wantedPos < POSITIONS.length) selected = wantedPos;

  const wanted = (location.hash.match(/state=([a-z-]+)/) || [])[1];
  const bootIndex = Math.max(0, stateChips.findIndex(c => c.dataset.stateKey === wanted));

  render();
  syncStage(false);
  setSpecimen(bootIndex, false);
  bindPrimary();
})();
