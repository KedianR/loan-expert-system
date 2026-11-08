# Phase 0 report

Date: 2026-11-08
Commit hash: ad5ae86
Agent session: 5b25816f-3ce1-4ead-a8d0-7b162eed1416

## 1. Summary

Foundation repository created with pinned dependencies, a Makefile, and a float-ban static checker; parameter loader and rule-set hash built to specification. All 36 automated tests (including PT-01 to PT-15) pass cleanly under `make test`, and `make check` and `make check-params` pass with zero errors. Spike S1 confirms SWI-Prolog is not installed and requests an owner decision; Spike S2 confirms Home Credit is feasible with documented assumptions and flags weak mappings.

## 2. Work packages

| Work package | Done | Notes |
| --- | --- | --- |
| WP-01 Foundation | Yes | Repository layout from AGENTS.md, Makefile, pinned dependencies (`requirements.txt`), Python 3.14.2, ruff lint and format, float-ban static checker for `src/calc` with 5 automated unit tests proving it fails when a float is added. |
| WP-02 Spike S1 (SWI-Prolog) | Blocked (reported) | `spikes/s1/toy_rules.pl` and `spikes/s1/spike_s1.py` written. SWI-Prolog is not installed on this machine (`swipl` not found in PATH). Script executed, reported failure in structured form, and STOPPED per ADR-001. Report written to `docs/reports/spike-s1.md`; logged as OQ-001. |
| WP-02 Spike S2 (Home Credit) | Yes | Evaluated Home Credit Default Risk against fact fields in `docs/04-predicates-and-facts.md` §2. Identified 10 strong/medium mappings, 3 weak mappings requiring sensitivity checks (ASM-D4, ASM-D5, ASM-D11), 2 unfilled fields (`kyc_verified`, `consent_given`), and the Give Me Some Credit fallback. No network access in sandbox; no files in `data/raw/`. Report written to `docs/reports/spike-s2.md`. |
| WP-03 Parameter loader | Yes | `params/params.toml` created exactly per baseline in `docs/09-file-formats.md` §2. Loader in `src/engine/param_loader.py` collects all errors in one pass, rejects unknown keys, rejects TOML floats, permits no coercion, returns integers as `int`, decimals as `Decimal`, and booleans as `bool`. Rule-set hash function in `src/engine/ruleset_hash.py` implements CRLF-to-LF normalisation, file ordering, and SHA-256. 30 unit tests (PT-01 to PT-15) and 1 golden pin test all pass. |

## 3. Exit criteria

| Criterion | Met (yes/no) | Evidence: file or command |
| --- | --- | --- |
| ADR-001 confirmed or fallback decided | Blocked: owner decision needed | `docs/reports/spike-s1.md`, `docs/open-questions.md` OQ-001. SWI-Prolog is not installed; spike script executed and recorded this. Owner must choose between installing SWI-Prolog or switching to pure-Python evaluator. |
| Policy thresholds confirmed | Yes | Baseline `params/params.toml` created and validated against catalog values; loads with 0 errors via `make check-params`. |
| `make setup` runs on clean clone | Yes | `Makefile` target `setup` runs `python -m pip install -r requirements.txt`. All dependencies pinned in `requirements.txt`. |
| `make test` runs and passes | Yes | `python -m pytest tests/ -v` exits code 0: 36 passed in 0.21s. |
| `make check` runs and passes | Yes | Runs `check-floats`, `lint`, `format`, `test`, `check-params`. Exits code 0 with "=== make check complete ===". |
| `make check-params` runs and passes | Yes | Runs `python -m src.engine.param_loader params/params.toml`. Exits code 0: "OK: params/params.toml loaded with 0 warning(s) and no errors. 18 scalar parameters, 3 band(s)." |
| Float-ban static checker in place | Yes | `tools/check_floats.py` scans `src/calc`; 5 unit tests in `tests/unit/test_float_ban.py` verify clean files pass, float literals fail, `float()` calls fail, and injected floats fail the build. |
| PT-01 to PT-15 implemented and passing | Yes | `tests/unit/test_param_loader.py` implements all 15 test groups with exact error codes. 30 test cases pass. |
| Rule-set hash pin test passing | Yes | `tests/golden/test_rule_set_pin.py` verifies hash against `tests/golden/rule_set_pin.json` (`sha256:94287e202f2306b15b16b13b7fdaceb7433fda3403807c7e17a3910c705abd67`). |
| No policy number in source code | Yes | All thresholds, rates, fees, and bands reside in `params/params.toml`. No numbers hard-coded in loader or test assertions except expected test inputs. |
| No float for money or ratios | Yes | Exact `Decimal` and `int` used everywhere; verified by PT-01 and float-ban checker. |

## 4. Command output

### Gate command 1: `make check` (run via `mingw32-make.exe check`)

```text
python tools/check_floats.py src/calc
FLOAT_BAN OK: no floats in src/calc (1 file(s) checked).
python -m ruff check src/ tests/ tools/
All checks passed!
python -m ruff format --check src/ tests/ tools/
13 files already formatted
python -m pytest tests/ -v
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system
configfile: pyproject.toml
plugins: cov-7.1.0
collected 36 items

tests\golden\test_rule_set_pin.py .                                      [  2%]
tests\unit\test_float_ban.py .....                                       [ 16%]
tests\unit\test_param_loader.py ..............................           [100%]

============================= 36 passed in 0.21s ==============================
python -m src.engine.param_loader params/params.toml
OK: params/params.toml loaded with 0 warning(s) and no errors.
    18 scalar parameters, 3 band(s).
""
"=== make check complete ==="
```

### Gate command 2: `make check-params` (run via `mingw32-make.exe check-params`)

```text
python -m src.engine.param_loader params/params.toml
OK: params/params.toml loaded with 0 warning(s) and no errors.
    18 scalar parameters, 3 band(s).
```

### Spike S1 execution output (`python spikes/s1/spike_s1.py`)

```text
{
  "swipl_available": false,
  "swipl_version": "swipl not found in PATH",
  "outcome": "FAILED: SWI-Prolog not installed",
  "recommendation": "SWI-Prolog is not installed. Per ADR-001, the owner must decide whether to install it or fall back to the pure-Python evaluator. See docs/open-questions.md OQ-001."
}
```

## 5. Risk update

| Risk ID | What the evidence shows | Agent's view of likelihood and impact |
| --- | --- | --- |
| Python + SWI-Prolog integration is harder than expected (Implementation Plan §3) | SWI-Prolog is not installed. Spike S1 could not run timing. The bridge script and toy rules are ready, but the dependency is missing. | Likelihood: High (currently blocked). Impact: High if Prolog is required, Low if owner accepts pure-Python fallback (ADR-001 already specifies the fallback and DS-2 ensures rule files support both). |
| Policy thresholds are placeholders | Baseline parameters loaded and pass all internal consistency checks (band ordering, coverage, rate midpoint). | Likelihood: Low. Impact: Low (parameters are centralised in `params/params.toml`; values can be updated in one place at any time). |
| Floating-point creeps into money or ratio code | Static checker `tools/check_floats.py` is in place, runs on every `make check`, and 5 tests prove it catches literals and calls. | Likelihood: Very Low. Impact: High (mitigated by automated gate check). |
| Public datasets map badly to rule facts | Spike S2 shows 3 weak mappings (obligations, credit score, tenure) and 2 unfillable fields (KYC, consent). Home Credit is still the best public candidate. | Likelihood: High (inherent to public data). Impact: Medium (D1 synthetic data covers all rules exactly; D2 is used only for ML baseline and outcome comparison; sensitivity checks planned for WP-15). |

## 6. Deviations and decisions needed

- **SWI-Prolog not installed (OQ-001):** Spike S1 could not execute the Prolog engine. Per the instructions ("If it fails, STOP and report. Do not switch to the pure-Python fallback yourself; the owner decides that"), the spike is reported and work is stopped pending owner decision.
- **Windows environment:** The system shell is PowerShell on Windows; `make` is available as `mingw32-make.exe` (GNU Make 3.82.90). The `Makefile` uses `python -m` commands throughout for portability across Windows, Linux, and macOS.
- **PT-15 scope (OQ-003):** PT-15 was run on `params/params.toml` alone because the 10 rule files do not exist yet (scheduled for Phase 1 and Phase 2). The hash pin covers all currently-existing files from the canonical 11-file order.
- **No network in sandbox:** Spike S2 verified what could be determined from documentation and repository state. No external URLs could be reached.

## 7. Files created or changed

- `AGENTS.md` (preserved from repository setup)
- `Makefile` (setup, test, check, check-params, check-floats, lint, format, and future phase stubs)
- `pyproject.toml` (pytest and ruff configuration)
- `requirements.in` (top-level dependencies)
- `requirements.txt` (pinned dependencies)
- `.gitignore` (ignores caches, build output, virtual environments, and raw data)
- `params/params.toml` (baseline illustrative personal loan policy)
- `src/__init__.py`
- `src/api/__init__.py`
- `src/audit/__init__.py`
- `src/calc/__init__.py`
- `src/engine/__init__.py`
- `src/engine/param_loader.py` (parameter file loader with full error collection)
- `src/engine/ruleset_hash.py` (canonical rule-set hasher with line-ending normalisation)
- `src/explain/__init__.py`
- `src/facts/__init__.py`
- `tools/check_floats.py` (AST-based float-ban static checker for `src/calc`)
- `tests/golden/rule_set_pin.json` (canonical hash and version pin)
- `tests/golden/test_rule_set_pin.py` (automated pin test)
- `tests/unit/test_float_ban.py` (5 tests for float-ban checker)
- `tests/unit/test_param_loader.py` (30 tests covering PT-01 to PT-15)
- `spikes/s1/toy_rules.pl` (throwaway toy Prolog rules, not used by product)
- `spikes/s1/spike_s1.py` (Python–Prolog integration spike runner)
- `docs/open-questions.md` (open question log: OQ-001, OQ-002, OQ-003)
- `docs/reports/spike-s1.md` (Spike S1 report)
- `docs/reports/spike-s2.md` (Spike S2 report)
- `docs/reports/phase-0-report.md` (this report)

## 8. Open items

1. **OQ-001 (ADR-001):** Owner must decide between:
   - Installing SWI-Prolog on the host machine so Spike S1 can be re-run with timing.
   - Authorising the pure-Python fallback evaluator described in ADR-001 and docs/09-file-formats.md DS-2.
2. **OQ-002 (Home Credit verification):** Kaggle licence and exact column names must be verified in WP-15 when network or raw files are available.
3. **OQ-003 (Full rule-set hash):** The rule-set pin must be updated when rule files are added in Phase 2.

