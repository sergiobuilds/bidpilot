/* BidPilot reference screen — interaction layer.
 * Criterion selection and Win Position selection are real radio inputs, so
 * both are keyboard-operable and announced. Everything rendered here is
 * derived from data.js with the same string templates the product uses. */

(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };

  var state = { scenario: 'pursue', criterion: 0, position: 0, phase: 'idle' };

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function icon(id, size) {
    var s = size || 16;
    return '<svg width="' + s + '" height="' + s + '" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><use href="#' + id + '"/></svg>';
  }

  function data() { return SCENARIOS[state.scenario]; }

  /* ------------------------------------------------- product templates */

  // Mirrors pursuit._blueprint: claim text and owner assignment.
  function claimFor(row, position) {
    var d = data();
    return position.title + ': ' + d.supplier.name + ' will address ' +
      row.criterion.toLowerCase() + ' through ' + d.tender.promisedOutcome + '.';
  }

  function ownerFor(row) { return row.weight >= 30 ? 'Solution lead' : 'Bid manager'; }

  // Mirrors pursuit._position: the statement string.
  function statementFor(position) {
    var d = data();
    var names = position.proof.slice(0, 2).map(function (p) { return p.label; }).join(', ') ||
      'the selected delivery team';
    return 'Win ' + position.title.toLowerCase() + ' with ' + names + ': ' +
      d.supplier.name + ' will deliver ' + d.tender.promisedOutcome + '.';
  }

  /* ------------------------------------------------------------ header */

  function renderHeader() {
    var d = data();
    $('tender-id').textContent = d.tender.id;
    $('tender-title').textContent = d.tender.title;
    $('buyer-objective').textContent = d.tender.buyerObjective;
    $('verdict-value').textContent = d.status;
    $('verdict-value').setAttribute('data-tone', d.tone);
    $('tender-tags').innerHTML = d.tender.tags.map(function (t) {
      return '<li class="tag">' + esc(t) + '</li>';
    }).join('');
  }

  /* ------------------------------------------------------ decision rail */

  function renderDecisionRail() {
    var d = data();
    $('rail-status').textContent = d.status;
    $('rail-status').setAttribute('data-tone', d.tone);
    $('rail-status-sentence').textContent = d.statusSentence;
    $('dims').innerHTML = d.dims.map(function (dim) {
      var glyph = dim.tone === 'positive' ? 'i-check' : (dim.tone === 'critical' ? 'i-block' : 'i-alert');
      return '<li class="dim">' +
        '<span class="dim__icon" data-tone="' + dim.tone + '">' + icon(glyph, 14) + '</span>' +
        '<span class="dim__label">' + esc(dim.label) +
        '<span class="dim__detail">' + esc(dim.detail) + '</span></span>' +
        '<span class="seed-badge__root seed-badge__root--size_medium seed-badge__root--variant_weak seed-badge__root--tone_' +
        dim.tone + '-variant_weak"><span class="seed-badge__label">' + esc(dim.value) + '</span></span>' +
        '</li>';
    }).join('');
  }

  /* ------------------------------------------------------- context rail */

  function renderContextRail() {
    var d = data();
    $('src-source').textContent = 'Fixture replay record — no source URL captured';
    $('src-version').textContent = d.tender.version;
    $('src-retrieved').textContent = 'Not applicable to a fixture replay record';
    $('src-instruction').textContent = 'None flagged';
    $('src-deadline').textContent = NOT_IN_CONTRACT;
    $('src-value').textContent = NOT_IN_CONTRACT;
    $('src-hours').textContent = d.tender.deliveryHours + ' planned delivery hours';

    $('sup-name').textContent = d.supplier.name;
    $('sup-credentials').textContent = d.supplier.credentials.join(' · ');
    $('sup-hours').textContent = d.supplier.availableHours + ' hours';
    $('sup-people').textContent = d.supplier.people.join(' · ');
    $('sup-projects').textContent = d.supplier.comparable === 0
      ? 'No project matches the tender scope tags'
      : d.supplier.comparableTitles.join(' · ');
  }

  /* --------------------------------------------------------- score map */

  function renderMatrix() {
    var d = data();
    var total = d.rows.reduce(function (a, r) { return a + r.weight; }, 0);
    var covered = d.rows.filter(function (r) { return r.readinessTone === 'covered'; })
      .reduce(function (a, r) { return a + r.weight; }, 0);
    var partial = d.rows.filter(function (r) { return r.readinessTone === 'partial'; })
      .reduce(function (a, r) { return a + r.weight; }, 0);
    var open = total - covered - partial;

    $('weight-total').textContent = total;
    $('covered-points').textContent = covered;
    $('readiness-bar').innerHTML =
      '<span class="readiness-bar__seg" data-tone="covered" style="flex:' + covered + '"></span>' +
      '<span class="readiness-bar__seg" data-tone="partial" style="flex:' + partial + '"></span>' +
      '<span class="readiness-bar__seg" data-tone="open" style="flex:' + open + '"></span>';
    $('readiness-caption').textContent =
      'Weighted readiness: ' + covered + ' points covered, ' + partial + ' points partial, ' +
      open + ' points open, of ' + total + ' total.';

    var position = d.positions[state.position];
    var toneBadge = { covered: 'positive', partial: 'warning', open: 'neutral' };

    $('matrix-body').innerHTML = d.rows.map(function (r, i) {
      var checked = i === state.criterion;
      return '<tr data-selected="' + checked + '" data-index="' + i + '">' +
        '<td data-label="Criterion">' +
          '<label class="crit">' +
            '<input type="radio" class="vh" name="criterion" value="' + i + '"' + (checked ? ' checked' : '') + '>' +
            '<span class="crit__name">' + esc(r.criterion) + '</span>' +
            '<span class="crit__owner">Owner · ' + esc(ownerFor(r)) + '</span>' +
          '</label>' +
        '</td>' +
        '<td class="n" data-label="Weight">' +
          '<span class="weight"><span class="weight__n num">' + r.weight + '</span>' +
          '<span class="weight__track"><span class="weight__fill" style="width:' + r.weight + '%"></span></span></span>' +
        '</td>' +
        '<td data-label="Readiness">' +
          '<span class="seed-badge__root seed-badge__root--size_medium seed-badge__root--variant_weak seed-badge__root--tone_' +
          toneBadge[r.readinessTone] + '-variant_weak"><span class="seed-badge__label">' + esc(r.readiness) + '</span></span>' +
        '</td>' +
        '<td data-label="Supporting supplier asset">' +
          '<span class="asset__label">' + esc(r.asset) + '</span>' +
          '<span class="asset__kind">' + esc(r.assetKind) + '</span>' +
        '</td>' +
        '<td data-label="Gap"><span class="gap-text" data-tone="' + r.gapTone + '">' + esc(r.gap) + '</span></td>' +
        '<td class="c-claim-cell" data-label="Planned claim">' +
          '<span class="claim-lead">' + esc(position.title) + '</span>' +
          '<span class="claim-text">' + esc(claimFor(r, position).slice(position.title.length + 2)) + '</span>' +
        '</td>' +
      '</tr>';
    }).join('');
  }

  function renderDetail() {
    var d = data();
    var r = d.rows[state.criterion];
    var position = d.positions[state.position];
    $('detail-title').textContent = r.criterion + ' — proposal section blueprint';
    $('detail-weight').textContent = r.weight + ' of 100 points';
    $('detail-claim').textContent = claimFor(r, position);
    $('detail-section').textContent = '## ' + r.criterion + ' (' + r.weight + ' points)';
    $('detail-owner').textContent = ownerFor(r);
    $('detail-proof').innerHTML = r.proof.map(function (p) {
      return '<li>' + icon('i-doc', 14) + '<span>' + esc(p) + '</span></li>';
    }).join('');
  }

  /* ----------------------------------------------------- win positions */

  function renderPositions() {
    var d = data();
    $('positions').innerHTML = d.positions.map(function (p, i) {
      var checked = i === state.position;
      return '<label class="position">' +
        '<input type="radio" class="vh" name="position" value="' + i + '"' + (checked ? ' checked' : '') + '>' +
        '<span class="position__head">' +
          '<span class="position__dot" aria-hidden="true"></span>' +
          '<span class="position__title">' + esc(p.title) + '</span>' +
        '</span>' +
        '<span class="position__targets">Targets ' + esc(p.targets.join(' + ')) + '</span>' +
        '<span class="position__statement">' + esc(statementFor(p)) + '</span>' +
        '<span class="position__block">' +
          '<span class="section-label">Proof cards</span>' +
          p.proof.map(function (c) {
            return '<span class="proof-card">' +
              '<span class="proof-card__kind">' + esc(c.kind) + '</span>' +
              '<span class="proof-card__label">' + esc(c.label) + '</span>' +
              '<span class="proof-card__detail">' + esc(c.detail) + '</span></span>';
          }).join('') +
        '</span>' +
        '<span class="risk">' +
          '<span><b>Weakness</b> — ' + esc(p.weakness || 'None recorded by the pursuit policy.') + '</span>' +
          '<span><b>Mitigation</b> — ' + esc(p.mitigation ||
            'Keep criterion owners and delivery assets traceable through the saved Bid Room run.') + '</span>' +
        '</span>' +
      '</label>';
    }).join('');
  }

  /* ---------------------------------------------------------- outputs */

  function renderBlueprint() {
    var d = data();
    var position = d.positions[state.position];
    $('blueprint').innerHTML = d.rows.map(function (r) {
      return '<div class="bp-row">' +
        '<span class="bp-row__w num">' + r.weight + '</span>' +
        '<span><span class="bp-row__title">' + esc(r.criterion) + '</span>' +
        '<span class="bp-row__claim">' + esc(claimFor(r, position)) + '</span>' +
        '<span class="bp-row__claim">Delivery assets: ' + esc(d.blueprintAssets.join(', ')) + '.</span></span>' +
        '<span class="bp-row__owner">' + esc(ownerFor(r)) + '</span>' +
      '</div>';
    }).join('');
  }

  // Mirrors proposal_writer._strategy_markdown.
  function renderDraft() {
    var d = data();
    var p = d.positions[state.position];
    var statement = statementFor(p);
    var assets = p.proof.map(function (c) { return c.label; }).join(', ');
    var html = '<h3>' + esc(d.tender.title) + '</h3>';
    html += '<h4>Executive Summary</h4><p>' + esc(d.supplier.name) +
      ' will pursue the buyer objective through the selected Win Position: ' + esc(statement) +
      ' The response prioritizes the highest-weighted criteria and assigns each claim to an accountable proposal owner.</p>';
    html += '<h4>Understanding of the Requirement</h4><p>The buyer needs ' +
      esc(d.tender.buyerObjective.toLowerCase()) +
      ' The proposed response must address the weighted evaluation matrix while remaining deliverable within ' +
      d.tender.deliveryHours + ' planned hours.</p>';
    html += '<h4>Win Position</h4><p>' + esc(statement) + '</p>';
    html += '<h4>Selected Delivery Assets</h4>' + p.proof.map(function (c) {
      return '<p><b>' + esc(c.label) + '</b> — ' + esc(c.detail) + '</p>';
    }).join('');
    html += d.rows.map(function (r) {
      return '<h4>' + esc(r.criterion) + ' (' + r.weight + ' points)</h4>' +
        '<p>' + esc(claimFor(r, p)) + '</p>' +
        '<p>Delivery assets: ' + esc(d.blueprintAssets.join(', ')) + '. Proposal owner: ' + esc(ownerFor(r)) + '.</p>';
    }).join('');
    html += '<h4>Risk and Mitigation</h4><p>' +
      esc(p.weakness || 'The current pursuit policy found no blocking eligibility or capacity gap.') + '</p>' +
      '<p>Mitigation: ' + esc(p.mitigation ||
        'Keep criterion owners and delivery assets traceable through the saved Bid Room run.') + '</p>';
    html += '<h4>Team and Governance</h4><p>The proposal owners named in the blueprint coordinate the response. ' +
      'Delivery evidence is anchored in ' + esc(assets) + ' and the selected supplier profile has ' +
      d.supplier.availableHours + ' available hours.</p>';
    $('draft').innerHTML = html;
  }

  // Mirrors proposal_writer.red_team_proposal / red_team_tasks checks.
  function renderRedTeam() {
    var d = data();
    var p = d.positions[state.position];
    var findings = [];
    var checks = d.rows.map(function (r) {
      return {
        crit: r.criterion,
        marks: [
          { what: 'Explicit "## ' + r.criterion + '" section', pass: true },
          { what: 'Bound to a selected supplier asset', pass: true }
        ]
      };
    });
    if (p.weakness) findings.push(p.mitigation || p.weakness);

    $('redteam-note').textContent = findings.length === 0
      ? 'No findings. Every score-bearing section passed both checks.'
      : findings.length + ' finding' + (findings.length > 1 ? 's' : '') + ' returned against the same evaluation matrix.';

    $('redteam-checks').innerHTML = checks.map(function (c) {
      return '<div class="check">' +
        '<span class="check__crit">' + esc(c.crit) + '</span>' +
        '<span class="check__marks">' + c.marks.map(function (m) {
          return '<span class="check__mark" data-pass="' + m.pass + '">' +
            icon(m.pass ? 'i-check' : 'i-alert', 15) + esc(m.what) + '</span>';
        }).join('') + '</span>' +
      '</div>';
    }).join('');

    $('redteam-findings').innerHTML = findings.length === 0 ? '' :
      '<div class="seed-callout__root seed-callout__root--tone_warning" style="margin-top:var(--seed-dimension-x4)">' +
        '<span class="seed-callout__content">' +
          '<span class="seed-callout__title seed-callout__title--tone_warning">Findings</span>' +
          '<span class="seed-callout__description seed-callout__description--tone_warning">' +
          findings.map(esc).join(' ') + '</span>' +
        '</span></div>';
  }

  function renderOwnerTasks() {
    var d = data();
    var rows = d.rows.map(function (r) {
      return { item: r.criterion, action: 'Author the ' + r.criterion.toLowerCase() +
        ' response and attach the selected delivery assets.', owner: ownerFor(r) };
    });
    d.nextActions.forEach(function (a) {
      rows.push({ item: 'Policy next action', action: a, owner: 'Bid manager' });
    });
    $('owner-tasks').innerHTML = rows.map(function (t) {
      return '<tr><td data-label="Item">' + esc(t.item) + '</td>' +
        '<td data-label="Action">' + esc(t.action) + '</td>' +
        '<td data-label="Owner">' + esc(t.owner) + '</td></tr>';
    }).join('');
  }

  function renderGapTasks() {
    var d = data();
    $('gap-tasks').innerHTML = d.gapTasks.map(function (t) {
      return '<tr><td data-label="Gap">' + esc(t.gap) + '</td>' +
        '<td data-label="Action">' + esc(t.action) + '</td>' +
        '<td data-label="Owner">' + esc(t.owner) + '</td></tr>';
    }).join('');
    if (d.blockedTitle) {
      $('blocked-callout').className = 'seed-callout__root seed-callout__root--tone_' + d.blockedTone;
      $('blocked-callout-title').className = 'seed-callout__title seed-callout__title--tone_' + d.blockedTone;
      $('blocked-callout-desc').className = 'seed-callout__description seed-callout__description--tone_' + d.blockedTone;
      $('blocked-callout-title').textContent = d.blockedTitle;
      $('blocked-callout-desc').textContent = d.blockedDesc;
    }
  }

  function renderRun() {
    var d = data();
    var run = d.savedRun;
    if (!run) return;
    var p = d.positions[state.position];
    var isNew = state.phase === 'built';
    $('run-id').textContent = 'run_id ' + (isNew ? run.newRunId : run.runId) +
      ' · ' + (isNew ? run.newCreatedAt : run.createdAt);
    $('run-version').textContent = d.tender.version;
    $('run-position').textContent = statementFor(p);
    $('run-provider').textContent = run.provider;
    $('run-state').textContent = run.state;
    $('run-steps').innerHTML = run.steps.map(function (s) {
      return '<span class="run__step">' + icon('i-check', 13) + esc(s) + '</span>';
    }).join('');
  }

  /* ---------------------------------------------------------- phasing */

  function applyPhase() {
    var d = data();
    var blocked = d.status !== 'PURSUE';
    var loading = state.phase === 'loading';
    var built = state.phase === 'built' || (!blocked && state.phase === 'idle' && d.savedRun);

    $('blocked-card').hidden = !blocked;
    $('loading-card').hidden = !loading;
    $('output').hidden = blocked || loading || !built;

    var btn = $('build-btn');
    btn.disabled = blocked;
    if (loading) { btn.setAttribute('data-loading', ''); } else { btn.removeAttribute('data-loading'); }
    btn.querySelector('.btn-label').textContent = blocked
      ? 'Proposal generation blocked'
      : (built ? 'Rebuild strategy-led proposal' : 'Build strategy-led proposal');

    $('action-note').textContent = blocked
      ? 'Status ' + d.status + '. ' + d.nextActions.join(' ')
      : (loading
        ? 'Running the blueprint, draft and red-team review against the selected Win Position.'
        : (built
          ? 'A Bid Room run already exists for this tender version and Win Position. Rebuilding replaces the preview and saves a new run.'
          : 'Status PURSUE. ' + d.nextActions.join(' ')));

    $('run-note').textContent = state.phase === 'built'
      ? 'Saved from this build. Replay reloads the pursuit brief, position, draft, findings and tasks.'
      : 'An existing saved run for this tender version and Win Position. Replay reloads every artefact.';
    $('run-badge').querySelector('.seed-badge__label').textContent =
      state.phase === 'built' ? 'New run saved' : 'Existing saved run';
  }

  /* ----------------------------------------------------------- render */

  function renderAll() {
    renderHeader();
    renderDecisionRail();
    renderContextRail();
    renderMatrix();
    renderDetail();
    renderPositions();
    renderBlueprint();
    renderDraft();
    renderRedTeam();
    renderOwnerTasks();
    renderGapTasks();
    renderRun();
    applyPhase();
  }

  function renderPositionDependent() {
    renderMatrix();
    renderDetail();
    renderBlueprint();
    renderDraft();
    renderRedTeam();
    renderRun();
  }

  /* ------------------------------------------------------------ events */

  document.addEventListener('change', function (e) {
    var t = e.target;
    if (t.name === 'criterion') {
      state.criterion = Number(t.value);
      Array.prototype.forEach.call(document.querySelectorAll('#matrix-body tr'), function (tr) {
        tr.setAttribute('data-selected', String(Number(tr.dataset.index) === state.criterion));
      });
      renderDetail();
    }
    if (t.name === 'position') {
      state.position = Number(t.value);
      renderPositionDependent();
    }
  });

  document.addEventListener('click', function (e) {
    var seg = e.target.closest('[data-scenario]');
    if (seg) {
      var items = Array.prototype.slice.call($('scenario-control').querySelectorAll('[data-scenario]'));
      state.scenario = seg.dataset.scenario;
      state.criterion = 0;
      state.position = 0;
      state.phase = 'idle';
      items.forEach(function (b, i) {
        var on = b === seg;
        b.setAttribute('aria-pressed', String(on));
        if (on) { b.setAttribute('data-checked', ''); $('scenario-control').style.setProperty('--segment-index', i); }
        else { b.removeAttribute('data-checked'); }
      });
      renderAll();
      return;
    }
    if (e.target.closest('#build-btn')) {
      if (state.phase === 'loading' || data().status !== 'PURSUE') return;
      state.phase = 'loading';
      applyPhase();
      window.setTimeout(function () {
        state.phase = 'built';
        renderPositionDependent();
        applyPhase();
        $('run').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }, 1400);
      return;
    }
    if (e.target.closest('#replay-btn')) {
      state.phase = 'loading';
      applyPhase();
      window.setTimeout(function () {
        state.phase = 'built';
        renderPositionDependent();
        applyPhase();
      }, 900);
    }
  });

  /* Deep link: #review, #nogo, #pursue select the pursuit state; #loading
     opens the in-progress state directly. */
  (function initFromHash() {
    var h = (window.location.hash || '').replace('#', '');
    if (h === 'loading') { state.phase = 'loading'; return; }
    if (!SCENARIOS[h]) return;
    state.scenario = h;
    var items = Array.prototype.slice.call($('scenario-control').querySelectorAll('[data-scenario]'));
    items.forEach(function (b, i) {
      var on = b.dataset.scenario === h;
      b.setAttribute('aria-pressed', String(on));
      if (on) { b.setAttribute('data-checked', ''); $('scenario-control').style.setProperty('--segment-index', i); }
      else { b.removeAttribute('data-checked'); }
    });
  })();

  renderAll();
})();
