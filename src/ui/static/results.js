/**
 * results.js — Results page ES module
 * Rules:
 *   1. NEVER use .innerHTML = (assignment). Only DOM methods.
 *   2. NEVER use parseFloat or Number() on money-ish variable names.
 *   3. Never mention protected column names.
 *   4. All API strings go in via el.textContent = value.
 *   5. No framework, no CDN import, no fetch of external URLs.
 *
 * FR-UI-06
 */

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

function setText(el, val) {
  if (el) el.textContent = String(val ?? '');
}

// ---------------------------------------------------------------------------
// Empty-state helper
// ---------------------------------------------------------------------------

function makeEmptyState(container) {
  container.textContent = '';
  const div = document.createElement('div');
  div.className = 'empty-state';
  const p = document.createElement('p');
  const prefix = document.createTextNode('Not generated yet; run ');
  const code = document.createElement('code');
  setText(code, 'make phase5');
  p.appendChild(prefix);
  p.appendChild(code);
  div.appendChild(p);
  container.appendChild(div);
}

// ---------------------------------------------------------------------------
// Chip helper (too_small / unstable)
// ---------------------------------------------------------------------------

function addChip(container, label) {
  const chip = document.createElement('span');
  chip.className = 'chip chip--' + label.replace('_', '-');
  setText(chip, label);
  container.appendChild(chip);
}

// ---------------------------------------------------------------------------
// Tab state
// ---------------------------------------------------------------------------

/** Currently active tab name */
let _activeTab = 'ml';
/** Tabs that have already been loaded (avoid re-fetching) */
const _loadedTabs = new Set();

// ---------------------------------------------------------------------------
// Tab switching
// ---------------------------------------------------------------------------

/**
 * Wire tab buttons for click and keyboard (arrow keys / Enter / Space).
 * FR-UI-06
 */
function initTabs() {
  const tabBtns = Array.from(document.querySelectorAll('[role="tab"]'));
  if (!tabBtns.length) return;

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => activateTab(btn.dataset.tab, tabBtns));
    btn.addEventListener('keydown', e => handleTabKeydown(e, btn, tabBtns));
  });
}

function activateTab(name, tabBtns) {
  if (!name) return;
  _activeTab = name;

  if (tabBtns && tabBtns.length > 0) {
    tabBtns.forEach(b => {
      const isThis = b.dataset.tab === name;
      b.setAttribute('aria-selected', isThis ? 'true' : 'false');
      b.classList.toggle('active', isThis);
      b.tabIndex = isThis ? 0 : -1;
    });
  }

  // Show/hide panels
  document.querySelectorAll('.tab-panel').forEach(panel => {
    if (panel.id === 'tab-' + name) {
      panel.hidden = false;
      panel.removeAttribute('hidden');
      panel.classList.add('active');
      panel.classList.add('tab-panel--active');
    } else {
      panel.hidden = true;
      panel.setAttribute('hidden', '');
      panel.classList.remove('active');
      panel.classList.remove('tab-panel--active');
    }
  });

  if (!_loadedTabs.has(name)) {
    _loadedTabs.add(name);
    loadTab(name);
  }
}

/** Arrow-key / Enter / Space keyboard navigation for tabs. WCAG 2.1 §4.1.2 */
function handleTabKeydown(e, btn, tabBtns) {
  const idx = tabBtns.indexOf(btn);
  let next = -1;

  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    next = (idx + 1) % tabBtns.length;
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    next = (idx - 1 + tabBtns.length) % tabBtns.length;
  } else if (e.key === 'Home') {
    next = 0;
  } else if (e.key === 'End') {
    next = tabBtns.length - 1;
  } else if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    activateTab(btn.dataset.tab, tabBtns);
    return;
  }

  if (next >= 0) {
    e.preventDefault();
    tabBtns[next].focus();
    activateTab(tabBtns[next].dataset.tab, tabBtns);
  }
}

// ---------------------------------------------------------------------------
// Tab content loaders
// ---------------------------------------------------------------------------

/**
 * Fetch and render content for the named tab.
 * FR-UI-06
 */
export async function loadTab(name) {
  switch (name) {
    case 'ml':
      await loadMlTab();
      break;
    case 'scorecard':
    case 'comparison':
      await loadComparisonTab();
      break;
    case 'fairness':
      await loadFairnessTab();
      break;
    case 'edge':
      await loadEdgeTab();
      break;
    default:
      break;
  }
}

// ---------------------------------------------------------------------------
// ML tab: metrics_d2_lr and metrics_d2_gb
// ---------------------------------------------------------------------------

async function loadMlTab() {
  const container = document.getElementById('content-ml') || document.getElementById('ml-metrics-content');
  if (!container) return;
  container.textContent = '';

  const reports = [
    { key: 'metrics_d2_lr', label: 'Logistic Regression Baseline (D2 Held-out Split)' },
    { key: 'metrics_d2_gb', label: 'Gradient Boosting Baseline (D2 Held-out Split)' },
  ];
  let loadedCount = 0;

  for (const { key, label } of reports) {
    try {
      const res = await fetch('/ui/report/' + key);
      if (!res.ok) throw new Error('not ok');
      const data = await res.json();

      if (data.available === false) {
        continue;
      }

      loadedCount++;
      renderModelMetricsCard(container, label, data);
    } catch (_) {
      // ignore
    }
  }

  if (loadedCount === 0) {
    makeEmptyState(container);
  }
}

function renderModelMetricsCard(container, label, data) {
  const card = document.createElement('div');
  card.className = 'card';
  card.style.marginBottom = 'var(--sp-6)';

  const h3 = document.createElement('h3');
  h3.style.marginBottom = 'var(--sp-4)';
  setText(h3, label);
  card.appendChild(h3);

  // Summary tiles row
  const tilesRow = document.createElement('div');
  tilesRow.className = 'summary-tiles';

  const testM = data.test_metrics || {};
  const valM = data.validation_metrics || {};

  const metrics = [
    { label: 'Model', value: data.model || '—' },
    { label: 'Validation AUC', value: valM.auc != null ? String(valM.auc) : '—' },
    { label: 'Test AUC', value: testM.auc != null ? String(testM.auc) : '—' },
    { label: 'Brier Score', value: testM.brier_score != null ? String(testM.brier_score) : '—' },
  ];

  metrics.forEach(({ label: mLabel, value: mVal }) => {
    const tile = document.createElement('div');
    tile.className = 'tile';
    const l = document.createElement('span');
    l.className = 'tile__label';
    setText(l, mLabel);
    const v = document.createElement('span');
    v.className = 'tile__value';
    setText(v, mVal);
    tile.appendChild(l);
    tile.appendChild(v);
    tilesRow.appendChild(tile);
  });
  card.appendChild(tilesRow);

  // Reliability calibration table if present
  if (Array.isArray(testM.reliability_table) && testM.reliability_table.length > 0) {
    const h4 = document.createElement('h4');
    h4.style.marginTop = 'var(--sp-4)';
    h4.style.marginBottom = 'var(--sp-2)';
    setText(h4, 'Calibration & Reliability Table (Test Split)');
    card.appendChild(h4);

    const tblWrap = document.createElement('div');
    tblWrap.className = 'table-scroll-wrap';

    const tbl = document.createElement('table');
    tbl.className = 'data-table';
    const thead = document.createElement('thead');
    const hrow = document.createElement('tr');
    ['Bin', 'Pred Range', 'Count', 'Mean Pred', 'Mean True'].forEach(col => {
      const th = document.createElement('th');
      setText(th, col);
      hrow.appendChild(th);
    });
    thead.appendChild(hrow);
    tbl.appendChild(thead);

    const tbody = document.createElement('tbody');
    testM.reliability_table.forEach(row => {
      const tr = document.createElement('tr');
      const cells = [
        String(row.bin ?? '—'),
        Array.isArray(row.range) ? `${row.range[0]}–${row.range[1]}` : String(row.range ?? '—'),
        String(row.count ?? '—'),
        row.mean_pred != null ? String(row.mean_pred) : '—',
        row.mean_true != null ? String(row.mean_true) : '—',
      ];
      cells.forEach(cVal => {
        const td = document.createElement('td');
        setText(td, cVal);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tbl.appendChild(tbody);
    tblWrap.appendChild(tbl);
    card.appendChild(tblWrap);
  }

  container.appendChild(card);
}

// ---------------------------------------------------------------------------
// Comparison tab: comparison_scorecard
// ---------------------------------------------------------------------------

async function loadComparisonTab() {
  const container = document.getElementById('content-scorecard') || document.getElementById('content-comparison');
  if (!container) return;
  container.textContent = '';

  try {
    const res = await fetch('/ui/report/comparison_scorecard');
    if (!res.ok) throw new Error('not ok');
    const data = await res.json();

    if (data.available === false) {
      makeEmptyState(container);
      return;
    }

    renderScorecardComparison(container, data);
  } catch (_) {
    makeEmptyState(container);
  }
}

function renderScorecardComparison(container, data) {
  const criteria = data.criteria || {};
  const scores = data.scores || {};

  const card = document.createElement('div');
  card.className = 'card';

  const h3 = document.createElement('h3');
  h3.style.marginBottom = 'var(--sp-4)';
  setText(h3, 'Four-Criterion System Evaluation Scorecard');
  card.appendChild(h3);

  const tblWrap = document.createElement('div');
  tblWrap.className = 'table-scroll-wrap';

  const tbl = document.createElement('table');
  tbl.className = 'data-table';

  const thead = document.createElement('thead');
  const hrow = document.createElement('tr');
  ['Criterion', 'Rule System', 'Logistic Regression', 'Gradient Boosting'].forEach(col => {
    const th = document.createElement('th');
    setText(th, col);
    hrow.appendChild(th);
  });
  thead.appendChild(hrow);
  tbl.appendChild(thead);

  const tbody = document.createElement('tbody');
  const critKeys = ['transparency', 'auditability', 'edge_cases', 'regulatory_defensibility'];

  critKeys.forEach(critKey => {
    const critInfo = criteria[critKey] || {};
    const critName = critInfo.name || critKey;

    const tr = document.createElement('tr');

    // Criterion column
    const tdCrit = document.createElement('td');
    const nameStrong = document.createElement('strong');
    setText(nameStrong, critName);
    tdCrit.appendChild(nameStrong);
    if (critInfo.question) {
      const qP = document.createElement('div');
      qP.style.fontSize = 'var(--fs-xs)';
      qP.style.color = 'var(--c-text-muted)';
      qP.style.marginTop = '2px';
      setText(qP, critInfo.question);
      tdCrit.appendChild(qP);
    }
    tr.appendChild(tdCrit);

    // Systems columns
    ['rule_system', 'logistic_regression', 'gradient_boosting'].forEach(sysKey => {
      const tdSys = document.createElement('td');
      const sysScore = (scores[sysKey] && scores[sysKey][critKey]) || {};
      const scoreNum = sysScore.score != null ? `${sysScore.score}/3` : '—';

      const scoreBadge = document.createElement('span');
      let badgeClass = 'badge--small ';
      if (sysScore.score === 3) badgeClass += 'badge--eligible';
      else if (sysScore.score === 2) badgeClass += 'badge--refer';
      else badgeClass += 'badge--ineligible';

      scoreBadge.className = 'badge ' + badgeClass;
      setText(scoreBadge, scoreNum);
      tdSys.appendChild(scoreBadge);

      if (sysScore.justification) {
        const justP = document.createElement('div');
        justP.style.fontSize = 'var(--fs-xs)';
        justP.style.color = 'var(--c-text-muted)';
        justP.style.marginTop = 'var(--sp-2)';
        justP.style.lineHeight = '1.4';
        setText(justP, sysScore.justification);
        tdSys.appendChild(justP);
      }
      tr.appendChild(tdSys);
    });

    tbody.appendChild(tr);
  });

  tbl.appendChild(tbody);
  tblWrap.appendChild(tbl);
  card.appendChild(tblWrap);
  container.appendChild(card);
}

// ---------------------------------------------------------------------------
// Fairness tab: d2_tables + d3_tables
// ---------------------------------------------------------------------------

async function loadFairnessTab() {
  const container = document.getElementById('content-fairness');
  if (!container) return;
  container.textContent = '';

  const sources = [
    { key: 'd2_tables', label: 'D2 Dataset Fairness Analysis' },
    { key: 'd3_tables', label: 'D3 Dataset Fairness Analysis' },
  ];
  let loadedCount = 0;

  for (const { key, label } of sources) {
    try {
      const res = await fetch('/ui/report/' + key);
      if (!res.ok) throw new Error('not ok');
      const data = await res.json();

      if (data.available === false) {
        continue;
      }

      loadedCount++;
      const card = document.createElement('div');
      card.className = 'card';
      card.style.marginBottom = 'var(--sp-6)';

      const h3 = document.createElement('h3');
      h3.style.marginBottom = 'var(--sp-3)';
      setText(h3, label);
      card.appendChild(h3);

      const content = data.content != null ? data.content : JSON.stringify(data, null, 2);

      // Add chips for too_small and unstable markers found in the content
      const chipRow = document.createElement('div');
      chipRow.className = 'chip-row';
      chipRow.style.display = 'flex';
      chipRow.style.gap = 'var(--sp-2)';
      chipRow.style.marginBottom = 'var(--sp-3)';
      let hasChips = false;
      if (content.includes('too_small')) { addChip(chipRow, 'too_small'); hasChips = true; }
      if (content.includes('unstable')) { addChip(chipRow, 'unstable'); hasChips = true; }
      if (hasChips) card.appendChild(chipRow);

      const pre = document.createElement('pre');
      pre.className = 'report-block';
      pre.style.whiteSpace = 'pre-wrap';
      pre.style.wordBreak = 'break-word';
      setText(pre, content);
      card.appendChild(pre);

      container.appendChild(card);
    } catch (_) {
      // ignore
    }
  }

  if (loadedCount === 0) {
    makeEmptyState(container);
  }
}

// ---------------------------------------------------------------------------
// Edge-cases tab: edge_case_summary
// ---------------------------------------------------------------------------

async function loadEdgeTab() {
  const container = document.getElementById('content-edge');
  if (!container) return;
  container.textContent = '';

  try {
    const res = await fetch('/ui/report/edge_case_summary');
    if (!res.ok) throw new Error('not ok');
    const data = await res.json();

    if (data.available === false) {
      makeEmptyState(container);
      return;
    }

    const card = document.createElement('div');
    card.className = 'card';

    const h3 = document.createElement('h3');
    h3.style.marginBottom = 'var(--sp-3)';
    setText(h3, 'Boundary and Missing-Data Edge Case Evaluation');
    card.appendChild(h3);

    const content = data.content != null ? data.content : JSON.stringify(data, null, 2);
    const pre = document.createElement('pre');
    pre.className = 'report-block';
    pre.style.whiteSpace = 'pre-wrap';
    pre.style.wordBreak = 'break-word';
    setText(pre, content);
    card.appendChild(pre);

    container.appendChild(card);
  } catch (_) {
    makeEmptyState(container);
  }
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  const tabBtns = Array.from(document.querySelectorAll('[role="tab"]'));
  initTabs();
  activateTab('ml', tabBtns);
});
