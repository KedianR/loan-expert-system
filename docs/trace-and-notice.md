# Trace and Notice Specification (Phase 3)

Requirements: FR-10, FR-11, FR-12, FR-13, CR-01, CR-02, WP-11, WP-12.  
Implements the decision trace, explanation notice, and counterfactual guidance without floating-point arithmetic or policy number hardcoding.

---

## 1. Decision Trace Builder (`src/explain/trace.py`)

- **Input**: The engine execution result dictionary returned by `src/engine/engine.py:decide`. It never accesses raw application input or makes a second pass over the rules (AGENTS.md rule 5).
- **Output**: JSON-serializable dictionary adhering strictly to `schemas/trace.schema.json`.
- **Content**:
  - `applicant_ref`: Stable `sha256:` pseudonym of `applicant_id`.
  - `input_hash`: `sha256:` digest over canonical JSON of the validated input.
  - `rule_set_version` and `rule_set_hash`: Identity of the active ruleset and parameter set.
  - `decision`: Winning outcome (`eligible`, `ineligible`, `refer`).
  - `steps`: Exactly 20 active rules in fixed layer order (`validation`, `knockout`, `referral`, `eligibility`, `amount`, `pricing`). Each step carries `order`, `rule_id`, `rule_version`, `layer`, `status` (`fired`, `not_fired`, `not_evaluated`, `skipped`), along with `outcome`, `reason_code`, `derived`, `facts_used`, `missing`, or `skipped_reason`.
  - `derived`: All intermediate calculations (exact ratios, caps, indicative rate, EMI, fee, APR).
  - `reason_codes`: Reason codes matching the winning outcome's fired rules in layer order (DT-2).
  - `offer`: Structured offer dictionary for `eligible` decisions; `null` otherwise.
  - `decision_id` and `evaluated_at`: Injected by the API layer after persistence.

---

## 2. Notice Builder (`src/explain/notice.py`)

- **Input**: The generated `trace`, `rule_set` (for parameter values), `config/notice_frame.toml`, and optional raw input (for counterfactual guidance search).
- **Output**: Structured notice object adhering to `schemas/response.schema.json#/$defs/notice`:
  - `headline`: Formatted title based on outcome (e.g. "Your application is eligible, on reduced terms.").
  - `reasons`: Filled catalog templates for each code in `trace.reason_codes`.
  - `guidance`: Verified counterfactual guidance (FR-12, P3-5).
  - `basis`: Breakdown lines for eligible applications (`band`, `instalment_limit`, `after_loan`, `binding_limit`).
  - `offer_summary`: Key Fact Statement summary rows and disclaimer for eligible decisions.

---

## 3. Notice Placeholder Mapping

Placeholders in catalog templates (`rules/reason_codes.toml`) and notice frames are resolved in order: step `facts_used`, step `derived`, `trace.derived`, then `params`. Missing placeholders raise `NoticeError`.

| Placeholder | Trace Source | Formatting Rule |
|---|---|---|
| `{missing_fields}` | Step V01 `facts_used.missing_fields` | Underscores replaced by spaces, comma-separated |
| `{requested_amount}` | Step A04/V03 `facts_used.requested_amount` | Whole rupees, Indian digit grouping (`8,00,000`) |
| `{requested_tenure}` | Step V04 `facts_used.requested_tenure_months` | Integer months |
| `{credit_score}` | Step K04/E02 `facts_used.credit_score` | Integer |
| `{income}` | Step K05 `facts_used.monthly_net_income` | Whole rupees, Indian digit grouping |
| `{employment_months}` | Step K06 `facts_used.employment_months` | Integer months |
| `{min_months}` | Step K06 `facts_used` min tenure parameter | Integer months |
| `{enquiries_6m}` | Step R02 `facts_used.enquiries_6m` | Integer |
| `{existing_foir_pct}` | Step E01 `facts_used.existing_foir` / `trace.derived` | Exact decimal &times; 100, `ROUND_CEILING` for E01, `ROUND_HALF_UP` otherwise |
| `{recommended_amount}` | Step A03/A04 `facts_used.recommended_amount` | Whole rupees, Indian digit grouping |
| `{reduction}` | Counterfactual search result `r` | Whole rupees, Indian digit grouping |
| `{new_obligations}` | `monthly_obligations - r` | Whole rupees, Indian digit grouping |

---

## 4. Counterfactual Guidance Computation (FR-12, P3-5)

- **Triggers**: Computed only when `reason_codes` contains solely `HIGH_EXISTING_OBLIGATIONS` (E01) or `INSUFFICIENT_REPAYMENT_CAPACITY` (A03).
- **Algorithm**: Binary search for minimal integer reduction $r \in [1, \text{monthly\_obligations}]$ such that re-running `decide()` returns `eligible`.
- **Integrity**: Probing re-runs `decide()` without touching the audit log; verifies monotonic transition at $r$ vs $r - 1$.

