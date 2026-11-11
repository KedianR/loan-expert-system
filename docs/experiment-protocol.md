# Experiment Protocol and Reproducibility Guide (v0.1)

Requirements: NFR-03, FR-21, DR-04, DR-05. Decisions D-05, D-06. Settings: `config/experiment.toml`, `config/ml.toml`, `config/generator.toml`, `config/d2_mapping.toml`. This protocol is fixed before any Phase 4 result is viewed. A change after that needs an amendment (section 7).

## 1. Seeds and determinism

- One master seed in `config/experiment.toml`. Every other seed is derived by name: `seed(name) = int(sha256(f"{master}:{name}").hexdigest(), 16) % 2**32`. Names: `split_d2`, `split_d3`, `d3_population`, `d3_bias`, `d3_sim_outcome`, `fallback_obligations`, `model_lr`, `model_gb`.
- Random draws that belong to one applicant (the obligations fallback in D2) use a generator seeded from `seed("fallback_obligations")` and the applicant key, so the value does not depend on row order or on how the file is chunked.
- The same raw files, config and seed give a byte-identical mapped D2 file and D3 population. Write files with a fixed column order, fixed line endings (LF), no index and no timestamps. Money and ratio fields in D2 are written as integers or exact decimal strings, never as floats.
- Versions are pinned in the dependency list; each metrics file records the versions of Python, pandas, NumPy and scikit-learn.

## 2. Commands and order

Each target prints what it wrote and the SHA-256 of each output.

| Order | Command | Does | Needs |
|---|---|---|---|
| 1 | `make data-d2` | Verifies raw checksums, maps D2, writes the mapped file, the protected store and the mapping table | `data/raw/` |
| 2 | `make data-d3` | Generates D3 and its protected store | none |
| 3 | `make decide-d3` | Runs the engine over all D3 rows; the decision is the D3 label (P4-2) | 2 |
| 4 | `make split` | Writes the D2 split (stratified on `TARGET`) and the D3 split (stratified on eligible versus not) | 1, 3 |
| 5 | `make decide-d2` | Runs the engine over the D2 validation and test rows | 4 |
| 6 | `make baseline` | Trains the models, chooses operating points on validation, writes models and metrics | 4, 5 |
| 7 | `make phase4` | Runs 1 to 6, then the Phase 4 checks, and writes the manifest | |

`make baseline` can be rerun on its own and must give the same metrics.

## 3. Evaluation population

- D2: every mapped row. No row is dropped for failing a product rule. Count and report how many rows fail V03 (amount limit), V04 (tenure limit) and K05 (minimum income), and the reason-code frequency of all decisions.
- A row that fails the input schema is counted by field and listed. If more than 1% of rows fail, STOP and ask.
- The rule system is evaluated on the same test applicants as the model, with the same mapped inputs.
- Batch decisions call the engine directly, as the API does, without the audit store. They are evaluation runs, not audited decisions.

## 4. Comparison protocol

1. Rule decisions on validation and test for D2. The rule system has no training; the validation rows are used only to read its approval share for the matched operating point.
2. Model scores on the same rows.
3. Operating points as in `docs/ml-baseline-spec.md` section 6: matched approval rate and cost-based, both chosen on validation.
4. Metrics on the test split for both systems, under refer treatments A and B.
5. The main comparison is the default rate among approved at the matched approval rate. AUC is reported for the model only; the rule system produces a decision, not a score.
6. Report the share of D2 decisions that are `refer`, and how many of those come from unknown facts (reason codes of V01 and R01). If that share is large, the evidence of the comparison is weak. Report it and let the reviewer decide (Phase 4 conditional go).

## 5. Group-size tables and the fairness guard

Phase 4 builds a group-size table and nothing more about groups:

- For D2 and D3, on the full set and on the test split, count applicants per group for gender, age band, education, family status (D2 only), region rating or tier, employment type and income band (quartiles of `monthly_net_income` computed on the train split).
- Mark every group under 100 as too small (D-06).
- **Do not compute any outcome metric by protected group** (approval rate, error rate, calibration or a model score by group). The fairness plan is committed in Phase 5 before any group result is seen. A test fails if the Phase 4 code reads the protected store in any module except the one that writes it and the group-size report.

## 6. Reproducibility checks for the Phase 4 gate

- Run `make data-d2` twice: the two SHA-256 values are equal.
- Run `make data-d3` twice: equal. Run it with another seed: different.
- Run `make baseline` twice: the metrics files are identical.
- The manifest lists the hashes of the raw files (matching `data/checksums/home_credit.sha256`), the mapped D2, D3, both split files, the rule-set hash and the params hash. The rule-set hash must still equal `tests/golden/rule_set_pin.json`.
- Tolerance for later comparisons (`make reproduce`, Phase 5): rule-system results must match exactly; ML metrics must match exactly on the same machine and to 1e-6 on another.

## 7. Amendments

A change to this protocol, to `config/experiment.toml` or to `config/ml.toml` after results have been viewed is a logged amendment: what changed, why, the date, and that results were viewed. Make no change to improve a result. Put each entry in `docs/open-questions.md` under "Phase 4 amendments".

## 8. Decisions taken for Phase 4

| ID | Decision |
|---|---|
| P4-1 | D2 is the Home Credit Default Risk data (owner default accepted 2026-11-12). Amounts are not rescaled to INR. Fallback dataset only if the terms record blocks use |
| P4-2 | The D3 label is the engine decision, not the oracle. The oracle is test code and must not be imported by data generation. Engine and oracle agree on all 85 D1 cases; they are not re-compared on D3 in lean mode |
| P4-3 | The monthly obligations rule of `config/d2_mapping.toml` section `[monthly_obligations]` refines ASM-D4. `written_off` and `severe_delinquency_36m` are unknown when the applicant has no bureau rows (no balance rows for delinquency) |
| P4-4 | `age` is not an ML feature. A with-age run is optional in Phase 5 |
| P4-5 | ML approval uses the matched-approval-rate operating point and a cost-based one, both chosen on validation |
| P4-6 | `refer` is shown under treatments A and B |
| P4-7 | No group-level outcome metric in Phase 4 |
| P4-8 | The D2 mapping code is exact (Decimal, no float) and is covered by the float ban. The D3 generator may use floats inside random draws but writes integers, booleans, strings and nulls. ML code may use floats |
| P4-9 | Batch evaluation decisions call the engine directly and write nothing to the audit store |
| P4-10 | Explanations for the logistic regression are exact linear contributions; no SHAP package is required |
| P4-11 | Every mapping constant is in `config/d2_mapping.toml`; none is typed into the mapping code |
| P4-12 | Cost ratios 3, 5 and 10, primary 5, are placeholders the owner may change before results are viewed |
