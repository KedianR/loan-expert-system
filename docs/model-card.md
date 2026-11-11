# Model Card: ML Baseline (outline, v0.1)

Requirement: CR-05 (model purpose, data, method, tests and approved use), CR-06 (bias testing, filled in Phase 5). The agent fills each section that Phase 4 can answer from its own outputs and leaves the others as `TODO Phase 5`. Do not invent a figure. Every number cites a file under `reports/ml/`.

## 1. Model details
Two models, logistic regression and gradient boosting. Library versions, hyperparameters (from `config/ml.toml`), seeds and the date trained. Name of the code that trains them.

## 2. Intended use
Comparison baseline for the rule-based loan eligibility system, on synthetic and public data, for an academic project. It never feeds, changes or overrides a decision. The reviewer page shows its score beside the rule trace, labelled "This score does not feed the decision."

## 3. Out of scope
Real lending, real applicants, any decision about a person, any use as a calibrated probability, any claim about lending in general.

## 4. Data
D2 (mapped Home Credit Default Risk) and D3 (synthetic population). For each: source, licence and terms (from `docs/datasheets/home-credit-terms.md`), row counts, label definition, class balance, split sizes and hashes, and the known limits: assumptions ASM-D1 to ASM-D13 with the share of rows affected, selection bias (repayment is seen only for approved applicants), amounts not rescaled to INR, and the circularity of the D3 policy label.

## 5. Features
The feature list actually used, from `reports/ml/feature_list.json`. The excluded list with reasons. The proxy review: `employment_type` and `monthly_net_income` are in; region rating, education, family status and occupation are out. Say plainly that `monthly_net_income` and `employment_type` can act as proxies.

## 6. Training procedure
Splits, preprocessing, class weighting, fixed hyperparameters, no tuning, the test split used once.

## 7. Performance
Tables from the metrics files for D2 and D3: AUC, approval rate, default rate among approved at the matched approval rate and at the cost-based point, precision, recall, F1, cost per applicant at each ratio, Brier score and the reliability table. The rule system's figures beside them under refer treatments A and B. State that the score is not a calibrated probability.

## 8. Explanations
Exact linear contributions for the logistic regression; permutation importance for gradient boosting. Reason codes from attributions and their faithfulness: `TODO Phase 5`.

## 9. Fairness
`TODO Phase 5`. Phase 4 reports group sizes only.

## 10. Limits and cautions
What the figures do not show. Weak mappings (ASM-D4, ASM-D5, ASM-D11). The share of D2 rows with a fallback obligation and the share that end as `refer` because of unknown facts. Rows that fail the amount, tenure or minimum-income rules.

## 11. Reproducibility
The commands, the seeds, the manifest hashes, and what is and is not committed.

## 12. Change log
Date, change, reason. Phase 4 amendments are copied here from `docs/open-questions.md`.
