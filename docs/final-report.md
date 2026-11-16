# Final Project Report: Rule-Based Loan Eligibility Expert System

**Project:** Unsecured Personal Loan Eligibility Expert System in INR  
**Author:** Antigravity / Engineering Team  
**Date:** 14 November 2026  
**Version:** 1.0.0 (`rules-1.0.0+params-0.1.0`)  
**Repository Pin:** `tests/golden/rule_set_pin.json` (`sha256:eb7073a388817e0a455997c0c2ea86ccb25524cdff07faf8bf5ca98bb267be5a`)

---

## 1. Problem Statement

Automated credit decisioning systems in retail finance face a fundamental tension between explainability, determinism, regulatory compliance, and predictive optimization. In retail unsecured personal lending in India, credit institutions must satisfy strict consumer protection and disclosure mandates (e.g., RBI Digital Lending Directions Key Fact Statement disclosures and specific adverse-action reasoning) while ensuring that credit policies are applied uniformly without arbitrary or unexplainable denials.

Contemporary machine learning (ML) models, while effective at ranking default probabilities, act as black-box scoring mechanisms. Post-hoc explanation techniques (such as SHAP or LIME) are statistical approximations that lack exact faithfulness to individual model decisions, may vary across implementations, and do not provide deterministic logical deduction.

This project designs, implements, and rigorously evaluates a **rule-based expert system utilizing predicate-based production rules in TOML, evaluated by a pure-Python AST evaluator** for unsecured personal loan eligibility in Indian Rupees (INR). Production rules decide `ELIGIBLE`, `INELIGIBLE`, or `REFER`, compute maximum loan capacity and risk-based pricing, and emit a complete, **hash-pinned and replay-checked trace** of every rule that fired. A machine learning baseline (Logistic Regression and HistGradientBoosting) is constructed solely as a comparative benchmark to contrast accuracy, explainability, operational cost, and fairness properties.

---

## 2. Policy and Legal Context

### 2.1 Regulatory Frameworks
The expert system was architected against three primary regulatory benchmarks (detailed in `docs/regulatory-mapping.md`):

1. **RBI (Digital Lending) Directions, 2025 & Fair Practices Code (India)**:
   - Requires upfront issuance of a Key Fact Statement (KFS) detailing loan amount, tenure, interest rate, processing fees, total repayment, and Annual Percentage Rate (APR).
   - Enforces explicit applicant consent (`consent_given`), purpose-bound data collection, and access to grievance escalation (`docs/regulatory-mapping.md` §1).
2. **US Equal Credit Opportunity Act (ECOA) / Regulation B (12 CFR Part 1002)**:
   - Mandates specific, factual reason codes on adverse action notices reflecting the actual factors considered.
   - Note: Recent CFPB revisions (effective 21 July 2026, confirm) remove disparate-impact liability under federal Regulation B; however, adverse-action notice duties remain unchanged.
3. **EU Artificial Intelligence Act (Regulation EU 2024/1689 & Digital Omnibus EU 2026/1744)**:
   - Classifies creditworthiness evaluation systems for natural persons as high-risk AI (Annex III, point 5b). Stand-alone high-risk obligations apply from 2 December 2027 (confirm). Requires human oversight, robust logging, transparency, and bias testing.

*Note on Confirm Items:* Per Checkpoint CP-15 (conducted 13 November 2026), regulatory summaries were sourced from legal analysis summaries; items marked "confirm" in `docs/regulatory-mapping.md` must be verified against official gazettes before commercial reliance.

### 2.2 Credit Policy Architecture
The credit policy is codified as data in `rules/*.toml` and parameterized in `params/params.toml`:
- **Validation layer (`rules/validation.toml`)**: Hard syntax, legal capacity (age $\ge 18$), and consent requirements.
- **Knockout layer (`rules/knockout.toml`)**: Absolute eligibility disqualifiers (severe delinquency in 36 months, write-offs, KYC verification, income floor, minimum employment tenure).
- **Referral layer (`rules/referral.toml`)**: Routing of applications with missing/unknown bureau data (`severe_delinquency_36m` or `written_off` unknown) or complex employment types to manual underwriting.
- **Eligibility layer (`rules/eligibility.toml`)**: Hard affordability gates (Fixed Obligations to Income Ratio, FOIR $\le 0.50$, credit score $\ge 650$, enquiry limits).
- **Amount determination (`rules/amount.toml`)**: Formulas F5–F7 computing repayment capacity, income multiple cap, product maximum, and binding limit tie-breaks.
- **Pricing layer (`rules/pricing.toml`)**: Risk-based interest bands (Band A: 11–13%, Band B: 13–16%, Band C: 16–20%) mapped to credit score.

---

## 3. System Design and Architecture

### 3.1 Architectural Principles
The implementation follows strict separation of concerns (`docs/05-architecture.md`):
1. **No Magic Numbers**: Zero numeric policy thresholds appear in Python or rule condition text; all values are injected dynamically from `params/params.toml` (`NFR-04`).
2. **Strict Arithmetic Typing**: Exact decimal arithmetic (`Decimal` and whole rupee integer math) is enforced across `src/calc/`, `src/facts/`, `src/explain/`, and data mapping. Floating-point numbers are completely banned and enforced via AST static scan `tools/check_floats.py` (`NFR-03`).
3. **Trace Derivation Only from Fired Rules**: Adverse action reason codes and customer-facing notices are built strictly from rules that fired during inference (`FR-07`, `FR-08`).
4. **Append-Only Immutable Audit Log**: Every audited decision writes canonical inputs and hashes to an append-only SQLite store protected by database triggers that abort `UPDATE` and `DELETE` operations (`FR-10`, `NFR-06`).
5. **Deterministic Replay**: Past decisions can be replayed from the stored input hash and rule-set version hash, verifying byte-identical reproducibility (`FR-11`, `NFR-01`, `NFR-07`).

---

## 4. Implementation Details

- **Fact Builder (`src/facts/`)**: Validates input JSON against `schemas/input.schema.json` (14 fields), converts inputs to exact Decimals, asserts known/unknown fact triples, and prevents missing field coercions.
- **Rule Engine (`src/engine/`)**: Evaluates forward-chaining production rules against the fact base using a pure-Python AST evaluator (`src/engine/engine.py`), adopted under the explicit fallback clause of ADR-001 (OQ-001). Rules are represented as declarative TOML data (`rules/*.toml`) with structured condition expressions parsed into syntax trees. The repository contains no production Prolog file and no Prolog code path; the only Prolog file is the toy test file under `spikes/s1/toy_rules.pl` created during the Phase 0 spike S1 (permitted by AGENTS.md under `spikes/`). SWI-Prolog was never run for this project on this host machine because `swipl` was not installed (documented in `docs/reports/spike-s1.md` and `docs/open-questions.md` OQ-001). Phase 2 tested the pure-Python AST evaluator, condition parser, rule loader, and rule hygiene analysis on golden vectors TV1–TV9 and the D1 test suite directly in Python.
- **Explanation & Notice Generation (`src/explain/`)**: Assembles rule firing traces and maps reason codes to clear, plain-language text templates (`rules/reason_codes.toml`).
- **Calculations Core (`src/calc/`)**: Implements mathematical formulas F1 through F9 (EMI amortisation, FOIR, capacity, income multiples, APR, and rounding rules).
- **Audit & Reviewer Subsystems (`src/audit/`, `src/api/`)**: SQLite store with SHA-256 canonical hashing, review override recording, and reviewer queue rendering.
- **Demo User Interface (`src/ui/`)**: Lightweight, zero-dependency browser application (`src/ui/app.py`, `src/ui/static/`) serving interactive application testing, TV1–TV9 preset loading, rule trace inspection, and ML score side-by-side display (`FR-25`).

---

## 5. Empirical Evaluation and Datasets

### 5.1 Dataset Specifications
As documented in `data/manifest.json`:
- **D1 (Reference Fixture)**: 50 synthetic test cases spanning all policy boundaries, used for continuous engine-oracle parity verification.
- **D2 (Home Credit Default Risk Benchmark)**: 307,511 mapped real-world loan applications (`data/mapped/d2_mapped.csv`). Partitioned into stratified splits: Train (70%, 215,257), Validation (15%, 46,127), and Test (15%, 46,127). Label: `TARGET` (8.07% default rate).
- **D3 (Synthetic Population)**: 20,000 generated synthetic applicants (`data/synthetic/d3_population.csv`) with known independent generative distributions. Partitioned into 70/15/15 splits.

### 5.2 Edge-Case Evaluation (WP-18)
The edge-case suite (`reports/edge_cases/summary.md`) evaluated 64 stress cases across five categories:
- Missing Data (MD: 9), Threshold Boundaries (TB: 40), Thin File (TF: 4), Rare Combinations (RC: 4), and Adversarial/Gamed Inputs (AD: 7).
- **Results**: 61 of 64 cases matched catalog expectations exactly (95.3% match rate). The 3 explained differences (EC-TB-16, EC-TB-17, EC-AD-02; logged in `docs/open-questions.md` as OQ-012) stem from mathematical FOIR-at-cap capacity exhaustion (F4/F7/A03 interaction) where existing obligations equal 50% of income, leaving zero EMI headroom.

---

## 6. Comparison: Rule System vs. ML Baselines (FR-22)

Following `docs/comparison-methodology.md`, the expert system and ML baselines (Logistic Regression and Gradient Boosting) were evaluated across the four pre-registered criteria on a scale of 0 to 3 using exact document anchors, documented in `reports/comparison/scorecard.json` and `reports/comparison/scorecard.md`:

| Criterion | System | Score | Anchor Met | Artifact Citations | Rationale |
|---|---|:---:|---|---|---|
| **Transparency** | Rule System | **3** | Every decision lists the rules that fired and the facts they used, and the applicant-facing reasons are exactly the reason codes of those rules (tested on all of D1). | `tests/integration/test_phase3_api_and_audit.py`, `src/explain/notice.py` | Every decision generates an exact trace containing only fired rules, with adverse notices rendered verbatim from reason code definitions in rules/reason_codes.toml. |
| | Logistic Regression | **2** | Each decision has an exact, per-decision explanation from the model's own arithmetic (the logistic regression's feature contributions), but the explanation is a score contribution, not a policy reason the applicant can act on. | `src/ml/baseline.py`, `reports/ml/metrics_d3_lr.json` | Linear feature contributions provide exact additive logit shifts per applicant, but output numerical score weights rather than actionable policy clauses. |
| | Gradient Boosting | **1** | Only a global explanation exists (permutation importance), not one per decision. | `reports/ml/metrics_d3_gb.json` | Provides global tree feature importances only; non-linear ensemble interactions lack exact closed-form per-decision explanations without complex local approximations. |
| **Auditability** | Rule System | **3** | A stored record per decision, a version for the logic used, and a replay that reproduces the decision and trace, with a mismatch reported when a parameter changes. | `tests/integration/test_phase3_api_and_audit.py`, `tests/golden/rule_set_pin.json`, `data/manifest.json` | Every decision is committed to an append-only SQLite audit log with input SHA-256 and ruleset hash, verifiable via byte-identical replay. |
| | Logistic Regression | **2** | Versioned artifact and seed, and the numbers reproduce, but no per-decision record or replay. | `models/d3_lr.joblib`, `reports/ml/metrics_d3_lr.json` | Model training reproduces deterministically from derived seed with recorded dataset and split hashes, but lacks an append-only decision audit store and replay capability. |
| | Gradient Boosting | **2** | Versioned artifact and seed, and the numbers reproduce, but no per-decision record or replay. | `models/d3_gb.joblib`, `reports/ml/metrics_d3_gb.json` | Reproducible training pipeline from fixed seed and versioned split hashes, without individual decision tracing or replay store. |
| **Edge cases** | Rule System | **3** | No unexplained difference in any category; every missing-data and boundary case ends in a stated outcome. | `reports/edge_cases/summary.md`, `reports/edge_cases/results.csv` | Evaluated on 64 edge cases across 5 categories with 61 exact catalog matches, 3 explained FOIR-capacity interactions (OQ-012), and zero unexplained differences. |
| | Logistic Regression | **1** | An unexplained difference in the missing-data or boundary categories. | `reports/edge_cases/summary.md`, `reports/edge_cases/results.csv` | Evaluated on 64 edge cases. Pipeline flags missing fields with indicators, but approves applicants with null mandatory income (EC-MD-01) and evaluates boundary thresholds continuously without discrete policy bounds. |
| | Gradient Boosting | **1** | An unexplained difference in the missing-data or boundary categories. | `reports/edge_cases/summary.md`, `reports/edge_cases/results.csv` | Evaluated on 64 edge cases. Tree pipeline handles missing data via imputation and indicator flags without error, but approves applicants with missing mandatory income (EC-MD-01) and lacks schema-level refusal. |
| **Regulatory defensibility** | Rule System | **3** | All six rows met with evidence. | `docs/regulatory-mapping.md` | Fully satisfies requirements CR-01 to CR-06 with verifiable tests for specific reason notices, KFS summaries, consent enforcement, and human referral. |
| | Logistic Regression | **1** | Two or three rows partly met or gaps. | `docs/regulatory-mapping.md` | Meets CR-05 (model card) and CR-06 (bias testing), but leaves gaps on CR-01 (actionable specific adverse reasons), CR-02 (KFS offer terms), and CR-04 (human referral). |
| | Gradient Boosting | **1** | Two or three rows partly met or gaps. | `docs/regulatory-mapping.md` | Meets CR-05 and CR-06, but cannot provide per-decision adverse reasons (CR-01), loan terms (CR-02), or human review routing (CR-04). |

*Note on Scoring Methodology*: In strict accordance with `docs/comparison-methodology.md`, criteria are scored on a discrete 0 to 3 scale using documented qualitative anchors. Criteria are not averaged and no weights are applied.

### Context Table: Predictive Accuracy and Default Control (Unscored)

> **Context note**: D2 rests on 776 approvals with overlapping intervals and D3 agreement is partly circular.

| Metric / Attribute | Rule System (Treatment A) | Rule System (Treatment B) | Logistic Regression | HistGradientBoosting |
|---|---|---|---|---|
| **D2 Test Approval Rate** | 1.68% (776 / 46,127) | 1.84% (776 / 42,072) | 1.56% (matched $\tau=0.1479$) | 1.71% (matched $\tau=0.0680$) |
| **D2 Default Rate among Approved** | 3.35% (95% CI: 2.14%–4.70%) | 3.35% (95% CI: 2.12%–4.67%) | 1.39% (95% CI: 0.56%–2.42%) | 1.27% (95% CI: 0.58%–2.12%) |
| **D2 ROC AUC** | N/A (discrete rules) | N/A (discrete rules) | 0.7248 | 0.7378 |
| **D2 Expected Cost per Applicant ($C_{FN}/C_{FP}=5$)** | 0.9058 | 0.8993 | 0.9050 | 0.9035 |
| **D3 Agreement with Policy ($\tau=0.50$)** | 100.0% (reference) | 100.0% (reference) | 80.97% | 98.53% |
| **D3 Test ROC AUC** | N/A | N/A | 0.8852 | 0.9902 |

---

## 7. Fairness and Algorithmic Audit Findings

The fairness review was executed strictly under the pinned audit protocol (`docs/fairness-audit-plan.md`, `reports/fairness/plan_pin.json`, `config/fairness.toml`).

### 7.1 Pipeline Validation Test (Pre-registered and Supplementary)
Evaluation under the pre-registered pipeline (`selection_rate_difference`, reference group M, evaluated group F, family-wise $\alpha = 0.05$ with Percentile bootstrap CIs (P5-4)):
- **Standard-Size Planted Bias Test (Pre-registered, P5-11)**: Evaluated on the standard synthetic D3 population with 15% income penalty planted on female applicants ($N = 20,000$, all rows, rules only). The pipeline detected the shift at standard size (marginally: upper bound -0.0013, close to zero; point estimate **$-0.0151$**, 95% bootstrap CI **$[-0.0286, -0.0013]$**, strictly excludes 0, $F < M$; **Flag = True**).
- **Standard-Size Control Test (Pre-registered, P5-11)**: On the unperturbed standard synthetic D3 population ($N = 20,000$, all rows), gender selection-rate difference was **$+0.0031$**, 95% bootstrap CI **$[-0.0100, +0.0168]$** (straddles 0; **Flag = False**).
- **Supplementary 100,000-Row Power Check (Amendment A-02)**: Evaluated on $N = 100,000$ to confirm asymptotic confidence interval narrowing. Planted run: clearly detected at 100,000 (difference **$-0.0186$**, 95% CI **$[-0.0247, -0.0127]$**; **Flag = True**). Control run: difference **$+0.0012$**, 95% CI **$[-0.0049, +0.0071]$**; **Flag = False**).
- **Mechanism of Effect**: A 15% income reduction for female applicants shifts the selection rate by roughly 1.5 to 1.9 percentage points (point estimates -0.0151 and -0.0186). This occurs because income operates through affordability rules (FOIR, disposable income, income floors) that affect only marginal applicants near threshold boundaries, rather than the entire population.
- **12-Row Hand Check**: Exact numerical point estimates matched manual mathematical derivations across Treatment A and Treatment B selection rates and EOD (`tests/unit/test_fairness.py`).

### 7.2 Findings on D2 Benchmark ($N = 46,127$)
Cited from `reports/fairness/d2_tables.md` and `reports/fairness/d2_rule_system.json`:
- **Low Baseline Approval Rate**: Because of conservative policy thresholds (income floor K05, minimum employment E01, and fallback obligations ASM-D4), the rule system approves only 1.68% of D2 test applicants (776 total).
- **Equal Opportunity Difference (EOD)** across Primary Attributes:
  - *Gender*: Male approval rate among repayers ($TARGET = 0$) was 2.22% vs. 1.54% for females (difference $+0.0067$, 95% CI $[+0.0036, +0.0101]$, flagged). This statistically significant gap arises because female applicants in the Home Credit sample have systematically lower recorded formal monthly income, failing the minimum monthly income floor of ₹15,000 (E01/K05) at higher rates.
  - *Age Band* (ref: 30-39): Cohort 21-29 has lower approval among repayers (difference $-0.0102$, 95% CI $[-0.0144, -0.0060]$, flagged) and cohort 60+ has lower approval (difference $-0.0141$, 95% CI $[-0.0180, -0.0102]$, flagged), while cohort 40-49 has higher approval (difference $+0.0095$, 95% CI $[+0.0045, +0.0146]$, flagged). Cohort 50-59 straddles zero (difference $-0.0012$, 95% CI $[-0.0058, +0.0033]$, not flagged).
  - *Employment Type* (ref: salaried): Self-employed applicants show a slight positive difference among repayers (difference $+0.0042$, 95% CI $[+0.0004, +0.0080]$, flagged). Applicants with employment type `other` are **never approved under the rules** (0 approvals, failing E01 which requires salaried $\ge 6$ months or self-employed $\ge 24$ months); having fewer than 20 approvals, this slice is marked `unstable` per P5-5 with no flag.
  - *Income Band* (ref: Q1): Reference quartile Q1 has 0 approvals (failing the ₹15,000 income floor); with $<20$ approvals in the reference group, all comparisons are marked `unstable` per P5-5 with no flag.
- **Small Cell and Instability Limits**: Intersectional slices and rare groups (e.g., academic degrees, older cohorts) contain fewer than 20 approvals, correctly reported as `unstable` or `too_small` per protocol P5-5.

### 7.3 Counterfactual Swap and Proxy Analysis
- **Counterfactual Swap (`reports/fairness/summary.json`)**: 1,000 D3 rows re-evaluated after shuffling the protected attribute store resulted in **0 decision changes across all three systems**: rule engine (FR-20), Logistic Regression (DR-02), and HistGradientBoosting (DR-02), each on 1,000 rows (`pass: true`).
- **Proxy Signal**: A logistic regression predicting applicant gender (`CODE_GENDER`) from the model feature set on D2 achieved an AUC of **0.6745** (P5-9: report only; no action), indicating moderate correlation between employment/income features and gender in the raw benchmark.

---

## 8. Limitations and Scope Boundaries

The following limits govern this coursework release and must be stated without omission:
1. **Illustrative Policy Values (Decision D-02)**: All thresholds, tenure bounds, interest bands, and multiplier caps are illustrative academic values stored in `params/params.toml`. They do not constitute an actual commercial credit underwriting policy.
2. **Mapped Benchmark Artifacts (D2 Limits)**:
   - D2 relies on 13 synthetic mapping assumptions (ASM-D1 to ASM-D13); 65.0% of records rely on beta-distributed fallback obligations (ASM-D4), and 70.0% have unknown severe delinquency (ASM-D7).
   - Only 776 applicants are approved by the rules on D2 test data. All subgroup findings rest on very small approval cell sizes with overlapping confidence intervals.
   - D2 suffers from historical lender selection bias (outcomes observed only for historically approved applicants).
3. **Circularity in D3**: D3 synthetic labels represent the rule engine's own decisions; ML performance on D3 measures imitation fidelity, not real credit risk.
4. **Regulatory Confirm Items**: Items marked "confirm" in `docs/regulatory-mapping.md` (RBI Digital Lending Directions implementation nuances, CFPB Regulation B updates (confirm), EU AI Act enforcement dates) rest on legal summaries and require primary gazette re-verification.
5. **Batch Throughput (NFR-06)**:
   - 1,000 D3 rows through the full service path with audit logging ran at 10.9 rows per second, which would take approximately 15 minutes for 10,000 rows.
   - `make decide-d3` (engine-direct path) evaluated 20,000 rows in 19.89 seconds (1,005.6 rows per second).
   - *Scope limit*: The NFR-06 requirement of evaluating a batch of 10,000 decisions under 5 minutes holds for the **engine-direct path only**. Batch processing through the full API and audit persistence layer requires database connection pooling or batched inserts for production scale.
6. **Lean-Mode Scope Cuts**: In accordance with `docs/06-test-plan.md` ("Lean mode"), the following tests were not conducted: Fairlearn library cross-check, formal SHAP faithfulness tests, comprehensive rule coverage percentages, sensitivity sweeps, and loader edge-case stress tests.
7. **Operational Review Process Scope**: Demonstration UI surfaces scoring and decision outputs independently without persistent database mutation; production-scale deployment requires managed review queue infrastructure and human override tracking.
8. **Unanalysed Protected Attributes**: Demographic attributes such as religion, caste, sexual orientation, and disability were not captured in public benchmark D2 or synthetic dataset D3, and were therefore not evaluated in algorithmic fairness audits.
9. **ML Edge Cases Handling**: Continuous ML models lack schema rejection gates; missing mandatory income is median-imputed with an indicator flag rather than rejected, resulting in approvals on incomplete inputs (e.g. EC-MD-01).
10. **Few-Default Screening Metrics on D2**: On D2 test data, only 26 defaults exist among the 776 approved applicants (96.65% non-default rate), producing wide bootstrap confidence intervals on default metrics.
11. **Known Polish Items**: The following known polish items are documented:
   - *Reviewer page facts*: Facts are displayed as Python dictionary representation in the reviewer queue view.
   - *Review report ML block*: Placeholder string in `src/api/review_report.py` retained to preserve Phase 3 test pass.
   - *R01 credit score null handling*: R01 referral handles None values correctly, but condition structure can be streamlined.
   - *Notice formatting*: Rounding on fee percentages and zero-max offer displays.
12. **Dependency Warning Note**:
   - `starlette.testclient` issues a deprecation warning regarding `httpx` (`'app' shortcut is deprecated...`). The pinned dependency list was not modified during this phase; this warning is noted as an upstream deprecation that does not impact test correctness.

---

## 9. Future Work

1. **Rejection Inference on D2**: Implement bivariate probit or parceling techniques to correct for historical selection bias on unapproved applicants.
2. **Hybrid Neuro-Symbolic Architecture**: Deploy ML classifiers for credit risk ranking while using the deterministic rule engine as an immutable safety and eligibility guardrail.
3. **Automated Adverse Action Recourse**: Enhance the notice builder to emit personalized counterfactual recourse advice (e.g., exact debt reduction needed to clear the FOIR threshold).
4. **Interactive Reviewer Queue Integration**: Connect the reviewer UI directly to an audited database with role-based access control and dual-authorization workflow.

---

## 10. Audit Sign-Off and Gate Verification

All gate commands have passed cleanly:
- `make check`: PASS (float ban, ruff lint, ruff format, param checks, rule checks)
- `make check-rules`: PASS (rule syntax, schemas, and rule hygiene analysis)
- `make oracle-diff`: PASS (0 differences on D1 reference suite)
- `make test`: PASS (198 total unit, property, golden, and integration tests across all test suites)
- `make phase5`: PASS (edge-case catalog, comparison scorecard, fairness audit, and manifest)
- `make reproduce`: PASS (Phase 4 and Phase 5 reproducibility verified against git HEAD)
- `make traceability`: PASS (47 of 47 requirement IDs mapped to tests; 100% coverage)
- `make check-docs`: PASS (0 missing rule IDs, 0 missing reason codes, secrets scan clean, scorecard consistency verified)


