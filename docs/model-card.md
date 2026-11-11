# Model Card: ML Baseline (v0.1)

Requirement: CR-05 (model purpose, data, method, tests and approved use), CR-06 (bias testing, filled in Phase 5).
Every figure in this model card cites an output file under `reports/ml/` or `data/manifest.json`.

---

## 1. Model details

- **Models**:
  1. Logistic Regression (`LogisticRegression`, L2 penalty, C=1.0, solver=`lbfgs`, max_iter=1000, class_weight=`balanced`).
  2. Gradient Boosting (`HistGradientBoostingClassifier`, max_iter=200, learning_rate=0.1, max_leaf_nodes=31, min_samples_leaf=20, l2_regularization=0.0, early_stopping=false, class_weight=`balanced`).
- **Code**: `src/ml/baseline.py`, `src/ml/features.py`. Configuration read from `config/ml.toml` and `config/experiment.toml`.
- **Date trained**: 2026-11-12
- **Seeds**:
  - `seed("ml_lr")`: `192429597` (derived from master seed `20261108` via SHA-256)
  - `seed("ml_gb")`: `1870778323` (derived from master seed `20261108` via SHA-256)
- **Library versions** (from `reports/ml/metrics_d2_lr.json`):
  - Python: `3.14.2`
  - pandas: `3.1.1`
  - numpy: `2.5.4`
  - scikit-learn: `1.9.1`
  - joblib: `1.6.0`

---

## 2. Intended use

Comparison baseline for the rule-based loan eligibility system, on synthetic and public data, for an academic prototype project. It never feeds, changes or overrides a decision. The reviewer page displays its score beside the rule trace labelled *"This score does not feed the decision."*

---

## 3. Out of scope

Real lending, real applicants, any real-world credit underwriting, any automated adverse action about a person, any use as a calibrated probability, or any empirical claim about credit risk in commercial banking.

---

## 4. Data

Two datasets are used (`data/manifest.json`):

1. **D2 (Home Credit Default Risk)**:
   - **Source**: Kaggle competition dataset `home-credit-default-risk`.
   - **Licence & terms**: Coursework and non-commercial research use permitted per `docs/datasheets/home-credit-terms.md`.
   - **Row count**: 307,511 applicants (`data/mapped/d2_mapped.csv`, SHA-256: `44de1b821cd3c4831b485b39435998e53c3f10754c7a069046bbca0f0ca6eae4`).
   - **Label**: `TARGET` binary default indicator (1 = default / payment difficulty, 0 = repaid).
   - **Class balance** (`reports/ml/metrics_d2_lr.json`): 8.07% positive across all splits.
     - Train (70%): 215,257 rows (17,377 positive, 8.07%).
     - Validation (15%): 46,127 rows (3,724 positive, 8.07%).
     - Test (15%): 46,127 rows (3,724 positive, 8.07%).
     - Split file SHA-256 (`data/splits/d2_split.csv`): `b4d17251eb41042137be01ea4e2363fae78b206ccedc2d87bcc6b89a95e19f47`.
   - **Known limits**: Selection bias (outcomes only observed for applicants previously approved by Home Credit); amounts are in original currency and not rescaled to INR; assumptions ASM-D1 to ASM-D13 applied (e.g., 65.0% of rows rely on fallback obligations ASM-D4; 70.0% have severe delinquency unknown ASM-D7).

2. **D3 (Synthetic Population)**:
   - **Source**: Deterministic synthetic generator (`data/synthetic/d3_generator.py`).
   - **Row count**: 20,000 applicants (`data/synthetic/d3_population.csv`, SHA-256: `2311690bfaf45d7e944f5e572bdd50d0f5a768494480d54d78a88b1b8ed619ef`).
   - **Label**: Primary label is rule-engine decision (`eligible` = 1, `ineligible` / `refer` = 0). Secondary label is `sim_default`.
   - **Class balance** (`reports/ml/metrics_d3_lr.json`): 47.2% eligible across all splits.
     - Train (70%): 14,000 rows (6,614 eligible, 47.24%).
     - Validation (15%): 3,000 rows (1,418 eligible, 47.27%).
     - Test (15%): 3,000 rows (1,417 eligible, 47.23%).
     - Split file SHA-256 (`data/splits/d3_split.csv`): `6f3b92f0ff0fa837e335eb779eadcb47253c108954d007bab8ae2446d0c08c6e`.
   - **Known limits**: Circularity of the policy label (trained to imitate the rule engine); synthetic distributions do not represent a real population.

---

## 5. Features

Feature set defined in `config/ml.toml` and verified in `reports/ml/feature_list.json`:

- **Numeric (7)**: `employment_months`, `monthly_net_income`, `monthly_obligations`, `credit_score`, `enquiries_6m`, `requested_amount`, `requested_tenure_months`.
- **Categorical (2)**: `employment_type`, `obligations_source`.
- **Tri-state (2)**: `severe_delinquency_36m`, `written_off` (encoded as `true`, `false`, `unknown`).
- **Derived (3)**: `existing_foir`, `amount_to_annual_income`, `instalment_to_income` (computed directly without importing engine modules).
- **Missing indicators (10)**: Indicator added for all 7 numeric features and 3 derived ratios prior to median imputation.

### Excluded Attributes
- **Protected attributes**: `CODE_GENDER`, `NAME_EDUCATION_TYPE`, `NAME_FAMILY_STATUS`, caste, religion, age band (isolated strictly to protected store).
- **Policy facts excluded**: `age` (excluded per P4-4), `kyc_verified`, `consent_given` (constant booleans), `region_tier`, `applicant_id`.
- **Raw Kaggle columns excluded**: All 105 unused raw columns including `OCCUPATION_TYPE` and `REGION_RATING_CLIENT`.

### Proxy Review (`config/ml.toml [proxy_review]`)
`monthly_net_income` and `employment_type` are included in the baseline feature set. It must be noted plainly that both can act as partial statistical proxies for socio-demographic status. Geographic rating, education type, marital status, and detailed occupation are strictly excluded by design.

---

## 6. Training procedure

- **Pipeline**: Scikit-learn Pipeline with custom missingness indicator transformer, `SimpleImputer(strategy='median')`, `StandardScaler` (for Logistic Regression), and `OneHotEncoder(handle_unknown='ignore', drop=None)` for categorical and tri-state features.
- **Data split**: 70% Train, 15% Validation, 15% Test. Fitted exclusively on Train split.
- **Operating points**: Tuned strictly on Validation split:
  1. *Matched approval rate*: Threshold chosen such that model approval rate on Validation matches the rule-engine approval rate.
  2. *Cost-based threshold*: Selected on Validation to minimize expected cost per applicant at primary cost ratio $C_{FN}/C_{FP} = 5$ ($C_{FN}=5$, $C_{FP}=1$).
- **Test evaluation**: Evaluated exactly once on the held-out Test split. No hyperparameters tuned on Test.

---

## 7. Performance

All metrics cited from `reports/ml/`.

### 7.1 D2 Dataset (Home Credit Default Risk, Test Split $N = 46,127$)

| System / Model | Operating Point / Threshold | Approval Rate | Default Rate among Approved | Precision | Recall | F1 | Cost/App ($c=3$) | Cost/App ($c=5$) | Cost/App ($c=10$) | AUC | Brier Score |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Logistic Regression** (`reports/ml/metrics_d2_lr.json`) | Matched ($\tau = 0.1479$) | 1.56% | 1.39% | 0.0818 | 0.9973 | 0.1512 | 0.9045 | 0.9050 | 0.9060 | 0.7248 | 0.2105 |
| **Logistic Regression** (`reports/ml/metrics_d2_lr.json`) | Cost-based ($\tau = 0.6684$) | 87.60% | 6.06% | 0.2227 | 0.3421 | 0.2698 | 0.2558 | 0.3620 | 0.6276 | 0.7248 | 0.2105 |
| **HistGradientBoosting** (`reports/ml/metrics_d2_gb.json`) | Matched ($\tau = 0.0680$) | 1.71% | 1.27% | 0.0819 | 0.9973 | 0.1514 | 0.9031 | 0.9035 | 0.9046 | 0.7378 | 0.1951 |
| **HistGradientBoosting** (`reports/ml/metrics_d2_gb.json`) | Cost-based ($\tau = 0.6889$) | 89.12% | 6.11% | 0.2420 | 0.3260 | 0.2778 | 0.2457 | 0.3545 | 0.6266 | 0.7378 | 0.1951 |
| **Rule System (Treatment A)** | Policy (refer = denied) | 1.68% | 3.35% | 0.0815 | 0.9930 | 0.1507 | 0.9047 | 0.9058 | 0.9086 | — | — |
| **Rule System (Treatment B)** | Policy (refer excluded) | 1.84% | 3.35% | 0.0870 | 0.9928 | 0.1599 | 0.8981 | 0.8993 | 0.9024 | — | — |

*Calibration warning*: Model probability estimates are uncalibrated (Brier score ~0.20 on D2). Scores must not be interpreted as posterior default probabilities.

### 7.2 D3 Dataset (Synthetic Policy Imitation, Test Split $N = 3,000$)

| Model | Operating Point ($\tau=0.5$) | Agreement with Policy | Precision | Recall | F1 | Test AUC | Brier Score |
|---|---|---|---|---|---|---|---|
| **Logistic Regression** (`reports/ml/metrics_d3_lr.json`) | 0.50 | 80.97% | 0.7768 | 0.8377 | 0.8061 | 0.8852 | 0.1346 |
| **HistGradientBoosting** (`reports/ml/metrics_d3_gb.json`) | 0.50 | 98.53% | 0.9744 | 0.9951 | 0.9846 | 0.9902 | 0.0134 |

*Note*: HistGradientBoosting imitates the expert system policy rules with 98.5% agreement and 0.990 AUC. Logistic regression captures linear trends with 81.0% agreement and 0.885 AUC.

---

## 8. Explanations

- **Logistic Regression**: Exact linear feature contributions $w_i \cdot x_i$ computed via dot product between model coefficients and scaled input vectors. Sample linear attributions are logged in `reports/ml/metrics_d3_lr.json` and `reports/ml/metrics_d2_lr.json`.
- **Gradient Boosting**: Permutation importance / tree attributions.
- **Reason codes from attributions**: `TODO Phase 5` (faithfulness evaluation against expert system rule reason codes).

---

## 9. Fairness

`TODO Phase 5`. Phase 4 computes group-size tables only (`data/group_sizes/d2_group_sizes.csv` and `data/group_sizes/d3_group_sizes.csv`). In compliance with AGENTS.md, zero outcome metrics by protected group are computed in Phase 4.

---

## 10. Limits and cautions

- **Fallback obligations**: 65.0% of D2 applicants (199,824 of 307,511) lack bureau active records or annuities and rely on the Beta fallback distribution (ASM-D4).
- **Referrals from unknown facts**: In D2 test split, 4,055 applicants receive a `refer` decision under policy rules primarily due to missing bureau data (`severe_delinquency_36m` unknown in 70.0% of rows; `written_off` unknown in 14.3%).
- **Policy range constraints**: 190,865 D2 rows fall below the policy monthly income floor (K05, ₹25,000); 34,671 fail requested tenure bounds (V04).
- **Selection bias**: Repayment data in D2 exists only for previously approved applicants; true default rates on rejected populations are unobserved.

---

## 11. Reproducibility

- **Pipeline commands**:
  - `make data-d2`: Maps raw Home Credit tables to `data/mapped/d2_mapped.csv` and `data/protected/d2_protected.csv`.
  - `make data-d3`: Generates synthetic population `data/synthetic/d3_population.csv` and `data/protected/d3_protected.csv`.
  - `make decide-d3`: Generates batch decisions for all 20,000 D3 rows.
  - `make split`: Generates stratified 70/15/15 splits for D2 and D3.
  - `make decide-d2`: Generates batch decisions for D2 validation and test splits (92,254 rows).
  - `make baseline`: Fits LR and GB models, determines validation thresholds, and computes test metrics.
  - `make phase4`: Runs all above targets in order and validates integrity.
- **Artifact tracking**: Output datasets under `data/mapped/`, `data/protected/`, `data/splits/`, `data/decisions/`, `data/synthetic/d3_*`, and `models/` are gitignored. Manifest hashes (`data/manifest.json`) and metrics files (`reports/ml/`) are tracked.

---

## 12. Change log

- **2026-11-12**: Initial Model Card created for Phase 4.
  - Added D2 and D3 baseline results for Logistic Regression and HistGradientBoosting.
  - Documented Step 0 raw column verification and terms confirmation.
  - Recorded OQ-010 regarding reviewer page ML block preservation to ensure Phase 3 regression test stability.
  - Section 9 marked as `TODO Phase 5` per AGENTS.md lean mode guidelines.
