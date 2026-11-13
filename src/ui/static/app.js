/* app.js — Loan Eligibility Demo UI
 * Rules (docs/ui-spec.md §2):
 *   1. Never compute a decision/amount/rate. Show what the service returns unchanged.
 *   2. ML score is a separate call; failure shows "Not available".
 *   3. No protected attribute collected, shown or mentioned.
 *   4. All API strings inserted with textContent, never innerHTML.
 *   5. No parseFloat/Number() on money fields — display as returned strings.
 */

'use strict';

// ---------------------------------------------------------------------------
// Utility: safe text setter (enforces rule 4)
// ---------------------------------------------------------------------------
function setText(el, value) {
  if (el) el.textContent = String(value == null ? '' : value);
}

// ---------------------------------------------------------------------------
// Presets
// ---------------------------------------------------------------------------
async function loadPresets() {
  const sel = document.getElementById('preset-select');
  if (!sel) return;
  try {
    const res = await fetch('/ui/presets');
    if (!res.ok) return;
    const data = await res.json();
    (data.presets || []).forEach(p => {
      const opt = document.createElement('option');
      opt.value = JSON.stringify(p.input);
      setText(opt, p.id + (p.description ? ' — ' + p.description : ''));
      sel.appendChild(opt);
    });
  } catch (_) { /* silent — presets are optional */ }
}

function applyPreset(inputJson) {
  const inp = JSON.parse(inputJson);
  const fields = [
    'applicant_id', 'age', 'employment_type', 'employment_months',
    'monthly_net_income', 'monthly_obligations', 'credit_score',
    'enquiries_6m', 'requested_amount', 'requested_tenure_months',
    'kyc_verified', 'consent_given', 'severe_delinquency_36m', 'written_off',
  ];
  fields.forEach(name => {
    const el = document.getElementById(name);
    if (!el) return;
    if (el.type === 'checkbox') {
      el.checked = !!inp[name];
    } else if (inp[name] !== undefined && inp[name] !== null) {
      el.value = inp[name];
    } else {
      el.value = '';
    }
  });
}

// ---------------------------------------------------------------------------
// Form submission → /ui/decide
// ---------------------------------------------------------------------------
function buildPayload() {
  const field = id => document.getElementById(id);
  const intOrNull = id => {
    const v = field(id) ? field(id).value.trim() : '';
    return v === '' ? null : parseInt(v, 10);
  };
  const floatOrNull = id => {
    const v = field(id) ? field(id).value.trim() : '';
    return v === '' ? null : parseFloat(v);  // credit_score only — not money
  };

  return {
    applicant_id: field('applicant_id') ? field('applicant_id').value.trim() : 'demo',
    age: intOrNull('age'),
    employment_type: field('employment_type') ? field('employment_type').value : 'salaried',
    employment_months: intOrNull('employment_months'),
    monthly_net_income: intOrNull('monthly_net_income'),
    monthly_obligations: intOrNull('monthly_obligations'),
    credit_score: floatOrNull('credit_score'),
    enquiries_6m: intOrNull('enquiries_6m'),
    requested_amount: intOrNull('requested_amount'),
    requested_tenure_months: intOrNull('requested_tenure_months'),
    kyc_verified: field('kyc_verified') ? field('kyc_verified').checked : true,
    consent_given: field('consent_given') ? field('consent_given').checked : true,
    severe_delinquency_36m: field('severe_delinquency_36m') ? field('severe_delinquency_36m').checked : false,
    written_off: field('written_off') ? field('written_off').checked : false,
  };
}

function clearErrors() {
  document.querySelectorAll('.field-error').forEach(el => setText(el, ''));
}

function showError(fieldId, msg) {
  const el = document.getElementById('err-' + fieldId);
  if (el) setText(el, msg);
}

function displayResult(data) {
  const section = document.getElementById('result-section');
  if (!section) return;
  section.hidden = false;

  // Decision (large label — not conveyed by color alone, also shown as text)
  const box = document.getElementById('decision-box');
  const label = document.getElementById('decision-label');
  const dec = data.decision || 'unknown';
  box.className = 'decision-box ' + dec;
  setText(label, dec.toUpperCase());

  // Offer (eligible only)
  const offerSection = document.getElementById('offer-section');
  if (data.offer && data.decision === 'eligible') {
    offerSection.hidden = false;
    const amount = document.getElementById('offer-amount');
    const band = document.getElementById('offer-band');
    // Rule: show as returned strings — do NOT use parseFloat/toFixed
    setText(amount, data.offer.recommended_amount != null
      ? '\u20B9' + String(data.offer.recommended_amount) : 'N/A');
    setText(band, data.offer.band || 'N/A');
  } else if (offerSection) {
    offerSection.hidden = true;
  }

  // Reasons
  const list = document.getElementById('reasons-list');
  if (list) {
    list.textContent = '';
    const reasons = (data.reason_codes || []);
    if (reasons.length === 0) {
      const li = document.createElement('li');
      setText(li, 'No specific reason codes.');
      list.appendChild(li);
    } else {
      reasons.forEach(code => {
        const li = document.createElement('li');
        // Try to show notice text if available
        let text = code;
        if (data.notice && typeof data.notice === 'object') {
          const bodyItems = data.notice.body || [];
          const match = bodyItems.find(b => b && b.code === code);
          if (match && match.text) text = code + ' — ' + match.text;
        }
        setText(li, text);
        list.appendChild(li);
      });
    }
  }

  // Trace (collapsible)
  const traceEl = document.getElementById('trace-content');
  if (traceEl && data.trace) {
    setText(traceEl, JSON.stringify(data.trace, null, 2));
  }
}

function displayMLResult(data) {
  const el = document.getElementById('ml-content');
  if (!el) return;
  el.textContent = '';  // clear first

  if (!data.available) {
    const p = document.createElement('p');
    setText(p, data.message || 'Not available');
    el.appendChild(p);
    return;
  }

  const scoreP = document.createElement('p');
  setText(scoreP, 'Default probability score: ' + String(data.score));
  el.appendChild(scoreP);

  const contribs = data.contributions || [];
  if (contribs.length > 0) {
    const h4 = document.createElement('h4');
    setText(h4, 'Top contributions:');
    el.appendChild(h4);
    const ul = document.createElement('ul');
    contribs.forEach(c => {
      const li = document.createElement('li');
      setText(li, typeof c === 'string' ? c : JSON.stringify(c));
      ul.appendChild(li);
    });
    el.appendChild(ul);
  }
}

async function handleSubmit(e) {
  e.preventDefault();
  clearErrors();

  const payload = buildPayload();
  const btn = document.getElementById('submit-btn');
  if (btn) btn.disabled = true;

  try {
    // 1. Call decision service
    const res = await fetch('/ui/decide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (res.ok && data.decision) {
      displayResult(data);

      // 2. Call ML scorer (separate, failure must not block decision display)
      try {
        const mlRes = await fetch('/ui/ml-score', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const mlData = await mlRes.json();
        displayMLResult(mlData);
      } catch (_) {
        displayMLResult({ available: false, message: 'Not available' });
      }
    } else if (data.errors) {
      // Field-level validation errors from service
      Object.entries(data.errors).forEach(([field, msg]) => showError(field, msg));
      displayMLResult({ available: false, message: 'Not available' });
    } else {
      const section = document.getElementById('result-section');
      if (section) section.hidden = false;
      const box = document.getElementById('decision-box');
      if (box) { box.className = 'decision-box'; setText(document.getElementById('decision-label'), 'Error'); }
      displayMLResult({ available: false, message: 'Not available' });
    }
  } catch (err) {
    console.error(err);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// Results page: tabs + report loading
// ---------------------------------------------------------------------------
function initResultsTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  if (!tabs.length) return;

  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      tabs.forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');

      document.querySelectorAll('.tab-content').forEach(s => {
        s.classList.remove('active');
        s.hidden = true;
      });
      const target = document.getElementById('tab-' + btn.dataset.tab);
      if (target) { target.classList.add('active'); target.hidden = false; }
    });
  });

  // Load all report data
  loadReportContent('metrics_d2_lr', 'ml-metrics-content');
  loadReportContent('comparison_scorecard', 'comparison-content');
  loadFairnessContent();
  loadReportContent('edge_case_summary', 'edge-content');
}

async function loadReportContent(reportName, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  try {
    const res = await fetch('/ui/report/' + reportName);
    const data = await res.json();
    if (data.available === false) {
      setText(el, data.message || 'Not generated yet; run `make phase5`');
      return;
    }
    if (data.content) {
      const pre = document.createElement('pre');
      pre.className = 'report-block';
      setText(pre, data.content);
      el.textContent = '';
      el.appendChild(pre);
    } else {
      const pre = document.createElement('pre');
      pre.className = 'report-block';
      setText(pre, JSON.stringify(data, null, 2));
      el.textContent = '';
      el.appendChild(pre);
    }
  } catch (_) {
    setText(el, 'Not generated yet; run `make phase5`');
  }
}

async function loadFairnessContent() {
  const el = document.getElementById('fairness-content');
  if (!el) return;
  try {
    const [d2, d3] = await Promise.all([
      fetch('/ui/report/d2_tables').then(r => r.json()),
      fetch('/ui/report/d3_tables').then(r => r.json()),
    ]);
    el.textContent = '';
    for (const [label, data] of [['D2', d2], ['D3', d3]]) {
      const h = document.createElement('h3');
      setText(h, label + ' Fairness Tables');
      el.appendChild(h);
      if (data.available === false) {
        const p = document.createElement('p');
        setText(p, 'Not generated yet; run `make fairness`');
        el.appendChild(p);
      } else if (data.content) {
        const pre = document.createElement('pre');
        pre.className = 'report-block';
        setText(pre, data.content);
        el.appendChild(pre);
      }
    }
  } catch (_) {
    setText(el, 'Not generated yet; run `make fairness`');
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
    const sel = document.getElementById('preset-select');
    if (sel) {
      sel.addEventListener('change', () => {
        if (sel.value) applyPreset(sel.value);
      });
    }
  }

  initResultsTabs();
});

