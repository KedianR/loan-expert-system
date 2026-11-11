# D3 Synthetic Population: Dataset Datasheet

## Source

Synthetically generated population of 20,000 personal loan applicants produced by the project's internal data generator (`data/synthetic/d3_generator.py`). Distributions and parameters are governed by `config/generator.toml`, with product limits read directly from `params/params.toml`.

## Motivation

Designed to benchmark the expert system against machine learning classifiers in a controlled environment with zero selection bias. D3 provides a clean testbed to evaluate whether a predictive model can reconstruct rule-based credit decisions and to validate the fairness evaluation harness without risking real personal data.

## Composition

Contains 20,000 rows across all 14 fact schema fields (age, employment type, employment months, income, obligations, credit score, enquiries, delinquency, write-off, KYC, consent, loan amount, tenure, region tier) plus `obligations_source` and `sim_default`. Audit-only protected attributes (gender, region tier, age band) are stored separately in `data/protected/d3_protected.csv`.

## Known limits

All generative distributions are illustrative synthetic placeholders and do not represent any real-world credit applicant demographic or credit risk distribution. Ground-truth labels reflect the rule engine's deterministic policy evaluations rather than real historical loan repayments.

## Licence and terms

Academic project work under the repository licence. Entirely synthetic; contains no confidential, proprietary, or personally identifiable information. Use is permitted for non-commercial educational and research evaluation.

## Intended use

Used in Phase 4 for training and evaluating baseline ML models on policy-decision imitation (predicting `eligible` vs not), and in Phase 5 for fairness reviews (including controlled planted-bias verification).

