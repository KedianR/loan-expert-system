# Decision Tables (v0.1)

Repo path: `docs/decision-tables.md`. Tier 2 document, written 8 November 2026 for Phase 2 (WP-07). It shows the rule combinations on paper, fixes four points the other documents leave open, and specifies the hygiene checks the loader format specification hands to "the Decision Tables".

**Who reads it.** The engine session reads it. The oracle session must NOT read it (the oracle works from the catalog, the calculations, the fact schema and D1 only). Every decision in section 7 that the oracle needs is stated in the oracle prompt.

**Where it sits.** If this document and the Credit Policy and Rule Catalog disagree, the catalog wins and this document is corrected. Nothing here changes a threshold, a formula or a reason-code text.

## 1. Fixed evaluation semantics

Values are **known**, **unknown** (input missing or null, or a derived value that cannot be computed) or **absent** (the rule that produces a derived value did not run).

| Situation for one rule | Trace status |
| --- | --- |
| Condition true | `fired` |
| Condition false | `not_fired` |
| The rule reads an unknown field (except through `known()` / `unknown()`) | `not_evaluated`, with the missing field |
| The rule reads an absent field | `skipped`, with the reason |
| The rule's `when` is `no_blocking_outcome`, or starts with `no_blocking_outcome and`, and a blocking outcome exists | `skipped`, with the reason "blocking outcome" |

A **blocking outcome** is an earlier rule that fired with outcome `ineligible` or `refer`. Outcomes `derive` and `reduced_offer` never block.

Order of work for one application: V01 to V04, K01 to K06, R01 to R03, E01, E02, A01 to A04, P01. Every rule in V, K and R is evaluated, so all reasons are reported. The full trace lists all 20 active rules.

## 2. What each rule reads, and what unknown does to it

| Rule | Reads | If a read field is unknown |
| --- | --- | --- |
| V01 | all fields the registry marks required | fires (this is its job) |
| V02 | consent_given | not_evaluated |
| V03 | requested_amount | not_evaluated |
| V04 | requested_tenure_months | not_evaluated |
| K01 | age | not_evaluated |
| K02 | kyc_verified | not_evaluated |
| K03 | severe_delinquency_36m, written_off | not_evaluated (if either is unknown) |
| K04 | credit_score | not_evaluated (null score) |
| K05 | monthly_net_income | not_evaluated |
| K06 | employment_type, employment_months | not_evaluated |
| R01 | credit_score, through `unknown()` | fires on a null score |
| R02 | enquiries_6m | not_evaluated |
| R03 | employment_type | not_evaluated |
| E01 | existing_foir | not_evaluated (income or obligations unknown, or income zero) |
| E02, A01, A02, P01 | per the registry; need no blocking outcome | skipped when blocked; not_evaluated if an input is unknown |
| A03, A04 | recommended_amount (A04 also requested_amount); A04 needs no blocking outcome | skipped when the derived field is absent or a blocking outcome exists |

**Invariant I-1.** With the baseline parameters, whenever E02, A01, A02, A03, A04 or P01 get to run, every input they read is known. A missing required field fires V01, a null score fires R01, and zero income fires K05 (the minimum income is above zero), and each of those blocks. The completeness check (section 6) tests I-1. If a parameter change breaks it (for example a minimum income of 0, so that zero income passes K05), existing_foir stays unknown, E02 is not_evaluated, no band is found, and the decision defaults to REFER with NO_RULE_APPLICABLE; the check reports that as a gap.

## 3. Decision and reason codes

The decision is INELIGIBLE if any rule fired with outcome `ineligible`; otherwise REFER if any fired with `refer`; otherwise ELIGIBLE when a band and a recommended amount exist; otherwise the default.

| Fired outcomes | Decision | `reason_codes` (in step order, each code once) |
| --- | --- | --- |
| At least one `ineligible` | INELIGIBLE | The codes of every fired `ineligible` rule. Fired `refer` codes stay in the trace only. |
| No `ineligible`, at least one `refer` | REFER | The codes of every fired `refer` rule. |
| No blocking outcome, band and amount derived, A04 fired | ELIGIBLE | The one A04 code. |
| No blocking outcome, band and amount derived, A04 not fired | ELIGIBLE | Empty. |
| No blocking outcome, no band or no amount | REFER | `NO_RULE_APPLICABLE` (the default; never reached on any golden case). |

**Decision DT-2 (owner decision, 8 November 2026).** The catalog says referral reasons "stay in the trace for the reviewer" when an INELIGIBLE rule also fires; it does not say whether they appear in `reason_codes`. They do not. The applicant notice for an INELIGIBLE decision shows only the reasons for the refusal, and the trace still lists the fired REFER rules.

## 4. The derivation path

After E01, if no blocking outcome exists, E02 finds the band and A01 and A02 compute the amount (formulas F4 to F6). Then:

| Recommended amount R* against minimum M (50,000) and request Q | A03 | A04 | P01 | Decision |
| --- | --- | --- | --- | --- |
| R* < M | fires, INSUFFICIENT_REPAYMENT_CAPACITY | skipped (blocking outcome) | skipped | INELIGIBLE |
| R* >= M and R* + step <= Q | not_fired | fires, one AMOUNT_LIMITED_BY_ code | fires | ELIGIBLE, reduced terms |
| R* >= M and R* + step > Q | not_fired | not_fired | fires | ELIGIBLE, as requested (within one step) |

**Decision DT-1 (found in Phase 2 preparation; catalog and format specification corrected).** As the catalog first stated A04, it also fired after A03, because A04 only read the recommended amount. TV6 and TV8 would then have reported both INSUFFICIENT_REPAYMENT_CAPACITY and AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY. A04 now reads `no_blocking_outcome and recommended_amount + amount_step <= requested_amount`.

**Binding limit.** The smallest of the capacity limit, 10 times income and the product maximum; ties between caps go to capacity, then income multiple, then product maximum (F6). The binding limit is `requested` whenever the request is equal to or smaller than all three caps, including when a cap equals the request exactly (decision DT-4). **AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM cannot occur while V03 is active**, because V03 already rejects any request above the product maximum. The code stays in the catalog; the firing matrix marks it "unreachable by design" and no test may require it.

## 5. Firing and boundary cases (baseline parameters)

Each row changes the base applicant (TV1: age 34, salaried, 48 months employed, income 80,000, obligations 10,000, score 735, 2 enquiries, no adverse history, KYC verified, consent given, request 700,000, 36 months) in the way stated. The engine session writes one test per row, and D1 must contain every row. **Fired** lists the rules that fired with outcome `ineligible`, `refer` or `reduced_offer`; for every ELIGIBLE row P01 and the derive rules also fire. Expected values were checked with an independent throwaway calculation; they are not a substitute for the oracle.

| Case | Rule | Change | Decision | reason_codes | Fired | Band | Recommended |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B0 | - | Base applicant (TV1) | ELIGIBLE | none | none | B | 700000 |
| V01-a | V01 | Income missing | REFER | INCOMPLETE_APPLICATION | V01 | - | - |
| V01-b | V01 | Requested amount missing | REFER | INCOMPLETE_APPLICATION | V01 | - | - |
| V01-c | V01 | Consent missing (V02 not evaluated) | REFER | INCOMPLETE_APPLICATION | V01 | - | - |
| V02-a | V02 | Consent false | INELIGIBLE | CONSENT_NOT_GIVEN | V02 | - | - |
| V03-49999 | V03 | Requested amount 49,999 | INELIGIBLE | AMOUNT_OUTSIDE_PRODUCT_LIMITS | V03 | - | - |
| V03-50000 | V03 | Requested amount 50,000 | ELIGIBLE | none | none | B | 50000 |
| V03-2500000 | V03 | Requested amount 2,500,000 | ELIGIBLE | AMOUNT_LIMITED_BY_INCOME_MULTIPLE | A04 | B | 800000 |
| V03-2500001 | V03 | Requested amount 2,500,001 | INELIGIBLE | AMOUNT_OUTSIDE_PRODUCT_LIMITS | V03 | - | - |
| V04-11 | V04 | Tenure 11 months | INELIGIBLE | TENURE_OUTSIDE_PRODUCT_LIMITS | V04 | - | - |
| V04-12 | V04 | Tenure 12 months | ELIGIBLE | AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY | A04 | B | 330000 |
| V04-60 | V04 | Tenure 60 months | ELIGIBLE | none | none | B | 700000 |
| V04-61 | V04 | Tenure 61 months | INELIGIBLE | TENURE_OUTSIDE_PRODUCT_LIMITS | V04 | - | - |
| K01-17 | K01 | Age 17 | INELIGIBLE | LEGAL_CAPACITY_NOT_MET | K01 | - | - |
| K01-18 | K01 | Age 18 | ELIGIBLE | none | none | B | 700000 |
| K02-a | K02 | KYC not verified | INELIGIBLE | KYC_NOT_VERIFIED | K02 | - | - |
| K03-a | K03 | Severe delinquency true | INELIGIBLE | ADVERSE_REPAYMENT_HISTORY | K03 | - | - |
| K03-b | K03 | Written off true | INELIGIBLE | ADVERSE_REPAYMENT_HISTORY | K03 | - | - |
| K04-649 | K04 | Credit score 649 | INELIGIBLE | CREDIT_SCORE_BELOW_MINIMUM | K04 | - | - |
| K04-650 | K04 | Credit score 650 | ELIGIBLE | none | none | C | 700000 |
| K05-14999 | K05 | Income 14,999, obligations 0 | INELIGIBLE | INCOME_BELOW_MINIMUM | K05 | - | - |
| K05-15000 | K05 | Income 15,000, obligations 0 | ELIGIBLE | AMOUNT_LIMITED_BY_INCOME_MULTIPLE | A04 | B | 150000 |
| K05-0 | K05 | Income 0 (E01 not evaluated, K05 wins) | INELIGIBLE | INCOME_BELOW_MINIMUM | K05 | - | - |
| K06-s5 | K06 | Salaried, 5 months | INELIGIBLE | EMPLOYMENT_TENURE_TOO_SHORT | K06 | - | - |
| K06-s6 | K06 | Salaried, 6 months | ELIGIBLE | none | none | B | 700000 |
| K06-e23 | K06 | Self-employed, 23 months | INELIGIBLE | EMPLOYMENT_TENURE_TOO_SHORT | K06 | - | - |
| K06-e24 | K06 | Self-employed, 24 months | ELIGIBLE | none | none | B | 700000 |
| R01-a | R01 | Credit score null | REFER | NO_CREDIT_HISTORY | R01 | - | - |
| R02-5 | R02 | 5 enquiries | ELIGIBLE | none | none | B | 700000 |
| R02-6 | R02 | 6 enquiries | REFER | HIGH_RECENT_ENQUIRIES | R02 | - | - |
| R03-a | R03 | Employment type other | REFER | EMPLOYMENT_TYPE_REQUIRES_REVIEW | R03 | - | - |
| E01-a | E01 | FOIR exactly 0.50 (income 100,000; obligations 50,000), score 650 | INELIGIBLE | INSUFFICIENT_REPAYMENT_CAPACITY | A03 | C | 0 |
| E01-b | E01 | FOIR 0.50001 (obligations 50,001) | INELIGIBLE | HIGH_EXISTING_OBLIGATIONS | E01 | - | - |
| E02-A-750-30000 | E02 | Band lookup A: score 750, FOIR 0.30 (income 100,000, request 50,000, 24 months) | ELIGIBLE | none | none | A | 50000 |
| E02-B-749-30000 | E02 | Band lookup B: score 749, FOIR 0.30 (income 100,000, request 50,000, 24 months) | ELIGIBLE | none | none | B | 50000 |
| E02-B-750-30001 | E02 | Band lookup B: score 750, FOIR 0.30001 (income 100,000, request 50,000, 24 months) | ELIGIBLE | none | none | B | 50000 |
| E02-B-700-40000 | E02 | Band lookup B: score 700, FOIR 0.40 (income 100,000, request 50,000, 24 months) | ELIGIBLE | none | none | B | 50000 |
| E02-C-699-40000 | E02 | Band lookup C: score 699, FOIR 0.40 (income 100,000, request 50,000, 24 months) | ELIGIBLE | none | none | C | 50000 |
| E02-C-700-40001 | E02 | Band lookup C: score 700, FOIR 0.40001 (income 100,000, request 50,000, 24 months) | ELIGIBLE | none | none | C | 50000 |
| E02-C-650-50000 | E02 | Band lookup C: score 650, FOIR 0.50 (income 100,000, request 50,000, 24 months) | INELIGIBLE | INSUFFICIENT_REPAYMENT_CAPACITY | A03 | C | 0 |
| A02-cap | A02/A04 | Capacity limit (TV2) | ELIGIBLE | AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY | A04 | A | 375000 |
| A02-inc | A02/A04 | Income multiple limit (TV3) | ELIGIBLE | AMOUNT_LIMITED_BY_INCOME_MULTIPLE | A04 | B | 500000 |
| A03-a | A03 | Recommended below minimum (TV8) | INELIGIBLE | INSUFFICIENT_REPAYMENT_CAPACITY | A03 | C | 0 |
| A03-b | A03 | No EMI room at all (TV6); A04 must not also fire | INELIGIBLE | INSUFFICIENT_REPAYMENT_CAPACITY | A03 | C | 0 |
| A04-777 | A04 | Request 777,777, room for the full amount: no A04 | ELIGIBLE | none | none | A | 775000 |
| A04-379999 | A04 | TV2 inputs, request 379,999: recommended 375,000 is 4,999 below, no A04 | ELIGIBLE | none | none | A | 375000 |
| A04-380000 | A04 | TV2 inputs, request 380,000: exactly one step above, A04 fires | ELIGIBLE | AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY | A04 | A | 375000 |
| A04-tie | A04 | Request equals 10 x income (500,000), capacity is higher: no A04 | ELIGIBLE | none | none | B | 500000 |
| X-multi | K03+K04+K05 | Severe delinquency, score 600, income 10,000 | INELIGIBLE | ADVERSE_REPAYMENT_HISTORY, CREDIT_SCORE_BELOW_MINIMUM, INCOME_BELOW_MINIMUM | K03, K04, K05 | - | - |
| X-ref-inel | R02+K04 | Score 600 and 7 enquiries: INELIGIBLE wins, REFER code stays out of reason_codes | INELIGIBLE | CREDIT_SCORE_BELOW_MINIMUM | K04, R02 | - | - |
| X-refonly | R02+R03 | 7 enquiries and employment other: both REFER codes | REFER | HIGH_RECENT_ENQUIRIES, EMPLOYMENT_TYPE_REQUIRES_REVIEW | R02, R03 | - | - |
| X-inc-consent | V01+V02 | Income missing and consent false: INELIGIBLE wins | INELIGIBLE | CONSENT_NOT_GIVEN | V01, V02 | - | - |
| X-null-score-amt | R01 | Null score on the TV2 applicant: REFER, no derivation | REFER | NO_CREDIT_HISTORY | R01 | - | - |

Also test one case per remaining required field missing in turn (V01 fires, the rules that read it are not_evaluated), and each boolean input with its adverse value.

## 6. Hygiene checks (the analyser)

The loader runs the orphan and cycle checks. The analyser runs the other three on the parsed condition trees and the parameter values, and `make check-rules` runs both. Any finding below is an error: exit non-zero and print every finding.

**The grid.** For every field an active rule's `when` reads, build the values the rules can tell apart: for each threshold it is compared with (a parameter, or a sum such as `recommended_amount + amount_step`), the value just below, exactly at and just above it, plus `unknown` where the registry allows it (nullable or required). Derived values come from the real calculation functions, never from a second implementation. The analyser prints the number of grid points, is deterministic, and finishes in about a minute. Level 1 is the full product over known values; level 2 sets each field to `unknown` in turn against every single value of each other field.

| Check | What it proves | Finding code | Seeded fault (test copy of the rule files) |
| --- | --- | --- | --- |
| Completeness | At every grid point exactly one decision results and it is never the NO_RULE_APPLICABLE default. Invariant I-1 holds. | `COMPLETENESS_GAP` | Remove band C from the parameters with the coverage check switched off: points with a score of 650 or more reach the default. |
| Contradiction | No two active rules with the same condition give different outcomes, and no two derive rules compute the same field. Overlaps of INELIGIBLE with REFER are allowed because precedence orders them; they are listed, not flagged. | `CONTRADICTION` | Add K07 with the same `when` as K04 and outcome `refer`. |
| Redundancy | No active rule fires only at points where another rule with the same outcome and reason code also fires. | `REDUNDANT_RULE` | Add K07 with `credit_score < min_credit_score and enquiries_6m > max_enquiries_6m`, outcome ineligible, code CREDIT_SCORE_BELOW_MINIMUM. |
| Cycles | No derived field depends on itself (loader, `CYCLE`). | `CYCLE` | Registry change so that two derived fields are each produced from the other. |
| Orphans | Every code in a rule exists, and every code is raised by a rule (loader, `ORPHAN_CODE`). | `ORPHAN_CODE` | Format specification test RT-11. |

**Protected-attribute check.** A static scan fails the build if a rule `when`, the field registry, the calculation registry, `src/facts` or `src/engine` names gender, religion, caste or any other audit-only attribute, and `make check-rules` runs it. Finding code `PROTECTED_ATTRIBUTE_READ`. Seeded fault: a line naming `gender` in a test copy of the fact builder.

**Firing matrix.** A generated table of rule against D1 case counts: how many D1 cases fire each rule, one row per rule. Every active rule has a count above zero, except that AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM is shown as unreachable by design.

## 7. Decisions recorded here

| ID | Decision | Where else it is stated |
| --- | --- | --- |
| DT-1 | A04 requires no blocking outcome. | Catalog (A04 row and notes), Format Specification (rule table, baseline TOML, point 6, condition language) |
| DT-2 | `reason_codes` holds the codes of the fired rules of the winning outcome only; refer codes stay in the trace when INELIGIBLE wins. | This document; the oracle prompt |
| DT-3 | AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM is unreachable while V03 is active; kept in the catalog. | This document |
| DT-4 | When the request equals the smallest cap, the whole request fits and the binding limit is `requested` (found in the Phase 2 oracle comparison, 9 November 2026). | Lending Calculations Specification, F6; the oracle prompt follow-up |
