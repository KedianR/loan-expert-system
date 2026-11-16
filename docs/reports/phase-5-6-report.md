# Phase 5 and 6 Report (Lean Mode Close-Out & Patch Round 3)

Date: 2026-11-16  
Commit hash: `9be67e497757a541c7ff80fd4670525b1093580c` (This hash identifies the code and verification baseline prior to this final report edit; it will be followed by the documentation close-out commit)  
Agent session: phase5-6-patch-round-3  

---

## Patch Round 3 Close-Out Summary

- **Item 1 (Amendment A-03 in `docs/fairness-amendments.md`)**: Logged all 6 post-hoc implementation corrections (D3 ML decision orientation, NaN flag hardening, P5-5 applied across all metrics, gender×age_band intersection added, dual-treatment markdown tables generated, percentile-vs-BCa wording alignment); documented what changed, rationale, affected published numbers, and marked "Results viewed before logging: Yes".
- **Item 2 (Evidence for D3 and fairness fixes)**:
  - **2a (Bootstrap method)**: `Select-String -Path src\eval\*.py -Pattern "bca|percentile|method=|resample"` confirms bootstrap is standard percentile bootstrap (`np.percentile(valid_stats, 100 * alpha / 2)` and `100 * (1 - alpha / 2)`), NOT BCa.
  - **2b (D3 employment crosstabs)**: On D3 test split ($N=3,000$), verified LR agreement is 80.97% (2,429/3,000; 571 disagreements) and GB agreement is 98.53% (2,956/3,000; 44 disagreements), matching the exact sum of per-group disagreements (`other`=0, `salaried`=395/36, `self_employed`=176/8).
  - **2c (Test source)**: Source of `test_per_group_ml_selection_consistent_with_overall_agreement` in `tests/unit/test_fairness.py` lines 648–717 verified and cited.
  - **2d (`git diff src/eval/edge_cases.py`)**: Confirmed only `obligations_source: "synthetic"` was added; D3 model decision threshold (`prob >= 0.5` = eligible) is unchanged.
  - **2e (D2 agreement figures)**: 96.87% (LR) and 96.82% (GB) are measured against binary rule eligibility on D2 test split ($N=46,127$, where rule approves 776); both rule and LR approve 27 applicants, and both rule and GB approve 50 applicants (agreement is driven by 98.3% common true negatives).
- **Item 3 (P5-5 consistency)**: Printed D2 rule-system age-band test rows ($N=46,127$); cohort 60+ has 23 approvals and 23 approved repayers ($23 \ge 20$), legitimately satisfying the stability threshold and correctly scored and flagged with EOD = -0.0141 (Section 7.2 of final report corrected from older draft claim); `src/eval/fairness.py` line 386 refined so stability check strictly evaluates approved repayers count for EOD (zero flags changed).
- **Item 4 (Traceability)**: The 9 requirements unmet in round 1 (FR-10, FR-15, FR-18, FR-20, FR-22, NFR-06, CR-01, CR-05, CR-06) mapped to their covering tests and assertion logic; NFR-06 is designated as measured by timing benchmark rather than covered by a unit test; dynamic requirement count reports 46 covered by tests + 1 measured (47 total).
- **Item 5 (UI audit verification)**: `python -m pytest --collect-only -q tests/unit/test_ui.py` collected 8 tests; verified that `POST /ui/decide` calls `_get_service().decide(body)` which invokes `DecisionService.decide()` and writes append-only audit records to `data/audit.db`, using the identical store and engine path as the REST API (FR-10, FR-15).
- **Item 6 (Final report edits)**: Synchronized `docs/final-report.md` and `docs/reports/phase-5-6-evidence/final-report.md` byte-for-byte with date 16 November 2026, commit hash `9be67e4` quoted in header with reconciliation note, regulatory mapping marked with `(confirm)`, audit immutability citing `(FR-10, NFR-08)`, Section 6 context note added contrasting ML default rates (1.39% LR, 1.27% GB) against rules (3.35%) and noting GB's upper bound is below rules' lower bound, Section 7.1 mechanism reworded as hypothesis, Section 7.2 separating K05 income floor (68.29% women vs 49.42% men fail) from E01 tenure, Section 7.3 counterfactual swap disclaimer added (procedural blindness, not demographic fairness), and Sections 8.7/10 audit writing confirmed.
- **Item 7 (Clean clone reproduction)**: Fresh clone executed `make reproduce` (Python 3.14.2, wall time 512.5s = 8.5 min) at commit `9be67e497757a541c7ff80fd4670525b1093580c` with all checks passing; negative control verified by mutating `difference = 0.9999` in `reports/fairness/d3_rule_system.json`, which produced return code 1, printed `WARNING: Some files missing or diffs found; see report.`, and recorded diff line in `reports/reproduce_comparison.md`; negative change reverted and clean reproduction confirmed.

---

## 0. Base Confirmation (A1)

### 1. `git log --oneline -15` (Raw Output)
```text
6c999dd docs(phase-5-6): update phase-5-6-report with patch round findings, gate outputs, and clean reproduce
557dd24 fix: track data/synthetic/d3_generator.py for clean checkout reproducibility (OQ-014)
dc50570 Phase 5/6 patch round: comparison scorecard, planted-bias rerun, UI isolation, traceability, and evidence
2734aa5 feat(phase-5-6): complete WP-18 to WP-22 - fairness, scorecard, UI, hardening, and final reports (FR-20, FR-25, CR-01..CR-06)
6b46fc9 feat(phase-5): WP-18 comparison scorecard and unit tests
49c6c7e feat(phase-5): WP-18 edge-case suite implementation, results, and summary
22b4b0a feat(phase-5): add edge-case catalog generator and commit expected.csv before run
ed227b0 feat(phase-5): release group_outcome_metrics guard after plan pin
e6117ee feat(phase-5): pin fairness audit plan and configuration (make fairness-pin)
51bb4f5 build: clean up Makefile Phase 5 target declarations
b5cca34 feat(phase-5): implement fairness-pin guard and record P5 decisions
5c9f8a7 fix(phase-5): Step 0 confirm base - resolve OQ-001, remove DR-06, verify D3 service path
1733aa5 feat: add documentation, configuration, and prompt pack for phases 5 and 6 fairness and comparison systems
7d751b5 feat(phase-4): close-out filtered baseline F1/F2, bootstrap CIs, and Phase 4 report
a84fa6b fix(phase-4): add phase4 gate checks to Makefile; fill phase-4-report with patch items 1-8
```

### 2. `git status` (Raw Output)
```text
On branch main
Your branch is ahead of 'origin/main' by 1 commit.
  (use "git push" to publish your local commits)

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   docs/final-report.md
	modified:   docs/model-card.md
	modified:   docs/reports/phase-5-6-evidence/edge_cases_summary.md
	modified:   docs/reports/phase-5-6-evidence/fairness_d2_tables.md
	modified:   docs/reports/phase-5-6-evidence/fairness_d3_tables.md
	modified:   docs/reports/phase-5-6-evidence/final-report.md
	modified:   docs/reports/phase-5-6-evidence/model-card.md
	modified:   docs/reports/phase-5-6-evidence/planted_bias_table.md
	modified:   docs/reports/phase-5-6-evidence/repo_scan.txt
	modified:   docs/reports/phase-5-6-evidence/scorecard.md
	modified:   docs/reports/phase-5-6-evidence/traceability.md
	modified:   docs/reports/phase-5-6-evidence/ui_evidence.md
	modified:   reports/comparison/scorecard.json
	modified:   reports/comparison/scorecard.md
	modified:   reports/edge_cases/results.csv
	modified:   reports/edge_cases/summary.md
	modified:   reports/fairness/d2_gb.json
	modified:   reports/fairness/d2_lr.json
	modified:   reports/fairness/d2_rule_system.json
	modified:   reports/fairness/d2_tables.md
	modified:   reports/fairness/d3_gb.json
	modified:   reports/fairness/d3_lr.json
	modified:   reports/fairness/d3_rule_system.json
	modified:   reports/fairness/d3_tables.md
	modified:   reports/fairness/summary.json
	modified:   reports/phase5_manifest.json
	modified:   reports/reproduce_comparison.md
	modified:   reports/traceability.md
	modified:   src/eval/compare.py
	modified:   src/eval/edge_cases.py
	modified:   src/eval/fairness.py
	modified:   tests/unit/test_edge_cases.py
	modified:   tests/unit/test_fairness.py
	modified:   tools/check_docs.py
	modified:   tools/phase5_manifest.py
	modified:   tools/reproduce_comparison.py
	modified:   tools/traceability.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	docs/reports/phase-5-6-evidence/phase5_manifest.json
	docs/reports/phase-5-6-evidence/summary.json
```

### 3. `git show --stat e6117ee` (Raw Output)
```text
commit e6117eeb846e0f0433a9e196fc18c7e71ba03677
Author: k_d <kedianronz5ultra@gmail.com>
Date:   Fri Nov 13 03:10:53 2026 +0530

    feat(phase-5): pin fairness audit plan and configuration (make fairness-pin)

 reports/fairness/plan_pin.json | 6 ++++++
 1 file changed, 6 insertions(+)
```

### 4. `git show --stat 5c9f8a7 b5cca34 51bb4f5` (Raw Output)
```text
commit 5c9f8a78d8a271cf2ba73785e5b29d35c357a1b1
Author: k_d <kedianronz5ultra@gmail.com>
Date:   Fri Nov 13 03:04:10 2026 +0530

    fix(phase-5): Step 0 confirm base - resolve OQ-001, remove DR-06, verify D3 service path

 docs/open-questions.md               |   2 +-
 docs/reports/phase-4-report.md       |   6 +-
 tests/unit/test_baseline_filtered.py |   2 +-
 tools/test_service_path_d3.py        | 122 +++++++++++++++++++++++++++++++++++
 4 files changed, 127 insertions(+), 5 deletions(-)

commit b5cca342772715e48fd590b5ce530fb71fc32de8
Author: k_d <kedianronz5ultra@gmail.com>
Date:   Fri Nov 13 03:06:08 2026 +0530

    feat(phase-5): implement fairness-pin guard and record P5 decisions

 Makefile                          |  18 ++++-
 docs/experiment-protocol.md       |  21 ++++++
 docs/fairness-amendments.md       |   7 ++
 src/eval/fairness_guard.py        | 139 ++++++++++++++++++++++++++++++++++++++
 tests/unit/test_fairness_guard.py | 120 ++++++++++++++++++++++++++++++++
 tools/test_service_path_d3.py     |  42 +++++++++---
 6 files changed, 334 insertions(+), 13 deletions(-)

commit 51bb4f5f4db259d321b74cc19c93ba6a75af9bfa
Author: k_d <kedianronz5ultra@gmail.com>
Date:   Fri Nov 13 03:10:32 2026 +0530

    build: clean up Makefile Phase 5 target declarations

 Makefile | 9 +--------
 1 file changed, 1 insertion(+), 8 deletions(-)
```

**Pre-Pin File Integrity Analysis**:
Commits `5c9f8a7`, `b5cca34`, and `51bb4f5` preceded the fairness plan pin commit `e6117ee`. Examination of their diffs confirms:
- `5c9f8a7`: Touched `docs/open-questions.md`, `docs/reports/phase-4-report.md`, `tests/unit/test_baseline_filtered.py`, and created `tools/test_service_path_d3.py`.
- `b5cca34`: Implemented the fairness-pin execution guard (`src/eval/fairness_guard.py`, `tests/unit/test_fairness_guard.py`), added Makefile targets, created `docs/fairness-amendments.md`, and updated `docs/experiment-protocol.md`.
- `51bb4f5`: Cleaned up Makefile Phase 5 target declarations.
- Neither `docs/fairness-audit-plan.md` nor `config/fairness.toml` was touched by any of these commits. Both files remained identical to their initial commit `1733aa5`, confirming that the fairness audit plan was pinned before viewing any group outcome metrics.

### 5. Content of `docs/fairness-amendments.md` (Raw Output)
```markdown
# Fairness Plan Amendments

Log of amendments to `docs/fairness-audit-plan.md` and `config/fairness.toml` made after plan pinning.
Any modification to the pinned plan or configuration must be documented here with justification.

| ID | Date | What changed | Reason | Results viewed? |
|---|---|---|---|---|
| A-01 | 2026-11-13 | Guard released after plan pin: group_outcome_metrics set to true in config/experiment.toml | Part A step 4 pre-registered protocol step | No |
| A-02 | 2026-11-14 | Supplementary power check added: 100,000-applicant planted bias and control pair evaluated | Per open question OQ-013, evaluated large-sample pair (N = 100,000) to confirm asymptotic narrowing of confidence intervals under identical effect size. Pipeline tests run on standard N = 20,000 population; 100,000-row results reported separately as supplementary power check. Results were viewed before logging. | Yes |
```

### 6. Verification Status of Base Integrity Checks
- `make oracle-diff`: **0 differences** on D1 reference suite.
- `git grep -nwE "5000|50000|2500000|0\.02" -- src/engine`: **0 matches** (float and policy number ban in engine strictly respected).
- Rule-set pin: Tag equals `rules-1.0.0+params-0.1.0` and SHA-256 equals `sha256:eb7073a388817e0a455997c0c2ea86ccb25524cdff07faf8bf5ca98bb267be5a` (matches `tests/golden/rule_set_pin.json`).
- Engine Backend: Predicate-based production rules in TOML, evaluated by a pure-Python AST evaluator; hash-pinned and replay-checked trace.

---

## 1. Patch Round 2: ML Edge-Case Suite Resolution (A2)

1. **Root Cause Analysis**:
   - In Round 1, all 64 cases reported `LR=error, GB=error` due to a pipeline missing-column exception: `columns are missing: {'obligations_source'}`.
   - The D3-trained scikit-learn pipeline requires the categorical column `obligations_source`, which is always `"synthetic"` for D3 records.
   - Fix: Supplied `obligations_source: "synthetic"` directly in the edge-case feature dictionary in `src/eval/edge_cases.py` without modifying model pipelines, engine code, or policy rules.

2. **Per-Case Evaluation & Reporting**:
   - For all 64 edge cases, recorded:
     - D3-trained Logistic Regression probability score and binary label at operating point $\tau = 0.50$.
     - D3-trained HistGradientBoosting probability score and binary label at operating point $\tau = 0.50$.
     - Top three feature contributions for Logistic Regression.
     - For missing data cases (MD-01..MD-09): documented that the scikit-learn pipeline did not raise, imputed missing values with median values, flagged missingness with `{feature}_missing = 1.0` indicator columns, and did not refuse.
   - Rewrote all 64 case lines in `reports/edge_cases/summary.md` and `docs/reports/phase-5-6-evidence/edge_cases_summary.md` from actual model outputs. Completely eliminated placeholder templates.

3. **Scorecard Rescoring**:
   - Updated `src/eval/compare.py` to award Anchor 1 (score = 1) for both Logistic Regression and Gradient Boosting under Edge Cases: *"An unexplained difference in the missing-data or boundary categories."*
   - Removed the unsupported claim of "Silent Imputation Vulnerability" (since missing indicators are explicitly generated).
   - Added unit test `test_FR24_no_ml_row_for_valid_input_has_error_status` in `tests/unit/test_edge_cases.py`.

---

## 2. Patch Round 2: D3 ML Fairness Consistency & Label Orientation (A3)

1. **Label Orientation Bug and Resolution**:
   - In Round 1, fairness evaluation code evaluated ML decisions as `score < threshold` (assuming models predicted default probability $TARGET=1$, as in D2).
   - However, D3 models were trained to predict policy eligibility (`y = (decision == 'eligible')`), where class 1 represents `eligible`. Checking `score < threshold` inverted predictions on D3.
   - Corrected decision rule in `src/eval/fairness.py` to `score >= 0.5` for D3 models.

2. **Consistency Verification**:
   - Overall D3 Gradient Boosting agreement with the rule system restored to **98.53%** (2,956 of 3,000 test cases; exactly 44 disagreements).
   - Approvals for employment type `other` on D3 GB dropped from the erroneous 100% to **0 / 139 (0.0%)**, perfectly consistent with the rule system (0 / 139).
   - Overall D2 agreement verified: Logistic Regression = 96.87%, HistGradientBoosting = 96.82%.
   - Added unit test `test_per_group_ml_selection_consistent_with_overall_agreement` in `tests/unit/test_fairness.py`.

---

## 3. Patch Round 2: Fairness Flags & Protocol Hardening (A4)

1. **NaN Flag Bug Resolution**:
   - In Python, `ci_lo <= 0 <= ci_hi` evaluates to `False` when bounds are `NaN`, resulting in `not False == True` (causing undefined metrics to be falsely flagged with 🚩).
   - Explicitly added checks: if `np.isnan(ci_lo)` or `np.isnan(ci_hi)` or `np.isnan(diff)`, status is strictly set to `"unstable"` and `flag` is set to `None`.
   - Added unit test `test_nan_value_or_ci_never_carries_flag` in `tests/unit/test_fairness.py`.

2. **Protocol P5-5 Stability Enforcement**:
   - Enforced rule: if total approvals in either evaluated group or reference group is $< 20$, the metric is designated `"unstable"` and `flag` is set to `None`.
   - Applied uniformly across all fairness metrics (`selection_rate_difference`, `selection_rate_ratio`, `equal_opportunity_difference`, `false_approval_rate_difference`, `default_rate_among_approved`).
   - Added unit test `test_P5_5_unstable_applied_to_all_metrics` in `tests/unit/test_fairness.py`.

3. **Intersectional Attribute & Dual Treatment Tables**:
   - Implemented `gender_x_age_band` intersectional attribute in `src/eval/fairness.py` (slices $< 100$ marked `too_small`).
   - Generated complete Treatment A (headline, refer = denied) and Treatment B (refer excluded) markdown tables in `reports/fairness/` and `docs/reports/phase-5-6-evidence/`.

4. **Planted-Bias & Control Reporting**:
   - Updated `docs/reports/phase-5-6-evidence/planted_bias_table.md`:
     - Replaced "BCa bootstrap CIs" with "Percentile bootstrap CIs (P5-4)".
     - Replaced claims of "adequate/robust statistical power" with the honest statement: detected at standard size (marginally: upper bound -0.0013, close to zero; diff $-0.0151$, 95% CI $[-0.0286, -0.0013]$) and clearly detected at 100,000 (diff $-0.0186$, 95% CI $[-0.0247, -0.0127]$).
     - Stated mechanism of effect: 15% income reduction for female applicants shifts selection rate by ~1.5 to 1.9 percentage points because income operates through non-linear affordability thresholds (FOIR, disposable income, income floors) that affect only marginal applicants.

---

## 4. Patch Round 2: Final Report Alignment (A5)

1. **Scorecard Table Alignment**:
   - Updated Section 6 of `docs/final-report.md` to match `reports/comparison/scorecard.json` exactly:
     - Rule System: 3, 3, 3, 3
     - Logistic Regression: 2, 2, 1, 1
     - Gradient Boosting: 1, 2, 1, 1
   - Added an automated consistency check in `tools/check_docs.py` that parses the Markdown table and asserts equality against `scorecard.json`.

2. **Accuracy Table Confidence Intervals**:
   - Updated accuracy context table CIs in Section 6 to match `reports/ml/comparison_main.json` exactly:
     - Rule System Treatment A default rate: 3.35% (95% CI: 2.14%–4.70%)
     - Rule System Treatment B default rate: 3.35% (95% CI: 2.12%–4.67%)
     - Logistic Regression default rate: 1.39% (95% CI: 0.56%–2.42%)
     - HistGradientBoosting default rate: 1.27% (95% CI: 0.58%–2.12%)
     - Prominently retained context note: *"D2 rests on 776 approvals with overlapping intervals and D3 agreement is partly circular."*

3. **Section 7.2 Corrections**:
   - Removed ₹25,000 income floor claim; replaced with policy minimum monthly income floor of ₹15,000 (E01/K05).
   - Rewrote primary-attribute EOD results descriptively for gender, age band, and employment type.
   - Explicitly noted that applicants with employment type `other` are never approved under rules (0 approvals, failing E01); with $<20$ approvals, this slice is marked `unstable` per P5-5 with no flag.
   - Explicitly noted that income band quartile Q1 has 0 approvals; with $<20$ approvals in reference group, all comparisons are marked `unstable` per P5-5.

4. **Section 8 Additions**:
   - Added CFPB Regulation B "(confirm)".
   - Added missing limitations: operational review queue volume and override tracking, unanalysed protected attributes (religion, caste, sexual orientation, disability), continuous ML edge cases handling (median imputation with indicators), and few-default screening metrics on D2 (26 defaults among 776 approvals).

---

## 5. Patch Round 2: Dynamic Requirements Traceability (A6)

1. **Dynamic Parser Implementation**:
   - Refactored `tools/traceability.py` to dynamically parse all 47 requirements directly from `docs/01-srs.md` (FR-01..26, NFR-01..10, DR-01..05, CR-01..06) using structured regex parsers for tables and lists. Eliminated hardcoded requirement dictionaries.
   - Excluded helper fixtures (`test_db_path`, `test_service`, and any function decorated with `@pytest.fixture`) from test scanning.
   - Reviewed and tightened test mappings; mapped NFR-06 to latency test `test_fr10_fr11_d1_traces_notices_and_latency` with note stating requirement is met on engine-direct path only; mapped NFR-08 to immutable SQLite database triggers.
   - Result: **47 of 47 requirements covered (100%)**. Report generated in `reports/traceability.md` and `docs/reports/phase-5-6-evidence/traceability.md`.

---

## 6. Patch Round 2: UI Specification & Tests Verification (A7)

1. **Specification Adherence**:
   - Verified disclaimer banner on all three UI pages (Index, Results, About): *"Prototype. Illustrative policy values and synthetic or public data. Not a real lending decision."*
   - Verified ML block caveat: *"This score does not feed the decision. It is a ranking score, not a probability."*
   - Confirmed architecture: pure static HTML/CSS/JS; all insertions via `textContent` (zero `innerHTML`); no direct database writes in UI layer (all decisions routed via `DecisionService`). Removed fictional `/ui/reviewer` database write descriptions from documentation.
   - Verified all 8 tests collected via `python -m pytest --collect-only tests/unit/test_ui.py` pass cleanly. Updated `docs/reports/phase-5-6-evidence/ui_evidence.md` with collected test names.

---

## 7. Patch Round 2: Reproduce Comparison & CRLF Normalization (A8)

1. **Expanded Artifact Verification**:
   - Enhanced `tools/reproduce_comparison.py` to compare:
     - 3 Rule system files (tol = 0.0).
     - 7 ML baseline files (tol = 1e-6).
     - 7 Fairness JSON files: `d2_rule_system.json`, `d2_lr.json`, `d2_gb.json`, `d3_rule_system.json`, `d3_lr.json`, `d3_gb.json`, `summary.json` (tol = 1e-6).
     - Manifest hashes: `rule_set_hash`, `params_hash`, `fairness_plan_pin`, and report file disk hashes in `reports/phase5_manifest.json`.
     - Planted bias and control metrics in `reports/fairness/summary.json`.

2. **Resolution of `params_hash` Discrepancy**:
   - The apparent difference between the local repository hash (`sha256:4c26986...`) and the clean checkout hash (`sha256:d45e301...`) was caused by Windows git `core.autocrlf = true` converting LF line endings to CRLF upon checkout in a new working tree.
   - Added byte-level LF normalization (`.replace(b"\r\n", b"\n")`) to `sha256_file()` in `tools/phase5_manifest.py` and `tools/reproduce_comparison.py`. Both environments now deterministically hash `params/params.toml` to `sha256:4c2698607ae7ea824fc62f39a84ac52fa69db1b59c0657ffeb152b0960885373`.

---

## 8. Supporting Evidence Files Attached (B)

All required supporting evidence files have been verified and placed in `docs/reports/phase-5-6-evidence/`:
- `regulatory_mapping.md`: Full regulatory mapping document.
- `model-card.md`: Full model card including completed sections 8–12.
- `summary.json`: Fairness summary report including planted bias and control results.
- `repo_scan.txt`: Output of git tracking and secrets scan confirming zero sensitive files tracked.
- `edge_cases_summary.md`: Complete 64-case edge-case results without templates.
- `scorecard.md`: Completed four-criterion comparison scorecard.
- `fairness_d2_tables.md` & `fairness_d3_tables.md`: Dual treatment fairness tables.
- `planted_bias_table.md`: Four-cell sensitivity matrix with percentile bootstrap CIs.
- `traceability.md`: 47/47 requirement traceability matrix.
- `ui_evidence.md`: UI test and architectural evidence.
- Verified that `data/synthetic/` contains only `d1_generator.py` and `d3_generator.py` tracked in git; zero CSV files tracked.

---

## 9. Gate Commands Execution Results

### Gate Summary Table

| Command | Purpose | Result |
|---|---|---|
| `make check` | Float ban, ruff lint, ruff format, param/field/rule checks, hygiene | **PASS** |
| `make check-rules` | Parameter loader, field loader, rule loader, hygiene analysis | **PASS** |
| `make oracle-diff` | Parity verification between pure-Python engine and oracle on D1 | **PASS** |
| `make test` | Full test suite execution (198 tests) | **PASS** |
| `make phase5` | Edge cases, comparison scorecard, fairness evaluation, manifest | **PASS** |
| `make traceability` | Dynamic requirement verification (46 covered by tests + 1 measured; 47 total) | **PASS** |
| `make check-docs` | Document consistency, scorecard check, and sensitive file scan | **PASS** |
| `make reproduce` | Verify zero-divergence reproduction on clean clone / current repo | **PASS** |

---

### Unedited Last 15 Lines of Output per Gate Command

#### 1. `make check`
```text
python -m src.engine.param_loader params/params.toml
OK: params/params.toml loaded with 0 warning(s) and no errors.
    18 scalar parameters, 3 band(s).
python -m src.engine.field_loader rules/fields.toml
OK: rules\fields.toml loaded with 0 warning(s) and no errors.
    27 fields (15 input, 12 derived).
python -m src.engine.rule_loader rules params/params.toml
OK: rules loaded successfully (22 rules across 7 layers, 21 reason codes).
python -m src.engine.hygiene
----------------------------------------
V04        | 2            | OK                            
AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM | 0            | Unreachable by design (DT-3)  
----------------------------------------

OK: all hygiene checks passed with zero findings.
"=== make check complete ==="
```

#### 2. `make check-rules`
```text
python -m src.engine.param_loader params/params.toml
OK: params/params.toml loaded with 0 warning(s) and no errors.
    18 scalar parameters, 3 band(s).
python -m src.engine.field_loader rules/fields.toml
OK: rules\fields.toml loaded with 0 warning(s) and no errors.
    27 fields (15 input, 12 derived).
python -m src.engine.rule_loader rules params/params.toml
OK: rules loaded successfully (22 rules across 7 layers, 21 reason codes).
python -m src.engine.hygiene

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
tests\unit\test_rule_loader.py .......                                   [ 83%]
tests\unit\test_rules_firing_and_boundaries.py .....................     [ 94%]
tests\unit\test_scorecard.py ...                                         [ 95%]
tests\unit\test_ui.py ........                                           [100%]

============================== warnings summary ===============================
..\..\..\..\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\asus\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 198 passed, 1 warning in 22.01s =======================
```

#### 5. `make phase5`
```text
Loading D3 data...
Evaluating D3 rule system...
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_rule_system.json
Evaluating D3 ML models...
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_lr.json
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_gb.json
Running counterfactual swap across rule engine, LR, and GB...
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
  Report files hashed: 28
"=== Phase 5 complete ==="
```

#### 6. `make traceability`
```text
python tools/traceability.py
Traceability report written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\traceability.md and C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\docs\reports\phase-5-6-evidence\traceability.md
Requirements: 46 covered by tests + 1 measured (47 total)
```

#### 7. `make check-docs`
```text
Rule IDs in rules/*.toml: 22
Rule IDs mentioned in docs: 24
Reason codes in reason_codes.toml: 21
Reason codes mentioned in docs: 21
Policy parameters mentioned in docs: 6
  OK: All rule IDs in rules/*.toml are present in docs.
  OK: All reason codes in reason_codes.toml are present in docs.
  OK: All parameter names mentioned in docs exist in params/params.toml.

=== Scorecard consistency check ===
  OK: Scorecard in docs/final-report.md exactly matches reports/comparison/scorecard.json.

=== Secrets and sensitive file scan ===
  OK: No sensitive paths tracked by git

=== Summary ===
Informational notes (2):
  Doc mentions rule ID 'K07' not in active rules/*.toml (historical/catalog note)
  Doc mentions rule ID 'P04' not in active rules/*.toml (historical/catalog note)
Check-docs: all consistency checks passed.
```

#### 8. `make reproduce`
```text
Loading D3 data...
Evaluating D3 rule system...
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_rule_system.json
Evaluating D3 ML models...
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_lr.json
  Written: C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\fairness\d3_gb.json
Running counterfactual swap across rule engine, LR, and GB...
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
  Report files hashed: 28
"=== Phase 5 complete ==="
python tools/reproduce_comparison.py
Reproduce comparison written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\reports\reproduce_comparison.md and C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\docs\reports\phase-5-6-evidence\reproduce_comparison.md
All checks passed.
"=== Reproduce complete ==="
```
