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
  // Create the text and <code> element via DOM, not innerHTML
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

  tabBtns.forEach(b => {
    const isThis = b.dataset.tab === name;
    b.setAttribute('aria-selected', isThis ? 'true' : 'false');
    b.classList.toggle('active', isThis);
    b.tabIndex = isThis ? 0 : -1;
  });

  // Show/hide panels
  document.querySelectorAll('.tab-panel, .tab-content').forEach(panel => {
    if (panel.id === 'tab-' + name) {
      panel.hidden = false;
      panel.classList.add('active');
    } else {
      panel.hidden = true;
      panel.classList.remove('active');
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

  const reports = ['metrics_d2_lr', 'metrics_d2_gb'];
  let anyAvailable = false;

  for (const name of reports) {
    try {
      const res = await fetch('/ui/report/' + name);
      if (!res.ok) throw new Error('not ok');
      const data = await res.json();

      const heading = document.createElement('h3');
      setText(heading, name);
      container.appendChild(heading);

      if (data.available === false) {
        const p = document.createElement('p');
        setText(p, data.message || 'Not generated yet.');
        container.appendChild(p);
      } else {
        anyAvailable = true;
        const pre = document.createElement('pre');
        pre.className = 'report-block';
        const content = data.content != null ? data.content : JSON.stringify(data, null, 2);
        setText(pre, content);
        container.appendChild(pre);
      }
    } catch (_) {
      const heading = document.createElement('h3');
      setText(heading, name);
      container.appendChild(heading);
      const p = document.createElement('p');
      setText(p, 'Not generated yet.');
      container.appendChild(p);
    }
  }

  if (!anyAvailable && container.childElementCount === 0) {
    makeEmptyState(container);
  }
}

// ---------------------------------------------------------------------------
// Comparison tab: comparison_scorecard
// ---------------------------------------------------------------------------

async function loadComparisonTab() {
  const container = document.getElementById('content-scorecard') || document.getElementById('content-comparison') || document.getElementById('comparison-content');
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

    // If the payload has a content string, show as pre
    if (data.content != null) {
      const pre = document.createElement('pre');
      pre.className = 'report-block';
      setText(pre, data.content);
      container.appendChild(pre);
      return;
    }

    // If data itself is an object (scorecard rows), render as table
    if (typeof data === 'object' && data !== null) {
      renderScorecardTable(container, data);
    } else {
      makeEmptyState(container);
    }
  } catch (_) {
    makeEmptyState(container);
  }
}

function renderScorecardTable(container, data) {
  const entries = Object.entries(data).filter(([k]) => k !== 'available' && k !== 'content');
  if (entries.length === 0) {
    makeEmptyState(container);
    return;
  }

  const tbl = document.createElement('table');
  tbl.className = 'data-table';
  const thead = document.createElement('thead');
  const hrow = document.createElement('tr');
  ['Metric', 'Value'].forEach(col => {
    const th = document.createElement('th');
    setText(th, col);
    hrow.appendChild(th);
  });
  thead.appendChild(hrow);
  tbl.appendChild(thead);

  const tbody = document.createElement('tbody');
  entries.forEach(([key, val]) => {
    const tr = document.createElement('tr');
    const keyTd = document.createElement('td');
    setText(keyTd, key);
    const valTd = document.createElement('td');
    setText(valTd, typeof val === 'object' ? JSON.stringify(val) : String(val));
    tr.appendChild(keyTd);
    tr.appendChild(valTd);
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
  container.appendChild(tbl);
}

// ---------------------------------------------------------------------------
// Fairness tab: d2_tables + d3_tables
// ---------------------------------------------------------------------------

async function loadFairnessTab() {
  const container = document.getElementById('content-fairness') || document.getElementById('fairness-content');
  if (!container) return;
  container.textContent = '';

  const sources = [
    { key: 'd2_tables', label: 'D2 Fairness Tables' },
    { key: 'd3_tables', label: 'D3 Fairness Tables' },
  ];

  for (const { key, label } of sources) {
    const h3 = document.createElement('h3');
    setText(h3, label);
    container.appendChild(h3);

    try {
      const res = await fetch('/ui/report/' + key);
      if (!res.ok) throw new Error('not ok');
      const data = await res.json();

      if (data.available === false) {
        const p = document.createElement('p');
        setText(p, 'Not generated yet; run make fairness');
        container.appendChild(p);
        continue;
      }

      const content = data.content != null ? data.content : JSON.stringify(data, null, 2);
      const pre = document.createElement('pre');
      pre.className = 'report-block';
      setText(pre, content);
      container.appendChild(pre);

      // Add chips for too_small and unstable markers found in the content
      const chipRow = document.createElement('div');
      chipRow.className = 'chip-row';
      let hasChips = false;
      if (content.includes('too_small')) { addChip(chipRow, 'too_small'); hasChips = true; }
      if (content.includes('unstable')) { addChip(chipRow, 'unstable'); hasChips = true; }
      if (hasChips) container.appendChild(chipRow);

    } catch (_) {
      const p = document.createElement('p');
      setText(p, 'Not generated yet; run make fairness');
      container.appendChild(p);
    }
  }
}

// ---------------------------------------------------------------------------
// Edge-cases tab: edge_case_summary
// ---------------------------------------------------------------------------

async function loadEdgeTab() {
  const container = document.getElementById('content-edge') || document.getElementById('edge-content');
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

    const content = data.content != null ? data.content : JSON.stringify(data, null, 2);
    const pre = document.createElement('pre');
    pre.className = 'report-block';
    setText(pre, content);
    container.appendChild(pre);
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

  // Set initial aria-selected and tabIndex
  tabBtns.forEach((btn, i) => {
    btn.setAttribute('aria-selected', i === 0 ? 'true' : 'false');
    btn.tabIndex = i === 0 ? 0 : -1;
  });

  // Load first tab (ml) immediately
  _loadedTabs.add('ml');
  loadTab('ml');
});
