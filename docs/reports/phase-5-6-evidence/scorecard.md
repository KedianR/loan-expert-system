# Comparison Scorecard: Rule System vs ML Baselines (WP-18, FR-22, CR-05)

> [!NOTE]
> **Illustrative Policy Values (D-02)**: The policy values and thresholds are illustrative coursework artifacts.
> This comparison demonstrates architectural and design trade-offs (transparency, auditability, edge cases, defensibility),
> not a contest of commercial underwriting efficacy. D2 results rest on 776 rule approvals driven by mapping constraints.

## 1. Multi-Criterion Comparison Scorecard

Scoring scale: **0 to 3** per criterion (anchors defined in `docs/comparison-methodology.md`).
Scores are not averaged or weighted.

| System | Transparency | Auditability | Edge Cases | Regulatory Defensibility |
|---|---|---|---|---|
| **Rule-Based Expert System** | **3**<br>Every decision lists the rules that fired and the facts they used, and the applicant-facing reasons are exactly the reason codes of those rules (tested on all of D1).<br>*Every decision generates an exact trace containing only fired rules, with adverse notices rendered verbatim from reason code definitions in rules/reason_codes.toml.*<br>Artifact: `tests/integration/test_phase3_api_and_audit.py` | **3**<br>A stored record per decision, a version for the logic used, and a replay that reproduces the decision and trace, with a mismatch reported when a parameter changes.<br>*Every decision is committed to an append-only SQLite audit log with input SHA-256 and ruleset hash, verifiable via byte-identical replay.*<br>Artifact: `tests/integration/test_phase3_api_and_audit.py` | **3**<br>No unexplained difference in any category; every missing-data and boundary case ends in a stated outcome.<br>*Evaluated on 64 edge cases across 5 categories with 61 exact catalog matches, 3 explained FOIR-capacity interactions (OQ-012), and zero unexplained differences.*<br>Artifact: `reports/edge_cases/summary.md` | **3**<br>All six rows met with evidence.<br>*Fully satisfies requirements CR-01 to CR-06 with verifiable tests for specific reason notices, KFS summaries, consent enforcement, and human referral.*<br>Artifact: `docs/regulatory-mapping.md` |
| **Logistic Regression (Transparent Baseline)** | **2**<br>Each decision has an exact, per-decision explanation from the model's own arithmetic (the logistic regression's feature contributions), but the explanation is a score contribution, not a policy reason the applicant can act on.<br>*Linear feature contributions provide exact additive logit shifts per applicant, but output numerical score weights rather than actionable policy clauses.*<br>Artifact: `src/ml/baseline.py` | **2**<br>Versioned artifact and seed, and the numbers reproduce, but no per-decision record or replay.<br>*Model training reproduces deterministically from derived seed with recorded dataset and split hashes, but lacks an append-only decision audit store and replay capability.*<br>Artifact: `models/d3_lr.joblib` | **1**<br>An unexplained difference in the missing-data or boundary categories.<br>*Silently imputes missing mandatory data with median training values without schema validation, and smoothly crosses policy thresholds without discrete bounds.*<br>Artifact: `reports/edge_cases/summary.md` | **1**<br>Two or three rows partly met or gaps.<br>*Meets CR-05 (model card) and CR-06 (bias testing), but leaves gaps on CR-01 (actionable specific adverse reasons), CR-02 (KFS offer terms), and CR-04 (human referral).*<br>Artifact: `docs/regulatory-mapping.md` |
| **Gradient Boosting (Non-linear Baseline)** | **1**<br>Only a global explanation exists (permutation importance), not one per decision.<br>*Provides global tree feature importances only; non-linear ensemble interactions lack exact closed-form per-decision explanations without complex local approximations.*<br>Artifact: `reports/ml/metrics_d3_gb.json` | **2**<br>Versioned artifact and seed, and the numbers reproduce, but no per-decision record or replay.<br>*Reproducible training pipeline from fixed seed and versioned split hashes, without individual decision tracing or replay store.*<br>Artifact: `models/d3_gb.joblib` | **1**<br>An unexplained difference in the missing-data or boundary categories.<br>*Imputes missing values without error flagging and produces continuous prediction manifolds across hard policy thresholds.*<br>Artifact: `reports/edge_cases/summary.md` | **1**<br>Two or three rows partly met or gaps.<br>*Meets CR-05 and CR-06, but cannot provide per-decision adverse reasons (CR-01), loan terms (CR-02), or human review routing (CR-04).*<br>Artifact: `docs/regulatory-mapping.md` |

## 2. Detailed Scores, Anchors, and Evidence

### Rule-Based Expert System

| Criterion | Score | Met Anchor | Artifacts | Rationale |
|---|---|---|---|---|
| **Transparency** | **3** | Every decision lists the rules that fired and the facts they used, and the applicant-facing reasons are exactly the reason codes of those rules (tested on all of D1). | `tests/integration/test_phase3_api_and_audit.py`<br>`src/explain/notice.py` | Every decision generates an exact trace containing only fired rules, with adverse notices rendered verbatim from reason code definitions in rules/reason_codes.toml. |
| **Auditability** | **3** | A stored record per decision, a version for the logic used, and a replay that reproduces the decision and trace, with a mismatch reported when a parameter changes. | `tests/integration/test_phase3_api_and_audit.py`<br>`tests/golden/rule_set_pin.json`<br>`data/manifest.json` | Every decision is committed to an append-only SQLite audit log with input SHA-256 and ruleset hash, verifiable via byte-identical replay. |
| **Edge Cases** | **3** | No unexplained difference in any category; every missing-data and boundary case ends in a stated outcome. | `reports/edge_cases/summary.md`<br>`reports/edge_cases/results.csv` | Evaluated on 64 edge cases across 5 categories with 61 exact catalog matches, 3 explained FOIR-capacity interactions (OQ-012), and zero unexplained differences. |
| **Regulatory Defensibility** | **3** | All six rows met with evidence. | `docs/regulatory-mapping.md` | Fully satisfies requirements CR-01 to CR-06 with verifiable tests for specific reason notices, KFS summaries, consent enforcement, and human referral. |

### Logistic Regression

| Criterion | Score | Met Anchor | Artifacts | Rationale |
|---|---|---|---|---|
| **Transparency** | **2** | Each decision has an exact, per-decision explanation from the model's own arithmetic (the logistic regression's feature contributions), but the explanation is a score contribution, not a policy reason the applicant can act on. | `src/ml/baseline.py`<br>`reports/ml/metrics_d3_lr.json` | Linear feature contributions provide exact additive logit shifts per applicant, but output numerical score weights rather than actionable policy clauses. |
| **Auditability** | **2** | Versioned artifact and seed, and the numbers reproduce, but no per-decision record or replay. | `models/d3_lr.joblib`<br>`reports/ml/metrics_d3_lr.json` | Model training reproduces deterministically from derived seed with recorded dataset and split hashes, but lacks an append-only decision audit store and replay capability. |
| **Edge Cases** | **1** | An unexplained difference in the missing-data or boundary categories. | `reports/edge_cases/summary.md`<br>`reports/edge_cases/results.csv` | Silently imputes missing mandatory data with median training values without schema validation, and smoothly crosses policy thresholds without discrete bounds. |
| **Regulatory Defensibility** | **1** | Two or three rows partly met or gaps. | `docs/regulatory-mapping.md` | Meets CR-05 (model card) and CR-06 (bias testing), but leaves gaps on CR-01 (actionable specific adverse reasons), CR-02 (KFS offer terms), and CR-04 (human referral). |

### Gradient Boosting

| Criterion | Score | Met Anchor | Artifacts | Rationale |
|---|---|---|---|---|
| **Transparency** | **1** | Only a global explanation exists (permutation importance), not one per decision. | `reports/ml/metrics_d3_gb.json` | Provides global tree feature importances only; non-linear ensemble interactions lack exact closed-form per-decision explanations without complex local approximations. |
| **Auditability** | **2** | Versioned artifact and seed, and the numbers reproduce, but no per-decision record or replay. | `models/d3_gb.joblib`<br>`reports/ml/metrics_d3_gb.json` | Reproducible training pipeline from fixed seed and versioned split hashes, without individual decision tracing or replay store. |
| **Edge Cases** | **1** | An unexplained difference in the missing-data or boundary categories. | `reports/edge_cases/summary.md`<br>`reports/edge_cases/results.csv` | Imputes missing values without error flagging and produces continuous prediction manifolds across hard policy thresholds. |
| **Regulatory Defensibility** | **1** | Two or three rows partly met or gaps. | `docs/regulatory-mapping.md` | Meets CR-05 and CR-06, but cannot provide per-decision adverse reasons (CR-01), loan terms (CR-02), or human review routing (CR-04). |

## 3. Accuracy Context Table (Not a Score)

The following context metrics are drawn from Phase 4 artifacts (`reports/ml/`). D2 evaluation rests on only 776 rule approvals with overlapping confidence intervals, and D3 agreement is partly circular by construction; these metrics do not support a claim that either system is a better lender.

### D2 Dataset (Home Credit Mapped, Test Split N = 46,127)

| System / Operating Point | Test AUC | Approval Rate | Default Rate among Approved (95% CI) | Cost / Applicant (Ratio 5) |
|---|---|---|---|---|
| **Rule System (Treatment A)** | N/A (rules) | 1.68% (776) | 3.35% [2.14% - 4.70%] | 0.9058 |
| **Rule System (Treatment B)** | N/A (rules) | 1.84% (776) | 3.35% [2.12% - 4.67%] | 0.8993 |
| **Logistic Regression (Matched)** | 0.7248 | 1.56% (720) | 1.39% [0.56% - 2.42%] | 0.9050 |
| **Gradient Boosting (Matched)** | 0.7378 | 1.71% (787) | 1.27% [0.58% - 2.12%] | 0.9035 |

### D3 Dataset (Synthetic Population, Test Split N = 3,000)

| Model | Test AUC | Policy Agreement Rate (Threshold 0.5) | Note |
|---|---|---|---|
| **Logistic Regression** | 0.8852 | 80.97% | Linear approximation of non-linear rule boundaries |
| **Gradient Boosting** | 0.9902 | 98.53% | Captures non-linear thresholds with high fidelity |

## 4. Key Architectural Trade-Offs and Edge-Case Disagreements

- **Auditability & Traceability**: The rule system guarantees bit-level replayability via SHA-256 rule set pinning and append-only SQLite tracing. ML baselines lack decision-level replayability and explanation integrity.
- **Silent Imputation Vulnerability**: On missing mandatory fields (`EC-MD-01` to `EC-MD-06`), ML baselines silently impute values with sample medians, producing plausible scores without error notifications, violating CR-01 and CR-03.
- **Non-compensatory Enforcement**: Rule knockouts (`EC-RC-01`) enforce legal boundaries strictly regardless of applicant wealth; linear models allow extreme income to compensate for disqualifying credit history.

