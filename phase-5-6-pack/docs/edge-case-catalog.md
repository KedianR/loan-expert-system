# Edge Case Catalog (v1.0)

Requirements: FR-24, NFR-01. Test Plan section 6, "Edge-case suite". Lean mode: the suite runs on both systems and records outputs side by side; it is not a loader test suite.

## 1. How the suite works

- Cases are fact records in the input schema's field names (INR, the 14 input fields). Case values that depend on a policy number are **derived at run time from `params/params.toml` and `rules/`**, never typed. A case that needs a number the catalog or parameters do not give is a Stop (invented policy value).
- The rule system is run through the same service function the API calls, in process, with the audit store pointed at a temporary file. Record decision, reason codes, recommended amount, band, the first line of the notice and whether a trace exists.
- The ML side is the D3-trained models (logistic regression is the main one, gradient boosting second), run through the same fact-to-feature path as training. Record the score, the label at the D3 operating point (eligible at 0.5), and for the logistic regression the top three contributions. ML cannot return REFER, so a REFER is compared with "not eligible".
- Output: `reports/edge_cases/results.csv` (one row per case, both systems side by side) and `reports/edge_cases/summary.md`.
- Write the expected behavior for each case from the Rule Catalog **before** running it, in `reports/edge_cases/expected.csv`. If the engine differs from the catalog, do not change the engine. Log it in `docs/open-questions.md`, mark the row, and report it. Each ML disagreement with the rules gets one line of explanation.
- Case IDs: `EC-<category>-<nn>`. A categorised count of "matched expected", "differs, explained", "differs, unexplained" feeds the Edge cases criterion in `docs/comparison-methodology.md`.

## 2. Categories and cases

| Category | Cases (build each from a base applicant who is ELIGIBLE in the golden set, changing one thing) | What to record |
|---|---|---|
| **MD** Missing or contradictory data | MD-01 income missing. MD-02 credit score null. MD-03 income zero. MD-04 obligations greater than income. MD-05 employment months missing. MD-06 requested amount missing. MD-07 consent false. MD-08 KYC false. MD-09 a field with the wrong type (rule system only; the model has no schema check, say so) | Decision, reason codes, whether the notice says what was missing, ML output |
| **TB** Threshold boundaries | For every numeric threshold that appears in `params/params.toml` or a rule file: one case below, one at and one above, built from the parameter value by the generator. Include the age check (17, 18), the product minimum and maximum amount, the amount step, the minimum and maximum tenure, and the request of 777,777 | Decision flips exactly where the catalog says. For the model: score and label at the same three points (a smooth model has no threshold, record where it flips if it does) |
| **TF** Thin file or new to credit | TF-01 no credit score. TF-02 shortest allowed employment history. TF-03 no score and short employment. TF-04 first-time borrower with obligations zero | Rules should refer or deny with a stated reason; model score and confidence (score distance from 0.5) |
| **RC** Rare combinations | RC-01 income far above the median with a score at the knock-out edge. RC-02 self-employed with a score at the top of the range. RC-03 maximum amount at the maximum tenure with income at the minimum. RC-04 salaried, tenure at the minimum and a large requested amount | Whether either system gives an unexplained result |
| **AD** Adversarial or gamed inputs | AD-01 income inflated by 25% over the base. AD-02 obligations set to the largest value that still clears the FOIR cap (derived). AD-03 amount set to the engine's maximum offer, then to one amount step above. AD-04 tenure set to the limit that gives the lowest EMI. AD-05 two near-identical applicants differing by one rupee of income | Whether the outcome shifts sharply, whether it is flagged, whether near-identical applicants get the same top reasons |

## 3. Counts and gaps

The case count follows from the parameters (the TB category alone is three per threshold). Report the total per category. Cases that cannot be built because a field or parameter does not exist are listed as "not applicable" with the reason.

## 4. Out of scope (lean mode)

Loader edge cases, sensitivity checks on weak mappings, running the oracle on the whole suite (running it on this suite is allowed if cheap), explanation-stability statistics beyond AD-05, and SHAP faithfulness.
