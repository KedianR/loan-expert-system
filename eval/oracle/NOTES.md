# Reference Oracle Implementation Notes

This document records ambiguities, silences, and edge-case interpretations encountered while developing the reference oracle (`eval/oracle/oracle.py`) directly from the Credit Policy (`docs/02-policy-and-rules.md`), Calculations (`docs/03-calculations.md`), and Predicate & Fact schemas (`docs/04-predicates-and-facts.md`).

---

## 1. Binding Limit When Requested Amount Equals a Cap or Minimum Cap

### Ambiguity / Silence
`docs/03-calculations.md` Formula F6 states:
> "If $P^*$ is below $R$, the binding limit is the smallest of the three caps; report it as the matching `AMOUNT_LIMITED_BY` code. If two caps tie, report capacity first, then income multiple, then product maximum."

And Section 4:
> "A cap tie in F6: apply the stated tie order (capacity, income multiple, product maximum)"

The document does not explicitly state what `binding_limit` should be when $P^*$ is not below $R$ (e.g. $P^* == R$), nor does it specify how ties between $R$ and the caps should be resolved.
In golden test vectors TV1, TV4, TV5, and TV9, $R$ is strictly less than all three caps ($R < \min(P_{\mathrm{EMI}}, 10\,I, 2500000)$), and `tests/golden/vectors.json` assigns `"binding_limit": "requested"`.
However, in cases like `cap_tie_income_prodmax`, $10\,I = 2,500,000$ and $\mathrm{product\_max} = 2,500,000$, while $R = 2,500,000$ (the maximum permitted requested amount under V03). If $R$ took precedence over caps on equality, `binding_limit` would evaluate to `"requested"`, and neither `income_multiple` nor `product_maximum` could ever be reported as a binding limit (and the stated tie-breaker between them could never be tested).

### Choice & Clause Relied On
- **Update (Owner Decision DT-4)**: Resolved by DT-4 — if the requested amount is equal to or smaller than all three caps, the whole request fits and `binding_limit` is `"requested"` (a cap is binding only when strictly below the request).
- If $R \le \min(\text{caps})$, `binding_limit` is `"requested"`.
- If $\min(\text{caps}) < R$, the lowest cap is chosen using the tie order:
  1. `capacity`
  2. `income_multiple`
  3. `product_maximum`
- Per Owner Decision #1 and DT-4, rule A04 (reduced offer) fires only when $P^* + \text{amount\_step} \le R$. Thus, when $R$ equals the lowest cap (e.g., $R = 500,000$ and $10\,I = 500,000$ as in `a04_tie_request_income`, or $R = 2,500,000$ in `cap_tie_income_prodmax`), the entire request fits, $P^* = R$, so no shortfall exists, A04 does not fire (`reason_codes: []`), and `binding_limit` is `"requested"`.

---

## 2. Output Schema for Ineligible or Referred Applications (No Offer)

### Ambiguity / Silence
`docs/03-calculations.md` Section 3 lists table values for TV6 as:
`Binding limit: EMI_max is -5,000`, `Recommended: none`, `EMI: none`, `Fee: none`, `APR: none`.
For TV7: `Binding limit: none`, `Recommended: none`.
In `tests/golden/vectors.json`, TV6, TV7, and TV8 have `"offer": null`, and do not include `binding_limit` or `recommended_amount`.
In the user prompt specification for `run_d1.py`:
> "band (A, B, C or null), recommended_amount (int or null), binding_limit (or null), indicative_rate (string or null), emi, fee, total_interest, apr, post_loan_foir (strings with the document's precision, or null when there is no offer)."

It was ambiguous whether `binding_limit` or `recommended_amount` should be populated when an application is rejected under rule A03 (insufficient repayment capacity) where an intermediate $P^*$ (< 50,000) was computed.

### Choice & Clause Relied On
- Whenever `decision != "eligible"` (no loan offer is made), all offer-related fields (`recommended_amount`, `binding_limit`, `indicative_rate`, `emi`, `fee`, `total_interest`, `apr`, `post_loan_foir`) are set to `null` (`None`).
- `band` preserves the pricing band derived by rule E02 if E02 ran before rejection (e.g., Band C for TV6 and TV8), and remains `null` if E02 was skipped (e.g., TV7, where E01 fired).
- Relied on `docs/02-policy-and-rules.md` Section 4 ("Derivation rules (E02, A01, A02, P01) run only when no INELIGIBLE or REFER outcome has been recorded") and the prompt's instruction ("null when there is no offer").

---

## 3. Multi-Field Rule Evaluation on Partial Information (Owner Decision DT-5)

### Rule / Decision
Per Owner Decision DT-5, `docs/04-predicates-and-facts.md` Section 1, and Owner Decision #3:
> "A rule that needs a field that is unknown (missing or null) is not evaluated and cannot fire."

A rule that reads several fields is NOT evaluated if ANY of the fields it reads is unknown (missing or null), even when another field it reads is already adverse. A rule never fires on partial information:
- Rule K03 reads both `severe_delinquency_36m` and `written_off`. If either field is missing or null, K03 is not evaluated and cannot fire, even if the other field is `True`. V01 fires instead and the decision is `refer` with `INCOMPLETE_APPLICATION`.
- Rule K06 reads both `employment_type` and `employment_months`. If either field is missing or null, K06 is not evaluated and cannot fire.
- Any other rule reading multiple fields likewise requires all fields it reads to be known before evaluating.

---

## 4. Zero Monthly Net Income and Existing FOIR

### Ambiguity / Silence
`docs/03-calculations.md` Section 4 notes:
> "Income of zero: do not divide; record existing_foir as unknown and let K05 fire INELIGIBLE, which takes precedence; never divide by zero"

Owner Decision #3 notes:
> "Income of zero: existing FOIR is unknown (never divide by zero)."

Does rule E01 fire if income is zero and obligations are positive?

### Choice & Clause Relied On
- Division by zero is strictly avoided. When `monthly_net_income == 0`, `existing_foir` is treated as `unknown` (`None`).
- Because `existing_foir` is unknown, rule E01 is not evaluated and does not fire.
- Rule K05 fires INELIGIBLE (`INCOME_BELOW_MINIMUM`) because `0 < 15,000`, which correctly determines the outcome as `ineligible`.

---

## 5. Non-Multiple-of-5000 Requested Amounts and Rule A04

### Ambiguity / Silence
`docs/03-calculations.md` Section 4:
> "Requested amount that is not a multiple of 5,000: floor to 5,000 as in F6 and report a reduced offer only if the result is below the request by at least one step"

Owner Decision #1:
> "Rule A04 (reduced offer) fires only when NO rule has fired with outcome ineligible or refer (including A03), and the recommended amount plus the amount step is at most the requested amount."

When $R$ is not a multiple of 5,000 (e.g. $R = 54,321$), flooring gives $P^* = 50,000$. The shortfall is $54,321 - 50,000 = 4,321 < 5,000$. What is the binding limit?

### Choice & Clause Relied On
- Because $\min(54321, P_{\mathrm{EMI}}, 10\,I, 2500000) = 54321$, the binding constraint prior to flooring is the requested amount.
- `binding_limit` is `"requested"`.
- Because $50,000 + 5,000 = 55,000 > 54,321$, A04 does not fire, no reason code is emitted (`reason_codes: []`), and decision is `eligible`.
- This is verified against D1 cases `req_not_mult_5000_54321`, `req_not_mult_5000_123456`, and `a04_777777`.

---

## 6. Precedence and Winning Outcome Reason Codes

### Clarification Confirmed by Owner Decisions
Owner Decision #2 provides explicit guidance on precedence:
1. `ineligible` rules take precedence over `refer` rules.
2. `reason_codes` lists the codes of fired rules for the winning outcome only, deduplicated, in rule layer order (V, K, R, E, A, P).
3. `fired_rules` in `oracle_expected.json` lists all rule IDs that fired with outcome `ineligible`, `refer`, or `reduced_offer`, in canonical rule order.
4. Default outcome when no rule determines an outcome is `refer` with reason code `NO_RULE_APPLICABLE`.

