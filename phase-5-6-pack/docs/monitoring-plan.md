# Monitoring Plan (v1.0, prototype scope)

Requirements: CR-04, CR-06, NFR-03. Lean mode: this is a plan, plus one cheap check. The prototype has no production traffic, so monitoring means what a deployer should watch and what this repository can already show.

## 1. What a deployer would monitor

| Signal | Why | How (prototype: documented only) |
|---|---|---|
| Applicant mix drift | The rules and the model were checked on one population | Compare monthly distributions of age band, employment type, income band and requested amount with the evaluation population |
| Decision mix | A parameter or data change shows up first here | Share of ELIGIBLE, INELIGIBLE and REFER, and the reason-code frequency table (the same table Phase 4 produces) |
| REFER share and unknown-fact share | In D2 a large share of refers came from unknown facts | Track V01 and R01 counts |
| Reviewer override rate and reasons | Overrides show where rules and people disagree | Count overrides by rule and reason; the audit log has them |
| Fairness re-check | Group gaps can appear when the mix changes | Rerun `make fairness` on a recent decision sample on a schedule, and after any rule or parameter change |
| Rule-set and parameter version | Any change needs a new hash | The rule-set tag and hash in every audit record (FR-15) |
| Model drift | The ML baseline is not used for decisions | Rerun `make baseline` on new labelled data; compare AUC and calibration |

## 2. What this repository provides now (WP-21)

- `make reproduce` regenerates every reported number and compares it with the committed values.
- `reports/ml/`, `reports/fairness/`, `reports/comparison/` and `reports/edge_cases/` are the baseline to compare against.
- One cheap check: `make monitor-sample` prints the decision mix and reason-code table for `data/decisions/d3_decisions.csv`. If it takes more than a few lines of code, skip it and say so.

## 3. Limits

No thresholds for alerts are set, because no real traffic or risk appetite exists. Setting them is a deployment decision.
