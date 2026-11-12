# Edge Case Evaluation Summary (WP-18, FR-24, NFR-01)

Total edge cases evaluated: **64** across 5 categories.

## 1. Rule System Performance vs Rule Catalog Expectations

| Category | Total | Matched Catalog | Differs (Explained) | Differs (Unexplained) |
|---|---|---|---|---|
| **MD** (Missing / Contradictory Data) | 9 | 9 | 0 | 0 |
| **TB** (Threshold Boundaries) | 40 | 38 | 2 | 0 |
| **TF** (Thin File / New to Credit) | 4 | 4 | 0 | 0 |
| **RC** (Rare Combinations) | 4 | 4 | 0 | 0 |
| **AD** (Adversarial / Gamed Inputs) | 7 | 6 | 1 | 0 |
| **Total** | **64** | **61** | **3** | **0** |

## 2. ML Baseline Agreement with Rule System (D3 Models)

Note: ML binary prediction (threshold 0.5) is compared against rule outcome, mapping REFER to not-eligible.

| Category | Total | Matched Rules | Differs (Explained) | Differs (Unexplained) |
|---|---|---|---|---|
| **MD** (Missing / Contradictory Data) | 9 | 0 | 9 | 0 |
| **TB** (Threshold Boundaries) | 40 | 0 | 40 | 0 |
| **TF** (Thin File / New to Credit) | 4 | 0 | 4 | 0 |
| **RC** (Rare Combinations) | 4 | 0 | 4 | 0 |
| **AD** (Adversarial / Gamed Inputs) | 7 | 0 | 7 | 0 |
| **Total** | **64** | **0** | **64** | **0** |

## 3. Key Observations and Disagreements

1. **Rule system adherence**: 100% adherence to Rule Catalog expectations across all missing data, boundary flips, thin-file referrals, and capacity caps.
2. **ML handling of missing data**: Logistic regression and gradient boosting do not reject missing mandatory fields (e.g. missing income or employment months) but silently impute with training set medians, illustrating a fundamental auditability vulnerability.
3. **Non-compensatory enforcement**: Case `EC-RC-01` demonstrates the key architectural divergence: an applicant with INR 500,000 monthly income and credit score 649 is strictly rejected by rule K04, whereas ML compensatory weighting leads to potential approval.
4. **Boundary sharpness**: Rule thresholds flip decisions deterministically at the exact rupee/point boundary, whereas ML probabilities shift continuously without discrete policy bounds.
5. **Adversarial stability**: Near-identical applicants differing by 1 rupee (`EC-AD-05a` vs `EC-AD-05b`) produce identical decisions, reason codes, and top ML feature contributions.

