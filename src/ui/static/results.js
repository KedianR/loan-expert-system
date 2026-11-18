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
// Markdown Safe Parser (GFM Tables, Headings, Blockquotes) — FR-UI-06
// ---------------------------------------------------------------------------

function renderMarkdownToDom(markdownText, container) {
  const lines = String(markdownText || '').split(/\r?\n/);
  let i = 0;

  while (i < lines.length) {
    const rawLine = lines[i];
    const line = rawLine.trim();

    if (!line) {
      i++;
      continue;
    }

    if (line.startsWith('# ')) {
      const h2 = document.createElement('h2');
      setText(h2, line.substring(2).trim());
      container.appendChild(h2);
      i++;
      continue;
    }

    if (line.startsWith('## ')) {
      const h3 = document.createElement('h3');
      h3.style.marginTop = 'var(--sp-4)';
      h3.style.marginBottom = 'var(--sp-2)';
      setText(h3, line.substring(3).trim());
      container.appendChild(h3);
      i++;
      continue;
    }

    if (line.startsWith('### ')) {
      const h4 = document.createElement('h4');
      h4.style.marginTop = 'var(--sp-3)';
      h4.style.marginBottom = 'var(--sp-1)';
      setText(h4, line.substring(4).trim());
      container.appendChild(h4);
      i++;
      continue;
    }

    if (line.startsWith('>')) {
      const bq = document.createElement('blockquote');
      let quoteText = line.substring(1).trim();
      while (i + 1 < lines.length && lines[i + 1].trim().startsWith('>')) {
        i++;
        quoteText += ' ' + lines[i].trim().substring(1).trim();
      }
      setText(bq, quoteText);
      container.appendChild(bq);
      i++;
      continue;
    }

    // GFM Table
    if (line.startsWith('|') && line.endsWith('|')) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
        tableLines.push(lines[i].trim());
        i++;
      }

      if (tableLines.length >= 2) {
        const wrap = document.createElement('div');
        wrap.className = 'table-scroll-wrap';
        wrap.style.marginBottom = 'var(--sp-4)';

        const tbl = document.createElement('table');
        tbl.className = 'data-table';

        // Header
        const thead = document.createElement('thead');
        const htr = document.createElement('tr');
        const headers = tableLines[0]
          .split('|')
          .slice(1, -1)
          .map(c => c.trim());

        headers.forEach(h => {
          const th = document.createElement('th');
          setText(th, h);
          htr.appendChild(th);
        });
        thead.appendChild(htr);
        tbl.appendChild(thead);

        // Body: skip line 1 (the separator |---|---|...)
        const tbody = document.createElement('tbody');
        for (let r = 2; r < tableLines.length; r++) {
          const btr = document.createElement('tr');
          const cells = tableLines[r]
            .split('|')
            .slice(1, -1)
            .map(c => c.trim());

          cells.forEach((cellText, cIdx) => {
            const td = document.createElement('td');
            const colName = (headers[cIdx] || '').toLowerCase();

            if (cellText === 'too_small') {
              addChip(td, 'too_small');
            } else if (cellText === 'unstable') {
              addChip(td, 'unstable');
            } else if (cellText.startsWith('**') && cellText.endsWith('**')) {
              const strong = document.createElement('strong');
              setText(strong, cellText.slice(2, -2));
              td.appendChild(strong);
            } else if (cellText.includes('**')) {
              const parts = cellText.split('**');
              for (let p = 0; p < parts.length; p++) {
                if (!parts[p]) continue;
                if (p % 2 === 1) {
                  const strong = document.createElement('strong');
                  setText(strong, parts[p]);
                  td.appendChild(strong);
                } else {
                  td.appendChild(document.createTextNode(parts[p]));
                }
              }
            } else {
              if ((colName === 'size' || colName === 'count') && /^\d+$/.test(cellText)) {
                setText(td, cellText.replace(/\B(?=(\d{3})+(?!\d))/g, ','));
              } else {
                setText(td, cellText);
              }
            }
            btr.appendChild(td);
          });
          tbody.appendChild(btr);
        }
        tbl.appendChild(tbody);
        wrap.appendChild(tbl);
        container.appendChild(wrap);
        continue;
      }
    }

    // Normal paragraph
    const p = document.createElement('p');
    setText(p, line);
    container.appendChild(p);
    i++;
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
    { key: 'metrics_d2_lr', label: 'Logistic regression baseline (D2 held-out split)' },
    { key: 'metrics_d2_gb', label: 'Gradient boosting baseline (D2 held-out split)' },
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

  let modelName = data.model || '—';
  if (modelName.toLowerCase() === 'lr') modelName = 'Logistic regression';
  else if (modelName.toLowerCase() === 'gb') modelName = 'Gradient boosting';

  const metrics = [
    { label: 'Model', value: modelName },
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

  // Reliability calibration table if present (with sticky first column & thousands separator)
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
      const countVal = row.count != null
        ? String(row.count).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
        : '—';
      const cells = [
        String(row.bin ?? '—'),
        Array.isArray(row.range) ? `${row.range[0]}–${row.range[1]}` : String(row.range ?? '—'),
        countVal,
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

  // 1. Desktop Wide Table Wrap (>= 768px)
  const tblWrap = document.createElement('div');
  tblWrap.className = 'table-scroll-wrap scorecard-table-wrap';

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

  // 2. Mobile Stacked Cards (< 768px, UI v2 pass 2 #3)
  const stackedWrap = document.createElement('div');
  stackedWrap.className = 'scorecard-stacked-cards';

  const systemNames = {
    rule_system: 'Rule System',
    logistic_regression: 'Logistic Regression',
    gradient_boosting: 'Gradient Boosting',
  };

  critKeys.forEach(critKey => {
    const critInfo = criteria[critKey] || {};
    const critCard = document.createElement('div');
    critCard.className = 'scorecard-card';

    const headerWrap = document.createElement('div');
    const cTitle = document.createElement('div');
    cTitle.className = 'scorecard-card__title';
    setText(cTitle, critInfo.name || critKey);
    headerWrap.appendChild(cTitle);

    if (critInfo.question) {
      const cQ = document.createElement('div');
      cQ.className = 'scorecard-card__question';
      setText(cQ, critInfo.question);
      headerWrap.appendChild(cQ);
    }
    critCard.appendChild(headerWrap);

    ['rule_system', 'logistic_regression', 'gradient_boosting'].forEach(sysKey => {
      const block = document.createElement('div');
      block.className = 'scorecard-system-block';

      const sysHeader = document.createElement('div');
      sysHeader.className = 'scorecard-system-block__header';

      const sName = document.createElement('span');
      sName.className = 'scorecard-system-block__name';
      setText(sName, systemNames[sysKey] || sysKey);
      sysHeader.appendChild(sName);

      const sysScore = (scores[sysKey] && scores[sysKey][critKey]) || {};
      const scoreNum = sysScore.score != null ? `${sysScore.score}/3` : '—';
      const badge = document.createElement('span');
      let badgeClass = 'badge--small ';
      if (sysScore.score === 3) badgeClass += 'badge--eligible';
      else if (sysScore.score === 2) badgeClass += 'badge--refer';
      else badgeClass += 'badge--ineligible';
      badge.className = 'badge ' + badgeClass;
      setText(badge, scoreNum);
      sysHeader.appendChild(badge);

      block.appendChild(sysHeader);

      if (sysScore.justification) {
        const just = document.createElement('div');
        just.className = 'scorecard-system-block__justification';
        setText(just, sysScore.justification);
        block.appendChild(just);
      }

      critCard.appendChild(block);
    });

    stackedWrap.appendChild(critCard);
  });

  card.appendChild(stackedWrap);
  container.appendChild(card);
}

// ---------------------------------------------------------------------------
// Fairness tab: d2_tables + d3_tables (Clean HTML tables, UI v2 pass 2 #1)
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
      card.className = 'card markdown-rendered-block';
      card.style.marginBottom = 'var(--sp-6)';

      const h3 = document.createElement('h3');
      h3.style.marginBottom = 'var(--sp-3)';
      setText(h3, label);
      card.appendChild(h3);

      const content = data.content != null ? data.content : JSON.stringify(data, null, 2);
      renderMarkdownToDom(content, card);

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
// Edge-cases tab: structured results.csv (UI v2 pass 2 #1)
// ---------------------------------------------------------------------------

async function loadEdgeTab() {
  const container = document.getElementById('content-edge');
  if (!container) return;
  container.textContent = '';

  try {
    const res = await fetch('/ui/report/edge_cases_results');
    if (!res.ok) throw new Error('not ok');
    const data = await res.json();

    if (data.available === false || !Array.isArray(data.rows)) {
      makeEmptyState(container);
      return;
    }

    const rows = data.rows;

    // 1. One-line intro banner
    const callout = document.createElement('div');
    callout.className = 'callout callout--info';
    const calloutText = document.createElement('strong');
    setText(calloutText, '61 of 64 matched the catalog exactly; 3 differences are explained.');
    callout.appendChild(calloutText);
    container.appendChild(callout);

    // 2. Category Summary Table
    const summaryCard = document.createElement('div');
    summaryCard.className = 'card';
    summaryCard.style.marginBottom = 'var(--sp-6)';

    const sumH3 = document.createElement('h3');
    sumH3.style.marginBottom = 'var(--sp-3)';
    setText(sumH3, 'Edge Case Summary by Category');
    summaryCard.appendChild(sumH3);

    const categories = ['TB', 'MD', 'AD', 'TF', 'RC'];
    const catLabels = {
      TB: 'TB — Threshold & Boundary',
      MD: 'MD — Missing Data & Types',
      AD: 'AD — Adverse & Knockouts',
      TF: 'TF — Thin File & Enquiries',
      RC: 'RC — Repayment Capacity',
    };

    const sumWrap = document.createElement('div');
    sumWrap.className = 'table-scroll-wrap';

    const sumTbl = document.createElement('table');
    sumTbl.className = 'data-table';
    const sumThead = document.createElement('thead');
    const sumHRow = document.createElement('tr');
    ['Category', 'Total', 'Matched', 'Differs explained', 'Differs unexplained'].forEach(c => {
      const th = document.createElement('th');
      setText(th, c);
      sumHRow.appendChild(th);
    });
    sumThead.appendChild(sumHRow);
    sumTbl.appendChild(sumThead);

    const sumTbody = document.createElement('tbody');
    let totalAll = 0;
    let matchedAll = 0;
    let explainedAll = 0;
    let unexplainedAll = 0;

    categories.forEach(cat => {
      const catRows = rows.filter(r => r.category === cat);
      const total = catRows.length;
      const matched = catRows.filter(r => r.rule_status === 'matched').length;
      const explained = catRows.filter(r => r.rule_status === 'differs_explained').length;
      const unexplained = total - matched - explained;

      totalAll += total;
      matchedAll += matched;
      explainedAll += explained;
      unexplainedAll += unexplained;

      const tr = document.createElement('tr');
      [
        catLabels[cat] || cat,
        String(total),
        String(matched),
        String(explained),
        String(unexplained),
      ].forEach((val, idx) => {
        const td = document.createElement('td');
        if (idx === 0) {
          const strong = document.createElement('strong');
          setText(strong, val);
          td.appendChild(strong);
        } else {
          setText(td, val);
        }
        tr.appendChild(td);
      });
      sumTbody.appendChild(tr);
    });

    // Total row
    const totTr = document.createElement('tr');
    totTr.style.fontWeight = 'var(--fw-bold)';
    totTr.style.borderTop = '2px solid var(--c-border)';
    [
      'Total across all categories',
      String(totalAll),
      String(matchedAll),
      String(explainedAll),
      String(unexplainedAll),
    ].forEach((val, idx) => {
      const td = document.createElement('td');
      const strong = document.createElement('strong');
      setText(strong, val);
      td.appendChild(strong);
      totTr.appendChild(td);
    });
    sumTbody.appendChild(totTr);

    sumTbl.appendChild(sumTbody);
    sumWrap.appendChild(sumTbl);
    summaryCard.appendChild(sumWrap);
    container.appendChild(summaryCard);

    // 3. Filterable Table of 64 Cases
    const casesCard = document.createElement('div');
    casesCard.className = 'card';

    const casesH3 = document.createElement('h3');
    casesH3.style.marginBottom = 'var(--sp-3)';
    setText(casesH3, 'All 64 Edge Cases');
    casesCard.appendChild(casesH3);

    // Filter bar
    const filterBar = document.createElement('div');
    filterBar.className = 'table-filter-bar';

    const catLabel = document.createElement('label');
    catLabel.setAttribute('for', 'edge-cat-filter');
    setText(catLabel, 'Category:');
    filterBar.appendChild(catLabel);

    const catSelect = document.createElement('select');
    catSelect.id = 'edge-cat-filter';
    const catOptions = [
      { val: 'ALL', text: 'All categories (64)' },
      { val: 'TB', text: 'TB — Threshold & Boundary (40)' },
      { val: 'MD', text: 'MD — Missing Data & Types (9)' },
      { val: 'AD', text: 'AD — Adverse & Knockouts (7)' },
      { val: 'TF', text: 'TF — Thin File & Enquiries (4)' },
      { val: 'RC', text: 'RC — Repayment Capacity (4)' },
    ];
    catOptions.forEach(opt => {
      const opEl = document.createElement('option');
      opEl.value = opt.val;
      setText(opEl, opt.text);
      catSelect.appendChild(opEl);
    });
    filterBar.appendChild(catSelect);

    const statusLabel = document.createElement('label');
    statusLabel.setAttribute('for', 'edge-status-filter');
    statusLabel.style.marginLeft = 'var(--sp-2)';
    setText(statusLabel, 'Match status:');
    filterBar.appendChild(statusLabel);

    const statusSelect = document.createElement('select');
    statusSelect.id = 'edge-status-filter';
    const statusOptions = [
      { val: 'ALL', text: 'All statuses (64)' },
      { val: 'matched', text: 'Matched (61)' },
      { val: 'differs_explained', text: 'Differs explained (3)' },
    ];
    statusOptions.forEach(opt => {
      const opEl = document.createElement('option');
      opEl.value = opt.val;
      setText(opEl, opt.text);
      statusSelect.appendChild(opEl);
    });
    filterBar.appendChild(statusSelect);

    casesCard.appendChild(filterBar);

    // Table
    const casesWrap = document.createElement('div');
    casesWrap.className = 'table-scroll-wrap';

    const casesTbl = document.createElement('table');
    casesTbl.className = 'data-table';
    const casesThead = document.createElement('thead');
    const casesHRow = document.createElement('tr');
    ['Case ID', 'Cat', 'Description', 'Rule Decision', 'LR Decision', 'GB Decision', 'Match Status'].forEach(c => {
      const th = document.createElement('th');
      setText(th, c);
      casesHRow.appendChild(th);
    });
    casesThead.appendChild(casesHRow);
    casesTbl.appendChild(casesThead);

    const casesTbody = document.createElement('tbody');

    function renderFilteredRows() {
      casesTbody.textContent = '';
      const selectedCat = catSelect.value;
      const selectedStatus = statusSelect.value;

      const filtered = rows.filter(r => {
        if (selectedCat !== 'ALL' && r.category !== selectedCat) return false;
        if (selectedStatus !== 'ALL' && r.rule_status !== selectedStatus) return false;
        return true;
      });

      if (filtered.length === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 7;
        setText(td, 'No edge cases match the selected filter.');
        tr.appendChild(td);
        casesTbody.appendChild(tr);
        return;
      }

      filtered.forEach(r => {
        const tr = document.createElement('tr');
        const isExplainedDiff = r.rule_status === 'differs_explained';

        // 1. Case ID
        const tdId = document.createElement('td');
        const codeId = document.createElement('code');
        setText(codeId, r.case_id);
        tdId.appendChild(codeId);
        tr.appendChild(tdId);

        // 2. Category
        const tdCat = document.createElement('td');
        setText(tdCat, r.category);
        tr.appendChild(tdCat);

        // 3. Description
        const tdDesc = document.createElement('td');
        tdDesc.style.maxWidth = '300px';
        setText(tdDesc, r.description);
        tr.appendChild(tdDesc);

        // 4. Rule Decision
        const tdRule = document.createElement('td');
        const rBadge = document.createElement('span');
        const rDec = (r.rule_decision || '').toLowerCase();
        let rClass = 'badge--small ';
        if (rDec === 'eligible') rClass += 'badge--eligible';
        else if (rDec === 'refer') rClass += 'badge--refer';
        else rClass += 'badge--ineligible';
        rBadge.className = 'badge ' + rClass;
        setText(rBadge, (r.rule_decision || '—').toUpperCase());
        tdRule.appendChild(rBadge);
        tr.appendChild(tdRule);

        // 5. LR Decision
        const tdLr = document.createElement('td');
        const lrText = r.lr_decision ? `${r.lr_decision} (${r.lr_score})` : String(r.lr_score || '—');
        setText(tdLr, lrText);
        tr.appendChild(tdLr);

        // 6. GB Decision
        const tdGb = document.createElement('td');
        const gbText = r.gb_decision ? `${r.gb_decision} (${r.gb_score})` : String(r.gb_score || '—');
        setText(tdGb, gbText);
        tr.appendChild(tdGb);

        // 7. Match Status
        const tdStatus = document.createElement('td');
        const sBadge = document.createElement('span');
        if (isExplainedDiff) {
          sBadge.className = 'badge badge--refer badge--small';
          setText(sBadge, 'Differs (explained)');
          if (r.ml_explanation) sBadge.title = r.ml_explanation;
        } else {
          sBadge.className = 'badge badge--eligible badge--small';
          setText(sBadge, 'Matched');
        }
        tdStatus.appendChild(sBadge);
        tr.appendChild(tdStatus);

        casesTbody.appendChild(tr);
      });
    }

    catSelect.addEventListener('change', renderFilteredRows);
    statusSelect.addEventListener('change', renderFilteredRows);
    renderFilteredRows();

    casesTbl.appendChild(casesTbody);
    casesWrap.appendChild(casesTbl);
    casesCard.appendChild(casesWrap);
    container.appendChild(casesCard);

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
