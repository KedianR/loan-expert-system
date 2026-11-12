# Comparison Methodology (v1.0)

Requirements: FR-22, CR-05. Test Plan section 6. Risks R-09, R-11. Lean mode: one scorecard in which every score cites an artifact.

## 1. What is compared

Three systems, scored separately on four criteria: the **rule system**, the **logistic regression** (the transparent ML reference) and the **gradient boosting** model. Both ML models are trained on the same mapped inputs as the rules see (Phase 4, R-09). The comparison is about transparency, auditability, edge-case behavior and regulatory defensibility. It is not a contest of predictive accuracy, and the D2 outcome numbers (776 rule approvals, overlapping intervals) cannot support a claim that either system is the better lender. The accuracy metrics are context, in a separate table.

## 2. Scoring rule

Score each system 0 to 3 on each criterion using the anchors below. A score is valid only with: the anchor it meets, one or more artifact paths (a test name, a file under `reports/`, a command output), and one sentence saying how the artifact meets the anchor. **No artifact, no score** ("not scored: no evidence"). Do not average the four criteria into one number and do not weight them. Anchors are the reviewer's rubric and may be changed only before the first score is written, with an entry in `docs/open-questions.md`.

## 3. Criteria and anchors

### 3.1 Transparency (can a person see why this decision was made?)

| Score | Anchor |
|---|---|
| 3 | Every decision lists the rules that fired and the facts they used, and the applicant-facing reasons are exactly the reason codes of those rules (tested on all of D1) |
| 2 | Each decision has an exact, per-decision explanation from the model's own arithmetic (the logistic regression's feature contributions), but the explanation is a score contribution, not a policy reason the applicant can act on |
| 1 | Only a global explanation exists (permutation importance), not one per decision |
| 0 | No explanation |

Evidence to look for: the trace-equals-fired-rules test, the notice reason-code test, the logistic regression contribution function and its tests, the gradient boosting permutation importance file, the reviewer page.

### 3.2 Auditability (can a decision be reconstructed and checked later?)

| Score | Anchor |
|---|---|
| 3 | A stored record per decision, a version for the logic used, and a replay that reproduces the decision and trace, with a mismatch reported when a parameter changes |
| 2 | Versioned artifact and seed, and the numbers reproduce, but no per-decision record or replay |
| 1 | Reproducible only by retraining, no versioned artifact hash |
| 0 | Not reproducible |

Evidence: replay test, audit record test, rule-set hash and `rule_set_pin.json`, `data/manifest.json`, the metrics files (seed, split-file hash, versions), the model file hash.

### 3.3 Edge cases (does it behave sensibly where inputs are odd?)

Use `reports/edge_cases/summary.md`. Count cases that matched the expectation, differed with an explanation, and differed with no explanation, by category.

| Score | Anchor |
|---|---|
| 3 | No unexplained difference in any category; every missing-data and boundary case ends in a stated outcome |
| 2 | Unexplained differences only in rare-combination or adversarial categories |
| 1 | An unexplained difference in the missing-data or boundary categories |
| 0 | Systematic, or a missing-data or boundary case ends without any outcome or with a crash |

For the model, "expectation" is the rule system's catalog behavior; a disagreement is not a failure of the model by itself, but a boundary or missing-data case the model handles silently (for example an imputed income with no flag) is recorded as a gap.

### 3.4 Regulatory defensibility (could this be defended against the framework in `docs/regulatory-mapping.md`?)

Use the requirement rows CR-01 to CR-06 of the mapping table. For each system mark each row met (with a test or file), partly met, or a gap.

| Score | Anchor |
|---|---|
| 3 | All six rows met with evidence |
| 2 | One row partly met or a gap |
| 1 | Two or three rows partly met or gaps |
| 0 | Four or more |

A row that depends on a deployment the prototype does not have (cooling-off, data localisation, a grievance officer) is marked "out of scope for the prototype", and is not counted as a gap for any system, but is listed.

## 4. Accuracy context table (not a score)

From the Phase 4 metrics files: AUC (models), approval rate, default rate among approved with CI, cost per applicant at the three ratios, under refer treatments A and B, for D2; agreement with the policy for D3. Say beside it that D3 agreement is partly circular and D2 rests on 776 approvals.

## 5. Output

`reports/comparison/scorecard.md`: one table (system by criterion) with the score and the artifact paths in the cell, then the accuracy table, then the list of disagreements from the edge-case suite that matter for the report. `reports/comparison/scorecard.json` holds the same data for `make reproduce`.

## 6. Reporting rules

State plainly: the policy values are illustrative (D-02); the rule system's approval rate on D2 is driven by mapping effects; the comparison favours whatever a rule-based design gives by construction (reason codes), so the scorecard shows a design property and not a performance result. Every claim in the final report cites a row of this scorecard or another artifact.
