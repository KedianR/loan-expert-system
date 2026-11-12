# Fairness Audit Plan (v1.0.0)

Requirements: FR-23, CR-06, DR-02. Decisions D-05, D-06 (Development Reference). Risks R-08, R-10, R-11. Settings: `config/fairness.toml`. Lean mode (Master Test Plan, "Lean mode") governs which tests are required.

**This plan is committed and pinned before any group result is seen.** The pin is the SHA-256 of this file and of `config/fairness.toml`, written to `reports/fairness/plan_pin.json` by `make fairness-pin`. After the pin, a change needs an entry in `docs/fairness-amendments.md` (what, why, date, and that no result had been viewed or that one had). An unlogged change is a Stop at the gate.

## 1. What this plan can and cannot show

Metrics describe how these two systems behave on this data. They do not prove fairness or unfairness. Limits that apply to every finding:

- D2 is Home Credit data mapped to this policy (ASM-D1 to D13). The rule system approves 1.68% of D2 test applicants (776 approvals) because of mapping effects (K04, K05, unknown delinquency). Group gaps in approval rates rest on very few approvals per group.
- Repayment is observed only for applicants the original lender approved (selection bias). Labels are noisy and reflect historical lending.
- D3 is synthetic. Its protected attributes are drawn independently of every other field, so with the bias switch off no group effect exists by construction. D3 results show the pipeline works and what the rules do to a population with no built-in group effect. They are not evidence about real people.
- Education, family status and occupation are in the protected store but are not analysed. Religion and caste do not exist in either dataset.
- Statistical flags are screening results. A flag asks for a policy review; it is not a finding of discrimination.

## 2. Decisions (P5-n; append to `docs/experiment-protocol.md` section 8)

| ID | Decision |
|---|---|
| P5-1 | Groups as in `config/fairness.toml`. D2 primary: gender, age band, region rating. D3 primary: gender, age band, region tier. Secondary on both: employment type and income band (quartiles of `monthly_net_income` fixed on the train split). One intersection: gender by age band, only cells of 100 or more |
| P5-2 | D2 group results use the test split only (N = 46,127). D3 headline uses the D3 test split. Validation rows are never used for a group result |
| P5-3 | Both refer treatments (A: refer is not approved; B: refer rows left out for both systems) are reported. A is the headline |
| P5-4 | Flag rule: per attribute, compare each group with the largest group; difference with a percentile bootstrap CI (1,000 resamples of applicants, derived seed `bootstrap`) at level 1 minus 0.05 divided by the number of non-reference groups. Flag only if the CI excludes 0. The four-fifths ratio below 0.80 is shown next to it as a screening signal and never flags on its own. The largest max-minus-min gap is reported descriptively and is never a test statistic |
| P5-5 | Groups under 100 are listed as too small and not scored (D-06). A group, or the reference group, with fewer than 20 approvals (for EOD, fewer than 20 approved repayers) is "unstable": its numbers are shown and it is not flagged (placeholder value) |
| P5-6 | Model metrics use the operating points chosen on validation in Phase 4: matched approval rate (headline) and cost-based (secondary). No per-group threshold, because that would use the protected attribute in a decision |
| P5-7 | D2 primary metric: equal opportunity difference = approval rate among applicants with `TARGET = 0` in the group minus the same rate in the reference group. D3 primary metric: selection-rate difference. `sim_default` is never used for a fairness finding |
| P5-8 | Rule-system calibration analogue: default rate among approved, by group, with a bootstrap CI. Model calibration: Brier score and mean score against observed default rate in 5 equal-count score bins (bins from the whole test split), by group |
| P5-9 | Counterfactual swap: replace the protected store with a shuffled copy and rerun 1,000 D3 rows through the engine and through both D3 models. Decisions must be identical (the rule engine by FR-20, the models because the feature list excludes protected columns). Also report how well a logistic regression on the D2 model features predicts gender (AUC on the test split), as a proxy signal. Report only |
| P5-10 | Mitigation options are listed in section 6. None is applied in this project. Applying one is a rule or model change and needs the catalog, a new hash and a new plan version |
| P5-11 | The pipeline test (section 5) runs on D3, all rows, rules only |
| P5-12 | The demo UI is a small separate app in `src/ui/` with static files, no framework, no new dependency, and no change to `src/api`, `src/engine`, `src/calc`, `src/explain` or `src/audit` (`docs/ui-spec.md`). It meets FR-25 (rule trace and ML score side by side). The reviewer page's ML block stays as Phase 4 left it |
| P5-13 | Edge cases run the rule system through the service function in process and the D3-trained models (logistic regression main, gradient boosting second); expected behavior is written from the Rule Catalog before the first run (`docs/edge-case-catalog.md`) |

## 3. Metrics

Per system (rule system; logistic regression; gradient boosting), per dataset, per primary group attribute, on the evaluated population:

| Metric | Definition | D2 | D3 |
|---|---|---|---|
| Group size | Applicants in the group | yes | yes |
| Selection rate | Approved / group size (rule system: `eligible`; model: score at the operating point; D3 model: predicted eligible at 0.5) | yes | **headline** |
| Selection-rate difference and ratio | Group minus reference; group divided by reference | screening | **headline** |
| Equal opportunity difference | Approval rate among `TARGET = 0`, group minus reference | **headline** | no |
| False-approval-rate difference | Approval rate among `TARGET = 1`, group minus reference | screening | no |
| Default rate among approved | `TARGET = 1` share among approved, with CI | screening | no |
| Calibration and Brier by group | Models only (P5-8) | screening | no |

Every metric has a 95% bootstrap CI (P5-4). The refer treatment is stated on every table.

**Metric conflict.** When base rates differ by group, equal opportunity, selection-rate parity and calibration cannot all hold. D-05 chose equal opportunity on D2 because it asks whether applicants who would repay are approved at the same rate. The report says so next to every table.

## 4. Outputs

`reports/fairness/<dataset>_<system>.json` and one Markdown table file per dataset, each listing group sizes first. `reports/fairness/plan_pin.json` holds the pin. A gap is written as "flag", "no flag", "unstable" or "too small", with the numbers.

## 5. Pipeline test (required)

1. **Planted bias.** `make data-d3-bias` generates D3 with `[bias] enabled = true` from `config/generator.toml` (gender F, income multiplied by 0.85) using the same seed, into separate files (`data/synthetic/d3_bias_population.csv` and its protected store). Run the engine over all rows. The pipeline must flag gender on selection-rate difference with F lower than M.
2. **No-bias control.** The normal D3 population (bias off, same seed). The pipeline must not flag gender on selection-rate difference.
3. **Hand check.** `tests/fixtures/fairness_hand_check.csv` has 12 rows. The test file contains, as literals with the working shown in comments, the hand-computed group sizes, selection rates, selection-rate difference and equal opportunity difference (no bootstrap involved). The pipeline's point estimates must equal them exactly.
4. If the bias is not flagged or the control is flagged: STOP. Do not change the planted shift, the alpha or the seed to get a pass.

The Fairlearn cross-check is not required in lean mode (stated as a limit).

## 6. Mitigation options (listed, not applied)

- **Rule system:** revise a rule or threshold with a written policy justification (for example, a floor or cap whose effect on one group cannot be justified by credit risk); each change needs the catalog row, a new rule-set hash and a rerun of this plan.
- **ML:** reweighting at training time; a single threshold change with the cost trade-off shown; constrained training. Per-group thresholds are not an option because they use the protected attribute in the decision.
- **Data:** a better-matched dataset or a mapping with fewer weak assumptions (the D2 limits are in docs/08-datasets.md).

## 7. Reporting rules

- Every statement of a finding cites a file in `reports/fairness/`.
- No group under 100 is reported as a finding.
- "Unstable" and "too small" are results, not omissions.
- The Phase 5/6 report restates the section 1 limits next to the first table.
