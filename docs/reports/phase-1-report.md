# Phase 1 report

Date: 2026-11-08
Commit hash: 72c33c17a45509c2b339c9498ad2dd64713aee97
Agent session: 4aa3e301-93e7-488b-9cb9-da51f0589dac

## 1. Summary

Phase 1 deliverable complete: the calculation core (WP-04) and fact builder (WP-05). Pure functions implementing formulas F1 to F9 were built using exact `Decimal` arithmetic with no floating-point numbers. The field registry `rules/fields.toml` was authored to specification and validated via `make check-fields`. The fact builder validates applications against `schemas/input.schema.json` using Draft 2020-12, handles absent and null values as unknown facts, derives `existing_foir` without division-by-zero risks, and rejects protected attributes. All 81 automated tests pass cleanly under `make test`, and `make check` succeeds with zero errors. Line coverage for `src/calc` is 99% (well above the 90% threshold).

## 2. Work packages

| Work package | Done | Notes |
| --- | --- | --- |
| WP-04 Calculation core | Yes | Pure functions for F1 to F9 in `src/calc/formulas.py` and registry in `src/calc/registry.py`. Exact `Decimal` arithmetic for money and ratios; no floats anywhere. Numbers come from `params/params.toml` via loader; none in code. Boundary cases TV2, TV4, TV5, TV6, TV7 handled without special-casing. APR solver uses numerical bisection with `APRConvergenceError`. Guard for $r=0$ implemented. 99% line coverage. |
| WP-05 Fact builder | Yes | Field registry in `rules/fields.toml` (27 fields: 15 input, 12 derived) with dedicated loader `src/engine/field_loader.py`. Fact builder in `src/facts/fact_builder.py` validates inputs with `jsonschema` against `schemas/input.schema.json`. Absent and null fields become `unknown`; income of zero records `existing_foir` as unknown without dividing. Protected attributes (`gender`, `religion`, `caste`) and unknown keys fail validation. Extended float ban to `src/facts`. Rule-set hash pin updated for `rules/fields.toml`. |

## 3. Exit criteria

| Criterion | Met (yes/no) | Evidence: file or command |
| --- | --- | --- |
| TV1 to TV9 numeric expectations match exactly | Yes | `tests/golden/test_calculations_tv.py` (9 tests pass; TV6 and TV8 intermediate numbers match, TV2, TV4, TV5, TV6, TV7 boundaries pass without special-casing). |
| Property tests pass with fixed seeds | Yes | `tests/property/test_calc_properties.py` (3 property groups, 100 examples each, fixed seed `20261108`: recommended amount bounded by caps, multiple of step, EMI within 1 rupee of max EMI, APR >= indicative rate). |
| Schema acceptance cases pass | Yes | `tests/golden/test_schema_cases.py` (all cases in `tests/golden/schema_cases.json` pass according to `valid` flag; absent/null score and income tested). |
| Registry vs schema consistency verified | Yes | `tests/unit/test_fields_registry_vs_schema.py` (field names, types, min, max, enum values match; registry `required` mapped to `x-v01-required`; nullability ignored per OQ-004). |
| Float-ban static checker covers `src/calc` and `src/facts` | Yes | `tools/check_floats.py` scans `src/calc` and `src/facts`; 7 tests in `tests/unit/test_float_ban.py` prove it fails if a float is added to either. |
| `make check-fields` passes | Yes | `python -m src.engine.field_loader rules/fields.toml` exits 0: 27 fields (15 input, 12 derived) with 0 errors and 0 warnings. |
| `make check-params` passes | Yes | `python -m src.engine.param_loader params/params.toml` exits 0: 18 scalar parameters, 3 bands with 0 errors. |
| `make test` runs and passes | Yes | `python -m pytest tests/ -v` exits 0: 81 passed in 4.32s. |
| `make check` runs and passes | Yes | Runs `check-floats`, `lint`, `format`, `test`, `check-params`, `check-fields`. Exits 0 with `=== make check complete ===`. |
| Rule-set hash pin test passing | Yes | `tests/golden/test_rule_set_pin.py` matches updated pin `sha256:bfd0f63e6edd0815d28544e6a14cf4cd9ac33140d2d277d3fb8b3015bc12f031`. |
| Calculation module coverage >= 90% | Yes | `pytest-cov` reports 99% coverage for `src/calc` (154/156 statements in `formulas.py`, 100% in `__init__.py` and `registry.py`). |

## 4. Command output

### Gate command 1: `make check` (run via `mingw32-make.exe check`)

Pass. Last 15 lines of output:

```text
tests\unit\test_calc_unit.py ................                            [ 38%]
tests\unit\test_facts_unit.py ...                                        [ 41%]
tests\unit\test_field_loader.py .....                                    [ 48%]
tests\unit\test_fields_registry_vs_schema.py .....                       [ 54%]
tests\unit\test_float_ban.py .......                                     [ 62%]
tests\unit\test_param_loader.py ..............................           [100%]

============================= 81 passed in 3.51s ==============================
python -m src.engine.param_loader params/params.toml
OK: params/params.toml loaded with 0 warning(s) and no errors.
    18 scalar parameters, 3 band(s).
python -m src.engine.field_loader rules/fields.toml
OK: rules\fields.toml loaded with 0 warning(s) and no errors.
    27 fields (15 input, 12 derived).
""
"=== make check complete ==="
```

### Gate command 2: `make check-params` (run via `mingw32-make.exe check-params`)

Pass. Last 15 lines of output:

```text
python -m src.engine.param_loader params/params.toml
OK: params/params.toml loaded with 0 warning(s) and no errors.
    18 scalar parameters, 3 band(s).
```

### Gate command 3: `make check-fields` (run via `mingw32-make.exe check-fields`)

Pass. Last 15 lines of output:

```text
python -m src.engine.field_loader rules/fields.toml
OK: rules\fields.toml loaded with 0 warning(s) and no errors.
    27 fields (15 input, 12 derived).
```

### Gate command 4: `make test` (run via `mingw32-make.exe test`)

Pass. Last 15 lines of output:

```text
python -m pytest tests/ -v
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system
configfile: pyproject.toml
plugins: hypothesis-6.170.15, cov-7.1.0
collected 81 items

tests\golden\test_calculations_tv.py .........                           [ 11%]
tests\golden\test_rule_set_pin.py .                                      [ 12%]
tests\golden\test_schema_cases.py ..                                     [ 14%]
tests\property\test_calc_properties.py ...                               [ 18%]
tests\unit\test_calc_unit.py ................                            [ 38%]
tests\unit\test_facts_unit.py ...                                        [ 41%]
tests\unit\test_field_loader.py .....                                    [ 48%]
tests\unit\test_fields_registry_vs_schema.py .....                       [ 54%]
tests\unit\test_float_ban.py .......                                     [ 62%]
tests\unit\test_param_loader.py ..............................           [100%]

============================= 81 passed in 4.32s ==============================
```

## 5. Risk update

| Risk ID | What the evidence shows | Agent's view of likelihood and impact |
| --- | --- | --- |
| Floating-point creeps into money or ratio code (Implementation Plan §3) | Float ban static checker extended to both `src/calc` and `src/facts`. 7 tests prove detection. Zero floats in AST. | Likelihood: Very Low. Impact: High (mitigated by automated gate check). |
| Policy thresholds hardcoded in calculations | All thresholds, steps, caps, fee rates, and band midpoints are read from `params/params.toml`. Functions take dynamic parameters. | Likelihood: Very Low. Impact: Medium (well decoupled). |
| Python + SWI-Prolog integration (OQ-001) | Still waiting for owner decision before Phase 2. `src/facts/fact_builder.py` produces structured `ApplicantFacts` with a `to_prolog_facts()` adapter, supporting either engine. | Likelihood: High (blocked until decided). Impact: High if Prolog required, Low if pure-Python evaluator accepted. |
| Schema and field registry drift | Automated test `test_fields_registry_vs_schema.py` ensures 100% agreement on names, types, ranges, enums, and required status. | Likelihood: Very Low. Impact: High (automated test catches drift). |

## 6. Deviations and decisions needed

- **Nullability in Schema vs Registry (OQ-004):** Resolved per owner instructions. The schema accepts `null` so that the fact builder can assert `unknown(A, Field)` and rule V01 can refer; the test compares required vs `x-v01-required` and does not compare nullability. Logged as resolved in `docs/open-questions.md`.
- **Property test seed:** Fixed seed `20261108` used in `tests/property/test_calc_properties.py` for reproducible runs across 100 generated examples per property.
- **Dependencies added:** `jsonschema` (4.26.0) and `hypothesis` (6.170.15) added to `requirements.in` and pinned in `requirements.txt`.
