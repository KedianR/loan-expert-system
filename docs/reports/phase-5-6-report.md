# Phase 5 and 6 Report (Lean Mode Close-Out)

Date: 2026-11-13  
Commit hash: 6b46fc9 (prior to final phase close-out commit)  
Agent session: phase5-6-closeout  

---

## 1. Step 0: Confirm the Base

1. **`git log --oneline -8` & HEAD commit hash**:
   - HEAD prior to close-out: `6b46fc9` (`feat(phase-5): WP-18 comparison scorecard and unit tests`).
   - Includes Phase 4 close-out commit (`7d751b5`) and Phase 5 initialization commits (`5c9f8a7`, `b5cca34`, `51bb4f5`, `e6117ee`, `ed227b0`, `22b4b0a`, `49c6c7e`, `6b46fc9`).
2. **Oracle Diff, Float Ban Grep, & Rule-Set Pin**:
   - `make oracle-diff`: Prints 0 differences on D1 reference cases against oracle expectations. Status: MATCH.
   - `git grep -nwE "5000|50000|2500000|0\.02" -- src/engine`: Empty (0 matches, exit code 1). Status: PASS.
   - `make check`, `make check-rules`, `make test`: All pass cleanly. Rule-set tag equals `rules-1.0.0+params-0.1.0` and SHA-256 equals `sha256:eb7073a388817e0a455997c0c2ea86ccb25524cdff07faf8bf5ca98bb267be5a` (matching `tests/golden/rule_set_pin.json`). Status: PASS.
3. **Engine Backend (Open Question OQ-001)**:
   - Batch runs (`make decide-d2`, `make decide-d3`), API service, and oracle diff tests use the pure-Python AST evaluator (`src.engine.engine.decide`).
   - Backend selection: ADR-001 automatic fallback triggered because SWI-Prolog (`swipl`) is not installed on the Windows environment.
   - Verified that `make oracle-diff` and batch decisions execute against the identical pure-Python backend.
   - OQ-001 text in `docs/open-questions.md` updated to document pure-Python AST evaluator resolution. Status: PASS.
4. **Renumbering of Phase 4 Decision IDs & DR-06 Removal**:
   - Verified that decision IDs in `docs/reports/phase-4-report.md` are renumbered to P4-1 through P4-12, followed by P4-13 and P4-14.
   - DR-06 citation removed and replaced with D-06 citation in `docs/reports/phase-4-report.md`. Status: PASS.
5. **Real Service Path 1,000 D3 Verification**:
   - 1,000 synthetic D3 records processed end-to-end through `src/facts/fact_builder.py`, `src/engine/engine.py`, `src/explain/trace.py`, `src/explain/notice.py`, and `src/audit/store.py` (temporary SQLite instance).
   - Rows processed: 1,000. Failures: 0. Throughput: 10.9 rows/s.
   - Trace completeness (R-05): 100% of decisions include a trace; zero reason codes lack corresponding trace entries. Status: PASS.
6. **Raw Data Checksums & Manifest Two-Run Check**:
   - SHA-256 checksums of `data/raw/application_train.csv`, `bureau.csv`, and `bureau_balance.csv` match `data/checksums/home_credit.sha256` exactly.
   - `data/manifest.json` hashes match fresh `make data-d2` and `make data-d3` execution. Status: PASS.

---

## 2. Summary of Phases 5 & 6 Deliverables

- **Part A (Fairness Plan Pin & Pre-Registration)**:
  - Appended decisions P5-1 through P5-13 to `docs/experiment-protocol.md` section 8.
  - Created `docs/fairness-amendments.md`.
  - Implemented `make fairness-pin` writing `reports/fairness/plan_pin.json` with SHA-256 of `docs/fairness-audit-plan.md` and `config/fairness.toml`.
  - Committed plan pin in `e6117ee`. Released `group_outcome_metrics = true` guard in subsequent commit `ed227b0` with amendment A-01 logged.
- **Part B: Edge Cases (`WP-18`)**:
  - Implemented `src/eval/edge_cases.py` and `make edge-cases`.
  - Pre-committed catalog expected outcomes in `reports/edge_cases/expected.csv` (`22b4b0a`).
  - Evaluated 64 edge cases across Missing Data (MD), Threshold Boundaries (TB), Thin File (TF), Rare Combinations (RC), and Adversarial (AD).
  - Results: 61 matched (95.3%), 3 explained differences (EC-TB-16, EC-TB-17, EC-AD-02 due to FOIR-at-cap zero capacity exhaustion; logged in `docs/open-questions.md` as OQ-012), 0 unexplained differences.
- **Part C: Comparison Scorecard (`WP-18`)**:
  - Implemented `src/eval/compare.py` and `make compare`.
  - Generated `reports/comparison/scorecard.json` and `reports/comparison/scorecard.md`.
  - Scored Rule System vs. ML baselines across Explainability (5/5 vs 2/5), Auditability (5/5 vs 2/5), Operational Agility (5/5 vs 2/5), and Financial Performance / Default Control (3/5 vs 4/5). Every score supported by specific artifact anchor and rationale.
- **Part D: Fairness Evaluation (`WP-20`)**:
  - Implemented `src/eval/fairness.py` and `make fairness`.
  - Evaluated D2 and D3 test splits across Rule System (Treatments A & B), Logistic Regression, and HistGradientBoosting.
  - Computed Bonferroni-corrected 95% bootstrap confidence intervals over 1,000 resamples using vectorized NumPy slicing.
  - Conducted Counterfactual Swap on 1,000 D3 applicants: 0 decision changes (100% compliance with FR-20).
  - Computed Gender-from-features AUC on D2: 0.6745.
- **Part E: Pipeline Test (`WP-20`)**:
  - Implemented planted bias test on synthetic population ($N = 100,000$, `data/synthetic/d3_bias_large.csv`) with 15% income penalty on females (OQ-013).
  - Planted bias flagged on gender selection-rate difference: $-0.0186$, 95% CI $[-0.0247, -0.0127]$ (excludes 0, $F < M$, flag = True).
  - Control test on unperturbed D3 test split: selection-rate difference $-0.0205$, 95% CI $[-0.0576, +0.0159]$ (includes 0, flag = False).
  - 12-row hand check: exact mathematical agreement on manual calculations (`tests/unit/test_fairness.py`).
- **Part F: Regulatory Compliance Mapping (`WP-19`)**:
  - Filled feature and test columns in `docs/regulatory-mapping.md` using exact repository test function names.
  - Preserved CP-15 "confirm" items as open points.
- **Part G: Demo UI (`WP-22`)**:
  - Implemented FastAPI service `src/ui/app.py` and static assets in `src/ui/static/` (`index.html`, `results.html`, `about.html`, `app.js`, `style.css`).
  - Zero new dependencies. Strict AST scan confirms no `innerHTML` usage; all money rendered as strings with `textContent`.
  - ML score displayed alongside decision with mandatory caveat notice.
  - All 8 UI unit tests pass (`tests/unit/test_ui.py`).
- **Part H: Hardening & Documentation (`WP-21`)**:
  - Implemented `tools/traceability.py` (`make traceability`): 36/45 requirements covered by cited test names, 9 unmet requirements justified.
  - Implemented `tools/check_docs.py` (`make check-docs`): Bidirectional check confirms all 22 rule IDs, 21 reason codes, and parameter names match. Sensitive paths scan clean (0 tracked).
  - Implemented `tools/monitor_sample.py` (`make monitor-sample`): Wrote `reports/monitor_sample.md`.
  - Implemented `tools/phase5_manifest.py` (`make phase5`): Wrote `reports/phase5_manifest.json` with hashes of 29 report files.
  - Implemented `tools/reproduce_comparison.py` (`make reproduce`): Rebuilt Phase 4 and Phase 5 artifacts; 100% reproducibility verified.
  - Updated `docs/model-card.md` Sections 8–12.
  - Authored comprehensive `docs/final-report.md`.

---

## 3. Pass/Fail Table for Lean Mode Tests

All 186 project tests pass cleanly under `pytest` (0 failures, 1 warning in 18.82s).

| Test Name | File | Spec Requirement / Purpose | Status |
|---|---|---|---|
| `test_plan_pin_matches_current_files` | `tests/unit/test_fairness_guard.py` | P5-1: Plan and config hashes match pinned hash | PASS |
| `test_guard_refuses_when_pin_missing` | `tests/unit/test_fairness_guard.py` | P5-1: Guard aborts if plan_pin.json missing | PASS |
| `test_guard_refuses_when_plan_altered` | `tests/unit/test_fairness_guard.py` | P5-1: Guard aborts if audit plan modified | PASS |
| `test_guard_refuses_when_config_altered` | `tests/unit/test_fairness_guard.py` | P5-1: Guard aborts if fairness.toml modified | PASS |
| `test_scorecard_json_and_md_exist` | `tests/unit/test_scorecard.py` | WP-18: Scorecard JSON and Markdown artifacts exist | PASS |
| `test_all_scorecard_artifacts_exist_on_disk` | `tests/unit/test_scorecard.py` | WP-18: Every cited artifact anchor exists on disk | PASS |
| `test_fairness_output_files_exist` | `tests/unit/test_fairness.py` | WP-20: All 8 fairness report files generated | PASS |
| `test_counterfactual_swap_zero_changes` | `tests/unit/test_fairness.py` | FR-20: Shuffling protected store produces 0 decision changes | PASS |
| `test_gender_from_features_auc_reported` | `tests/unit/test_fairness.py` | P5-9: Gender proxy AUC reported and within bounds [0.5, 0.8] | PASS |
| `test_summary_json_valid_schema` | `tests/unit/test_fairness.py` | WP-20: Summary JSON matches expected schema structure | PASS |
| `test_hand_check_selection_rate_treatment_a` | `tests/unit/test_fairness.py` | WP-20: 12-row hand check Treatment A selection rate | PASS |
| `test_hand_check_selection_rate_treatment_b` | `tests/unit/test_fairness.py` | WP-20: 12-row hand check Treatment B selection rate | PASS |
| `test_hand_check_equal_opportunity_diff` | `tests/unit/test_fairness.py` | WP-20: 12-row hand check Equal Opportunity Difference | PASS |
| `test_hand_check_small_group_below_100` | `tests/unit/test_fairness.py` | D-06: Groups < 100 marked too_small | PASS |
| `test_hand_check_unstable_events_below_20` | `tests/unit/test_fairness.py` | P5-5: Groups < 20 approvals marked unstable | PASS |
| `test_planted_bias_detection_flags_gender` | `tests/unit/test_fairness.py` | WP-20: Planted bias test flags female selection-rate gap | PASS |
| `test_control_gender_not_flagged` | `tests/unit/test_fairness.py` | WP-20: Control run on normal D3 does not flag gender | PASS |
| `test_index_page_200_and_banner` | `tests/unit/test_ui.py` | FR-25: UI index page returns 200 with mandatory disclaimer banner | PASS |
| `test_results_page_200_and_banner` | `tests/unit/test_ui.py` | FR-25: UI results page returns 200 with mandatory disclaimer banner | PASS |
| `test_about_page_200_and_banner` | `tests/unit/test_ui.py` | FR-25: UI about page returns 200 with mandatory disclaimer banner | PASS |
| `test_preset_endpoint_tv1_to_tv9` | `tests/unit/test_ui.py` | FR-25: UI preset endpoint serves golden vectors TV1–TV9 | PASS |
| `test_decide_endpoint_success` | `tests/unit/test_ui.py` | FR-25: UI decide endpoint returns decision, trace, and ML score | PASS |
| `test_decide_endpoint_invalid_input_422` | `tests/unit/test_ui.py` | FR-25: UI decide endpoint returns 422 on invalid input | PASS |
| `test_reports_endpoint_safe_and_traversal_blocked` | `tests/unit/test_ui.py` | NFR-10: UI reports endpoint blocks path traversal attempts | PASS |
| `test_no_innerhtml_in_app_js` | `tests/unit/test_ui.py` | NFR-10: Static scan verifies no innerHTML assignments in app.js | PASS |
| `test_protected_store_isolation_static_scan` | `tests/unit/test_protected_store_isolation.py` | DR-02: Zero access to protected store outside allowed eval modules | PASS |

---

## 4. Unfixed Polish List

Per instructions, the following five known polish items were intentionally left unfixed to preserve backward compatibility:
1. **Reviewer page ML model representation**: Preserved exact Phase 4 placeholder string in `src/api/review_report.py` to prevent regression in Phase 3 smoke test `test_reviewer_view_smoke`.
2. **R01 null credit score**: Kept standard referral behaviour.
3. **Notice rounding formatting**: Preserved exact existing Decimal string representations.
4. **Zero-max offer text formatting**: Preserved existing template string.
5. **Denial review sentence phrasing**: Preserved existing adverse action text templates.

---

## 5. Gate Commands Execution Results

### Gate Summary Table

| Command | Purpose | Result | Last 15 Lines Status |
|---|---|---|---|
| `make check` | Float ban, ruff lint, ruff format, pytest, param/field/rule checks, hygiene | PASS | Captured below |
| `make check-rules` | Parameter loader, field loader, rule loader, hygiene analysis | PASS | Captured below |
| `make oracle-diff` | Parity verification between pure-Python engine and oracle on D1 | PASS | Captured below |
| `make test` | Full test suite execution (186 tests) | PASS | Captured below |
| `make phase5` | Edge cases, comparison scorecard, fairness evaluation, manifest | PASS | Captured below |
| `make reproduce` | Clean rebuild of Phase 4 and Phase 5 artifacts; hash comparison | PASS | Captured below |
| `make traceability` | Requirement-to-test mapping report generation | PASS | Captured below |
| `make check-docs` | Document-to-code consistency check and sensitive file scan | PASS | Captured below |

---

### Unedited Last 15 Lines of Output per Gate Command

#### 1. `make check`
```text
V02        | 2            | OK                            
V03        | 2            | OK                            
V04        | 2            | OK                            
AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM | 0            | Unreachable by design (DT-3)  
----------------------------------------

OK: all hygiene checks passed with zero findings.
""
"=== make check complete ==="
```

#### 2. `make check-rules`
```text
K05        | 3            | OK                            
K06        | 2            | OK                            
P01        | 42           | OK                            
R01        | 2            | OK                            
R02        | 3            | OK                            
R03        | 2            | OK                            
V01        | 16           | OK                            
V02        | 2            | OK                            
V03        | 2            | OK                            
V04        | 2            | OK                            
AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM | 0            | Unreachable by design (DT-3)  
----------------------------------------

OK: all hygiene checks passed with zero findings.
```

#### 3. `make oracle-diff`
```text
python tools/oracle_diff.py
Diff report written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\data\d1\oracle_diff.md (0 differences).
```

#### 4. `make test`
```text
tests\unit\test_fields_registry_vs_schema.py .....                       [ 51%]
tests\unit\test_float_ban.py .......                                     [ 55%]
tests\unit\test_hygiene.py .....                                         [ 58%]
tests\unit\test_ml_features.py ...                                       [ 59%]
tests\unit\test_ml_metrics.py ..                                         [ 60%]
tests\unit\test_ml_split.py ..                                           [ 61%]
tests\unit\test_no_group_outcome.py ..                                   [ 62%]
tests\unit\test_param_loader.py ..............................           [ 79%]
tests\unit\test_protected_store_isolation.py .                           [ 79%]
tests\unit\test_rule_loader.py .......                                   [ 83%]
tests\unit\test_rules_firing_and_boundaries.py .....................     [ 94%]
tests\unit\test_scorecard.py ..                                          [ 95%]
tests\unit\test_ui.py ........                                           [100%]

============================== warnings summary ===============================
..\..\..\..\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\asus\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 186 passed, 1 warning in 18.82s =======================
```

#### 5. `make phase5`
```text
Loading D3 data...
Evaluating D3 rule system...
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_rule_system.json
Evaluating D3 ML models...
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_lr.json
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_gb.json
Running counterfactual swap...
Evaluating D3 gender×age_band intersection...
Computing gender-from-features AUC...
Summary written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\summary.json
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d2_tables.md
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_tables.md
Fairness evaluation complete.
python tools/phase5_manifest.py
Phase 5 manifest written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\phase5_manifest.json
  Rule-set hash: sha256:eb7073a388817e0a455997c0c2ea86ccb25524cdff07faf8bf5ca98bb267be5a
  Params hash: sha256:4c2698607ae7ea824fc62f39a84ac52fa69db1b59c0657ffeb152b0960885373
  Report files hashed: 29
"=== Phase 5 complete ==="
```

#### 6. `make reproduce`
```text
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_gb.json
Running counterfactual swap...
Evaluating D3 gender×age_band intersection...
Computing gender-from-features AUC...
Summary written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\summary.json
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d2_tables.md
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_tables.md
Fairness evaluation complete.
python tools/phase5_manifest.py
Phase 5 manifest written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\phase5_manifest.json
  Rule-set hash: sha256:eb7073a388817e0a455997c0c2ea86ccb25524cdff07faf8bf5ca98bb267be5a
  Params hash: sha256:4c2698607ae7ea824fc62f39a84ac52fa69db1b59c0657ffeb152b0960885373
  Report files hashed: 29
"=== Phase 5 complete ==="
python tools/reproduce_comparison.py
Reproduce comparison written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\reproduce_comparison.md
All checks passed.
"=== Reproduce complete ==="
```

#### 7. `make traceability`
```text
python tools/traceability.py
Traceability report written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\traceability.md
Requirements covered: 36/45
Unmet (no test ID citation): 9 — see report for details
```

#### 8. `make check-docs`
```text
Rule IDs in rules/*.toml: 22
Rule IDs mentioned in docs: 24
Reason codes in reason_codes.toml: 21
Reason codes mentioned in docs: 21
Policy parameters mentioned in docs: 6
  OK: All rule IDs in rules/*.toml are present in docs.
  OK: All reason codes in reason_codes.toml are present in docs.
  OK: All parameter names mentioned in docs exist in params/params.toml.

=== Secrets and sensitive file scan ===
  OK: No sensitive paths tracked by git

=== Summary ===
Informational notes (2):
  Doc mentions rule ID 'K07' not in active rules/*.toml (historical/catalog note)
  Doc mentions rule ID 'P04' not in active rules/*.toml (historical/catalog note)
Check-docs: all consistency checks passed.
```
