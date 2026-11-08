# SRS: Loan Eligibility Expert System (v0.1)

Nov 5, 2026 · @Kulvinder

## 1. Introduction

This SRS defines what the loan eligibility expert system must do, so a coding agent can build it without guessing. Requirement IDs (FR-, NFR-, DR-, CR-) are stable and must be cited in code comments and tests.

**Purpose.** Build a rule-based expert system, using production rules and first-order predicate logic, that evaluates an unsecured personal loan application. It decides eligibility, recommends a loan amount and an interest band, and produces a complete rule-based rationale. A simple ML classifier is built only as a comparison baseline.

**In scope**

- Rule-based eligibility, amount and interest-band decisions for one product: unsecured personal loan in INR
- Decision trace, applicant-facing reason codes and a KFS-style offer summary
- Human referral path and decision audit log
- ML baseline, four-criterion comparison and group-level fairness review
- Synthetic and public datasets only

**Out of scope**

- Real disbursal, payments, collections or real credit bureau integration
- Fraud detection and identity verification (KYC is a simulated yes/no input)
- Secured, home and SME loans
- Any use with real applicant data or in production

**Definitions**

| Term | Meaning |
| --- | --- |
| FOIR | Fixed obligations to income ratio: monthly obligations divided by monthly net income |
| EMI | Equated monthly instalment |
| APR | Annualised all-in cost of the loan, including fees |
| KFS | Key Fact Statement shown to the borrower before the contract |
| Adverse action | Denial, or an offer on worse terms than requested |
| Reason code | Stable identifier for a specific, applicant-facing reason for an adverse action |
| Trace | Ordered record of every rule fired and the facts it used |

**Related documents.** Development Reference (research and checklist), Predicate and Fact Schema, Lending Calculations Specification, and Credit Policy and Rule Catalog.

## 2. Overall description

The system is a standalone prototype with a rule engine at its core and an ML baseline beside it, never feeding the rule engine's decisions.

**Users**

| User | Need |
| --- | --- |
| Applicant (simulated) | Receives a decision, reasons, an offer summary and a way to request review |
| Credit reviewer | Sees the rule trace and ML score side by side, and can record an override with a reason |
| Policy owner / developer | Edits rules, runs tests, and compares versions |
| Evaluator / auditor | Reruns the comparison and fairness review and checks reproducibility |

**Product perspective.** Pipeline: input validation, fact-base builder, inference engine, amount and pricing module, explanation generator, audit log. A separate evaluation package trains the ML baseline and runs comparison and fairness analysis offline.

**Constraints**

- Primary jurisdiction is India (RBI framework); US and EU rules are used for comparison in the defensibility analysis.
- Rules must be stored as plain, versioned text files, never hard-coded in application logic.
- Protected attributes (gender, religion, caste) are never decision inputs. Age is used only for the legal-capacity check. All are stored separately for the fairness audit.
- Default stack, subject to ADR-001: Python 3.11 or later for orchestration, evaluation and API; SWI-Prolog as the rule engine.

**Assumptions**

- The credit policy in the Rule Catalog is illustrative, not a real bank's policy.
- KYC status and credit score arrive as input fields; no bureau or KYC service is called.
- One decision per application; no re-evaluation history beyond the audit log.

## 3. Functional requirements

Priority: M = must, S = should, C = could. Every requirement needs at least one automated test that cites its ID.

| ID | Requirement | Pri | Acceptance criterion |
| --- | --- | --- | --- |
| FR-01 | Accept an application as structured JSON that follows the Predicate and Fact Schema | M | Malformed input returns field-level errors and no decision |
| FR-02 | Validate required fields, types and ranges | M | Missing required fields give REFER with the missing-field list; no silent defaults |
| FR-03 | Build the fact base and compute derived facts (existing FOIR, income multiple and similar) | M | Derived values match the Lending Calculations Specification test vectors |
| FR-04 | Evaluate rules in layer order: validation, knock-outs, eligibility, amount, pricing, referral | M | Order is fixed and shown in every trace |
| FR-05 | Evaluate all knock-out rules and report every one that fires | M | An applicant failing three rules sees three reasons |
| FR-06 | Return exactly one decision: ELIGIBLE, INELIGIBLE or REFER, with precedence INELIGIBLE over REFER over ELIGIBLE | M | Conflict tests confirm precedence |
| FR-07 | Recommend a loan amount that never exceeds the requested amount, the product maximum or any policy cap | M | Property test over generated applicants |
| FR-08 | Assign an interest band and an indicative rate | M | Band follows the Rule Catalog for every test vector |
| FR-09 | Honour the requested tenure within product limits, otherwise explain the adjustment | M | Out-of-range tenure yields a documented outcome |
| FR-10 | Produce a decision trace listing each fired rule ID, rule version, input facts and result | M | Trace validates against the trace schema |
| FR-11 | Produce applicant-facing reason codes only from rules that actually fired | M | No reason code appears without a matching trace entry |
| FR-12 | Provide counterfactual guidance where it can be computed | S | For capacity denials, state the maximum feasible amount or the obligation reduction needed |
| FR-13 | Produce a KFS-style offer summary for ELIGIBLE decisions: amount, tenure, rate band, EMI, fees, total interest, APR | M | Figures match the calculation spec |
| FR-14 | Route REFER cases to a reviewer queue; reviewer records approve, deny or override with a mandatory reason | M | Override without a reason is rejected |
| FR-15 | Write an append-only audit record per decision: input hash, rule-set version, output, timestamp | M | Records cannot be edited through the application |
| FR-16 | Replay any audit record against its recorded rule version | M | Replay reproduces the same decision and trace |
| FR-17 | Load rules from versioned plain-text files | M | Changing a rule needs no application code change |
| FR-18 | Run rule hygiene checks: completeness, contradiction, redundancy, cycles | M | A deliberately conflicting rule set fails the check |
| FR-19 | Behave deterministically | M | Same input and rule version always give identical output |
| FR-20 | Keep protected attributes in a separate store the rule engine cannot read | M | Static test shows no rule references a protected attribute |
| FR-21 | Train and evaluate an ML baseline on the same splits as the rule evaluation | M | Metrics report generated by one command |
| FR-22 | Run the four-criterion comparison: transparency, auditability, edge cases, regulatory defensibility | M | Report with a scoring table and evidence links |
| FR-23 | Run the fairness review on both systems with group metrics and confidence intervals | M | Selection-rate, parity, error-rate and calibration tables per group |
| FR-24 | Run the edge-case suite against both systems | M | Per-case results for missing data, boundaries, thin files, rare combinations and adversarial inputs |
| FR-25 | Show the rule trace and ML score side by side in a reviewer view | S | Both visible for one applicant on one screen |
| FR-26 | Allow optional experimental rules, such as an age-linked rule, to be switched on for fairness experiments | C | Disabled by default; the switch is recorded in the rule-set version |

## 4. Non-functional requirements

| ID | Requirement | Measure |
| --- | --- | --- |
| NFR-01 Explainability | Every decision carries a human-readable rationale and a machine-readable trace | 100% of decisions in the test set have both |
| NFR-02 Auditability | Every rule links to a policy clause, an owner and a version; every decision links to the rule-set version used | Rule Catalog has no row missing these fields |
| NFR-03 Reproducibility | Fixed random seeds, pinned dependencies and versioned data and rules | A clean checkout plus one command reproduces all reported numbers |
| NFR-04 Maintainability | A threshold change touches one rule file and its tests only | Change-impact check in review |
| NFR-05 Testability | Each rule has a unit test; each policy clause has a scenario test | Coverage report maps tests to rule IDs |
| NFR-06 Performance | Single decision completes quickly on a laptop | Under 1 second for one decision; batch of 10,000 under 5 minutes |
| NFR-07 Privacy | Only synthetic or anonymised data; only fields needed for the decision are collected | Data-minimisation list reviewed |
| NFR-08 Security | Audit log is append-only; configuration holds no secrets | Log tampering test fails as expected |
| NFR-09 Usability | Applicant text avoids jargon and states what could change the outcome | Plain-language review of all reason codes |
| NFR-10 Portability | Runs on Linux, macOS and Windows with documented setup | Setup guide tested on at least two systems |

## 5. Interfaces, data and compliance requirements

**Interfaces**

- **Decision API:** one endpoint accepts an application and returns decision, amount, band, offer summary, reason codes and trace. Full contract goes in the API Specification (to be written).
- **Reviewer interface:** queue of REFER cases, side-by-side rule trace and ML score, override form.
- **Command line:** commands to run tests, rule hygiene checks, the ML baseline, the comparison and the fairness review.

**Data requirements**

- DR-01: Applicant input fields and types follow the Predicate and Fact Schema.
- DR-02: Protected attributes live in a separate table keyed by applicant ID and are read only by the fairness module.
- DR-03: The audit log stores an input hash, not raw personal fields, plus the full trace.
- DR-04: Every public dataset used has a column-to-predicate mapping and a datasheet.
- DR-05: Synthetic applicants cover every rule and every threshold boundary, with documented generation rules.

**Compliance requirements**

| ID | Requirement | Source |
| --- | --- | --- |
| CR-01 | Adverse-action reasons are specific and reflect the factors actually considered | ECOA / Regulation B |
| CR-02 | Offer summary discloses amount, instalment, fees, total cost and APR before any contract step | RBI digital lending framework (KFS) |
| CR-03 | Collect only the data needed for the decision, with a recorded consent flag | RBI framework; DPDP Act |
| CR-04 | Provide a human referral and review path, and log overrides | EU AI Act human oversight; good practice |
| CR-05 | Document model purpose, data, method, tests and approved use | SR 11-7 |
| CR-06 | Document bias testing and results | EU AI Act; fairness review |

Exact legal wording must be confirmed against the current official texts before it is cited in a report.

## 6. Acceptance criteria and open questions

The project is accepted when all must-priority requirements pass their acceptance criteria and the following hold.

- [ ] Every rule in the Rule Catalog has a passing unit test and a boundary test
- [ ] Replaying 100% of audit records reproduces identical decisions
- [ ] The golden test set passes with zero unexplained differences
- [ ] The comparison report covers all four criteria with evidence
- [ ] The fairness report covers both systems, with confidence intervals and a stated metric priority
- [ ] A clean checkout reproduces every number in the final report with one command

**Open questions, to settle before coding starts**

- [x] ADR-001: Python plus SWI-Prolog accepted on 2026-11-06 (fallback: pure-Python engine if the WP-02 spike fails)
- [x] India (RBI) accepted as the primary jurisdiction on 2026-11-06; lender modelled as a bank or NBFC
- [x] Illustrative policy thresholds accepted as working values on 2026-11-06; replace them with a real policy source before the final report
- [ ] Primary fairness metric chosen on 2026-11-06 (see the Development Reference decision log); still to confirm: the groups the chosen dataset supports
- [ ] Decide whether the reviewer interface is a web page or a simple report
