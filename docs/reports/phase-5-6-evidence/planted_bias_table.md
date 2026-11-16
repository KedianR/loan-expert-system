# Planted-Bias and Control Evaluation (P5 §5, P5-11, Amendment A-02)

Evaluation of disparate impact detection under the pre-registered pipeline (`selection_rate_difference`, reference group M, evaluated group F, family-wise $\alpha = 0.05$ with Percentile bootstrap CIs (P5-4)).

## Four-Cell Power and Sensitivity Matrix

| Evaluation Run | Population Size ($N$) | Point Estimate (Diff F - M) | 95% Bootstrap CI | Flagged? | Power & Methodology Finding |
|---|---|---|---|---|---|
| **Standard Planted Bias** (Pre-registered) | 20,000 | -0.0151 | [-0.0286, -0.0013] | **Flagged (🚩)** | Detected at standard size (marginally: upper bound -0.0013, close to zero). Confirms the pre-registered audit pipeline flags the shift without parameter modifications. |
| **Standard Control** (Pre-registered) | 20,000 | +0.0031 | [-0.0100, +0.0168] | **Not Flagged** | Confirms low false-positive risk under standard sample size, correctly showing zero significant demographic disparity in uncorrupted synthetic data. |
| **Supplementary 100k Planted** (Amendment A-02) | 100,000 | -0.0186 | [-0.0247, -0.0127] | **Flagged (🚩)** | Clearly detected at 100,000 with confidence intervals tightening by ~50%, confirming stable point estimation under the large-sample regime. |
| **Supplementary 100k Control** (Amendment A-02) | 100,000 | +0.0012 | [-0.0049, +0.0071] | **Not Flagged** | Confirms that even with high sample size capable of detecting minute effects, the control process does not produce false-positive flagging when underlying bias is absent. |

## Notes on Audit Protocol
1. **Pre-registered Specification**: In accordance with P5-11, planted bias runs against the full standard D3 population with fixed master seed and rules only. The control run uses the unshifted D3 population.
2. **Empirical Verification**: The standard-size planted bias is flagged without requiring modifications to shift parameters, alpha, seed, or population size.
3. **Amendment A-02**: The 100,000-row supplementary pair is recorded in `docs/fairness-amendments.md` as an asymptotic power check.
4. **Mechanism of Effect**: A 15% income reduction for female applicants shifts the selection rate by roughly 1.5 to 1.9 percentage points (point estimates -0.0151 and -0.0186). This occurs because income operates through affordability rules (FOIR, disposable income, income floors) that affect only marginal applicants near threshold boundaries, rather than the entire population.


