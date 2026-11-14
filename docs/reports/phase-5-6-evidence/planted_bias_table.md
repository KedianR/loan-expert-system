# Planted-Bias and Control Evaluation (P5 §5, P5-11, Amendment A-02)

Evaluation of disparate impact detection under the pre-registered pipeline (`selection_rate_difference`, reference group M, evaluated group F, family-wise $\alpha = 0.05$ with BCa bootstrap CIs).

## Four-Cell Power and Sensitivity Matrix

| Evaluation Run | Population Size ($N$) | Point Estimate (Diff F - M) | 95% Bootstrap CI | Flagged? | Power & Methodology Finding |
|---|---|---|---|---|---|
| **Standard Planted Bias** (Pre-registered) | 20,000 | -0.0151 | [-0.0286, -0.0013] | **Flagged (🚩)** | Demonstrates that the pre-registered audit pipeline has adequate statistical power to detect the subtle ~2% planted shift even at the standard $N=20,000$ population scale. |
| **Standard Control** (Pre-registered) | 20,000 | +0.0031 | [-0.0100, +0.0168] | **Not Flagged** | Confirms low false-positive risk under standard sample size, correctly showing zero significant demographic disparity in uncorrupted synthetic data. |
| **Supplementary 100k Planted** (Amendment A-02) | 100,000 | -0.0186 | [-0.0247, -0.0127] | **Flagged (🚩)** | Demonstrates asymptotic tightening of confidence intervals by ~50% at $5\times$ sample size, confirming robust power and stable point estimation under large-sample regime. |
| **Supplementary 100k Control** (Amendment A-02) | 100,000 | +0.0012 | [-0.0049, +0.0071] | **Not Flagged** | Confirms that even with high sample size capable of detecting minute effects, the control process does not produce false-positive flagging when underlying bias is absent. |

## Notes on Audit Protocol
1. **Pre-registered Specification**: In accordance with P5-11, planted bias runs against the full standard D3 population with fixed master seed and rules only. The control run uses the unshifted D3 population.
2. **Empirical Verification**: The standard-size planted bias is flagged without requiring modifications to shift parameters, alpha, seed, or population size.
3. **Amendment A-02**: The 100,000-row supplementary pair is recorded in `docs/fairness-amendments.md` as an asymptotic power check.

