# AGENTS.md

Rule-based loan eligibility expert system for an unsecured personal loan in INR. Production rules and first-order logic decide ELIGIBLE, INELIGIBLE or REFER, recommend an amount and an interest band, and explain every decision. A simple ML classifier is built only as a comparison baseline, then a fairness review covers both systems. This is an academic prototype on synthetic or public data. The policy values are illustrative.

## How you work

- The owner tells you ONE phase at a time and which documents to read. Do only that phase. Do not read ahead or start the next one.
- Test scope: the "Lean mode" section of `docs/06-test-plan.md` governs. Write the tests it requires; do not write extra tests unless told.
- At the end of a phase, run its gate commands, write `docs/reports/phase-N-report.md` from `docs/10-phase-report-template.md`, and STOP. Give a pass or fail table and, per command, the last 15 lines of its output, unedited; paste full output only for a failure.
- If a document is silent, ambiguous, or two documents disagree: STOP and ask. Record it in `docs/open-questions.md`. Never choose silently.
- Never invent a policy value, rule, threshold, formula or reason-code text.

## Sources of truth (highest wins)

1. `docs/02-policy-and-rules.md`: thresholds, rules, reason codes, precedence
2. `docs/03-calculations.md`: formulas F1 to F9, rounding, test vectors TV1 to TV9
3. `docs/04-predicates-and-facts.md`: field names, predicates, trace format
4. `docs/09-file-formats.md`: format of the parameter, field, reason-code and rule files
5. `docs/01-srs.md`: requirement IDs and acceptance criteria
6. `docs/05-architecture.md`, `docs/06-test-plan.md`, `docs/07-implementation-plan.md`, `docs/08-datasets.md`
7. `docs/00-reference.md`: background, decision log, checkpoints

Golden files in `tests/golden/` and schemas in `schemas/` are the expected values. If code and a golden file disagree, the code is wrong until the owner says otherwise.

## Hard rules

1. No number from the policy in code or rule text. Every threshold, rate, band and fee is read by name from `params/params.toml`.
2. Money and ratios use exact decimals (`Decimal`, or integers for whole rupees). Never a float. A float anywhere in `src/calc` fails the build.
3. Rules are data in `rules/*.toml`, written in the condition language of `docs/09-file-formats.md`. Never hand-write rule logic in Prolog; Prolog is generated. The one exception is the throwaway toy file in the Phase 0 spike S1, which stays under `spikes/` and is never used by the product.
4. Gender, religion, caste and any other audit-only attribute are never read by the rules, the fact builder or the ML features. They are used only by the fairness module.
5. Every decision produces a trace built only from the rules that fired. Reason codes come only from fired rules; notice text comes only from the trace.
6. Never reuse or renumber a rule ID. Retire it instead.
7. Never edit a golden file, test vector, policy value or catalog rule to make a test pass.
8. Never weaken, skip or delete a failing test.
9. No real personal data. Never commit files from `data/raw/`.
10. No feature, loan type or data source that is not in `docs/01-srs.md`.
11. Cite requirement IDs (FR-, NFR-, DR-, CR-) and rule IDs in code comments and test names.

## Stop and ask before

Computing money or a ratio with a float; inventing or changing a policy value; changing a rule without the catalog; building a trace or explanation from anything but fired rules; passing a protected attribute to a rule or model; weakening a test; reading `src/` or `rules/` when told you are the oracle session; using the test split to tune or choose a model; changing a document marked as a source of truth.

## Repository layout

```text
AGENTS.md
Makefile
params/params.toml        policy parameters, bands, experimental switches
rules/                    manifest.toml, fields.toml, reason_codes.toml,
                          validation|knockout|referral|eligibility|amount|pricing|experimental.toml
schemas/                  JSON Schemas: input, response, trace
api/openapi.yaml
src/calc/                 formulas F1 to F9 and the calculation registry
src/facts/                fact builder: input validation, derived facts, unknown handling
src/engine/               loaders, condition parser, Prolog generator, inference, hygiene checks
src/explain/              trace builder, notice rendering
src/audit/                append-only audit log, replay
src/api/                  decision service
ml/                       baseline models
eval/oracle/              independent reference implementation (own session)
eval/comparison/  eval/fairness/
data/                     raw/ (never committed), d1/, d2/, d3/
build/                    generated Prolog and other build output (not edited by hand)
tests/                    unit/, property/, integration/, golden/
docs/                     numbered specs, reports/, datasheets/, open-questions.md
```

Python 3.11 or newer (the standard `tomllib` reads the policy files). Pin every dependency in a lock file.

## Commands

| Command | Does |
| --- | --- |
| `make setup` | Install pinned dependencies |
| `make test` | All tests, including the golden vectors |
| `make check` | Tests, float ban, lint, format and the checks below |
| `make check-params` | Load and validate `params/params.toml` |
| `make check-rules` | Load and validate every rule file, then the hygiene checks |
| `make decide INPUT=file.json` | One application: decision with trace |
| `make demo` | Send TV1 to TV9 through the API and print decisions with explanations |
| `make replay ID=...` | Replay an audit record against its recorded rule-set version |
| `make oracle-diff` | Compare engine output with the oracle's output on D1 |
| `make baseline` / `compare` / `fairness` | ML baseline, four-criterion comparison, fairness review |
| `make reproduce` | Rebuild every reported number from a clean clone |

A phase adds only the commands it needs; add the rest as their phase arrives.

## Engineering standards

- Small pure functions in `src/calc`. No `assert` or `retract` inside rule logic; the fact builder asserts inputs and the evaluator only reads.
- Fixed seeds for every random process, written to the reports. The same input and rule set must give a byte-identical decision, trace and explanation; take time from an injected clock.
- Loaders collect all errors, never default a missing value, never coerce a type, and exit non-zero on error.
- Type hints and docstrings on public functions. Commit after each work package with a message naming the IDs involved.

## Definition of done for every task

- [ ] The change cites the requirement or rule IDs it implements
- [ ] Tests added or updated; `make test` passes
- [ ] `make check-params` and `make check-rules` pass if any parameter or rule changed
- [ ] The rule-set hash pin in `tests/golden/rule_set_pin.json` and the version are updated together if policy changed
- [ ] No policy number outside `params/params.toml`
- [ ] Trace and reason codes still agree
- [ ] Documents updated if behaviour changed, or the conflict logged in `docs/open-questions.md`
- [ ] No protected attribute read anywhere in `src/engine` or `src/facts`
