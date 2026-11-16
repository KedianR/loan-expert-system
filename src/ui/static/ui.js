/**
 * ui.js — Apply page ES module
 * Rules:
 *   1. NEVER use .innerHTML = (assignment). Only DOM methods.
 *   2. NEVER use parseFloat or Number() on money-ish variable names.
 *      credit_score uses parseInt (it is an integer field).
 *   3. Never mention protected column names.
 *   4. All API strings go in via el.textContent = value (or setText helper).
 *   5. No framework, no CDN import, no fetch of external URLs.
 *
 * FR-UI-01, FR-UI-02, FR-UI-03, FR-UI-04, FR-UI-05
 */

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

/** Sets el.textContent safely. Use everywhere instead of innerHTML. */
export function setText(el, val) {
  if (el) el.textContent = String(val ?? '');
}

// ---------------------------------------------------------------------------
// SVG icons — built with DOM, never innerHTML
// ---------------------------------------------------------------------------

function makeSvgEl(tag, attrs) {
  const NS = 'http://www.w3.org/2000/svg';
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    el.setAttribute(k, v);
  }
  return el;
}

function iconCheckmark() {
  const svg = makeSvgEl('svg', { viewBox: '0 0 20 20', width: '20', height: '20', 'aria-hidden': 'true', fill: 'none', stroke: 'currentColor', 'stroke-width': '2.5', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });
  const poly = makeSvgEl('polyline', { points: '3,10 8,16 17,5' });
  svg.appendChild(poly);
  return svg;
}

function iconCross() {
  const svg = makeSvgEl('svg', { viewBox: '0 0 20 20', width: '20', height: '20', 'aria-hidden': 'true', fill: 'none', stroke: 'currentColor', 'stroke-width': '2.5', 'stroke-linecap': 'round' });
  const l1 = makeSvgEl('line', { x1: '4', y1: '4', x2: '16', y2: '16' });
  const l2 = makeSvgEl('line', { x1: '16', y1: '4', x2: '4', y2: '16' });
  svg.appendChild(l1);
  svg.appendChild(l2);
  return svg;
}

function iconClock() {
  const svg = makeSvgEl('svg', { viewBox: '0 0 20 20', width: '20', height: '20', 'aria-hidden': 'true', fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round' });
  const circle = makeSvgEl('circle', { cx: '10', cy: '10', r: '8' });
  const hand1 = makeSvgEl('line', { x1: '10', y1: '5', x2: '10', y2: '10' });
  const hand2 = makeSvgEl('line', { x1: '10', y1: '10', x2: '14', y2: '12' });
  svg.appendChild(circle);
  svg.appendChild(hand1);
  svg.appendChild(hand2);
  return svg;
}

// ---------------------------------------------------------------------------
// Presets
// ---------------------------------------------------------------------------

/**
 * Fetch GET /ui/presets and populate #preset-buttons with preset buttons.
 * FR-UI-01
 */
export async function loadPresets() {
  const container = document.getElementById('preset-buttons');
  if (!container) return;
  try {
    const res = await fetch('/ui/presets');
    if (!res.ok) throw new Error('fetch failed');
    const data = await res.json();
    const presets = data.presets || [];
    container.textContent = '';
    presets.forEach(preset => {
      const btn = document.createElement('button');
      btn.className = 'btn btn--secondary preset-btn';
      btn.type = 'button';
      setText(btn, preset.id + ' — ' + (preset.description || ''));
      btn.addEventListener('click', () => {
        applyPreset(preset.input);
        const form = document.getElementById('app-form');
        if (form) form.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      container.appendChild(btn);
    });
  } catch (_) {
    container.textContent = '';
    const msg = document.createElement('span');
    setText(msg, 'Example presets not available');
    container.appendChild(msg);
  }
}

/**
 * Fill form fields from a preset input object.
 * FR-UI-01
 */
export function applyPreset(inputObj) {
  const intFields = [
    'age', 'employment_months', 'monthly_net_income', 'monthly_obligations',
    'credit_score', 'enquiries_6m', 'requested_amount', 'requested_tenure_months',
  ];
  const checkboxFields = [
    'kyc_verified', 'consent_given', 'severe_delinquency_36m', 'written_off',
  ];
  const selectFields = ['employment_type'];
  const textFields = ['applicant_id'];
  const intNullable = ['region_tier'];

  const setField = (name, val) => {
    const el = document.getElementById(name);
    if (!el) return;
    if (checkboxFields.includes(name)) {
      el.checked = !!val;
    } else if (intNullable.includes(name)) {
      el.value = val != null ? String(val) : '';
    } else if (intFields.includes(name)) {
      el.value = val != null ? String(val) : '';
    } else if (selectFields.includes(name)) {
      el.value = val != null ? val : '';
    } else if (textFields.includes(name)) {
      el.value = val != null ? String(val) : '';
    }
  };

  [
    'applicant_id', 'age', 'employment_type', 'employment_months',
    'monthly_net_income', 'monthly_obligations', 'credit_score',
    'enquiries_6m', 'requested_amount', 'requested_tenure_months',
    'region_tier',
  ].forEach(name => setField(name, inputObj[name] ?? null));

  checkboxFields.forEach(name => setField(name, inputObj[name] ?? false));
}

// ---------------------------------------------------------------------------
// Payload builder
// ---------------------------------------------------------------------------

/**
 * Read form fields and return JSON-serialisable payload object.
 * Uses parseInt for integer fields; leaves null if empty.
 * Does NOT parse money fields as numbers at display time.
 * FR-UI-02
 */
export function buildPayload() {
  const field = id => document.getElementById(id);
  const strVal = id => (field(id) ? field(id).value.trim() : '');
  const intOrNull = id => { const v = strVal(id); return v === '' ? null : parseInt(v, 10); };

  // credit_score: integer field — use parseInt, not parseFloat
  const creditScoreVal = strVal('credit_score');
  const creditScore = creditScoreVal === '' ? null : parseInt(creditScoreVal, 10);

  const regionTierVal = strVal('region_tier');
  const regionTier = regionTierVal === '' ? null : parseInt(regionTierVal, 10);

  const payload = {
    applicant_id: strVal('applicant_id') || 'demo',
    age: intOrNull('age'),
    employment_type: strVal('employment_type') || 'salaried',
    employment_months: intOrNull('employment_months'),
    monthly_net_income: intOrNull('monthly_net_income'),
    monthly_obligations: intOrNull('monthly_obligations'),
    credit_score: creditScore,
    enquiries_6m: intOrNull('enquiries_6m'),
    severe_delinquency_36m: field('severe_delinquency_36m') ? field('severe_delinquency_36m').checked : false,
    written_off: field('written_off') ? field('written_off').checked : false,
    kyc_verified: field('kyc_verified') ? field('kyc_verified').checked : true,
    consent_given: field('consent_given') ? field('consent_given').checked : true,
    requested_amount: intOrNull('requested_amount'),
    requested_tenure_months: intOrNull('requested_tenure_months'),
  };

  // Only include region_tier if field has a value
  if (regionTier !== null) {
    payload.region_tier = regionTier;
  }

  return payload;
}

// ---------------------------------------------------------------------------
// Error display
// ---------------------------------------------------------------------------

/** Clear all .form-group__error elements. FR-UI-03 */
export function clearErrors() {
  document.querySelectorAll('.form-group__error').forEach(el => setText(el, ''));
  // Also support legacy .field-error class
  document.querySelectorAll('.field-error').forEach(el => setText(el, ''));
}

/** Set text on #err-{fieldId}. FR-UI-03 */
export function showFieldError(fieldId, msg) {
  const el = document.getElementById('err-' + fieldId);
  if (el) setText(el, msg);
}

// ---------------------------------------------------------------------------
// Button loading state
// ---------------------------------------------------------------------------

/** Add/remove btn--loading class and disabled attr. FR-UI-02 */
export function setButtonLoading(btn, isLoading) {
  if (!btn) return;
  if (isLoading) {
    btn.classList.add('btn--loading');
    btn.setAttribute('disabled', '');
  } else {
    btn.classList.remove('btn--loading');
    btn.removeAttribute('disabled');
  }
}

// ---------------------------------------------------------------------------
// Money display helper
// ---------------------------------------------------------------------------

/** Prepend ₹ if the string does not already start with ₹. Never reformats. */
function displayMoney(str) {
  if (str == null) return '—';
  const s = String(str);
  return s.startsWith('₹') ? s : '₹' + s;
}

// ---------------------------------------------------------------------------
// ML result display
// ---------------------------------------------------------------------------

/**
 * Fill the ML card inside the report container.
 * FR-UI-05
 */
export function displayMLResult(mlData, container) {
  if (!container) return;
  container.textContent = '';

  // Required disclaimer line
  const disclaimer = document.createElement('p');
  disclaimer.className = 'ml-disclaimer';
  setText(disclaimer, 'This score does not feed the decision. It is a ranking score, not a probability.');
  container.appendChild(disclaimer);

  if (!mlData || mlData.available === false) {
    const msg = document.createElement('p');
    setText(msg, mlData ? (mlData.message || 'Not available') : 'Not available');
    container.appendChild(msg);
    return;
  }

  // Score value
  const scoreP = document.createElement('p');
  const scoreLabel = document.createElement('strong');
  setText(scoreLabel, 'Score: ');
  scoreP.appendChild(scoreLabel);
  const scoreVal = document.createElement('span');
  setText(scoreVal, String(mlData.score ?? '—'));
  scoreP.appendChild(scoreVal);
  container.appendChild(scoreP);

  // Top-3 contributions table
  const contribs = (mlData.contributions || []).slice(0, 3);
  if (contribs.length > 0) {
    const h4 = document.createElement('h4');
    setText(h4, 'Top contributions');
    container.appendChild(h4);

    const tbl = document.createElement('table');
    tbl.className = 'data-table';
    const thead = document.createElement('thead');
    const hrow = document.createElement('tr');
    ['Feature', 'Contribution'].forEach(col => {
      const th = document.createElement('th');
      setText(th, col);
      hrow.appendChild(th);
    });
    thead.appendChild(hrow);
    tbl.appendChild(thead);

    const tbody = document.createElement('tbody');
    contribs.forEach(c => {
      const tr = document.createElement('tr');
      const featureTd = document.createElement('td');
      const contribTd = document.createElement('td');
      if (typeof c === 'object' && c !== null) {
        setText(featureTd, String(c.feature ?? ''));
        setText(contribTd, String(c.contribution ?? ''));
      } else {
        setText(featureTd, String(c));
        setText(contribTd, '');
      }
      tr.appendChild(featureTd);
      tr.appendChild(contribTd);
      tbody.appendChild(tr);
    });
    tbl.appendChild(tbody);
    container.appendChild(tbl);
  }
}

// ---------------------------------------------------------------------------
// Report builder
// ---------------------------------------------------------------------------

/**
 * Build the full report DOM tree inside #report-section.
 * Uses ONLY DOM methods — no innerHTML assignment.
 * FR-UI-04
 */
export function buildReport(data) {
  const section = document.getElementById('report-section');
  if (!section) return;
  section.textContent = '';
  section.removeAttribute('hidden');

  const decision = (data.decision || 'unknown').toLowerCase();

  // ----- Section 1: Header card -----
  const headerCard = document.createElement('div');
  headerCard.className = 'card report-header';

  // Status badge
  const badge = document.createElement('span');
  badge.className = 'badge badge--' + decision;

  let icon;
  if (decision === 'eligible') icon = iconCheckmark();
  else if (decision === 'ineligible') icon = iconCross();
  else icon = iconClock();
  badge.appendChild(icon);

  const badgeLabel = document.createElement('span');
  badgeLabel.className = 'badge__label';
  const decisionWord = decision.charAt(0).toUpperCase() + decision.slice(1);
  setText(badgeLabel, decisionWord);
  badge.appendChild(badgeLabel);
  headerCard.appendChild(badge);

  // Subtitle
  const subtitle = document.createElement('p');
  subtitle.className = 'report-subtitle';
  setText(subtitle, 'Application ' + (data.applicant_id || ''));
  headerCard.appendChild(subtitle);

  // Buttons row
  const btnRow = document.createElement('div');
  btnRow.className = 'report-actions';

  const printBtn = document.createElement('button');
  printBtn.className = 'btn btn--ghost btn--print';
  printBtn.type = 'button';
  setText(printBtn, 'Print / save as PDF');
  printBtn.addEventListener('click', () => window.print());
  btnRow.appendChild(printBtn);

  const newBtn = document.createElement('button');
  newBtn.className = 'btn btn--ghost';
  newBtn.type = 'button';
  setText(newBtn, 'New application');
  newBtn.addEventListener('click', () => clearForm());
  btnRow.appendChild(newBtn);

  headerCard.appendChild(btnRow);
  section.appendChild(headerCard);

  // ----- Section 2: Summary tiles -----
  const tilesDiv = document.createElement('div');
  tilesDiv.className = 'summary-tiles';

  if (decision === 'eligible' && data.offer) {
    const recAmount = data.offer.amount != null ? data.offer.amount : data.offer.recommended_amount;
    const rateVal = data.offer.indicative_rate != null ? (data.offer.indicative_rate + '%') : (data.offer.rate_pct != null ? (data.offer.rate_pct + '%') : (data.offer.interest_rate || '—'));
    const tileData = [
      { label: 'Recommended amount', value: displayMoney(recAmount) },
      { label: 'Band', value: data.offer.band || '—' },
      { label: 'Interest rate', value: rateVal },
      { label: 'Monthly EMI', value: displayMoney(data.offer.emi) },
    ];
    tileData.forEach(({ label, value }) => {
      const tile = document.createElement('div');
      tile.className = 'tile';
      const tileLabel = document.createElement('span');
      tileLabel.className = 'tile__label';
      setText(tileLabel, label);
      const tileValue = document.createElement('span');
      tileValue.className = 'tile__value';
      setText(tileValue, value);
      tile.appendChild(tileLabel);
      tile.appendChild(tileValue);
      tilesDiv.appendChild(tile);
    });
  } else if (decision === 'ineligible') {
    const tile = document.createElement('div');
    tile.className = 'tile';
    const tileLabel = document.createElement('span');
    tileLabel.className = 'tile__label';
    setText(tileLabel, 'Main reason');
    const tileValue = document.createElement('span');
    tileValue.className = 'tile__value';
    const notices = Array.isArray(data.notice) ? data.notice : (data.notice && Array.isArray(data.notice.reasons) ? data.notice.reasons : []);
    const firstReason = notices.length > 0
      ? (notices[0].text || notices[0].code || '—')
      : ((data.reason_codes || [])[0] || '—');
    setText(tileValue, firstReason);
    tile.appendChild(tileLabel);
    tile.appendChild(tileValue);
    tilesDiv.appendChild(tile);
  } else {
    // refer
    const tile = document.createElement('div');
    tile.className = 'tile';
    const tileLabel = document.createElement('span');
    tileLabel.className = 'tile__label';
    setText(tileLabel, 'Status');
    const tileValue = document.createElement('span');
    tileValue.className = 'tile__value';
    setText(tileValue, 'Goes to a human reviewer');
    tile.appendChild(tileLabel);
    tile.appendChild(tileValue);
    tilesDiv.appendChild(tile);
  }
  section.appendChild(tilesDiv);

  // ----- Section 3: Accordion sections -----

  // 3a — Applicant inputs
  section.appendChild(makeAccordion('1 Applicant inputs', el => {
    buildApplicantInputs(el, data);
  }));

  // 3b — Why
  section.appendChild(makeAccordion('2 Why', el => {
    buildWhySection(el, data);
  }));

  // 3c — Offer summary (only for eligible)
  if (decision === 'eligible') {
    section.appendChild(makeAccordion('3 Offer summary', el => {
      buildOfferSummary(el, data);
    }));
  }

  // 3d — Rule trace
  section.appendChild(makeAccordion('4 Rule trace', el => {
    buildRuleTrace(el, data);
  }));

  // 3e — Record
  section.appendChild(makeAccordion('5 Record', el => {
    buildRecord(el, data);
  }));

  // 3f — ML comparison
  section.appendChild(makeAccordion('6 ML comparison — comparison only', el => {
    const loadingP = document.createElement('p');
    loadingP.id = 'ml-report-container';
    setText(loadingP, 'Loading ML score\u2026');
    el.appendChild(loadingP);
  }));
}

// ---------------------------------------------------------------------------
// Accordion helper
// ---------------------------------------------------------------------------

function makeAccordion(title, populateFn) {
  const details = document.createElement('details');
  details.className = 'report-section';
  details.setAttribute('open', '');

  const summary = document.createElement('summary');
  summary.className = 'section-header';
  setText(summary, title);
  details.appendChild(summary);

  const body = document.createElement('div');
  body.className = 'section-body';
  populateFn(body);
  details.appendChild(body);

  return details;
}

// ---------------------------------------------------------------------------
// Accordion section builders
// ---------------------------------------------------------------------------

const FIELD_LABELS = {
  applicant_id: 'Applicant ID',
  age: 'Age',
  employment_type: 'Employment type',
  employment_months: 'Employment duration (months)',
  monthly_net_income: 'Monthly net income',
  monthly_obligations: 'Monthly obligations',
  credit_score: 'Credit score',
  enquiries_6m: 'Enquiries (last 6 months)',
  severe_delinquency_36m: 'Severe delinquency (last 36 months)',
  written_off: 'Written off',
  kyc_verified: 'KYC verified',
  consent_given: 'Consent given',
  requested_amount: 'Requested amount',
  requested_tenure_months: 'Requested tenure (months)',
  region_tier: 'Region tier',
};

function buildApplicantInputs(el, data) {
  const payload = data._submitted_payload || data.input || {};
  const dl = document.createElement('dl');
  dl.className = 'applicant-inputs-list';

  const fields = Object.keys(FIELD_LABELS);
  fields.forEach(key => {
    if (!(key in payload)) return;
    const val = payload[key];
    const dt = document.createElement('dt');
    setText(dt, FIELD_LABELS[key] || key);
    const dd = document.createElement('dd');
    if (val === null || val === undefined) {
      setText(dd, '\u2014');
    } else if (typeof val === 'boolean') {
      setText(dd, val ? 'Yes' : 'No');
    } else {
      setText(dd, String(val));
    }
    dl.appendChild(dt);
    dl.appendChild(dd);
  });

  if (!dl.hasChildNodes()) {
    const p = document.createElement('p');
    setText(p, 'No submitted fields available.');
    el.appendChild(p);
  } else {
    el.appendChild(dl);
  }
}

function buildWhySection(el, data) {
  const notices = Array.isArray(data.notice) ? data.notice : (data.notice && Array.isArray(data.notice.reasons) ? data.notice.reasons : []);
  const reasonCodes = data.reason_codes || [];
  const decision = (data.decision || '').toLowerCase();

  if (decision === 'eligible' && notices.length === 0 && reasonCodes.length === 0) {
    const p = document.createElement('p');
    setText(p, 'All policy rules passed.');
    el.appendChild(p);
    return;
  }

  if (notices.length > 0) {
    notices.forEach(item => {
      const div = document.createElement('div');
      div.className = 'reason-item';
      if (item.code) {
        const codeSpan = document.createElement('span');
        codeSpan.className = 'reason-code';
        setText(codeSpan, item.code);
        div.appendChild(codeSpan);
      }
      if (item.text) {
        const textP = document.createElement('p');
        setText(textP, item.text);
        div.appendChild(textP);
      }
      el.appendChild(div);
    });
  } else if (reasonCodes.length > 0) {
    // Show codes only
    reasonCodes.forEach(code => {
      const div = document.createElement('div');
      div.className = 'reason-item';
      const codeSpan = document.createElement('span');
      codeSpan.className = 'reason-code';
      setText(codeSpan, String(code));
      div.appendChild(codeSpan);
      el.appendChild(div);
    });
  } else {
    const p = document.createElement('p');
    setText(p, 'All policy rules passed.');
    el.appendChild(p);
  }
}

function buildOfferSummary(el, data) {
  const offer = data.offer || {};
  const recAmount = offer.amount != null ? offer.amount : offer.recommended_amount;
  const rateVal = offer.indicative_rate != null ? (offer.indicative_rate + '%') : (offer.rate_pct != null ? (offer.rate_pct + '%') : (offer.interest_rate || '—'));
  const feeVal = offer.fee != null ? offer.fee : offer.processing_fee;
  const totalVal = offer.total_repayment != null ? displayMoney(offer.total_repayment) : (offer.total_interest != null ? ('Total interest: ' + displayMoney(offer.total_interest)) : '—');
  const rows = [
    ['Recommended amount', displayMoney(recAmount)],
    ['Band', offer.band || '—'],
    ['Rate', rateVal],
    ['EMI', displayMoney(offer.emi)],
    ['Processing fee', displayMoney(feeVal)],
    ['APR', offer.apr != null ? (String(offer.apr) + '%') : '—'],
    ['Total repayment', totalVal],
  ];

  const tbl = document.createElement('table');
  tbl.className = 'data-table';
  const tbody = document.createElement('tbody');
  rows.forEach(([label, value]) => {
    const tr = document.createElement('tr');
    const th = document.createElement('th');
    setText(th, label);
    const td = document.createElement('td');
    setText(td, value);
    tr.appendChild(th);
    tr.appendChild(td);
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
  el.appendChild(tbl);
}

function buildRuleTrace(el, data) {
  const trace = Array.isArray(data.trace) ? data.trace : (data.trace && Array.isArray(data.trace.steps) ? data.trace.steps : []);

  if (trace.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    setText(empty, 'No trace available.');
    el.appendChild(empty);
    return;
  }

  const tbl = document.createElement('table');
  tbl.className = 'data-table';

  const thead = document.createElement('thead');
  const hrow = document.createElement('tr');
  ['Rule ID', 'Rule version', 'Facts used', 'Result'].forEach(col => {
    const th = document.createElement('th');
    th.style.position = 'sticky';
    th.style.top = '0';
    setText(th, col);
    hrow.appendChild(th);
  });
  thead.appendChild(hrow);
  tbl.appendChild(thead);

  const tbody = document.createElement('tbody');
  trace.forEach(entry => {
    const tr = document.createElement('tr');
    let factsStr = '';
    if (Array.isArray(entry.facts_used)) {
      factsStr = entry.facts_used.join(', ');
    } else if (entry.facts_used && typeof entry.facts_used === 'object') {
      factsStr = Object.entries(entry.facts_used)
        .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
        .join(', ');
    } else {
      factsStr = String(entry.facts_used || '—');
    }

    let resultStr = entry.result || entry.status || '';
    if (entry.outcome) {
      resultStr += ` (${entry.outcome})`;
    }

    const cells = [
      String(entry.rule_id || '—'),
      String(entry.rule_version || '—'),
      factsStr || '—',
      resultStr || '—',
    ];
    cells.forEach(val => {
      const td = document.createElement('td');
      setText(td, val);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
  el.appendChild(tbl);
}

function buildRecord(el, data) {
  const rows = [
    ['Decision ID', data.decision_id || data.id || '—'],
    ['Rule-set tag / version', data.rule_set_tag || data.rule_set_version || '—'],
    ['Rule-set hash', data.rule_set_hash || '—'],
    ['Audit stored', data.audit_stored === true ? 'Yes' : data.audit_stored === false ? 'No' : (data.decision_id ? 'Yes' : 'Unknown')],
  ];

  const tbl = document.createElement('table');
  tbl.className = 'data-table';
  const tbody = document.createElement('tbody');
  rows.forEach(([label, value]) => {
    const tr = document.createElement('tr');
    const th = document.createElement('th');
    setText(th, label);
    const td = document.createElement('td');
    setText(td, value);
    tr.appendChild(th);
    tr.appendChild(td);
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
  el.appendChild(tbl);
}

// ---------------------------------------------------------------------------
// Inline toast
// ---------------------------------------------------------------------------

function showToast(msg) {
  let toast = document.getElementById('inline-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'inline-toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  setText(toast, msg);
  toast.classList.add('toast--show');
  setTimeout(() => toast.classList.remove('toast--show'), 5000);
}

// ---------------------------------------------------------------------------
// Form submit handler
// ---------------------------------------------------------------------------

/**
 * Handle form submission.
 * FR-UI-02, FR-UI-04, FR-UI-05
 */
export async function handleSubmit(e) {
  e.preventDefault();
  clearErrors();

  const btn = document.getElementById('submit-btn');
  setButtonLoading(btn, true);

  const payload = buildPayload();

  try {
    const res = await fetch('/ui/decide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (res.ok && data.decision) {
      // Attach submitted payload so buildReport can display applicant inputs
      data._submitted_payload = payload;
      buildReport(data);

      const reportSection = document.getElementById('report-section');
      if (reportSection) {
        reportSection.scrollIntoView({ behavior: 'smooth' });
      }

      // ML score — separate call, failure must not block decision display
      const mlContainer = document.getElementById('ml-report-container');
      if (mlContainer) {
        setText(mlContainer, 'Loading ML score\u2026');
        try {
          const mlRes = await fetch('/ui/ml-score', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          const mlData = await mlRes.json();
          displayMLResult(mlData, mlContainer);
        } catch (_) {
          displayMLResult({ available: false, message: 'Not available' }, mlContainer);
        }
      }
    } else if (data.errors && typeof data.errors === 'object') {
      Object.entries(data.errors).forEach(([field, msg]) => showFieldError(field, msg));
    } else {
      showToast('Service unavailable \u2014 please try again.');
    }
  } catch (_) {
    showToast('Service unavailable \u2014 please try again.');
  } finally {
    setButtonLoading(btn, false);
  }
}

// ---------------------------------------------------------------------------
// Clear form
// ---------------------------------------------------------------------------

/** Reset all form fields to empty/defaults, hide #report-section. FR-UI-03 */
export function clearForm() {
  const form = document.getElementById('app-form');
  if (form) form.reset();
  clearErrors();
  const reportSection = document.getElementById('report-section');
  if (reportSection) {
    reportSection.setAttribute('hidden', '');
    reportSection.textContent = '';
  }
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('app-form');
  if (form) {
    form.addEventListener('submit', handleSubmit);
    loadPresets();
  }
  const clearBtn = document.getElementById('clear-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', clearForm);
  }
});
