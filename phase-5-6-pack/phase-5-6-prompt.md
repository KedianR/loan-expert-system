# Phase 5 and 6, one session (paste into Antigravity)

You are starting Phases 5 and 6 of the loan eligibility expert system, run as one phase with one review at the end (lean mode). Work: edge cases and comparison (WP-18), the regulatory mapping (WP-19), the fairness review (WP-20), a demo UI (WP-22), then hardening, reproducibility and the final report (WP-21). Read AGENTS.md first and follow it. Phases 0 to 4 are done. This phase must not change a decision, a rule, a parameter, a schema or a golden file. It evaluates and wraps the working system.

Lean mode (docs/06-test-plan.md, "Lean mode") governs the tests. Do NOT write: the Fairlearn cross-check, a coverage figure, SHAP faithfulness tests, sensitivity checks, a separate Phase 6 review, the rule-level X01/X02 audit, or loader edge cases.

## Read these (and nothing else)
- AGENTS.md, docs/06-test-plan.md ("Lean mode" and section 6), docs/07-implementation-plan.md (WP-18 to WP-22), docs/00-reference.md (fairness metrics, D-05, D-06, regulation sections)
- docs/fairness-audit-plan.md, config/fairness.toml, docs/edge-case-catalog.md, docs/comparison-methodology.md, docs/regulatory-mapping.md, docs/ui-spec.md, docs/monitoring-plan.md (new; do not change a value in config/fairness.toml or section 2 to 5 of the plan after Part A)
- docs/experiment-protocol.md (section 8 decisions P4-1 to P4-14; section 6 tolerances), docs/ml-baseline-spec.md, docs/model-card.md, docs/08-datasets.md
- docs/reports/phase-0-report.md to phase-4-report.md, docs/open-questions.md
- docs/01-srs.md (requirements and acceptance criteria), the rule files and params/params.toml (names; derive values at run time, never copy them)

Decisions already taken (do not reopen): P4-1 to P4-14 and P5-1 to P5-13 (the P5 decisions are in docs/fairness-audit-plan.md section 2; append them to docs/experiment-protocol.md section 8 in Part A). Phase 4 verdict was Conditional go: D2 stays Home Credit with its limits (65% fallback obligations, 70% unknown delinquency, the rule system approves 1.68% of D2 test applicants). Carry those limits into every report.

## Step 0: confirm the base (put results in the first lines of the report)
1. `git log --oneline -8` and `git status`. Quote the HEAD commit hash. The Phase 4 report quotes a84fa6b, the commit before the close-out; say whether HEAD includes the close-out.
2. `make oracle-diff` prints 0. `git grep -nwE "5000|50000|2500000|0\.02" -- src/engine` is empty. `make check`, `make check-rules`, `make test` pass; rule-set tag and hash equal `tests/golden/rule_set_pin.json`. If any fails, STOP.
3. **Engine backend (open question OQ-001).** Print which backend the batch runs used (SWI-Prolog or the pure-Python evaluator), how it is selected (config, environment variable or fallback) and which one `make decide-d2` uses. Run `make oracle-diff` with that same backend. If the batch backend is not the one the oracle checks, STOP and ask. Fix the OQ-001 text either way.
4. Renumber the decision IDs in docs/reports/phase-4-report.md to the protocol (P4-1 to P4-12, then P4-13 and P4-14) and remove the citation of DR-06 (it does not exist).
5. Run 1,000 D3 rows through the real service path (fact builder, engine, trace builder, notice builder, audit write to a temporary store) and report: rows, failures, rows per second, and that every decision has a trace with no reason code lacking a trace entry (R-05).
6. `data/raw/` checksums equal `data/checksums/home_credit.sha256`, and `data/manifest.json` hashes equal a fresh `make data-d2`, `make data-d3` run (two-run check from Phase 4).
You may NOT change `rules/`, `params/`, `schemas/`, `tests/golden/`, `src/engine`, `src/calc`, `src/explain`, `src/audit`, `src/api`. You may add `src/eval/`, `src/ui/`, tests, docs named below, `docs/open-questions.md`, `Makefile` targets, `.gitignore` lines, and the pinned dependency list (list additions in the report).

## Part A: fix the fairness plan first (before any group result exists)
1. Confirm no file under `reports/fairness/` exists and that `config/experiment.toml` has `[fairness] group_outcome_metrics = false`. If any group outcome result already exists, STOP.
2. Append P5-1 to P5-13 to `docs/experiment-protocol.md` section 8. Create `docs/fairness-amendments.md` (empty log header).
3. Implement `make fairness-pin`: write `reports/fairness/plan_pin.json` with the SHA-256 of `docs/fairness-audit-plan.md` and `config/fairness.toml`. Implement the guard: `make fairness`, `make data-d3-bias` results and every group metric function refuse to run if the pin is missing or either hash differs (unless the difference is logged in `docs/fairness-amendments.md`). A test proves the refusal on a changed file.
4. Run `make fairness-pin`, then **commit the plan, the config and the pin in one commit, with no other change**. Show the commit hash. Only then set `group_outcome_metrics = true` (a second commit; this change is logged in the amendments file as "guard released after plan pin").

## Part B: edge cases (WP-18)
Build `src/eval/edge_cases.py` as docs/edge-case-catalog.md says. Write `reports/edge_cases/expected.csv` from the Rule Catalog first and commit it before the first run. Run both systems, write `reports/edge_cases/results.csv` and `summary.md` with counts per category (matched, differs and explained, differs and unexplained). Any difference between the engine and the catalog goes to `docs/open-questions.md`; do not change the engine. `make edge-cases`.

## Part C: comparison scorecard (WP-18)
Write `reports/comparison/scorecard.md` and `.json` following docs/comparison-methodology.md. Every score needs an anchor, an artifact path and one sentence. Include the accuracy context table. A score without an artifact is "not scored". `make compare`.

## Part D: fairness run (WP-20)
Implement `src/eval/fairness.py` and `make fairness` for D2 (test split) and D3 (test split), three systems each (rule system, logistic regression, gradient boosting) under refer treatments A and B (rule system only; the models have no refer), as docs/fairness-audit-plan.md sections 2 and 3 say. Groups come from the protected store; this module and the group-size report are the only code under `src/` besides the writers that may read it. Output tables with group sizes first; "too small" and "unstable" shown as results. Also: the counterfactual swap (P5-9) and the gender-from-features AUC on D2. Never use per-group thresholds. Never compute a metric for a group under 100 as a finding.

## Part E: pipeline test (required)
As docs/fairness-audit-plan.md section 5: `make data-d3-bias` (switch the bias on with a command-line flag or an environment variable; do not edit `config/generator.toml` or `config/experiment.toml`), engine over all rows, planted bias must be flagged (gender, selection-rate difference, F lower than M); control (normal D3) must not be flagged; the 12-row hand check with literals and working in comments. If either result is wrong, STOP; do not change the shift, alpha or seed.

## Part F: regulatory mapping (WP-19)
Fill the feature and test columns of docs/regulatory-mapping.md section 2 from the repository, using test names. Rows without a test become gaps. Do not change the "confirm" items in section 1 and do not research them; mark them open in the report. Write the completed table to `docs/regulatory-mapping.md`.

## Part G: demo UI (WP-22)
Build exactly what docs/ui-spec.md says, in the order: app and static files, the four tests, `make demo-ui`. The UI meets FR-25. Do not touch `src/api/review_report.py`; the ML block there stays as Phase 4 left it (say so in the report). Do not add a dependency.

## Part H: hardening and the final report (WP-21)
1. `make phase5` runs Parts B to E in order and writes `reports/phase5_manifest.json` (hashes of every report file, rule-set hash, params hash, plan pin). `make reproduce` = `make phase4`, then `make phase5`, then a comparison with the committed expected values: rule-system numbers must match exactly; ML metrics exactly on the same machine and to 1e-6 on another; write `reports/reproduce_comparison.md`. Because Home Credit files are not in the repository, a clean-machine run is: fresh `git clone`, copy the three raw files into `data/raw/`, `make setup`, `make reproduce`, with no manual step beyond that. Run it once on a clean checkout (a new directory or a clean virtual environment is enough if no second machine is available; say which). Show the complete output.
2. Requirement-to-test table: for every SRS requirement ID, the test names that cite it and their latest result, built from test names by a script (`make traceability`, output `reports/traceability.md`). Unmet requirements are listed with a reason, not hidden.
3. Document-to-code consistency check (`make check-docs`): rule IDs, reason codes and parameter names that appear in the documents are present in the rule and parameter files, and the reverse for rule IDs and reason codes. Fix a document, never a rule. Differences are listed and explained.
4. Pin every dependency version; record the rule-set hash and parameter version in the manifest.
5. Secrets and data: scan the repository, the logs and the audit records for raw Home Credit rows, protected columns, tokens (`kaggle.json`) and personal data. Nothing under `data/raw`, `data/protected`, `data/mapped`, `data/splits`, `data/decisions`, `data/synthetic/d3_*` or `models/` may be tracked. Show `git ls-files` filtered for those.
6. `docs/model-card.md`: fill the Phase 5 sections (fairness, proxies, limits) from the artifacts.
7. `docs/final-report.md` (outline from docs/00-reference.md: problem, policy and legal context, design, implementation, evaluation, comparison, fairness findings, limitations, future work). Every claim cites an artifact path. A "Limits" section states plainly: policy values are illustrative (D-02); datasets are mapped or synthetic, so this is a worked example and not a production credit policy; the D2 mapping effects and 776 approvals; D3 circularity; selection bias in D2 labels; the regulatory confirm items and their dates; the lean-mode cuts (Fairlearn cross-check, SHAP faithfulness, coverage, sensitivity checks); the denial notice does not say how to ask for a review; protected groups not analysed.
8. Polish items you noticed go in a list in the report; do not fix them unless they are documents or UI. The following are known and must not be fixed in this phase: reviewer page facts shown as Python repr; the R01 step lacking a null credit score; notices not mentioning rounding down to the amount step; the zero-maximum-offer catalog text; the denial notice review sentence.

## Tests (lean mode: these, no more)
- Fairness: the pin guard refuses; the 12-row hand check; the planted bias flagged; the control not flagged; groups under 100 marked too small and absent from findings; the counterfactual swap gives zero changes; no module under `src/` other than the D2 mapping, the D3 generator, the group-size report and `src/eval/fairness.py` mentions a protected column name.
- Edge cases: every catalog case has a row with both systems' outputs; an expected-behavior file existed before the results (commit order).
- Scorecard: every score cell has an artifact path that exists (a test).
- UI: the four tests in docs/ui-spec.md.
- Traceability and consistency scripts run and write their outputs.
- Requirement and decision IDs (FR-22 to FR-25, CR-01 to CR-06, DR-02, P5-n) in test names and comments.
Not required: coverage figure, Fairlearn, SHAP faithfulness, sensitivity, decision tree.

## Stop and ask if
A document is silent or two disagree (log it in `docs/open-questions.md`); the batch backend differs from the oracle's; a group outcome result exists before the plan pin; the plan, config or thresholds would need a change after results were viewed without a logged amendment; a metric is wanted for a group under 100; the planted bias is not flagged or the control is flagged; a protected attribute would reach a decision or a model; the UI would need a change in `src/api`, `src/engine`, `src/calc`, `src/explain` or `src/audit`; you need a float for money, an invented policy value, a changed rule, parameter, schema or golden file; two runs with the same seed differ; `make reproduce` needs a manual step; a regulatory point would have to be filled in rather than marked "confirm".

## Finish
Run `make check`, `make check-rules`, `make oracle-diff`, `make test`, `make phase5`, `make reproduce`, `make traceability`, `make check-docs`. Write `docs/reports/phase-5-6-report.md` from `docs/10-phase-report-template.md`. Include: Step 0 results with the commit hash; a pass or fail table naming the lean tests; per gate command its last 15 lines of output, unedited; and as evidence (in the report or as files named in it under `docs/reports/phase-5-6-evidence/`):
- The commit hash of the fairness plan pin and the amendments file (empty or listed).
- The scorecard with citations; the edge-case summary and every unexplained difference.
- The fairness tables for both systems on D2 and D3 with group sizes first (too small and unstable visible); the planted-bias, control and hand-check output.
- The completed regulatory mapping and its gaps.
- The demo UI: commands, URL, the four test results, a description of each page for TV1, one INELIGIBLE and one REFER case, and screenshots if a tool exists.
- The clean-machine `make reproduce` output start to finish and `reports/reproduce_comparison.md`.
- The traceability table, the consistency check output, the dependency lock and recorded hashes, the repository scan result.
- `docs/final-report.md`; new dependencies; every source change outside `src/eval` and `src/ui`; the polish list.
Do not start any further work. STOP.
