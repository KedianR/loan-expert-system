# Phase 2 report

Date: 2026-11-09
Commit hash: 56dc68b0e4d8b1e1d0ba1e69a1277e936024d34e
Agent session: engine-session

## 1. Summary

Phase 2 deliverable complete: rule engine, hygiene analyser, D1 coverage set, and reference oracle comparison (WP-06 to WP-10 and WP-16a). Rules and reason codes were authored into 7 layer TOML files under `rules/` conforming to the condition grammar in `docs/09-file-formats.md` and Credit Policy `docs/02-policy-and-rules.md`, with owner amendments DT-1 (A04 no blocking outcome), DT-2 (winning outcome reason codes only in `reason_codes`), and DT-3 (AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM unreachable by design). 

A deterministic Prolog generator produces `build/rules.pl`. The engine evaluates applications in layer order with exact `Decimal` arithmetic crossing boundaries, executing pure calculation functions from `src/calc`. The hygiene analyser verifies completeness, contradiction, redundancy, protected-attribute bans, and generates the rule firing matrix across D1. D1 contains 82 deterministic synthetic cases in `data/d1/d1_cases.json`, all validating against `schemas/input.schema.json`. Every active rule fires at least once on D1. 

All 122 unit, property, and golden vector tests pass cleanly under `make test`. `make check`, `make check-rules`, and `make oracle-diff` succeed with zero errors.

## 2. Work packages

| Work package | Done | Notes |
| --- | --- | --- |
| WP-06 Rule and reason code catalog | Yes | 22 rules across 7 layer TOML files (`validation.toml`, `knockout.toml`, `referral.toml`, `eligibility.toml`, `amount.toml`, `pricing.toml`, `experimental.toml`) and 21 reason codes in `rules/reason_codes.toml`. Rule set version `1.0.0`. No numeric literals in `when` conditions; all parameters referenced by name. |
| WP-07 Condition parser and Prolog generator | Yes | `src/engine/condition_parser.py` parses condition grammar, type-checks against `rules/fields.toml`, rejects unknown names, magic numbers, and type mismatches. `src/engine/prolog_generator.py` generates deterministic Prolog clauses with unknown guards and discontiguous directives in `build/rules.pl`. Syntax verified with SWI-Prolog 10.1.20. |
| WP-08 Rule engine | Yes | `src/engine/engine.py` implements `decide(application, rule_set) -> result`. Evaluates layers in fixed order (V01-V04, K01-K06, R01-R03, E01, E02, A01-A04, P01). Implements skip logic for absent derived fields (`band`, `max_principal_emi`, `recommended_amount`). Synthesizes DT-2 winning outcome reason codes. Full trace steps recorded. Python/Prolog exchange uses JSON lines over a persistent `swipl` process (OQ-005). |
| WP-09 Hygiene analyser | Yes | `src/engine/hygiene.py` implements static checks for `COMPLETENESS_GAP`, `CONTRADICTION`, `REDUNDANT_RULE`, `PROTECTED_ATTRIBUTE_READ` (scanning rules, facts, calc, and engine), and generates the D1 firing matrix. Integrated into `make check-rules`. |
| WP-10 Rule tests and test vectors | Yes | 21 rule firing and threshold-boundary tests in `tests/unit/test_rules_firing_and_boundaries.py`. Loader tests RT-01 to RT-11 in `tests/unit/test_rule_loader.py`. Seeded hygiene fault tests in `tests/unit/test_hygiene.py`. Engine behaviour tests in `tests/unit/test_engine_behaviours.py`. Golden test vectors TV1 to TV9 in `tests/golden/test_engine_tv.py` match all expected outputs. |
| WP-16a D1 coverage set and oracle diff | Yes | Deterministic generator in `data/synthetic/d1_generator.py` produces 82 cases in `data/d1/d1_cases.json`, fully conforming to `schemas/input.schema.json`. `tools/oracle_diff.py` and `make oracle-diff` compare engine decisions against `data/d1/oracle_expected.json`. |

## 3. Exit criteria

| Criterion | Met (yes/no) | Evidence: file or command |
| --- | --- | --- |
| 21 rule firing and boundary tests pass | Yes | `tests/unit/test_rules_firing_and_boundaries.py` (21 passed). |
| Loader tests RT-01, RT-02, RT-04, RT-05, RT-07, RT-09, RT-11 pass | Yes | `tests/unit/test_rule_loader.py` (7 passed). |
| Hygiene checks detect all seeded faults | Yes | `tests/unit/test_hygiene.py` (4 passed: completeness gap, contradiction, redundancy, protected attribute read). |
| Engine behaviour tests pass | Yes | `tests/unit/test_engine_behaviours.py` (6 passed: null score, missing required field, derivation skip, default refer, 777,777 amount, A03/A04 mutex). |
| Golden test vectors TV1 to TV9 pass full outcome | Yes | `tests/golden/test_engine_tv.py` (all decisions, reason codes, fired rules, offer figures match; APR within 0.01 tolerance). |
| D1 rule coverage complete | Yes | `tests/golden/test_d1_coverage.py` (all 82 cases valid against schema; every active rule fires at least once; DT-3 verified). |
| Rule-set hash pin verified | Yes | `tests/golden/test_rule_set_pin.py` matches `sha256:eb7073a388817e0a455997c0c2ea86ccb25524cdff07faf8bf5ca98bb267be5a`, version `rules-1.0.0+params-0.1.0`. |
| Float-ban static checker passes | Yes | `tools/check_floats.py` scans `src/calc` and `src/facts` (5 files, 0 floats). |
| `make check-rules` passes | Yes | Exits 0: loads params, fields, rules, runs hygiene checks and protected-attribute scan, outputs firing matrix. |
| `make check` passes | Yes | Exits 0: float-ban, ruff lint, ruff format, 122 tests, check-params, check-fields, check-rules. |
| `make oracle-diff` passes | Yes | Exits 0: compares 82 cases against `data/d1/oracle_expected.json`. |

## 4. D1 Dataset and Rule Firing Matrix

Total D1 cases generated: **82 cases** (stored in `data/d1/d1_cases.json`).

```text
Rule Firing Matrix (D1 Dataset)
----------------------------------------
Rule ID    | Fired Count  | Notes                         
----------------------------------------
A01        | 47           | OK                            
A02        | 47           | OK                            
A03        | 5            | OK                            
A04        | 12           | OK                            
E01        | 1            | OK                            
E02        | 47           | OK                            
K01        | 1            | OK                            
K02        | 1            | OK                            
K03        | 3            | OK                            
K04        | 3            | OK                            
K05        | 3            | OK                            
K06        | 2            | OK                            
P01        | 42           | OK                            
R01        | 2            | OK                            
R02        | 3            | OK                            
R03        | 2            | OK                            
V01        | 13           | OK                            
V02        | 2            | OK                            
V03        | 2            | OK                            
V04        | 2            | OK                            
AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM | 0            | Unreachable by design (DT-3)  
----------------------------------------
```

## 5. Reference Oracle Comparison (`make oracle-diff`)

Across all 82 D1 cases, decisions, reason codes, adverse fired rules, pricing bands, recommended amounts, indicative rates, EMIs, fees, total interest, post-loan FOIRs, and APRs (within 0.01 tolerance) match 100% between the engine and the reference oracle.

Exactly **3 differences** were found, all on the `binding_limit` field:

| Case ID | Input Summary | Engine Output | Oracle Output | Resolution |
| --- | --- | --- | --- | --- |
| `a04_tie_request_income` | Request 500,000, Income 50,000 ($10 \times I = 500,000$) | `requested` | `income_multiple` | Documented in OQ-006 and `eval/oracle/NOTES.md`. Engine retains `src/calc` F6 behavior: when $P^{*} = R$, the applicant receives 100% of request, A04 does not fire, and `binding_limit` is `"requested"`. The oracle applied policy cap tie order on equality ($\min(\text{caps}) \le R$). |
| `cap_tie_income_prodmax` | Request 2,500,000, Income 250,000, Product Max 2,500,000 | `requested` | `income_multiple` | Same as above. Full request granted ($P^{*} = R = 2,500,000$). |
| `cap_tie_capacity_prodmax` | Request 2,500,000, Product Max 2,500,000, Capacity 4,480,927 | `requested` | `product_maximum` | Same as above. Full request granted ($P^{*} = R = 2,500,000$). |

Both implementations agree on the loan offer and zero shortfall ($P^{*} = R$). The discrepancy stems from whether `binding_limit` applies only when a cap restricts the request ($P^{*} < R$) per `docs/03-calculations.md` F6, or also labels ties when $R = \text{cap}$.

## 6. Gate commands output

### Gate command 1: `make check` (run via `mingw32-make check`)

Pass. Last 15 lines of output:

```text
K03        | 3            | OK                            
K04        | 3            | OK                            
K05        | 3            | OK                            
K06        | 2            | OK                            
P01        | 42           | OK                            
R01        | 2            | OK                            
R02        | 3            | OK                            
R03        | 2            | OK                            
V01        | 13           | OK                            
V02        | 2            | OK                            
V03        | 2            | OK                            
V04        | 2            | OK                            
AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM | 0            | Unreachable by design (DT-3)  
----------------------------------------

OK: all hygiene checks passed with zero findings.
""
"=== make check complete ==="
```

### Gate command 2: `make check-rules` (run via `mingw32-make check-rules`)

Pass. Last 15 lines of output:

```text
K03        | 3            | OK                            
K04        | 3            | OK                            
K05        | 3            | OK                            
K06        | 2            | OK                            
P01        | 42           | OK                            
R01        | 2            | OK                            
R02        | 3            | OK                            
R03        | 2            | OK                            
V01        | 13           | OK                            
V02        | 2            | OK                            
V03        | 2            | OK                            
V04        | 2            | OK                            
AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM | 0            | Unreachable by design (DT-3)  
----------------------------------------

OK: all hygiene checks passed with zero findings.
```

### Gate command 3: `make oracle-diff` (run via `mingw32-make oracle-diff`)

Pass. Output:

```text
python tools/oracle_diff.py
Diff report written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\data\d1\oracle_diff.md (3 differences).
  a04_tie_request_income: binding_limit engine=`requested` oracle=`income_multiple`
  cap_tie_income_prodmax: binding_limit engine=`requested` oracle=`income_multiple`
  cap_tie_capacity_prodmax: binding_limit engine=`requested` oracle=`product_maximum`
```
