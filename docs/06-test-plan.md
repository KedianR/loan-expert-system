# Master Test Plan (v0.1)

Nov 5, 2026 · @Kulvinder

## 1. Test strategy

The plan proves four things: every rule does what the policy says, every number matches the formulas, every decision can be explained and replayed, and the two systems are compared fairly. Tests are automated and run with `make test` unless stated.

| Level | What it proves | Tool (default) | Run when |
| --- | --- | --- | --- |
| Unit: rule | One rule fires or does not fire for given facts | `pytest` driving the engine, or `plunit` for Prolog | Every commit |
| Unit: calculation | Each formula F1 to F9 returns the right value | `pytest` | Every commit |
| Boundary | Behaviour just below, at and just above each threshold | `pytest`, generated from the parameter file | Every commit |
| Property | Invariants hold across many generated applicants | `hypothesis` | Every commit |
| Golden set | Known applicants always give the recorded decision, trace and offer | `pytest` with stored expected outputs | Every commit |
| Rule-set hygiene | The rule set is complete, consistent, non-redundant and acyclic | `make check-rules` | Every rule or parameter change |
| Explanation and audit | Trace, reason codes and notices agree; replay reproduces decisions | `pytest` | Every commit |
| Integration | API to engine to audit log works end to end, including failures | `pytest` with a test client | Every commit |
| Evaluation | Comparison, edge-case and fairness results are produced and reproducible | `make compare`, `make fairness` | Before each report version |

**Principles**

- A failing golden vector means either the code or a document is wrong. Decide which before changing anything; never edit an expected value just to pass.
- Tests cite requirement IDs and rule IDs in their names, for example `test_FR05_K03_reports_all_knockouts`.
- Tests use synthetic data only and fixed random seeds.

## 2. Traceability and coverage targets

Every requirement maps to tests, and every rule maps to tests. A script generates the traceability matrix from test names so it never goes stale.

| Item | Must be covered by | Target |
| --- | --- | --- |
| Each functional requirement FR-01 to FR-26 | At least one test whose name cites the ID | 100% of must-priority; 100% of should and could that are implemented |
| Each non-functional requirement NFR-01 to NFR-10 | A test or a documented check (for example a review checklist for NFR-09) | 100% |
| Each active rule (20 rules) | One unit test per outcome, plus boundary tests for every threshold it reads | 100% |
| Each reason code | A test showing it appears when its rule fires and never otherwise | 100% |
| Each formula F1 to F9 | Unit tests against the golden vectors, plus property tests | 100% |
| Each compliance requirement CR-01 to CR-06 | A named test or a report section that evidences it | 100% |
| Engine and calculation code | Line and branch coverage reported by `pytest-cov` | At least 90% lines in `src/engine`, `src/calc`, `src/explain` |

Coverage percentage is a smoke alarm, not proof. The matrix above is the real measure.

## 3. Rule-level tests

Every rule needs the same minimum set. Boundary tests are generated from the parameter file, so changing a threshold moves the tests with it.

| Test type | What to check | Example |
| --- | --- | --- |
| Fires | The rule fires and records the right outcome and reason code when its condition holds | K04 fires for credit score 649 |
| Does not fire | It does not fire when the condition fails | K04 does not fire for 650 |
| Boundary | Just below, at and just above each threshold it reads | Score 649, 650, 651; income 14,999, 15,000, 15,001; FOIR exactly 0.50 and just above |
| Missing fact | If a needed fact is unknown, the rule is recorded as `not_evaluated` and never fires wrongly | K04 with null score: not evaluated; R01 fires |
| Layer order | The rule appears at its layer position in the trace | Knock-outs precede referral rules |
| Independence | A knock-out does not stop other knock-outs from being evaluated | An applicant failing K03, K04 and K05 gets all three reason codes (FR-05) |

**Specific cases to include**

- [ ] Precedence: INELIGIBLE and REFER both fire; decision is INELIGIBLE and the referral reason stays in the trace (FR-06)
- [ ] Only REFER rules fire: decision is REFER and no offer is produced
- [ ] Derivation rules E02, A01, A02 and P01 are `skipped` when any INELIGIBLE or REFER outcome exists
- [ ] No rule applies: default REFER with NO\_RULE\_APPLICABLE; this must never occur on any golden case
- [ ] Credit score null produces R01 and not V01
- [ ] Experimental rules X01 and X02 do nothing while disabled, and change the rule-set version when enabled
- [ ] A rule that reads a protected attribute fails the static check (FR-20)

**Rule-set hygiene tests (`make check-rules`)**

- [ ] A deliberately conflicting rule pair is detected as a contradiction
- [ ] A rule whose reason code is missing from the catalog is detected as an orphan
- [ ] A catalog reason code with no rule is detected
- [ ] A rule that depends on its own output is detected as a cycle
- [ ] A rule covered by another rule with the same outcome is flagged as redundant
- [ ] Completeness: an exhaustive grid over the outcome-relevant fact values reaches a defined outcome every time
- [ ] The checks fail the build, and the engine refuses to start on a failing rule set

## 4. Calculation, golden-set and property tests

**Golden set.** Start with the nine vectors TV1 to TV9 in the Lending Calculations Specification. Store each as an input file plus an expected-output file holding the decision, reason codes, recommended amount, EMI, fee, APR, post-loan FOIR and the list of fired rule IDs. Grow the set as bugs are found and as new policy clauses are added.

| Vector | What it protects against |
| --- | --- |
| TV1 | Plain approval at the requested amount |
| TV2 | Capacity cap, and exact FOIR 0.30 qualifying for band A |
| TV3 | Income multiple cap, and zero obligations |
| TV4 | Exact credit score 700 qualifying for band B |
| TV5 | Exact score 750 and FOIR 0.30 together qualifying for band A |
| TV6 | Exact FOIR 0.50 with negative maximum EMI: no negative loan amount |
| TV7 | FOIR just above 0.50: rule E01 fires and no band is assigned |
| TV8 | Recommended amount below the 50,000 minimum: rule A03 |
| TV9 | Band C pricing and a high APR |

**Add vectors for the gaps the nine do not cover**

- [ ] A REFER case with no credit score (R01)
- [ ] A REFER case with more than 5 enquiries (R02)
- [ ] A case failing several knock-outs at once, to check every reason is reported
- [ ] A requested amount that is not a multiple of 5,000
- [ ] Requested amount at exactly 50,000 and exactly 25,00,000; tenure at exactly 12 and 60
- [ ] Self-employed applicant just below and just above 24 months
- [ ] Two caps tied at the same value, to check the tie order in formula F6

**Property tests (`hypothesis`)**

- [ ] Recommended amount never exceeds the requested amount, the capacity maximum, 10 times income or 25,00,000
- [ ] Recommended amount is always a multiple of 5,000 and, if offered, at least 50,000
- [ ] EMI on the capacity maximum is within one rupee of the maximum affordable EMI
- [ ] Post-loan FOIR on an offer never exceeds the band's cap, allowing for rounding down
- [ ] The same input and rule-set version always produce an identical result (FR-19)
- [ ] Increasing income, all else equal, never turns an offer into a denial or lowers the recommended amount
- [ ] APR is at least the band's indicative rate whenever the fee is positive
- [ ] No generated input ever causes an unhandled exception; bad inputs give errors or REFER

**Numeric rules for tests.** Compare money exactly. Compare APR with a tolerance of 0.01 percentage points (see the calculation specification).

## 5. Explanation, audit and replay tests

These tests protect the regulatory claim: every reason given is specific, accurate and actually used.

- [ ] **Trace validity:** every decision's trace validates against the JSON Schema (FR-10)
- [ ] **Reason code consistency:** every code in `reason_codes` has a fired step with the same code, and every fired adverse step has its code reported (FR-11, CR-01)
- [ ] **No generic reasons:** notice text is rendered only from catalog templates and trace facts; a test fails if a template field is left unfilled
- [ ] **Number agreement:** every figure in the notice and offer summary equals the value in the trace
- [ ] **Counterfactual check:** for a capacity denial, applying the suggested change (a lower amount or obligation) and re-running gives an ELIGIBLE decision (FR-12)
- [ ] **Audit write:** every returned decision has exactly one audit record; a forced audit failure returns an error and no decision (FR-15)
- [ ] **Append-only:** an attempt to update or delete an audit record through the application fails; edits to the underlying file break the hash chain and are detected (NFR-08)
- [ ] **Replay:** replaying 100% of stored records with their recorded rule-set version reproduces identical decisions and traces (FR-16)
- [ ] **Version change:** changing any rule or parameter changes the rule-set version; old records still replay against the old version
- [ ] **Override logging:** a reviewer override without a reason is rejected; with a reason it is stored and linked to the decision (FR-14)
- [ ] **Privacy:** audit records and logs contain no raw applicant fields; protected attributes appear in no engine input (DR-02, DR-03)
- [ ] **Plain language:** a checklist review of all reason code templates for jargon and for stating what could change the outcome (NFR-09)

## 6. Evaluation tests: ML baseline, comparison, edge cases and fairness

These tests check that the comparison is valid and repeatable, not that either system is "good". Both systems run on the same applicants, labels and splits.

**ML baseline and comparison validity**

- [ ] Train, validation and test splits are fixed by seed and saved; no applicant appears in two splits
- [ ] A leakage check confirms no feature is derived from the label
- [ ] The ML model never receives protected attributes as features; proxy features are listed and reviewed
- [ ] Both systems are scored on identical test applicants, with the same mapped inputs
- [ ] Re-running `make baseline` with the same seed reproduces the same metrics
- [ ] SHAP-based reason codes are tested for faithfulness: removing the top-attributed feature changes the prediction in the expected direction for most cases, and the share is reported
- [ ] Explanation stability: near-identical applicants get the same top reasons; the share that differs is reported

**Edge-case suite (run against both systems)**

| Category | Cases | What to record |
| --- | --- | --- |
| Missing or contradictory data | Missing income, null score, income of zero, obligations above income | Decision, and whether the system explained why |
| Threshold boundaries | Every threshold at below, at and above | Decision flips exactly where policy says it should |
| Thin-file or new-to-credit | No score; very short employment history | Rules refer; ML score and its stated confidence |
| Rare combinations | High income with a very low score; self-employed with a very high score | Whether either system gives an unexplained result |
| Adversarial or gamed inputs | Inflated income, obligations just under the limit, amount chosen to just clear a cap | Whether the outcome shifts sharply and whether it is flagged |

For every case, store both systems' outputs side by side and mark each disagreement for manual review. Disagreements are the main source of findings for the report.

**Fairness review checks**

- [ ] Group metrics are computed for both systems: selection rate, demographic parity difference and ratio, true- and false-positive rate gaps, calibration by group
- [ ] Each group metric reports a confidence interval; groups below a stated minimum size are flagged, not silently reported
- [ ] Intersectional results are produced where group sizes allow
- [ ] The four-fifths ratio is reported as a screening signal only, with the caveats in the Development Reference
- [ ] Counterfactual swap test: change only the protected attribute (in the ML input where it exists as a proxy), and report how many decisions change; for the rule engine the count must be zero
- [ ] Rule-level audit: for each rule, the approval-rate impact by group is reported, with the experimental X01 and X02 rules switched on and off to show their effect
- [ ] The chosen primary fairness metric and the reasons for the choice are stated before results are viewed
- [ ] Label and selection bias limits are written into the report

## 7. Exit criteria, test data and open items

**Exit criteria** (these match the SRS acceptance criteria)

- [ ] All must-priority requirements have passing tests that cite their IDs
- [ ] Every active rule has a passing unit test and boundary tests
- [ ] The golden set passes with zero unexplained differences, and no golden case reaches the NO\_RULE\_APPLICABLE default
- [ ] `make check-rules` passes
- [ ] Replay of all audit records reproduces identical decisions
- [ ] Line coverage is at least 90% in `src/engine`, `src/calc` and `src/explain`, and the traceability matrix shows no gaps
- [ ] The comparison and fairness reports are generated by one command from a clean checkout and match the figures in the final report

**Test data management**

- Synthetic applicants are produced by a documented generator with a fixed seed. It must cover every rule and every boundary, plus a realistic mixed population for evaluation.
- Public datasets are mapped to the fact schema through a recorded mapping table; unmappable columns are listed, not guessed.
- Golden inputs and expected outputs are version-controlled and change only with a note explaining why.
- No real personal data enters the repository, tests or logs.

**Defect handling**

- A bug found by any test or review gets a new test that fails first, then a fix.
- If a bug is in a document rather than code, correct the document and log the change in the change log.

**Open items**

- [ ] Confirm `pytest`, `hypothesis` and `plunit` as the test tools once the rule engine is chosen (ADR-001)
- [ ] Write the Edge Case Catalog as its own document from section 6
- [ ] Decide the minimum group size for fairness reporting
- [ ] Decide whether continuous integration is available to run `make test` on every commit
