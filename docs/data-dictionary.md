# Data Dictionary (v0.1)

Requirements: DR-01 to DR-03, NFR-07, CR-01, CR-03, NFR-09. This file lists every field the system stores or returns, its class, who may read it, and how notice text is filled. Field names, types and ranges for the input are fixed by `schemas/input.schema.json` and `rules/fields.toml`; this file does not repeat them, it classifies them.

## 1. Data classes

| Class | Meaning | Rule |
|---|---|---|
| D-IN | Decision input: the 14 fields the rules may read | Collected only because a rule needs it (CR-03). Stored only in `audit_inputs`. |
| D-DER | Derived value or outcome computed by the engine | Stored in the trace. |
| D-REF | Pseudonymous reference or hash (`applicant_ref`, `input_hash`, `decision_id`) | Safe to log. |
| D-PROT | Audit-only attributes: gender, religion, caste and similar | Never in the input schema, the trace, the audit log, a log line, the notice or any model feature. Held in a separate store read only by `eval/` (DR-02, FR-20). Phase 4 builds that store. |
| D-REV | Reviewer identity, action and reason | Stored in `reviewer_actions`. |
| D-OP | Operational setting | `config/app.toml`. |

## 2. Input fields (D-IN)

All 14 are in the input schema. Phase 3 changes none of them. Purpose is the rule or check that reads the field.

| Field | Purpose |
|---|---|
| `applicant_id` | identifies the application; source of `applicant_ref` |
| `age` | legal-capacity check (K01) |
| `employment_type`, `employment_months` | K06, R03 |
| `monthly_net_income`, `monthly_obligations` | existing FOIR, K05, E01, A01, A02 |
| `credit_score` | K04, E02, R01 |
| `enquiries_6m` | R02 |
| `severe_delinquency_36m`, `written_off` | K03 |
| `kyc_verified` | K02 |
| `consent_given` | V02 (the recorded consent flag, CR-03) |
| `requested_amount`, `requested_tenure_months` | V03, V04, A01, A02, A04 |

`region_tier` is accepted only when experimental rule X02 is on; it is off in the baseline.

## 3. Response and trace fields

Defined by `schemas/response.schema.json` and `schemas/trace.schema.json`. Classes: `decision_id`, `applicant_ref`, `input_hash`, `rule_set_version`, `rule_set_hash` are D-REF; everything else in the trace is D-DER, except `steps[].facts_used`, which repeats the values of D-IN fields that the step read. This is deliberate: the trace is the explanation (NFR-01) and the audit log must show what each rule saw. It is the reason the audit log is treated as synthetic-data-only (docs/privacy-statement.md).

Naming in `steps[].facts_used`: one key per fact or parameter the rule read, using the field and parameter names from `rules/fields.toml` and `params/params.toml`. A parameter read by the rule appears with its parameter name (for example `min_credit_score`). Nothing in `facts_used` may be a protected attribute (a test scans the keys against the list in `docs/decision-tables.md` section 6).

## 4. How notice text is filled

The notice (`notice` in the response) is built from the trace and two text files. It reads no input field and recomputes nothing (AGENTS.md rule 5, CR-01).

**Reasons.** For each code in `trace.reason_codes`, in order, take the template from `rules/reason_codes.toml` and fill its placeholders from the trace. The values come from `facts_used` of the fired step that carries that code, then from that step's `derived`, then from `trace.derived`. A placeholder with no value is an error (`NoticeError`), never a blank and never a computed substitute. If the template names a value the trace does not record, stop and report it; do not add a calculation to the explanation code and do not change a rule file.

Placeholder map (the first key is the placeholder; the alternatives are the names the trace may use for the same value):

| Placeholder | Trace key (alternatives) | Format |
|---|---|---|
| `{missing_fields}` | V01 `facts_used.missing_fields` | field names with `_` replaced by a space, joined by `, `, in the order in the trace |
| `{requested_amount}` | `requested_amount` | whole rupees, Indian grouping |
| `{requested_tenure}` | `requested_tenure`, `requested_tenure_months` | integer |
| `{credit_score}` | `credit_score` | integer |
| `{income}` | `monthly_net_income` | whole rupees, Indian grouping |
| `{employment_months}` | `employment_months` | integer |
| `{min_months}` | the minimum-months parameter that K06 recorded in its `facts_used` | integer |
| `{enquiries_6m}` | `enquiries_6m` | integer |
| `{existing_foir_pct}` | `existing_foir` | ratio times 100, see below |
| `{recommended_amount}` | `recommended_amount` | whole rupees, Indian grouping |

Formats. Indian grouping: last three digits, then groups of two (`800000` gives `8,00,000`; `1234567` gives `12,34,567`), no currency symbol and no decimals for whole-rupee values. Percent: multiply the exact decimal by 100 with `Decimal`, round half up to 2 decimal places, remove trailing zeros and a trailing point (`0.5500` gives `55`, `0.5469` gives `54.69`). No `float` in the notice code (AGENTS.md rule 2).

One exception to half-up rounding: `{existing_foir_pct}` in the text for `HIGH_EXISTING_OBLIGATIONS` rounds **up** (`ROUND_CEILING`) to 2 decimal places. The rule fires only when the ratio is above the limit, so a rounded-up figure is always above it too; half-up could print "50% ... above our limit of 50%" (vector TV7: the exact ratio is 0.50001, the text must say 50.01). This needs the trace to hold the exact ratio the rule compared, not the 4-decimal display value. If the E01 step's `facts_used.existing_foir` (or the trace's `derived.existing_foir`) is already rounded to 4 decimals, stop and report; do not recompute it in the explanation code.

Literal numbers inside a catalog template (for example "minimum of 650") are part of the reason-code file. A test compares each literal number in the 21 templates with the matching parameter value and reports any difference as a finding in the phase report. It does not edit `rules/reason_codes.toml` (the file is pinned by the rule-set hash).

**Headline, basis, guidance, offer summary.** Texts come from `config/notice_frame.toml` (`[headline]`, `[basis]`, `[basis_binding]`, `[guidance]`, `[offer_summary]`).

- Headline: `eligible_reduced` if any fired step has outcome `reduced_offer`, otherwise the key equal to the decision.
- Basis (eligible only), in this order: `band`, `instalment_limit`, `after_loan`, then the `[basis_binding]` text for `binding_limit`. A line whose placeholders are not all in the trace is left out. Placeholder values: `band`, `credit_score`, `existing_foir`, `max_emi`, `max_principal_emi`, `post_loan_foir`, `binding_limit` from the trace. `max_emi` and `max_principal_emi` are money with paise: Indian grouping on the whole part, `.` and two digits. `post_loan_foir_pct` uses the percent format above.
- Offer summary (eligible only). Rows in this order, values from `trace.offer`: amount as `INR` plus grouped whole rupees; tenure as `<n> months`; interest band as `<band>: <low>% to <high>%` from `rate_range`; indicative rate as `<rate>%`; EMI, fee and total interest as `INR` plus grouped value with two decimals; APR as `<apr>%`. Labels from `[offer_summary.labels]`. No other figure is added (no totals the calculation spec does not define).
- Refer decisions: reasons only. No amount, no band, no offer, and no promise of an outcome.

## 5. Error codes in the 422 body

`fields[].code` values are the codes the Phase 1 validator already produces for a malformed value, an unknown key and a type error. In Phase 3, read them from the validator and list them here in a table (code, meaning, example field), without inventing new ones. A missing or null field is not an error: it becomes an unknown fact and rule V01 or R01 decides (FR-02).

## 6. Counterfactual guidance (FR-12, decision P3-5)

For these two reason codes only, and only when the decision's `reason_codes` contain no other code:

- `HIGH_EXISTING_OBLIGATIONS` (E01) and `INSUFFICIENT_REPAYMENT_CAPACITY` (A03).

Method: find the smallest whole-rupee reduction `r`, with `1 <= r <= monthly_obligations`, such that re-running `decide()` on the same input with `monthly_obligations - r` returns `eligible`. Use a binary search on `r`; each probe is a normal `decide()` call that writes nothing. Accept `r` only if the probe at `r` returns `eligible` and the probe at `r - 1` does not. If no `r` works, or the probes disagree with this monotone assumption, omit the guidance. Record `verified_decision: "eligible"` with each statement. Fill `{reduction}` and `{new_obligations}` in whole rupees, Indian grouping. All other codes get no guidance in v0.1 (the counterfactual for a credit score or a delinquency is not computable from a single re-run).

## 7. Retention and deletion

Retention is the life of the project (docs/privacy-statement.md). There is no deletion path in the application, by design (append-only). Deleting the project's `data/audit/` folder removes everything.
