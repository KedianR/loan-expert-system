# System Architecture and Design (v0.1)

Nov 5, 2026 · @Kulvinder

## 1. Architecture at a glance

The system is one linear decision path (centre column) with its inputs and outputs on the sides. The rule engine is the only place decisions are made; it loads versioned rules and parameters, calls the pure calculation functions, and logs every rule it reads. Evaluation work (ML baseline, comparison, fairness review) runs offline from the audit log and the protected-attribute store, so it can never change a live decision.

&#91;embedded content: component diagram · 11 parts, one decision path\]

Read top to bottom: the API passes one application through validation, rule evaluation and explanation, and the result is written to the append-only audit log. The reviewer view and offline evaluation both read from that log.

## 2. Component responsibilities and interfaces

Each component has one job and a narrow interface, so it can be tested alone. Folder names follow the proposed layout in the AGENTS.md draft.

| Component | Folder | Responsibility | Input | Output | Requirements |
| --- | --- | --- | --- | --- | --- |
| Decision API | `src/api/` | Accept an application, call the pipeline, return the result; expose the reviewer queue | Application JSON | Decision, offer, reason codes, trace | FR-01, FR-14 |
| Validator and fact builder | `src/engine/` | Check types and ranges; build the fact base; assert `unknown` for missing fields; compute derived facts that need no rule | Application JSON, schema | Fact base or field-level errors | FR-01, FR-02, FR-03 |
| Rule loader and hygiene checker | `src/engine/` | Load rule and parameter files; compute the rule-set version; run completeness, contradiction, redundancy, cycle and orphan checks | Rule and parameter files | Loaded rule set, or a failed check | FR-17, FR-18 |
| Rule engine | `src/engine/` | Evaluate layers in order; apply skip logic; record every step | Fact base, rule set | Fired and skipped rules, derived facts | FR-04 to FR-09, FR-19 |
| Calculation module | `src/calc/` | Pure functions for formulas F1 to F9 using exact decimals | Numbers and parameters | Numbers | FR-03, FR-07, FR-08, FR-13 |
| Explanation generator | `src/explain/` | Build the trace; derive reason codes and notice text from fired rules only; compute counterfactual guidance | Engine result | Trace, reason codes, notice, offer summary | FR-10 to FR-13 |
| Audit log | `src/audit/` | Append one record per decision; replay a record against its rule version | Decision record | Stored record; replay result | FR-15, FR-16 |
| Reviewer queue and view | `src/api/` | List REFER cases; show trace beside the ML score; record an override with a mandatory reason | Audit records, ML score | Reviewer decision record | FR-14, FR-25 |
| ML baseline | `ml/` | Train and score the classifier on the shared splits; produce SHAP explanations | Dataset splits | Scores, metrics, explanations | FR-21 |
| Evaluation | `eval/` | Comparison, edge-case suite and fairness review for both systems | Audit log, ML outputs, protected-attribute store | Reports | FR-22 to FR-24 |

**Interface rules**

- Calls go downward only: API, then validator, then engine, then explanation, then audit. A lower component never calls an upper one.
- The engine receives parameters and rules only through the loader. No component reads parameter files directly.
- The ML baseline and evaluation packages import nothing from `src/engine` except through the public decision function, so they cannot alter engine behaviour.
- Only `eval/` may read the protected-attribute store, and it never writes to it (FR-20).

## 3. Decision flow

One application takes these steps in this fixed order. The order, skip logic and defaults come from the Credit Policy and Rule Catalog and must not be changed in code.

1. **Receive and validate.** Malformed input returns field-level errors and stops; no decision and no audit record is written for a request that cannot be parsed.
2. **Build facts.** Assert input facts; assert `unknown` for each absent required field.
3. **Validation layer (V01 to V04).** Missing fields, consent, amount and tenure limits.
4. **Knock-out layer (K01 to K06).** Evaluate every rule, not just the first that fires, so all reasons are reported.
5. **Referral layer (R01 to R03).** Evaluate every rule.
6. **Eligibility layer (E01, E02).** E01 always runs. E02 derives the band only if no INELIGIBLE or REFER outcome has been recorded.
7. **Amount layer (A01 to A04) and pricing (P01).** Derivation rules run only when no INELIGIBLE or REFER outcome has been recorded. A03 may then turn the result into INELIGIBLE.
8. **Decide.** INELIGIBLE beats REFER beats ELIGIBLE. If no rule determines an outcome, default to REFER with reason code NO\_RULE\_APPLICABLE.
9. **Explain.** Build the trace, reason codes, notice and, for ELIGIBLE, the offer summary.
10. **Record.** Append the audit record, then return the response. If the audit write fails, return an error, not a decision.

**Skip logic and failure handling**

| Situation | Behaviour |
| --- | --- |
| A rule reads an unknown fact | Trace step `not_evaluated`, with the missing field; V01 fires |
| A derivation rule is blocked by an earlier outcome | Trace step `skipped`, with the reason |
| An exception is raised inside a rule or calculation | Stop, return a REFER-style system error to the caller, log the exception with the input hash; never guess a value |
| APR solver does not converge | Treat as a calculation error as above |
| Rule set fails hygiene checks at start-up | Refuse to start; never serve decisions from an unchecked rule set |
| Audit log unavailable | Fail closed: no decision is returned |

## 4. Data design

Five stores, each with one writer and a clear reader list. Table and field names are a starting point; the coding agent may refine them, but not the access rules.

| Store | Contents | Written by | Read by |
| --- | --- | --- | --- |
| Rule and parameter files | Rules, thresholds, bands, fees, reason code catalog | Policy owner, through Git | Rule loader only |
| Decision audit log | `decision_id`, input hash, rule-set version, timestamp, decision, full trace, offer, system flags | Audit component, append-only | Reviewer view, replay, evaluation |
| Replay input store | The validated input, keyed by input hash (synthetic data only) | Audit component, append-only, same transaction as the decision record | Replay only |
| Reviewer actions | `decision_id`, reviewer, action (approve, deny, override), reason, timestamp | Reviewer view | Evaluation, audit reports |
| Protected-attribute store | `applicant_ref`, gender, religion, caste and other audit-only fields | Data loader, once per dataset | Fairness module only |
| Experiment outputs | ML models, metrics, comparison and fairness reports, with seeds and versions | Evaluation and ML packages | Report generation |

**Design rules**

- The audit log holds an input hash, not raw personal fields, plus the full trace. The validated input is kept in a separate replay input store that only replay reads, because replay (FR-16) needs it; the audit log table itself holds no raw fields (DR-03; decision P3-3, see the audit log specification).
- Audit records cannot be updated or deleted through the application. For a SQL store, use insert-only permissions; for a file store, an append-only file with a hash chain so edits are detectable (NFR-08).
- The protected-attribute store is keyed by `applicant_ref`, which matches the audit log's reference, so fairness analysis can join outcomes to groups without the engine ever seeing the groups (DR-02).
- Default storage is SQLite for the audit log and reviewer actions, and plain files for rules and experiment outputs. This is enough for the prototype and keeps setup to one command (NFR-10).
- Retention for the prototype is the life of the project. State this in the privacy statement.

## 5. ADR-001: Rule engine choice

**Status:** Pure-Python evaluator adopted under fallback clause on 2026-11-08 (OQ-001).
**Delivered Engine:** Pure-Python AST evaluator (`src.engine.engine.decide`) evaluating declarative conditions loaded from `rules/*.toml`.

**Context.** The project must use production rules and first-order predicate logic, expose a complete trace of every rule used, and let the policy be edited without code changes. The comparison criteria (transparency, auditability) reward an engine whose rules read like the policy.

| Option | For | Against |
| --- | --- | --- |
| SWI-Prolog, called from Python | Rules are first-order logic clauses, so the report and the code match; backtracking and meta-interpretation make traces natural; mature and free | Two languages to set up and test; team must learn Prolog; decimal arithmetic needs care |
| Pure Python rule engine (declarative TOML + custom AST evaluator) | One language; simplest setup and debugging; exact decimals guaranteed; portable | Rule language parser and evaluator built in Python; no external Prolog runtime needed |
| Drools | Matches real bank practice; strong tooling | Java stack; heavy for a prototype; weaker link to first-order logic |
| Clingo (answer-set programming) | Strong at consistency and constraint checks | Poor fit for step-by-step traces and numeric calculation |

**Decision History.**
- On 2026-11-06: SWI-Prolog was accepted provisionally, subject to the WP-02 spike and the explicit fallback clause to a pure-Python evaluator if setup/integration failed.
- On 2026-11-08 (Phase 0, WP-02 / Spike S1, OQ-001): SWI-Prolog (`swipl`) was not installed on the Windows environment. The fallback clause was triggered per ADR-001 and `docs/09-file-formats.md` DS-2.
- Delivered architecture: The pure-Python rule engine (`src/engine/engine.py`) directly parses declarative TOML conditions (`rules/*.toml`), evaluates layer order, executes exact decimal calculations, and generates full audit traces. No Prolog file or runtime is used in the delivered system.

## 6. Cross-cutting design

| Concern | Design decision | Requirement |
| --- | --- | --- |
| Determinism | No clock, random numbers or external calls inside rules or calculations. Timestamps and IDs are added by the API layer after the decision is computed, so replay is exact. | FR-19 |
| Versioning | The rule-set version is a hash of all rule and parameter files plus experimental switches. Every audit record stores it. Changing any rule or parameter changes the version. | FR-16, FR-17 |
| Exact arithmetic | Money and ratios use `Decimal` or rationals end to end. Floats are allowed only inside the APR solver and are converted back to a rounded decimal. | NFR-03 |
| Configuration | Parameters, experimental switches and storage paths come from configuration files, never code. No secrets are stored in the repository. | NFR-04, NFR-08 |
| Logging | Application logs hold decision IDs and input hashes, never raw applicant fields. | NFR-07 |
| Testing hooks | The engine exposes one public function, `decide(application, rule_set) -> result`, so tests, replay, the ML comparison and the API all use the same entry point. | NFR-05 |
| Error handling | Fail closed: any internal error returns an error, never an approval. | FR-15 |
| Performance | One decision in under 1 second on a laptop. Load the rule set once at start-up, not per request. | NFR-06 |
| Portability | Pin Python and SWI-Prolog versions; document setup for Linux, macOS and Windows. | NFR-10 |

**Open design items**

- [ ] Choose the API framework (FastAPI is the default assumption)
- [ ] Decide whether the reviewer view is a small web page or a generated report
- [ ] Decide how Python and Prolog exchange data (for example a Python Prolog bridge library or a subprocess with JSON)
- [ ] Write the API specification (OpenAPI) from the decision response in the Predicate and Fact Schema
- [ ] Write sequence diagrams for the three paths: approve, deny, refer
