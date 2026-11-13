# Final Project Report: Rule-Based Loan Eligibility Expert System

**Project:** Unsecured Personal Loan Eligibility Expert System in INR  
**Author:** Antigravity / Engineering Team  
**Date:** 13 November 2026  
**Version:** 1.0.0 (`rules-1.0.0+params-0.1.0`)  
**Repository Pin:** `tests/golden/rule_set_pin.json` (`sha256:eb7073a388817e0a455997c0c2ea86ccb25524cdff07faf8bf5ca98bb267be5a`)

---

## 1. Problem Statement

Automated credit decisioning systems in retail finance face a fundamental tension between explainability, determinism, regulatory compliance, and predictive optimization. In retail unsecured personal lending in India, credit institutions must satisfy strict consumer protection and disclosure mandates (e.g., RBI Digital Lending Directions Key Fact Statement disclosures and specific adverse-action reasoning) while ensuring that credit policies are applied uniformly without arbitrary or unexplainable denials.

Contemporary machine learning (ML) models, while effective at ranking default probabilities, act as black-box scoring mechanisms. Post-hoc explanation techniques (such as SHAP or LIME) are statistical approximations that lack exact faithfulness to individual model decisions, may vary across implementations, and do not provide deterministic logical deduction.

This project designs, implements, and rigorously evaluates a **first-order logic, rule-based expert system** for unsecured personal loan eligibility in Indian Rupees (INR). Production rules decide `ELIGIBLE`, `INELIGIBLE`, or `REFER`, compute maximum loan capacity and risk-based pricing, and emit a complete, cryptographically verified explanation trace of every rule that fired. A machine learning baseline (Logistic Regression and HistGradientBoosting) is constructed solely as a comparative benchmark to contrast accuracy, explainability, operational cost, and fairness properties.

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
- **Rule Engine (`src/engine/`)**: Evaluates forward-chaining production rules against the fact base using pure AST evaluation (`src/engine/engine.py`), matching the formal reference semantics of SWI-Prolog (`tools/oracle_diff.py`).
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
- Missing Data (MD), Threshold Boundaries (TB), Thin File (TF), Rare Combinations (RC), and Adversarial/Gamed Inputs (AD).
- **Results**: 61 of 64 cases matched catalog expectations exactly (95.3% match rate). The 3 explained differences (EC-TB-16, EC-TB-17, EC-AD-02; logged in `docs/open-questions.md` as OQ-012) stem from mathematical FOIR-at-cap capacity exhaustion (F4/F7/A03 interaction) where existing obligations equal 50% of income, leaving zero EMI headroom.

---

## 6. Comparison: Rule System vs. ML Baselines

Following `docs/comparison-methodology.md`, the expert system and ML baselines (Logistic Regression, HistGradientBoosting) were evaluated across four core criteria on the held-out D2 test split ($N = 46,127$) and documented in `reports/comparison/scorecard.json`:

| Criterion | Metric / Artifact Anchor | Rule System (Treat. A) | Logistic Regression | HistGradientBoosting |
|---|---|---|---|---|
| **Accuracy / Default** | Approval Rate (`reports/ml/metrics_d2_lr.json`) | 1.68% (776 app.) | 1.56% (matched $\tau=0.1479$) | 1.71% (matched $\tau=0.0680$) |
| | Default Rate among Approved | 3.35% (95% CI: 2.1–4.7%) | 1.39% | 1.27% |
| | Test AUC | N/A (categorical decision) | 0.7248 | 0.7378 |
| | Cost per Applicant ($C_{FN}/C_{FP}=5$) | 0.9058 | 0.9050 | 0.9035 |
| **Explainability** | Reason Code Generation | 100% exact from fired rules | Post-hoc linear weights only | Tree split importances |
| | Counterfactual Stability | 100% deterministic | Continuous score shifts | High sensitivity |
| **Auditability** | Replay Reproducibility | Byte-identical (`make replay`) | Numeric approx. | Numeric approx. |
| **Operational Agility**| Policy Change Latency | Instant (TOML edit) | Requires full retraining | Requires full retraining |

### Scorecard Summary
Per `reports/comparison/scorecard.md`:
- **Explainability**: Rule System: 5/5; ML Baseline: 2/5.
- **Auditability**: Rule System: 5/5; ML Baseline: 2/5.
- **Operational Agility**: Rule System: 5/5; ML Baseline: 2/5.
- **Financial Performance / Default Control**: Rule System: 3/5; ML Baseline: 4/5.

---

## 7. Fairness and Algorithmic Audit Findings

The fairness review was executed strictly under the pinned audit protocol (`docs/fairness-audit-plan.md`, `reports/fairness/plan_pin.json`, `config/fairness.toml`).

### 7.1 Pipeline Validation Test (Part E)
- **Planted Bias Test**: Conducted on synthetic population with 15% income penalty planted on female applicants (`data/synthetic/d3_bias_large.csv`, $N = 100,000$, `data/decisions/d3_bias_large_decisions.csv`). The pipeline flagged gender on selection-rate difference ($F < M$, difference $-0.0186$, 95% bootstrap CI $[-0.0247, -0.0127]$, strictly excluding 0).
- **Control Test**: On unperturbed synthetic D3 ($N = 20,000$), gender selection-rate difference was $-0.0205$ with 95% CI $[-0.0576, +0.0159]$ (includes 0; no flag triggered).
- **12-Row Hand Check**: Exact numerical point estimates matched manual mathematical derivations across Treatment A and Treatment B selection rates and EOD (`tests/unit/test_fairness.py`).

### 7.2 Findings on D2 Benchmark ($N = 46,127$)
Cited from `reports/fairness/d2_tables.md` and `reports/fairness/d2_rule_system.json`:
- **Low Baseline Approval Rate**: Because of conservative policy thresholds (income floor K05 and fallback obligations ASM-D4), the rule system approves only 1.68% of D2 test applicants (776 total).
- **Equal Opportunity Difference (EOD)**: Male approval rate among repayers ($TARGET = 0$) was 2.22% vs. 1.54% for females (difference $+0.0067$, 95% CI $[+0.0036, +0.0101]$). This statistically significant gap arises because female applicants in the Home Credit sample have systematically lower recorded formal monthly income, failing the absolute ₹25,000 income floor (K05) at higher rates.
- **Small Cell and Instability Limits**: Intersectional slices and rare groups (e.g., academic degrees, older cohorts) contain fewer than 20 approvals, correctly reported as `unstable` or `too_small` per protocol P5-5.

### 7.3 Counterfactual Swap and Proxy Analysis
- **Counterfactual Swap (`reports/fairness/summary.json`)**: 1,000 D3 rows re-evaluated after shuffling the protected attribute store resulted in **0 decision changes** (`pass: true`), confirming strict compliance with FR-20 and DR-02.
- **Proxy Signal**: A logistic regression predicting applicant gender (`CODE_GENDER`) from the model feature set on D2 achieved an AUC of **0.6745**, indicating moderate correlation between employment/income features and gender in the raw benchmark.

---

## 8. Limitations and Scope Boundaries

The following limits govern this coursework release and must be stated without omission:
1. **Illustrative Policy Values (Decision D-02)**: All thresholds, tenure bounds, interest bands, and multiplier caps are illustrative academic values stored in `params/params.toml`. They do not constitute an actual commercial credit underwriting policy.
2. **Mapped Benchmark Artifacts (D2 Limits)**:
   - D2 relies on 13 synthetic mapping assumptions (ASM-D1 to ASM-D13); 65.0% of records rely on beta-distributed fallback obligations (ASM-D4), and 70.0% have unknown severe delinquency (ASM-D7).
   - Only 776 applicants are approved by the rules on D2 test data. All subgroup findings rest on very small approval cell sizes.
   - D2 suffers from historical lender selection bias (outcomes observed only for historically approved applicants).
3. **Circularity in D3**: D3 synthetic labels represent the rule engine's own decisions; ML performance on D3 measures imitation fidelity, not real credit risk.
4. **Regulatory Confirm Items**: Items marked "confirm" in `docs/regulatory-mapping.md` (RBI Digital Lending Directions implementation nuances, CFPB Regulation B updates, EU AI Act enforcement dates) rest on legal summaries and require primary gazette re-verification.
5. **Lean-Mode Scope Cuts**: In accordance with `docs/06-test-plan.md` ("Lean mode"), the following tests were not conducted: Fairlearn library cross-check, formal SHAP faithfulness tests, comprehensive rule coverage percentages, sensitivity sweeps, and loader edge-case stress tests.
6. **Unfixed Polish List**: Per phase instructions, the following five known polish items were intentionally left unfixed to preserve backward compatibility and prevent regression: (a) reviewer page ML model representation in `src/api/review_report.py` (kept as Phase 4 placeholder string to maintain Phase 3 test pass), (b) R01 null credit score handling, (c) notice rounding formatting, (d) zero-max offer text formatting, and (e) denial review sentence phrasing.

---

## 9. Future Work

1. **Rejection Inference on D2**: Implement bivariate probit or parceling techniques to correct for historical selection bias on unapproved applicants.
2. **Hybrid Neuro-Symbolic Architecture**: Deploy ML classifiers for credit risk ranking while using the deterministic rule engine as an immutable safety and eligibility guardrail.
3. **Automated Adverse Action Recourse**: Enhance the notice builder to emit personalized counterfactual recourse advice (e.g., exact debt reduction needed to clear the FOIR threshold).
4. **Interactive Reviewer Queue Integration**: Connect the reviewer UI directly to an audited database with role-based access control and dual-authorization workflow.

---

## 10. Audit Sign-Off and Gate Verification

All gate commands have passed cleanly:
- `make check`: PASS (164 tests, float ban, lint, format, param and rule checks)
- `make check-rules`: PASS (rule syntax, schemas, and hygiene analysis)
- `make oracle-diff`: PASS (0 differences on D1 reference suite)
- `make test`: PASS (196 total unit, property, golden, and integration tests)
- `make phase5`: PASS (edge-case catalog, comparison scorecard, fairness audit, and manifest)
- `make reproduce`: PASS (Phase 4 and Phase 5 reproducibility verified)
- `make traceability`: PASS (36 requirement IDs mapped to tests; 9 documented)
- `make check-docs`: PASS (0 missing rule IDs, 0 missing reason codes, secrets scan clean)

