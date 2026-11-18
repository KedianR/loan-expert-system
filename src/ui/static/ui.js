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
// Money formatting (Indian numbering system: ₹X,XX,XXX.XX)
// Pure string/regex formatting without parseFloat/Number on money names.
// ---------------------------------------------------------------------------

export function formatIndianCurrency(val) {
  if (val === null || val === undefined || val === '') return '—';
  let str = String(val).trim();
  str = str.replace(/^₹\s*/, '');
  const parts = str.split('.');
  let integerPart = parts[0];
  const decimalPart = parts.length > 1 ? parts[1] : null;

  const isNegative = integerPart.startsWith('-');
  if (isNegative) integerPart = integerPart.substring(1);

  if (/^\d+$/.test(integerPart)) {
    if (integerPart.length > 3) {
      const lastThree = ',' + integerPart.substring(integerPart.length - 3);
      const otherNumbers = integerPart.substring(0, integerPart.length - 3);
      const formattedOther = otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ',');
      integerPart = (isNegative ? '-' : '') + formattedOther + lastThree;
    } else {
      integerPart = (isNegative ? '-' : '') + integerPart;
    }
  }

  if (decimalPart !== null) {
    return '₹' + integerPart + '.' + decimalPart;
  }
  return '₹' + integerPart;
}

export function displayMoney(val) {
  return formatIndianCurrency(val);
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

const PRESET_METADATA = {
  TV1: {
    title: 'TV1 — Typical applicant (Band B/C)',
    chip: 'ELIGIBLE',
    chipClass: 'badge--eligible',
    desc: 'Requested amount is the binding limit.',
  },
  TV2: {
    title: 'TV2 — Band A boundary (FOIR 0.30)',
    chip: 'ELIGIBLE',
    chipClass: 'badge--eligible',
    desc: 'Limited by repayment capacity (rule A04).',
  },
  TV3: {
    title: 'TV3 — Zero obligations (10x income)',
    chip: 'ELIGIBLE',
    chipClass: 'badge--eligible',
    desc: 'Limited by income multiple cap.',
  },
  TV4: {
    title: 'TV4 — Band B boundary (Score 700)',
    chip: 'ELIGIBLE',
    chipClass: 'badge--eligible',
    desc: 'Score is exactly 700.',
  },
  TV5: {
    title: 'TV5 — Band A boundary (Score 750)',
    chip: 'ELIGIBLE',
    chipClass: 'badge--eligible',
    desc: 'Score exactly 750 and FOIR 0.30.',
  },
  TV6: {
    title: 'TV6 — Existing FOIR 0.50 (no spare EMI)',
    chip: 'INELIGIBLE',
    chipClass: 'badge--ineligible',
    desc: 'No room left for EMI; A03 fires.',
    notes: 'Existing FOIR exactly 0.50 is allowed (E01 must NOT fire); no room left for any EMI, so A03 fires.',
  },
  TV7: {
    title: 'TV7 — High FOIR > 0.50',
    chip: 'INELIGIBLE',
    chipClass: 'badge--ineligible',
    desc: 'Existing obligations exceed 50% income; E01 fires.',
    notes: 'Existing FOIR just above 0.50: E01 fires. All later rules are skipped.',
  },
  TV8: {
    title: 'TV8 — Minimal capacity (< ₹50,000)',
    chip: 'INELIGIBLE',
    chipClass: 'badge--ineligible',
    desc: 'Recommended amount below ₹50,000 minimum; A03 fires.',
    notes: 'Band C with almost no spare EMI: recommended amount is below the 50,000 minimum, so A03 fires.',
  },
  TV9: {
    title: 'TV9 — Typical applicant (Band C)',
    chip: 'ELIGIBLE',
    chipClass: 'badge--eligible',
    desc: 'Requested amount is the binding limit.',
  },
};

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
      btn.className = 'preset-btn';
      btn.type = 'button';

      const meta = PRESET_METADATA[preset.id] || {
        title: preset.id + ' — ' + (preset.description || ''),
        chip: 'EXAMPLE',
        chipClass: 'badge--eligible',
        desc: preset.description || '',
      };

      const headerDiv = document.createElement('div');
      headerDiv.className = 'preset-btn__header';

      const titleSpan = document.createElement('span');
      titleSpan.className = 'preset-btn__title';
      setText(titleSpan, meta.title);
      headerDiv.appendChild(titleSpan);

      const chipSpan = document.createElement('span');
      chipSpan.className = 'badge ' + (meta.chipClass || 'badge--eligible') + ' badge--small';
      setText(chipSpan, meta.chip);
      headerDiv.appendChild(chipSpan);

      btn.appendChild(headerDiv);

      const descDiv = document.createElement('div');
      descDiv.className = 'preset-btn__desc';
      setText(descDiv, meta.desc);
      if (meta.notes) {
        descDiv.title = meta.notes;
      }
      btn.appendChild(descDiv);

      btn.addEventListener('click', () => {
        // Highlight active preset (UI v2 pass 2 #8)
        container.querySelectorAll('.preset-btn').forEach(b => {
          b.classList.remove('selected', 'preset-btn--selected');
        });
        btn.classList.add('selected', 'preset-btn--selected');

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
 * Preserves checkbox visual and DOM states.
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
  const selectFields = ['employment_type', 'region_tier'];
  const textFields = ['applicant_id'];

  const setField = (name, val) => {
    const el = document.getElementById(name);
    if (!el) return;
    if (checkboxFields.includes(name)) {
      el.checked = Boolean(val);
      if (val) {
        el.setAttribute('checked', 'checked');
      } else {
        el.removeAttribute('checked');
      }
    } else if (selectFields.includes(name)) {
      el.value = val != null ? String(val) : '';
    } else if (intFields.includes(name)) {
      el.value = val != null ? String(val) : '';
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
    kyc_verified: field('kyc_verified') ? field('kyc_verified').checked : false,
    consent_given: field('consent_given') ? field('consent_given').checked : false,
    requested_amount: intOrNull('requested_amount'),
    requested_tenure_months: intOrNull('requested_tenure_months'),
  };

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
// ML result display & helpers (UI v2 pass 2 #7)
// ---------------------------------------------------------------------------

export function formatModelScore(val) {
  if (val == null || val === '' || val === '—') return '—';
  const s = String(val).trim();
  const n = Number(s);
  if (isNaN(n)) return s;
  if (n > 0 && n < 0.0001) return '<0.0001';
  if (n === 0) return '0.0000';
  return n.toFixed(4);
}

const FEATURE_LABELS = {
  existing_foir: 'Existing obligations ratio',
  credit_score: 'Credit score',
  employment_type: 'Employment type',
  severe_delinquency_36m: 'Severe delinquency (36 months)',
  monthly_net_income: 'Monthly net income',
  requested_amount: 'Requested amount',
  requested_tenure_months: 'Requested tenure',
  age: 'Age',
  bankruptcies: 'Bankruptcies',
  credit_enquiries_6m: 'Credit enquiries (6 months)',
  employment_months: 'Employment duration (months)',
  residential_status: 'Residential status',
  region_tier: 'Region tier',
};

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
    msg.className = 'ml-unavailable';
    setText(msg, 'ML score unavailable');
    container.appendChild(msg);
    return;
  }

  // Scores grid: show LR and GB scores (A.2, Pass 2 #7)
  const scoresGrid = document.createElement('div');
  scoresGrid.className = 'ml-scores-grid';

  const lrCard = document.createElement('div');
  lrCard.className = 'ml-score-card';
  const lrLabel = document.createElement('span');
  lrLabel.className = 'ml-score-label';
  setText(lrLabel, 'Logistic Regression score');
  const lrVal = document.createElement('span');
  lrVal.className = 'ml-score-value';
  setText(lrVal, formatModelScore(mlData.lr_score ?? mlData.score));
  lrCard.appendChild(lrLabel);
  lrCard.appendChild(lrVal);
  scoresGrid.appendChild(lrCard);

  if (mlData.gb_score != null) {
    const gbCard = document.createElement('div');
    gbCard.className = 'ml-score-card';
    const gbLabel = document.createElement('span');
    gbLabel.className = 'ml-score-label';
    setText(gbLabel, 'Gradient Boosting score');
    const gbVal = document.createElement('span');
    gbVal.className = 'ml-score-value';
    setText(gbVal, formatModelScore(mlData.gb_score));
    gbCard.appendChild(gbLabel);
    gbCard.appendChild(gbVal);
    scoresGrid.appendChild(gbCard);
  }

  container.appendChild(scoresGrid);

  // Caption (UI v2 pass 2 #7)
  const caption = document.createElement('p');
  caption.className = 'card__hint';
  caption.style.marginTop = 'var(--sp-2)';
  setText(caption, 'Higher = more likely to be eligible. Not a probability. Does not affect the decision.');
  container.appendChild(caption);

  // Top-3 feature contributions table
  const contribs = (mlData.contributions || []).slice(0, 3);
  if (contribs.length > 0) {
    const h4 = document.createElement('h4');
    h4.style.marginTop = 'var(--sp-4)';
    h4.style.marginBottom = 'var(--sp-2)';
    setText(h4, 'Top-3 feature contributions (Logistic Regression)');
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
        const featKey = String(c.feature ?? '');
        setText(featureTd, FEATURE_LABELS[featKey] || featKey.replace(/_/g, ' '));
        const sign = (typeof c.contribution === 'number' && c.contribution > 0) ? '+' : '';
        setText(contribTd, sign + String(c.contribution ?? ''));
      } else {
        const featKey = String(c);
        setText(featureTd, FEATURE_LABELS[featKey] || featKey.replace(/_/g, ' '));
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
  headerCard.id = 'report-header';

  // Status badge
  const badge = document.createElement('div');
  badge.className = 'badge badge--' + decision;

  let icon;
  if (decision === 'eligible') icon = iconCheckmark();
  else if (decision === 'ineligible') icon = iconCross();
  else icon = iconClock();
  badge.appendChild(icon);

  const badgeLabel = document.createElement('span');
  badgeLabel.className = 'badge__label';
  const decisionWord = decision.toUpperCase();
  setText(badgeLabel, decisionWord);
  badge.appendChild(badgeLabel);
  headerCard.appendChild(badge);

  // One-sentence summary
  const summaryP = document.createElement('p');
  summaryP.className = 'report-summary-sentence';
  if (decision === 'eligible') {
    setText(summaryP, 'Application meets all credit and policy criteria and is eligible for an unsecured personal loan offer.');
  } else if (decision === 'ineligible') {
    setText(summaryP, 'Application does not meet the eligibility policy requirements.');
  } else {
    setText(summaryP, 'Application requires manual underwriting assessment.');
  }
  headerCard.appendChild(summaryP);

  // Subtitle (Applicant reference)
  const subtitle = document.createElement('p');
  subtitle.className = 'report-subtitle';
  setText(subtitle, 'Application reference: ' + (data.applicant_id || data._submitted_payload?.applicant_id || '—'));
  headerCard.appendChild(subtitle);

  // Action buttons
  const btnRow = document.createElement('div');
  btnRow.className = 'report-actions';

  const editBtn = document.createElement('button');
  editBtn.className = 'btn btn--outline';
  editBtn.type = 'button';
  setText(editBtn, 'Edit application');
  editBtn.addEventListener('click', () => {
    const form = document.getElementById('app-form');
    if (form) {
      form.scrollIntoView({ behavior: 'smooth' });
      const firstInput = document.getElementById('applicant_id');
      if (firstInput) firstInput.focus();
    }
  });
  btnRow.appendChild(editBtn);

  const printBtn = document.createElement('button');
  printBtn.className = 'btn btn--outline btn--print';
  printBtn.type = 'button';
  setText(printBtn, 'Print / save as PDF');
  printBtn.addEventListener('click', () => window.print());
  btnRow.appendChild(printBtn);

  const newBtn = document.createElement('button');
  newBtn.className = 'btn btn--outline';
  newBtn.type = 'button';
  setText(newBtn, 'New application');
  newBtn.addEventListener('click', () => clearForm());
  btnRow.appendChild(newBtn);

  headerCard.appendChild(btnRow);
  section.appendChild(headerCard);

  // ----- Outcome summary block (C.3) -----
  if (decision === 'eligible' && data.offer) {
    const tilesDiv = document.createElement('div');
    tilesDiv.className = 'summary-tiles';

    const recAmount = data.offer.amount != null ? data.offer.amount : data.offer.recommended_amount;
    const rateVal = data.offer.indicative_rate != null
      ? (data.offer.indicative_rate + '%')
      : (data.offer.rate_pct != null ? (data.offer.rate_pct + '%') : (data.offer.interest_rate || '—'));

    const tileData = [
      { label: 'Recommended amount', value: formatIndianCurrency(recAmount) },
      { label: 'Band', value: data.offer.band || '—' },
      { label: 'Interest rate', value: rateVal },
      { label: 'Monthly EMI', value: formatIndianCurrency(data.offer.emi) },
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
    section.appendChild(tilesDiv);
  } else if (decision === 'ineligible') {
    const box = document.createElement('div');
    box.className = 'card outcome-summary-box';

    const boxLabel = document.createElement('span');
    boxLabel.className = 'outcome-summary-box__label';
    setText(boxLabel, 'Main reason');
    box.appendChild(boxLabel);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'outcome-summary-box__content';

    const notices = Array.isArray(data.notice)
      ? data.notice
      : (data.notice && Array.isArray(data.notice.reasons) ? data.notice.reasons : []);
    const firstReasonText = notices.length > 0 ? (notices[0].text || '') : '';
    const firstReasonCode = (data.reason_codes && data.reason_codes[0]) || (notices[0] && notices[0].code) || '';

    if (firstReasonCode) {
      const chip = document.createElement('span');
      chip.className = 'chip chip--neutral';
      setText(chip, firstReasonCode);
      contentDiv.appendChild(chip);
    }
    const reasonSpan = document.createElement('span');
    setText(reasonSpan, firstReasonText || 'Policy criteria not met.');
    contentDiv.appendChild(reasonSpan);

    box.appendChild(contentDiv);
    section.appendChild(box);
  } else {
    // Refer
    const box = document.createElement('div');
    box.className = 'card outcome-summary-box';

    const boxLabel = document.createElement('span');
    boxLabel.className = 'outcome-summary-box__label';
    setText(boxLabel, 'Referral reason');
    box.appendChild(boxLabel);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'outcome-summary-box__content';

    const notices = Array.isArray(data.notice)
      ? data.notice
      : (data.notice && Array.isArray(data.notice.reasons) ? data.notice.reasons : []);
    const firstReasonText = notices.length > 0 ? (notices[0].text || '') : '';
    const firstReasonCode = (data.reason_codes && data.reason_codes[0]) || (notices[0] && notices[0].code) || '';

    if (firstReasonCode) {
      const chip = document.createElement('span');
      chip.className = 'chip chip--neutral';
      setText(chip, firstReasonCode);
      contentDiv.appendChild(chip);
    }
    const reasonSpan = document.createElement('span');
    setText(reasonSpan, firstReasonText || 'Referred for manual review.');
    contentDiv.appendChild(reasonSpan);

    box.appendChild(contentDiv);

    const nextP = document.createElement('p');
    nextP.className = 'outcome-summary-box__next';
    setText(nextP, 'What happens next: A human reviewer will assess the application.');
    box.appendChild(nextP);

    section.appendChild(box);
  }

  // ----- Contiguous Sections 1-6 (C.2) -----

  // 1. Applicant inputs
  section.appendChild(makeAccordion('1 Applicant inputs as submitted', el => {
    buildApplicantInputs(el, data);
  }));

  // 2. Why
  section.appendChild(makeAccordion('2 Why', el => {
    buildWhySection(el, data);
  }));

  // 3. Offer summary (UI v2 pass 2 #9)
  let offerTitle = '3 Offer summary';
  if (decision === 'refer') {
    offerTitle = '3 Offer summary: pending review';
  } else if (decision !== 'eligible') {
    offerTitle = '3 Offer summary: no offer made';
  }
  section.appendChild(makeAccordion(offerTitle, el => {
    buildOfferSummary(el, data);
  }));

  // 4. Rule trace
  section.appendChild(makeAccordion('4 Rule trace', el => {
    buildRuleTrace(el, data);
  }));

  // 5. Record
  section.appendChild(makeAccordion('5 Record', el => {
    buildRecord(el, data);
  }));

  // 6. ML comparison
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
  employment_months: 'Employment duration',
  monthly_net_income: 'Monthly net income',
  monthly_obligations: 'Monthly obligations',
  credit_score: 'Credit score',
  enquiries_6m: 'Credit enquiries (6m)',
  severe_delinquency_36m: 'Severe delinquency (36m)',
  written_off: 'Account written off',
  kyc_verified: 'KYC verified',
  consent_given: 'Consent given',
  requested_amount: 'Requested amount',
  requested_tenure_months: 'Requested tenure',
  region_tier: 'Region tier',
};

function formatApplicantValue(key, val) {
  if (val === null || val === undefined || val === '') return '—';
  if (typeof val === 'boolean') return val ? 'Yes' : 'No';
  if (key === 'monthly_net_income' || key === 'monthly_obligations' || key === 'requested_amount') {
    return formatIndianCurrency(val);
  }
  if (key === 'employment_type') {
    if (val === 'salaried') return 'Salaried';
    if (val === 'self_employed') return 'Self-employed';
    if (val === 'other') return 'Other';
    return String(val);
  }
  if (key === 'region_tier') {
    if (String(val) === '1') return '1 — Metro';
    if (String(val) === '2') return '2 — Urban';
    if (String(val) === '3') return '3 — Semi-urban';
    return String(val);
  }
  if (key === 'employment_months') return `${val} months`;
  if (key === 'requested_tenure_months') return `${val} months`;
  if (key === 'age') return `${val} years`;
  return String(val);
}

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
    setText(dd, formatApplicantValue(key, val));
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
  const notices = Array.isArray(data.notice)
    ? data.notice
    : (data.notice && Array.isArray(data.notice.reasons) ? data.notice.reasons : []);
  const reasonCodes = data.reason_codes || [];
  const decision = (data.decision || '').toLowerCase();

  if (decision === 'eligible' && notices.length === 0 && reasonCodes.length === 0) {
    const p = document.createElement('p');
    setText(p, 'Application meets all credit and risk policy requirements.');
    el.appendChild(p);
    return;
  }

  if (notices.length > 0) {
    notices.forEach(item => {
      const div = document.createElement('div');
      div.className = 'reason-item';
      if (item.code) {
        const codeSpan = document.createElement('span');
        codeSpan.className = 'chip chip--neutral';
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
    reasonCodes.forEach(code => {
      const div = document.createElement('div');
      div.className = 'reason-item';
      const codeSpan = document.createElement('span');
      codeSpan.className = 'chip chip--neutral';
      setText(codeSpan, code);
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
  const decision = (data.decision || '').toLowerCase();
  if (decision === 'refer') {
    const p = document.createElement('p');
    setText(p, 'No offer yet: pending manual review.');
    el.appendChild(p);
    return;
  }
  if (decision !== 'eligible') {
    const p = document.createElement('p');
    setText(p, 'No loan offer is generated because the application was not approved.');
    el.appendChild(p);
    return;
  }

  const offer = data.offer || {};
  const recAmount = offer.amount != null ? offer.amount : offer.recommended_amount;
  const rateVal = offer.indicative_rate != null
    ? (offer.indicative_rate + '%')
    : (offer.rate_pct != null ? (offer.rate_pct + '%') : (offer.interest_rate || '—'));
  const feeVal = offer.fee != null ? offer.fee : offer.processing_fee;

  // Separate rows for Total interest and Total repayment (A.3)
  const totalRepayment = offer.total_repayment != null
    ? formatIndianCurrency(offer.total_repayment)
    : '—';
  const totalInterest = offer.total_interest != null
    ? formatIndianCurrency(offer.total_interest)
    : '—';

  const rows = [
    ['Recommended amount', formatIndianCurrency(recAmount)],
    ['Band', offer.band || '—'],
    ['Rate', rateVal],
    ['Tenure', offer.tenure_months != null ? `${offer.tenure_months} months` : '—'],
    ['Monthly EMI', formatIndianCurrency(offer.emi)],
    ['Processing fee', formatIndianCurrency(feeVal)],
    ['APR', offer.apr != null ? (String(offer.apr) + '%') : '—'],
    ['Total interest', totalInterest],
    ['Total repayment', totalRepayment],
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
  const trace = Array.isArray(data.trace)
    ? data.trace
    : (data.trace && Array.isArray(data.trace.steps) ? data.trace.steps : []);

  if (trace.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    setText(empty, 'No trace available.');
    el.appendChild(empty);
    return;
  }

  const hasDescriptions = trace.some(entry => {
    const desc = entry.description || entry.rule_description;
    return desc && desc !== '—' && desc.trim() !== '';
  });

  const scrollWrap = document.createElement('div');
  scrollWrap.className = 'table-scroll-wrap';

  const tbl = document.createElement('table');
  tbl.className = 'data-table trace-table';

  const thead = document.createElement('thead');
  const hrow = document.createElement('tr');
  const cols = hasDescriptions
    ? ['Rule ID', 'Description', 'Rule version', 'Facts used', 'Result']
    : ['Rule ID', 'Rule version', 'Facts used', 'Result'];

  cols.forEach(col => {
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

    // Format facts used without quotes around decimals
    let factsStr = '';
    if (Array.isArray(entry.facts_used)) {
      factsStr = entry.facts_used.join(', ');
    } else if (entry.facts_used && typeof entry.facts_used === 'object') {
      factsStr = Object.entries(entry.facts_used)
        .map(([k, v]) => {
          if (typeof v === 'string' && /^-?\d+(\.\d+)?$/.test(v)) {
            return `${k}=${v}`;
          }
          return `${k}=${typeof v === 'string' ? v : JSON.stringify(v)}`;
        })
        .join(', ');
    } else {
      factsStr = String(entry.facts_used || '—');
    }

    // Determine status label and dot class (C.4)
    const status = (entry.status || '').toLowerCase();
    const outcome = (entry.outcome || '').toLowerCase();
    const rawToken = `status: ${entry.status || 'unknown'}${entry.outcome ? `, outcome: ${entry.outcome}` : ''}`;

    let label = 'Passed';
    let dotClass = 'dot--passed';

    if (status === 'fired') {
      if (outcome === 'derive') {
        label = 'Applied';
        dotClass = 'dot--applied';
      } else if (outcome === 'refer') {
        label = 'Triggered';
        dotClass = 'dot--refer';
      } else {
        label = 'Triggered';
        dotClass = 'dot--triggered';
      }
    } else if (status === 'not_fired') {
      label = 'Passed';
      dotClass = 'dot--passed';
    } else if (status === 'skipped') {
      label = 'Skipped';
      dotClass = 'dot--skipped';
    } else if (status === 'not_evaluated') {
      label = 'Not evaluated';
      dotClass = 'dot--not-evaluated';
    }

    // Rule ID cell
    const ruleTd = document.createElement('td');
    setText(ruleTd, String(entry.rule_id || '—'));
    tr.appendChild(ruleTd);

    // Description cell (only if descriptions are present)
    if (hasDescriptions) {
      const descTd = document.createElement('td');
      setText(descTd, String(entry.description || entry.rule_description || '—'));
      tr.appendChild(descTd);
    }

    // Version cell
    const verTd = document.createElement('td');
    setText(verTd, String(entry.rule_version || '—'));
    tr.appendChild(verTd);

    // Facts cell
    const factsTd = document.createElement('td');
    factsTd.className = 'trace-facts';
    setText(factsTd, factsStr || '—');
    tr.appendChild(factsTd);

    // Result cell with color dot and tooltip
    const resTd = document.createElement('td');
    const statusWrap = document.createElement('span');
    statusWrap.className = 'trace-status';
    statusWrap.title = rawToken;

    const dot = document.createElement('span');
    dot.className = `trace-dot ${dotClass}`;
    statusWrap.appendChild(dot);

    const textSpan = document.createElement('span');
    setText(textSpan, label);
    statusWrap.appendChild(textSpan);

    resTd.appendChild(statusWrap);
    tr.appendChild(resTd);

    tbody.appendChild(tr);
  });

  tbl.appendChild(tbody);
  scrollWrap.appendChild(tbl);
  el.appendChild(scrollWrap);
}

function buildRecord(el, data) {
  const hashVal = data.rule_set_hash || '—';

  const rows = [
    ['Decision ID', data.decision_id || data.id || '—'],
    ['Rule-set tag / version', data.rule_set_tag || data.rule_set_version || '—'],
    ['Rule-set hash', hashVal],
    ['Audit stored', typeof data.audit_stored === 'string' ? data.audit_stored : (data.demo_mode ? 'Yes (demo, temporary)' : (data.audit_stored === true ? 'Yes' : (data.audit_stored === false ? 'No' : (data.decision_id ? 'Yes' : 'Unknown'))))],
  ];

  const tbl = document.createElement('table');
  tbl.className = 'data-table';
  const tbody = document.createElement('tbody');
  rows.forEach(([label, value]) => {
    const tr = document.createElement('tr');
    const th = document.createElement('th');
    setText(th, label);
    const td = document.createElement('td');

    if (label === 'Rule-set hash' && value !== '—') {
      td.className = 'record-hash-cell';
      const code = document.createElement('code');
      code.className = 'record-hash';
      setText(code, value);
      td.appendChild(code);

      const copyBtn = document.createElement('button');
      copyBtn.type = 'button';
      copyBtn.className = 'btn-copy';
      copyBtn.setAttribute('aria-label', 'Copy rule-set hash');
      setText(copyBtn, 'Copy');
      copyBtn.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(value);
          setText(copyBtn, 'Copied!');
          setTimeout(() => setText(copyBtn, 'Copy'), 2000);
        } catch (_) {}
      });
      td.appendChild(copyBtn);
    } else {
      setText(td, value);
    }

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
      data._submitted_payload = payload;
      buildReport(data);

      const reportSection = document.getElementById('report-section');
      if (reportSection) {
        reportSection.removeAttribute('hidden');
        reportSection.scrollIntoView({ behavior: 'smooth' });
        const reportHeader = reportSection.querySelector('.report-header') || reportSection;
        reportHeader.tabIndex = -1;
        reportHeader.focus();
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
          displayMLResult({ available: false, message: 'ML score unavailable' }, mlContainer);
        }
      }
    } else if (data.errors && typeof data.errors === 'object') {
      Object.entries(data.errors).forEach(([fieldId, msg]) => {
        showFieldError(fieldId, String(msg));
      });
      showToast('Please fix the errors below.');
    } else if (data.error) {
      showToast('Error: ' + data.error);
    } else {
      showToast('Unexpected response from decision service.');
    }
  } catch (err) {
    showToast('Network error: ' + (err.message || 'could not reach decision service'));
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
  const presetContainer = document.getElementById('preset-buttons');
  if (presetContainer) {
    presetContainer.querySelectorAll('.preset-btn').forEach(b => {
      b.classList.remove('selected', 'preset-btn--selected');
    });
  }
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

  // Mobile collapsed / desktop open preset panel
  const presetPanel = document.getElementById('preset-panel');
  if (presetPanel) {
    if (window.innerWidth >= 768) {
      presetPanel.setAttribute('open', '');
    } else {
      presetPanel.removeAttribute('open');
    }
  }

  // Check demo mode configuration (Requirement 8)
  fetch('/ui/config')
    .then(r => r.json())
    .then(cfg => {
      if (cfg && cfg.vercel) {
        const demoEl = document.getElementById('demo-notice');
        if (demoEl) demoEl.removeAttribute('hidden');
        const aboutDemoEl = document.getElementById('about-demo-notice');
        if (aboutDemoEl) aboutDemoEl.removeAttribute('hidden');
      }
    })
    .catch(() => {});
});
