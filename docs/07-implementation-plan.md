# Implementation Plan and Work Breakdown (v0.1)

Nov 5, 2026 · @Kulvinder

## 1. Plan overview

The build runs in six phases. Each phase ends at a gate: a check that must pass before the next phase starts. Work is sized as S (under half a day), M (about one day) or L (two to three days) for one developer or one coding-agent session. No calendar dates are set, because the project start date and team size are not known; add dates once they are.

| Phase | Goal | Gate to leave the phase |
| --- | --- | --- |
| 0. Decide and set up | Settle open decisions and create the repository | ADR-001 confirmed, policy thresholds confirmed, `make setup` and `make test` run on an empty project |
| 1. Calculations and facts | Pure formulas and the fact builder | Golden vectors TV1 to TV9 pass for the calculation module; property tests pass |
| 2. Rule engine | All 20 rules, hygiene checks and decision precedence | Every rule has unit and boundary tests; `make check-rules` passes; no golden case reaches the default rule |
| 3. Explanation, audit and API | Trace, reason codes, notices, offer summary, audit log, replay, reviewer queue | Replay reproduces 100% of stored decisions; trace schema validates; reason codes match fired rules |
| 4. Data and ML | Dataset mapping, synthetic generator, ML baseline | Fixed splits saved; baseline metrics reproduce from one command |
| 5. Evaluation and report | Comparison, edge cases, fairness review, final report | `make reproduce` rebuilds every reported number from a clean checkout |

**Regrouping in the playbook.** The [Coding Agent Playbook](https://claude.ai/artifact/CL7euKCiRuJ9Fdv5drCHDE) regroups this work into seven phases, 0 to 6, ordered by risk. WP-16 splits in two: WP-16a (the D1 coverage set and the reference oracle) moves to Phase 2, so the rule engine is checked against an independent implementation as soon as it exists, and WP-16b (the D3 synthetic population) stays later, in Phase 4. D1 is synthetic and does not need the dataset mapping, so WP-16a can move earlier.

| Playbook phase | Work packages |
| --- | --- |
| 0 | WP-01, WP-02, WP-03 |
| 1 | WP-04, WP-05 |
| 2 | WP-06 to WP-10, WP-16a |
| 3 | WP-11 to WP-14 |
| 4 | WP-15, WP-16b, WP-17 |
| 5 | WP-18 to WP-20 |
| 6 | WP-21 and the final checks |

The work packages themselves and their "done when" checks are unchanged. Where this plan's phase table and the playbook group the work differently, the playbook governs.

From 8 November 2026 the playbook runs in lean mode: Phases 5 and 6 are one phase with one review, and a "done when" check that asks for more tests than the "Lean mode" section of the Master Test Plan lists is optional.

**Ground rules**

- Follow the order of precedence in the AGENTS.md draft when documents disagree, and log conflicts in `docs/open-questions.md`.
- Finish each work package with its tests and its documentation changes, not later.
- Commit after each work package with a message naming the requirement and rule IDs.
- Phase 4 can start in parallel with phases 2 and 3 once phase 1 is done, because the data work does not depend on the rule engine. Phase 5 needs all of them.

## 2. Work breakdown

WP IDs are permanent. Size is S, M or L as defined above. "Done when" is the check that closes the package.

| WP | Phase | Work package | Depends on | Size | Requirements | Done when |
| --- | --- | --- | --- | --- | --- | --- |
| WP-01 | 0 | Resolve open decisions: engine (ADR-001), policy thresholds, jurisdiction, primary fairness metric | None | S | SRS section 6 | Decisions recorded in the documents; open-questions file created |
| WP-02 | 0 | Create repository, folder layout, pinned dependencies, Makefile with `setup`, `test` and stub commands | WP-01 | M | NFR-03, NFR-10 | `make setup` and `make test` pass on a clean machine |
| WP-03 | 0 | Parameter file and loader holding every threshold, band and fee by name | WP-02 | S | FR-17 | No threshold appears outside the parameter file (static check) |
| WP-04 | 1 | Calculation module: formulas F1 to F9 with exact decimals | WP-03 | M | FR-03, FR-07, FR-08, FR-13 | TV1 to TV9 match expected values; unit and property tests pass |
| WP-05 | 1 | Input schema, validator and fact builder, including `unknown` handling | WP-03 | M | FR-01, FR-02, FR-03 | Malformed input gives field errors; missing field gives `unknown` facts |
| WP-06 | 2 | Rule loader: parse rule files, compute rule-set version, run hygiene checks | WP-03 | L | FR-17, FR-18 | A deliberately conflicting rule set fails `make check-rules` |
| WP-07 | 2 | Validation and knock-out rules V01 to V04, K01 to K06 with tests | WP-05, WP-06 | L | FR-02, FR-05, FR-20 | Fire, no-fire, boundary and missing-fact tests pass for each rule |
| WP-08 | 2 | Referral rules R01 to R03 and eligibility rules E01, E02 with tests | WP-07 | M | FR-04, FR-06 | Same test set passes; band tie order verified |
| WP-09 | 2 | Amount and pricing rules A01 to A04, P01, calling the calculation module | WP-04, WP-08 | M | FR-07 to FR-09 | TV1 to TV9 pass end to end through the engine |
| WP-10 | 2 | Decision precedence, default REFER and skip logic | WP-09 | S | FR-06 | Precedence and default tests pass; no golden case hits the default |
| WP-11 | 3 | Trace builder and JSON Schema; trace written for every rule | WP-10 | M | FR-10 | Every golden decision's trace validates |
| WP-12 | 3 | Reason codes, notice rendering, offer summary, counterfactual guidance | WP-11 | M | FR-11, FR-12, FR-13, CR-01, CR-02 | Notices render with no unfilled fields; counterfactual re-run gives ELIGIBLE |
| WP-13 | 3 | Audit log (append-only), replay command | WP-11 | M | FR-15, FR-16, NFR-08 | Replay reproduces 100% of stored records; tamper test detected |
| WP-14 | 3 | Decision API and reviewer queue with mandatory override reason | WP-12, WP-13 | L | FR-01, FR-14, FR-25 | End-to-end tests pass for approve, deny and refer paths; audit failure returns an error |
| WP-15 | 4 | Dataset selection, column-to-fact mapping tables and datasheets | WP-05 | M | DR-04 | Mapping documented for each chosen dataset; unmapped columns listed |
| WP-16 | 4 | Synthetic applicant generator covering every rule and boundary, plus a mixed population | WP-05 | L | DR-05 | Generator output exercises all 20 rules; fixed seed reproduces the same file |
| WP-17 | 4 | Splits, preprocessing and ML baseline (logistic regression, tree, boosting), SHAP explanations | WP-15, WP-16 | L | FR-21 | `make baseline` reproduces the same metrics; no leakage |
| WP-18 | 5 | Edge-case catalog and suite, run on both systems | WP-14, WP-17 | M | FR-24 | Side-by-side results stored; disagreements marked |
| WP-19 | 5 | Comparison on the four criteria with evidence | WP-18 | M | FR-22 | Scoring table filled with links to evidence |
| WP-20 | 5 | Fairness review: group metrics, confidence intervals, rule-level audit, experimental rules on and off | WP-14, WP-17 | L | FR-23, FR-26, CR-06 | Report covers both systems; primary metric stated; limits written |
| WP-21 | 5 | Final report, README, demo script, slides, `make reproduce` | WP-19, WP-20 | L | NFR-03 | Clean checkout reproduces every reported number |

**Critical path:** WP-01, WP-02, WP-03, WP-06, WP-07, WP-08, WP-09, WP-10, WP-11, WP-12, WP-14, WP-18, WP-19, WP-21. The data and ML work (WP-15 to WP-17) and the fairness review (WP-20) run beside it and join at phase 5.

## 3. Build risks and mitigations

| Risk | Effect | Mitigation | Owner |
| --- | --- | --- | --- |
| Python and SWI-Prolog integration is harder than expected | Phase 2 slows | Spike the integration in WP-02 with one rule and one test; fall back to the pure-Python evaluator in ADR-001 if the spike fails | Developer |
| Policy thresholds are placeholders | Results look arbitrary to a reviewer | Confirm or replace them in WP-01; document the source for each value | You |
| Rule changes during the build break many tests | Rework | Boundary tests are generated from the parameter file; golden set changes need a written reason | Developer |
| Public datasets map badly to the rule facts | Comparison is weak | Use synthetic data for rule coverage and public data only for the ML baseline and fairness; document every mapping assumption | Developer |
| No protected attributes in the chosen dataset | Fairness review is thin | Check candidate datasets for usable attributes in WP-15 before choosing; state what is missing | Developer |
| Floating-point creeps into money or ratio code | Boundary tests fail unpredictably | Static check that bans float types in `src/calc` and `src/engine`; review in WP-04 | Developer |
| Scope creep (extra loan types, UI polish) | Core work slips | Anything not in the SRS goes to `docs/open-questions.md` | You |
| Time runs short in phase 5 | Weak report | Keep the phase 5 packages small and start the report skeleton during phase 3 | You |

## 4. Decisions needed and progress tracking

**Decisions needed before WP-02 starts**

- [x] ADR-001: SWI-Prolog plus Python accepted on 2026-11-06
- [x] Illustrative policy thresholds accepted as working values on 2026-11-06; a real policy source can replace them later
- [x] India as the primary jurisdiction and a bank or NBFC lender accepted on 2026-11-06
- [x] Primary fairness metric and minimum group size chosen on 2026-11-06 (see the Development Reference decision log)
- [ ] Confirm the project start date, team size and any hard deadline, so phases can be dated
- [ ] Confirm whether continuous integration is available

**Progress tracker.** Tick each package when its "done when" check passes.

- [ ] WP-01 to WP-03 (Phase 0)
- [ ] WP-04, WP-05 (Phase 1)
- [ ] WP-06 to WP-10 (Phase 2)
- [ ] WP-11 to WP-14 (Phase 3)
- [ ] WP-15 to WP-17 (Phase 4)
- [ ] WP-18 to WP-21 (Phase 5)

**How to use this plan with a coding agent.** Give the agent one work package at a time, with the four core specs and the AGENTS.md draft. Ask it to state which requirement and rule IDs it is implementing, then to run `make test` before it reports the package done.
