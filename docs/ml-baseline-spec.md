# ML Baseline Specification (v0.1)

Requirements: FR-21, DR-02, DR-04, CR-05, CR-06. Decisions D-05 and D-06 (Development Reference). Risks R-08, R-09. Lean mode (Master Test Plan, "Lean mode") governs which tests are required. Settings are in `config/ml.toml` and `config/experiment.toml`; this file explains them.

The ML baseline exists only to compare with the rule system. It never feeds, changes or overrides a decision. It is deliberately simple, so the comparison is about transparency and defensibility and not about model tuning.

## 1. Datasets and labels

| Dataset | Label | Positive class | What the experiment tests |
|---|---|---|---|
| D2 (mapped Home Credit) | `TARGET` | 1 = payment difficulty (call it "default" in reports) | Outcome experiment: do the rules and the model pick borrowers who repay? |
| D3 (synthetic population) | engine decision (decision P4-2) | `eligible` versus not (`ineligible` and `refer` are both "not eligible" for the model; the three-way label is kept for analysis) | Policy experiment: can a model imitate the rules, and where does it disagree? Partly circular by design; say so. |
| D3 simulated outcome | `sim_default` | 1 = simulated default | Pipeline check only: the same code runs on a dataset with an outcome label. Never reported as evidence. |
| D1 | none | none | Not used for ML. |

D2 results describe this policy on this mapped data, not lending in general. Repayment is observed only for applicants the lender approved, so selection bias applies.

## 2. Splits

70% train, 15% validation, 15% test, stratified on the binary label, one seed per dataset (`split_d2`, `split_d3`, derived as in `docs/experiment-protocol.md` section 1). Split by applicant; no applicant is in two splits. Save the split file (`applicant_id`, `split`) and record its SHA-256. Every model and the rule system use the same file.

- All preprocessing is fitted on the train split only.
- The validation split is for choosing an operating point (section 6). It is not used to tune hyperparameters in Phase 4: they are fixed in `config/ml.toml`.
- The test split is used once, at the end, to compute reported metrics. It is never used to fit, tune, choose a threshold or choose a model.

## 3. Features

**Allowed:** the mapped facts and ratios listed in `config/ml.toml` section `[features]`.

| Group | Features |
|---|---|
| Numeric facts | `employment_months`, `monthly_net_income`, `monthly_obligations`, `credit_score`, `enquiries_6m`, `requested_amount`, `requested_tenure_months` |
| Categorical | `employment_type`, `obligations_source` (the flag from the mapping: `bureau`, `bureau_partial`, `bureau_zero`, `fallback_no_bureau`, `fallback_missing_annuity`; for D3 always `synthetic`) |
| Three-state | `severe_delinquency_36m`, `written_off` (true, false, unknown) |
| Ratios | `existing_foir` = obligations / income; `amount_to_annual_income` = requested amount / (12 x income); `instalment_to_income` = (requested amount / requested tenure) / income. Interest is ignored, as in the tenure mapping |
| Missing indicators | One per numeric feature and per ratio, added by the imputer. Missingness is informative here (doc 08, section 5) |

**Excluded, and why:**

| Excluded | Reason |
|---|---|
| Every protected attribute, and any column listed in `docs/decision-tables.md` section 6 | DR-02, R-08 |
| `age` | It is the source of the age-band fairness group, and the rules use it only for the 18-and-over check (decision P4-4). A with-age run is a Phase 5 option, not a Phase 4 task |
| `kyc_verified`, `consent_given` | Constant true in the mapped data (ASM-D9); no information |
| `region_tier` | Used only by experimental rule X02, which is off |
| `REGION_RATING_CLIENT`, education, family status, occupation | Proxy candidates; they stay in the protected store or unused (`config/ml.toml` `[proxy_review]`) |
| `EXT_SOURCE_1`, `EXT_SOURCE_2`, `EXT_SOURCE_3` | The model sees the same mapped `credit_score` the rules see, so the comparison is like for like (R-09). Using the raw scores would give the model information the rules do not have |
| Identifiers (`applicant_id`, `SK_ID_CURR`) | Not predictive and would allow memorising |
| Labels and anything derived from one (`TARGET`, `policy_decision`, `policy_eligible`, `sim_default`) | Leakage |

**Proxy review.** `employment_type` and `monthly_net_income` are in the feature list and can stand in for gender or age. They are listed in the model card and reported in Phase 5. Phase 4 does not run a no-proxy variant.

## 4. Preprocessing

One scikit-learn pipeline per model, fitted on the train split only: median imputation with missing indicators for numeric features and ratios; one-hot encoding for categorical and three-state features; standard scaling for the logistic regression only. Imbalance is handled once, with balanced class weights. Record the class balance (counts and share of the positive class) in each metrics file. A test confirms the pipeline accepts a row with unknown values.

## 5. Models

Two models, both with fixed hyperparameters from `config/ml.toml` and a seed derived from the master seed (`model_lr`, `model_gb`):

1. Logistic regression, the transparent reference.
2. Gradient boosting (`HistGradientBoostingClassifier`), for contrast.

No decision tree, no third model, no hyperparameter search (lean mode). Each is trained on D2 and on D3. A logistic regression is also trained once on the D3 simulated outcome as a pipeline check. That makes five metrics files.

If scikit-learn or pandas has no wheel for the project's Python version, STOP and ask. Do not change the Python version and do not substitute another library.

## 6. Scores, operating points and approvals

The model score is the predicted probability of the positive class under balanced class weights. It is a ranking score, not a calibrated probability, and every report and the reviewer page say so.

**D2 approval.** The model approves when its predicted default probability is at or below a threshold. Two operating points, both chosen on the **validation** split and applied unchanged to the test split:

- **Matched approval rate.** The threshold at which the model's approval share on validation equals the rule system's approval share on validation. This is the like-for-like comparison.
- **Cost-based.** The threshold that minimises cost on validation, where cost = (ratio x false approvals) + false denials, with the primary ratio from `config/experiment.toml` `[cost]`. A false approval is approved with `TARGET = 1`; a false denial is denied with `TARGET = 0`. The test-split cost is also reported at the other ratios.

**Rule system approval.** `eligible` is an approval, `ineligible` a denial. `refer` has no ML equivalent and is handled in two ways, both reported (docs/08, section 5):

- Treatment A: `refer` counts as not approved.
- Treatment B: `refer` rows are left out of the population for both systems.

**D3.** The model predicts `eligible` at probability 0.5. Report agreement with the engine, and the disagreements by the true three-way class.

## 7. Metrics

Per model and dataset, on validation and on test:

- AUC (threshold-free, ML only).
- At each operating point: approval rate, default rate among approved, precision, recall and F1 for the positive class (predicted positive = not approved), confusion counts, cost per applicant at each ratio.
- Calibration: Brier score and a 10-bin reliability table (mean score against observed rate). Report it as is; class weighting distorts it, and say so.
- Class balance and row counts.
- The rule system gets the same operating-point metrics from its decisions, under both refer treatments, on the same test applicants.

**Not in Phase 4:** any metric by protected group. Only the group-size table is built (`docs/experiment-protocol.md` section 5). The fairness plan is committed in Phase 5 before any group result is seen.

## 8. Explanations

For the logistic regression, the contribution of each feature to one applicant's score is the coefficient times the standardised value minus the train mean of that standardised feature, summed over a feature's encoded columns. This is exact for a linear model and equals the SHAP value of a linear model with independent features. The reviewer page shows the score and the top three contributions. No SHAP package is required. For gradient boosting, report global permutation importance on the validation split. Install `shap` only if it installs cleanly on the project's Python; if it does not, say so in the report and the model card. Reason codes from attributions and their faithfulness test are Phase 5 work.

## 9. Outputs

| File | Content |
|---|---|
| `reports/ml/metrics_<dataset>_<model>.json` | Metrics, seed, split-file hash, dataset hash, feature list, library versions, class balance, operating points. Committed. Five files |
| `models/<dataset>_<model>.joblib` | Fitted pipeline. Not committed |
| `data/splits/<dataset>_split.csv` | Split assignment. Not committed; hash in the manifest |
| `data/manifest.json` | Hashes of the raw files, mapped D2, D3, split files, rule-set hash and params hash. Committed |
| `reports/ml/feature_list.json` | The feature list actually used by each model |

`make baseline` rebuilds the metrics from the saved splits and the same seed and reproduces them exactly on the same machine.

## 10. Required tests (lean mode)

- Feature-list test: no protected attribute, no identifier and no label-derived column is a feature; every feature is in `config/ml.toml`.
- Same split for every model and for the rule system; the test split is never used for fitting or tuning. Method: shuffle the test labels and refit; the fitted coefficients or trees must be identical.
- Two models with a metrics file and a seed each, for D2 and for D3.
- The protected store is read by nothing under `src/` except the mapping and generator modules that write it (static scan for the column names).
- Tests use small synthetic fixtures with the right column names. They never need `data/raw/`.

## 11. Stop and ask

A feature in the list is protected, an identifier or label-derived; the test split was touched before the metrics step; a group-level outcome metric is wanted; a library will not install; the metrics differ between two runs with the same seed.
