# Predicate and Fact Schema (v0.1)

Nov 5, 2026 · @Kulvinder

## 1. Conventions

This document fixes the vocabulary the rules, the code and the tests share. Rule IDs and reason codes come from the Credit Policy and Rule Catalog; formulas come from the Lending Calculations Specification.

**Naming and types**

- Predicate and field names use `snake_case`. The first argument of every applicant fact is the applicant constant, for example `a001`.
- Money values are whole rupees (integers) in inputs. Computed amounts use exact decimals or rationals, never binary floats.
- Booleans are `true` or `false`. Enumerations are lower-case atoms such as `salaried`.

**Three kinds of bad data**

| Case | Example | Handling |
| --- | --- | --- |
| Malformed or out-of-domain value | credit score 1,000, age "abc" | Schema error returned to the caller; no decision is made (FR-01) |
| Required field absent or null | no `monthly_net_income` | The fact builder asserts `unknown(A, Field)`; rule V01 fires and the decision is REFER |
| Credit score null | no bureau record | `unknown(A, credit_score)` is asserted; rule R01 fires; V01 does not |

**Closed-world rule.** Within the engine, anything not provable is false. A rule that needs a fact guarded by `unknown` must not run on it: the engine records the rule as not evaluated and states which fact was missing.

**Protected attributes.** Gender, religion and caste never enter the fact base. They live in a separate audit table keyed by applicant ID and are read only by the fairness module. Age and region tier are in the fact base only because rules K01, X01 and X02 use them.

## 2. Input facts

Each row is one input field, the base predicate it becomes, and the rules that read it. A rule may read only the predicates listed against it.

| Field | Predicate | Type and valid range | Required | Read by rules |
| --- | --- | --- | --- | --- |
| `applicant_id` | constant | Unique string, for example `a001` | Yes | All |
| `age` | `age(A, Years)` | Integer, 0 to 120 | Yes | K01, X01 |
| `employment_type` | `employment_type(A, T)` | `salaried`, `self_employed` or `other` | Yes | K06, R03 |
| `employment_months` | `employment_months(A, M)` | Integer, 0 to 600; months in current employment or business | Yes | K06 |
| `monthly_net_income` | `monthly_net_income(A, Rs)` | Integer rupees, 0 or more | Yes | K05, E01, A01, A02 |
| `monthly_obligations` | `monthly_obligations(A, Rs)` | Integer rupees, 0 or more; existing EMIs and similar fixed payments | Yes | E01, E02, A01 |
| `credit_score` | `credit_score(A, S)` | Integer, 300 to 900, or null for no bureau record | No (null allowed) | K04, E02, R01 |
| `enquiries_6m` | `enquiries_6m(A, N)` | Integer, 0 or more | Yes | R02 |
| `severe_delinquency_36m` | `severe_delinquency_36m(A, Bool)` | Boolean; any payment 90+ days overdue in the last 36 months | Yes | K03 |
| `written_off` | `written_off(A, Bool)` | Boolean; any written-off account | Yes | K03 |
| `kyc_verified` | `kyc_verified(A, Bool)` | Boolean | Yes | K02 |
| `consent_given` | `consent_given(A, Bool)` | Boolean | Yes | V02 |
| `requested_amount` | `requested_amount(A, Rs)` | Integer rupees, above 0 | Yes | V03, A02 |
| `requested_tenure_months` | `requested_tenure(A, N)` | Integer, above 0 | Yes | V04, A01 |
| `region_tier` | `region_tier(A, Tier)` | Integer 1 to 3 | No (loaded only when X02 is enabled) | X02 |

**Example application (JSON)**

```json
{
  "applicant_id": "a001",
  "age": 34,
  "employment_type": "salaried",
  "employment_months": 48,
  "monthly_net_income": 40000,
  "monthly_obligations": 12000,
  "credit_score": 760,
  "enquiries_6m": 2,
  "severe_delinquency_36m": false,
  "written_off": false,
  "kyc_verified": true,
  "consent_given": true,
  "requested_amount": 800000,
  "requested_tenure_months": 48
}
```

This example is test vector TV2 in the Lending Calculations Specification. Rule K03 reads two separate fields so each can be reported and tested on its own, while both feed the single reason code ADVERSE\_REPAYMENT\_HISTORY.

**Audit-only store (never read by the rule engine):** `gender`, `religion`, `caste`, and any other attribute used only to measure group outcomes.

## 3. Derived and outcome predicates

Derived predicates are computed from input facts by the formulas in the Lending Calculations Specification or by rules in the catalog. Outcome predicates record what the system concluded. Everything in the last two tables must appear in the decision trace.

**Derived predicates**

| Predicate | Meaning | Defined by |
| --- | --- | --- |
| `existing_foir(A, F)` | Obligations divided by net income | Formula F1 |
| `band(A, B)` | Pricing band `a`, `b` or `c`; absent when no band row matches | Rule E02 |
| `max_emi(A, Rs)` | Largest affordable EMI under the band's post-loan cap | Formula F4, rule A01 |
| `max_principal_emi(A, Rs)` | Largest principal that EMI supports at the indicative rate and requested tenure | Formula F5, rule A01 |
| `recommended_amount(A, Rs)` | Offered amount, rounded down to 5,000 | Formula F6, rule A02 |
| `binding_limit(A, L)` | `requested`, `capacity`, `income_multiple` or `product_maximum` | Formula F6 |
| `indicative_rate(A, Pct)` | Midpoint rate of the band | Rule P01 |
| `emi(A, Rs)` | EMI on the recommended amount | Formula F3 |
| `fee(A, Rs)` | Processing fee | Formula F7 |
| `apr(A, Pct)` | Annualised all-in cost | Formula F9 |
| `post_loan_foir(A, F)` | FOIR after adding the new EMI | Formula F8 |

**Outcome and control predicates**

| Predicate | Meaning |
| --- | --- |
| `fired(A, RuleId, Outcome, Reason)` | Rule `RuleId` fired with outcome `ineligible`, `refer`, `derive` or `reduced_offer`, and reason code (or `none`) |
| `not_evaluated(A, RuleId, Field)` | Rule skipped because `Field` is unknown |
| `skipped(A, RuleId, Why)` | Rule skipped for another reason, for example an earlier INELIGIBLE or REFER outcome |
| `decision(A, D)` | Final decision: `eligible`, `ineligible` or `refer` |
| `reason(A, Code)` | Reason code reported to the applicant; one per fired adverse rule |
| `unknown(A, Field)` | Input field absent or null |

**Rule of thumb for the coding agent.** A rule is a clause whose head is `fired/4` or a derived predicate. A rule never reads a derived value that is computed after it in layer order, and never reads an outcome predicate, except that derivation rules E02, A01, A02 and P01 first check that no INELIGIBLE or REFER outcome has been recorded.

## 4. First-order logic rules and Prolog encoding

Every catalog rule is written twice: as a first-order formula for the report, and as a Prolog clause for the engine. The examples below cover one rule per layer plus the decision rule; the coding agent encodes the rest the same way. This is a sketch to fix the shape, not final code, and it assumes the default engine in ADR-001 (SWI-Prolog).

**Formulas**

V01, a required field is missing:

```latex
\forall A\,\big(\exists f\,(\mathrm{required}(f) \land \mathrm{unknown}(A,f)) \rightarrow \mathrm{fired}(A,\mathrm{v01},\mathrm{refer})\big)
```

K04, credit score below the minimum:

```latex
\forall A\,\forall S\,\big(\mathrm{credit\_score}(A,S) \land S < \mathrm{min\_credit\_score} \rightarrow \mathrm{fired}(A,\mathrm{k04},\mathrm{ineligible})\big)
```

R01, no credit score:

```latex
\forall A\,\big(\mathrm{unknown}(A,\mathrm{credit\_score}) \rightarrow \mathrm{fired}(A,\mathrm{r01},\mathrm{refer})\big)
```

E01, existing obligations too high:

```latex
\forall A\,\forall F\,\big(\mathrm{existing\_foir}(A,F) \land F > \mathrm{max\_existing\_foir} \rightarrow \mathrm{fired}(A,\mathrm{e01},\mathrm{ineligible})\big)
```

Decision precedence:

```latex
\begin{aligned}
&\forall A\,\big(\exists r\,\mathrm{fired}(A,r,\mathrm{ineligible}) \rightarrow \mathrm{decision}(A,\mathrm{ineligible})\big)\\
&\forall A\,\big(\lnot\exists r\,\mathrm{fired}(A,r,\mathrm{ineligible}) \land \exists r\,\mathrm{fired}(A,r,\mathrm{refer}) \rightarrow \mathrm{decision}(A,\mathrm{refer})\big)
\end{aligned}
```

**Prolog encoding**

```prolog
% Parameters come from the parameter file, never from rule text.
% param(min_credit_score, 650).  param(max_existing_foir, 0.50).
% band_param(Band, MinScore, MaxFoir, IndicativeRate, PostLoanFoirCap).

required_field(F) :- member(F, [age, employment_type, employment_months,
    monthly_net_income, monthly_obligations, enquiries_6m,
    severe_delinquency_36m, written_off, kyc_verified, consent_given,
    requested_amount, requested_tenure]).

% V01
fired(A, v01, refer, incomplete_application) :-
    findall(F, (required_field(F), unknown(A, F)), [_|_]).

% K04 (not evaluated when the score is unknown; see trace rules)
fired(A, k04, ineligible, credit_score_below_minimum) :-
    \+ unknown(A, credit_score),
    credit_score(A, S), param(min_credit_score, Min), S < Min.

% R01
fired(A, r01, refer, no_credit_history) :- unknown(A, credit_score).

% E01
fired(A, e01, ineligible, high_existing_obligations) :-
    existing_foir(A, F), param(max_existing_foir, Max), F > Max.

% Layers that can block the amount and pricing steps.
blocked_before_amount(A) :-
    fired(A, Id, Out, _), memberchk(Out, [ineligible, refer]),
    rule_layer(Id, L), memberchk(L, [validation, knockout, referral, eligibility]).

% E02: first matching band in the order a, b, c wins.
band(A, B) :-
    \+ blocked_before_amount(A),
    member(B, [a, b, c]),
    band_param(B, MinScore, MaxFoir, _Rate, _Cap),
    credit_score(A, S), existing_foir(A, F),
    S >= MinScore, F =< MaxFoir, !.

% A03
fired(A, a03, ineligible, insufficient_repayment_capacity) :-
    \+ blocked_before_amount(A),
    recommended_amount(A, P), param(min_amount, Min), P < Min.

% Final decision: precedence, then the CP-8.1 default.
decision(A, ineligible) :- fired(A, _, ineligible, _), !.
decision(A, refer)      :- fired(A, _, refer, _), !.
decision(A, eligible)   :- band(A, _), recommended_amount(A, _), !.
decision(_, refer).     % no rule applied: reason no_rule_applicable
```

**Notes for the coding agent**

- The engine must capture, for every `fired/4` and every skipped rule, the facts it used. Either return them from the rule or run rules through a small meta-interpreter that logs each call. Section 5 gives the target format.
- Do not use `assert` or `retract` inside rule bodies; the fact builder asserts inputs before evaluation and the evaluator only reads.
- Rules for experimental X01 and X02 live in the `experimental` file and are loaded only when the configuration enables them.
- Add the missing-fact guards shown in K04 to every rule that reads a nullable or required field, so a missing input is traced as "not evaluated" rather than failing silently.

## 5. Decision trace schema

The trace is the single source for the audit log, the applicant notice, the reviewer view and the explanation tests. Reason codes and notice text are generated from it, never recomputed.

| Field | Meaning |
| --- | --- |
| `decision_id` | Unique ID for this decision |
| `applicant_ref` | SHA-256 of the applicant ID (prefixed sha256:); a stable, non-raw reference that joins the audit log to the audit-only attribute store |
| `input_hash` | SHA-256 of the canonical JSON of the validated input (prefixed sha256:); the key to the replay input snapshot (see the audit log specification) |
| `rule_set_version` | Tag of all rule and parameter files, including experimental switches; a separate field rule\_set\_hash holds their SHA-256 (see the Rule File and Parameter File Format Specification) |
| `evaluated_at` | UTC timestamp |
| `decision` | `eligible`, `ineligible` or `refer` |
| `steps` | Every active rule in layer order, each with a status |
| `steps[].rule_version, steps[].layer` | The rule's version and layer from its metadata, on every step (FR-10) |
| `steps[].status` | `fired`, `not_fired`, `not_evaluated` or `skipped` |
| `steps[].facts_used` | Names and values of the facts the rule read |
| `steps[].missing` | For `not_evaluated`, the unknown field |
| `derived` | Every computed value: FOIR, band, caps, amounts, EMI, fee, APR |
| `reason_codes` | Reason codes from fired adverse or reduced-offer rules, in step order |
| `offer` | Present only for eligible decisions: amount, tenure, rate band, indicative rate, EMI, fee, total interest, APR |

The full trace lists all 20 active rules every time, so a reader can see what did not apply. The example below is test vector TV2 shortened to the steps that matter.

```json
{
  "decision_id": "d-0001",
  "applicant_ref": "sha256:...",
  "rule_set_version": "rules-0.1.0+params-0.1.0",
  "rule_set_hash": "sha256:...",
  "evaluated_at": "2026-11-05T09:00:00Z",
  "decision": "eligible",
  "steps": [
    {"order": 1, "rule_id": "V01", "status": "not_fired", "facts_used": {"missing_fields": []}},
    {"order": 8, "rule_id": "K04", "status": "not_fired", "facts_used": {"credit_score": 760, "min_credit_score": 650}},
    {"order": 14, "rule_id": "E01", "status": "not_fired", "facts_used": {"existing_foir": "0.30", "max_existing_foir": "0.50"}},
    {"order": 15, "rule_id": "E02", "status": "fired", "outcome": "derive", "facts_used": {"credit_score": 760, "existing_foir": "0.30"}, "derived": {"band": "A"}},
    {"order": 16, "rule_id": "A01", "status": "fired", "outcome": "derive", "derived": {"max_emi": "10000.00", "max_principal_emi": "379739.59"}},
    {"order": 17, "rule_id": "A02", "status": "fired", "outcome": "derive", "derived": {"recommended_amount": 375000, "binding_limit": "capacity"}},
    {"order": 18, "rule_id": "A03", "status": "not_fired", "facts_used": {"recommended_amount": 375000, "min_amount": 50000}},
    {"order": 19, "rule_id": "A04", "status": "fired", "outcome": "reduced_offer", "reason_code": "AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY", "facts_used": {"requested_amount": 800000, "recommended_amount": 375000}},
    {"order": 20, "rule_id": "P01", "status": "fired", "outcome": "derive", "derived": {"indicative_rate": "12.0", "fee": "7500.00"}}
  ],
  "derived": {"existing_foir": "0.3000", "emi": "9875.19", "post_loan_foir": "0.5469", "apr": "13.09"},
  "reason_codes": ["AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY"],
  "offer": {"amount": 375000, "tenure_months": 48, "band": "A", "rate_range": "11.0-13.0", "indicative_rate": "12.0", "emi": "9875.19", "fee": "7500.00", "total_interest": "99009.12", "apr": "13.09"}
}
```

**Trace requirements**

- [ ] Trace validates against a JSON Schema checked in with the code
- [ ] Numbers that are money or ratios are strings holding exact decimals, so no precision is lost
- [ ] Every reason code in `reason_codes` has a fired step with the same code
- [ ] Replaying an input with the recorded `rule_set_version` regenerates an identical trace
- [ ] Applicant notice text is generated only from `reason_codes` and the facts in the trace
