# Loan Expert System: Development Reference

Nov 5, 2026 · @Kulvinder

## Purpose and how to use this doc

This is the working reference for building the loan-eligibility expert system and comparing it with an ML classifier. Each section lists what to decide, build or test; the last section tracks progress.

**Problem statement.** Develop an expert system that evaluates loan applications using production rules and first-order predicate logic. It should determine eligibility, recommend a loan amount and interest band, and give a complete rule-based decision rationale. Compare it with a simple ML classifier on transparency, auditability, edge cases and regulatory defensibility, and add a fairness review to identify potential group-level disadvantages.

**Deliverables to plan for:**

- Eligibility decision (eligible, ineligible, or refer to a human)
- Recommended loan amount and interest band
- Rationale trace for every decision, plus applicant-facing reason codes
- ML baseline and a four-criterion comparison
- Fairness review covering both the rule system and the ML model

**Currency note.** Regulatory points were researched on 2026-11-05. EU AI Act dates and RBI directions have both changed recently, so confirm against official text before citing them in a report.

## Regulatory framing

Choose one primary jurisdiction (India, given RBI relevance) and use the US and EU rules as comparison points in the defensibility analysis. The US adverse-action rule is the strongest argument for a rule-based system, so make the explanation output produce reason codes natively.

| Framework | Region | What it requires | Design implication |
| --- | --- | --- | --- |
| [ECOA / Regulation B](https://files.consumerfinance.gov/f/documents/cfpb_adverse_action_notice_circular_2023-09.pdf) | US | Denied applicants get a statement of specific reasons that relate to and accurately describe the factors actually considered or scored. The Regulation B sample checklist is illustrative, not exhaustive. The CFPB says black-box underwriting is not allowed if specific, accurate reasons cannot be given. | Generate reason codes from the rules that fired; do not pick from a generic checklist. |
| [RBI Digital Lending Directions 2025](https://www.mondaq.com/india/financial-services/1625008/rbi-notifies-reserve-bank-of-india-digital-lending-directions-2025) | India | Covers the whole lending process from underwriting to grievance redressal. A Key Fact Statement must show the instalment, total credit cost and penalties, and APR must be disclosed upfront. Data collection needs explicit consent and must be limited to what the loan needs. | Output a KFS-style summary; keep the input schema minimal; log consent. Verify the current text on rbi.org.in. |
| RBI Fair Practices Code and DPDP Act | India | General fair-conduct and data-protection obligations. | Check both when defining stored fields and retention. |
| [EU AI Act, Annex III(5)(b)](https://regulations.ai/glossary/credit-scoring-ai) | EU | AI systems evaluating creditworthiness of natural persons are high-risk (fraud detection excepted). Obligations include risk management, human oversight, bias testing and documentation. A score that a human then acts on is still covered. | Include human referral, a risk register and bias testing. Application dates have shifted, so check the current one before citing. |
| [SR 11-7](https://ryanoconnellfinance.com/?p=13970) | US | Model risk guidance expecting documentation of theory, data, methodology, test results and approved use, plus independent validation. It also applies to vendor and third-party models. | Use its documentation list as the rubric for auditability scoring. |

**Open decision:** confirm India as the primary jurisdiction, and whether the system models a bank, an NBFC or a digital lender. Decided 2026-11-06: India is primary and the lender is modelled as a bank or NBFC (see the decision log below).

## Problem definition and knowledge engineering

Fix the loan type and the policy source before writing any rule, because thresholds and rules differ between personal, home and SME loans.

**Decisions to make first**

- [ ] Loan type: personal, home or SME
- [ ] Policy source: a published bank credit policy, RBI circulars and CIBIL score bands. Without a human expert, document your policy assumptions explicitly and treat them as the "expert".
- [ ] Definition of "eligible": policy compliance versus historical repayment (these are different ground truths)

**Inputs (applicant schema)**

- Income, employment type and tenure
- Existing EMIs and credit score
- Credit history flags: defaults, recent enquiries
- Loan purpose, requested amount and tenure
- Collateral, age and KYC status

**Derived metrics:** FOIR or DTI, LTV, EMI affordability, and an income-multiple cap.

**Outputs**

- Decision: eligible, ineligible or refer to human
- Recommended amount and interest band
- Internal audit trace and applicant-facing reason codes
- Counterfactual guidance (for example, "eligible if FOIR falls below X")

**Protected and proxy attributes**

- Keep gender, religion, caste and age out of the decision rules.
- Store them separately and use them only in the fairness audit.
- Document proxy risks such as pin code, employer type and employer name.

## Rule base design

Organise rules in layers so every decision can be traced from raw facts to final output, and so each rule maps to one policy clause.

**Rule layers, in evaluation order**

1. Data validation and KYC gates
2. Hard knock-outs (for example a recent default, or below the minimum age)
3. Eligibility thresholds or scoring
4. Loan amount calculation
5. Interest band assignment
6. Referral and exception rules

**First-order logic vocabulary.** Define predicates such as `employed(A)`, `income(A,X)`, `foir(A,R)` and `high_risk(A)`, then write policy as quantified rules, for example:

```latex
\forall A\,(\mathrm{stable\_income}(A) \land \mathrm{low\_foir}(A) \land \mathrm{good\_history}(A) \rightarrow \mathrm{eligible}(A))
```

**Conflict resolution and defaults**

- Define rule priority and specificity ordering.
- Define a default when nothing fires (deny or refer, never silent approval).
- Handle missing and contradictory facts explicitly, through certainty factors, fuzzy bands, or strict thresholds with human referral.

**Rule hygiene checks**

- Completeness: every input combination reaches an outcome
- Consistency: no two rules give contradictory results for one applicant
- Redundancy and cycle detection

**Metadata on every rule:** ID, policy source and clause, owner, effective date, version, and plain-language text.

**Explanation engine.** Log every rule that fired together with the facts it used. Produce three outputs from the same log: an internal audit trace, an applicant-facing reason list, and counterfactual guidance.

## Tools and architecture

Pick the inference engine by how well it exposes an explanation trace, since that drives the whole comparison.

| Option | Type | Fit for this project |
| --- | --- | --- |
| SWI-Prolog | Logic programming | Closest to first-order logic; traces are natural to extract |
| Python `experta` or `pyDatalog` | Rule library in Python | Easy to combine with pandas and scikit-learn |
| Drools | Industry rule engine | Matches real bank practice; heavier setup |
| Clingo | Answer-set programming | Strong for consistency and constraint checks |

**Supporting stack:** Python, pandas, scikit-learn, Fairlearn and AIF360, SHAP, a small UI or API (Streamlit or FastAPI), and a database or log store for decisions.

**Components to build**

- Input validator and consent log
- Fact-base builder (maps applicant data to predicates)
- Inference engine
- Explanation generator
- Amount and pricing module
- Audit log
- Test harness

**Versioning.** Keep rules as plain files (YAML or Prolog) in Git, with a change log and an approval step so every decision can be tied to a rule version.

## Data for testing and the ML comparison

Public credit datasets will not map neatly onto your rule vocabulary, so budget time for a mapping layer and for synthetic test applicants.

| Dataset | Source | Notes |
| --- | --- | --- |
| German Credit | [UCI](<https://archive.ics.uci.edu/ml/datasets/statlog+(german+credit+data)>) | 1,000 records from a 1994 German bank. Old, and one study says its protected attribute (sex) cannot be reliably retrieved. |
| Taiwan credit-card default | [UCI](https://archive.ics.uci.edu/ml/datasets/default+of+credit+card+clients) | Larger sample; useful for the ML baseline |
| Give Me Some Credit | [Kaggle](https://kaggle.com/c/givemesomecredit) | Ten features; age is commonly used as the sensitive attribute, for example split at 30 |
| Home Credit Default Risk | [Kaggle](https://kaggle.com/c/home-credit-default-risk) | Richer features; heavier preprocessing |

**Caveats to state in the report.** A survey of fairness datasets calls the popular benchmarks (including German Credit) into question as general-purpose benchmarks because of contrived tasks, noisy data, coding mistakes and age.

**Work items**

- [ ] Write a column-to-predicate mapping table and record every assumption
- [ ] Generate synthetic applicants that exercise every rule and every threshold boundary
- [ ] Define the ground-truth label and document why
- [ ] Fix train, validation and test splits and check for leakage

## ML baseline

Keep the baseline simple so the comparison is about transparency and defensibility, not model tuning. Start with logistic regression as the transparent reference, then add a decision tree and gradient boosting for contrast.

**Pipeline**

- Preprocessing: imputation, encoding, scaling, class-imbalance handling
- Leakage checks between features and label
- Same train, validation and test splits as the rule-system evaluation

**Metrics**

- AUC, precision, recall and F1
- Calibration of predicted probabilities
- Cost-sensitive error, where a false approval costs more than a false denial

**Explanations.** Use SHAP or LIME for feature attributions and derive reason codes from them. Then test whether those reasons are faithful to what the model actually used, because the CFPB requires reasons that reflect the factors actually considered.

## Comparison framework

Score both systems on the same four criteria using the same test set. The last column holds hypotheses to confirm or refute with evidence, not conclusions.

| Criterion | How to measure | Hypothesis to test |
| --- | --- | --- |
| Transparency | Can a non-expert read the decision logic? Are explanations exact (rules) or approximate (SHAP, LIME)? | Rules give exact explanations; ML explanations are post-hoc approximations |
| Auditability | Can any decision be replayed? Are versions, logs and policy clauses linked? Score against the SR 11-7 documentation list. | Rules tie directly to policy clauses; ML needs extra tooling to match |
| Edge cases | Run a purpose-built suite (see below) against both systems | Rules are rigid at boundaries and gaps; ML may extrapolate badly on rare inputs |
| Regulatory defensibility | Can each decision produce specific, accurate reasons? Is there human oversight, bias testing and documentation? Map to ECOA, RBI and EU AI Act. | Rules defend reasons more easily; ML needs reason-faithfulness evidence |

**Edge-case suite**

- Missing or contradictory data
- Applicants exactly at threshold boundaries
- Thin-file or new-to-credit applicants
- Rare combinations the rules never anticipated
- Adversarial or gamed inputs

**Honest trade-offs to include in the report.** Rules are brittle, costly to maintain, and may encode outdated or biased policy. ML can be more accurate but harder to defend. Discuss a hybrid, with rules as guardrails around an ML score, as a conclusion.

## Fairness review

Run the same group-level checks on both the rule system and the ML model, and state up front which fairness metric you prioritise, because the common criteria conflict.

**Groups.** Gender, age bands, region (urban or rural), income band and employment type, plus intersections. Use whichever attributes your dataset supports, and say what is missing.

| Metric | What it checks | Library call |
| --- | --- | --- |
| Selection rate by group | Share approved in each group | `MetricFrame` |
| Demographic parity difference and ratio | Gap in approval rates between groups | `demographic_parity_difference`, `demographic_parity_ratio` |
| Equal opportunity and equalized odds | Gaps in true-positive and false-positive rates | `equalized_odds_difference` |
| Calibration by group | Whether a given score means the same risk in each group | Custom or AIF360 |

**Four-fifths rule.** The common heuristic flags a group whose selection rate is below 80% of the highest group's rate. Treat it as a screening signal only: one paper argues it is not the same as disparate impact, and Fairlearn deliberately avoids recommending such thresholds.

**Metric conflicts.** Demographic parity, equalized odds and calibration cannot all hold at once when base rates differ between groups. Document the trade-off and the metric you chose.

**Rule-level audit**

- [ ] Check each rule's effect by group (income floors, age caps, employer-type rules)
- [ ] Search for proxy features correlated with protected attributes
- [ ] Run counterfactual swaps that change only the sensitive attribute
- [ ] For the rule system, mitigation means revising a rule or threshold with a policy justification; for ML, try reweighting, threshold adjustment or constrained training

**Limits to acknowledge:** small group sizes, noisy labels, historical bias in the data, and the fact that metrics cannot prove fairness.

## Testing and validation

Test the rules the way a validator would: every clause, every boundary, and every change.

- [ ] One unit test per rule
- [ ] Scenario tests for each policy clause
- [ ] Boundary tests at every threshold (just below, at, just above)
- [ ] Consistency test: the same input always gives the same output
- [ ] Regression suite that runs on every rule change
- [ ] Expert review of the rule catalog, or a documented self-review checklist if no expert is available
- [ ] Decision latency check (likely minor for this project)

## Governance, ethics and deliverables

Build the human-oversight and documentation items in from the start, because both the EU AI Act and SR 11-7 expect them.

**Human in the loop**

- Define which cases are decided automatically and which go to a reviewer
- Log every override with a reason

**Applicant-facing outputs**

- Plain-language decision notice with specific adverse-action reasons
- KFS-style loan summary: amount, rate band, tenure, APR and fees

**Documentation set**

- [ ] System or model card
- [ ] Rule catalog
- [ ] Datasheet for each dataset used
- [ ] Fairness report
- [ ] Limitations and risk register
- [ ] Third-party library list (SR 11-7 applies to vendor models too)

**Monitoring plan:** drift in applicant mix, rule override rates, and periodic fairness re-checks.

**Disclaimer to include:** this is an academic prototype, not production credit advice, and it uses no real personal data.

**Final report outline:** problem, policy and legal context, design, implementation, evaluation, comparison, fairness findings, limitations, future work.

## Additional items needed to complete the project

The sections above cover the core build. These extra items close the gaps that usually surface late: planning, domain calculations, evaluation depth, privacy and final delivery. They come from general project and credit-modelling practice rather than the regulatory research.

### Project management and requirements

- [ ] Acceptance criteria for each requirement, such as "every decision produces a trace" or "every policy clause has a test"
- [ ] Scope boundaries: state what is out of scope (fraud detection, bureau integration, collections, real disbursal)
- [ ] Timeline and milestones, with a buffer for rule rework, which is usually the slowest part
- [ ] Project risk register: no domain expert, dataset mismatch, scope creep, tool learning curve
- [ ] Literature review: classic expert systems (MYCIN, CLIPS), credit scoring research, explainable AI in lending, fairness in credit

### Knowledge acquisition and rule quality

- [ ] Elicitation method: structured interviews, policy-document analysis or case walkthroughs, with a record of how each rule was sourced
- [ ] Decision tables or a decision model (such as DMN) before coding, so gaps and overlaps show up on paper
- [ ] Rule maintenance cost study: time to change a policy threshold in the rules versus retraining the ML model
- [ ] Rule-base metrics: number of rules, depth of chaining, average rules fired per decision

### Lending calculations that are easy to underestimate

- [ ] EMI formula and amortisation schedule, plus a tenure-aware maximum loan amount derived from income, FOIR and rate
- [ ] APR calculation including fees, since the RBI framework requires disclosure of the all-inclusive cost
- [ ] Interest band logic: risk-based pricing tiers, rate floors and ceilings, and how bands map to score or risk category
- [ ] Regulatory caps for your loan type: loan-to-value, tenure and income-multiple limits (check current RBI norms)
- [ ] KYC and AML gate: a simulated verification step, optionally with sanctions-style flags
- [ ] Mock credit bureau input: score band, active loans and recent enquiries

### Evaluation depth

- [ ] Statistical rigour: cross-validation, confidence intervals and significance tests when comparing the two systems
- [ ] Disagreement analysis: isolate applicants where rules and ML disagree and study them case by case, since this is usually where the real insight sits
- [ ] Sensitivity analysis: vary each threshold slightly and record how decisions and group outcomes shift
- [ ] Ablation: remove one rule at a time to see its contribution to approvals and to group impact
- [ ] Explanation quality: fidelity (does the SHAP explanation match model behaviour), stability (do similar applicants get similar reasons), and a small comprehensibility check with a few readers if possible
- [ ] Reproducibility: fixed random seeds, a pinned environment (requirements file or Docker), and versioned data and rule files

### Fairness extras

- [ ] Label and selection bias: historical data only has repayment outcomes for approved applicants, so state this limit and discuss reject inference if possible
- [ ] Confidence intervals on group metrics, because small groups make gaps look larger or smaller than they are
- [ ] Fairness-accuracy trade-off chart showing what each mitigation costs
- [ ] Less-discriminatory alternatives: for any rule or feature with a disparity, test whether another rule meets the same business goal with a smaller gap
- [ ] Intersectional results, such as gender combined with age band, not only single attributes

### Security, privacy and data handling

- [ ] Use synthetic or anonymised data only, with a short data-handling statement
- [ ] Consent record and a data-minimisation list showing why each input field is needed
- [ ] Access control and audit-log integrity, so logs cannot be silently edited
- [ ] Retention rule for stored decisions and applicant data

### User-facing and operational pieces

- [ ] Applicant-facing explanation design: plain language, no jargon, and constructive guidance on what would change the outcome
- [ ] Appeals and grievance path: a way to request human review, aligned with the grievance-officer concept in the RBI rules
- [ ] Optional local-language support (Hindi or Punjabi) to show accessibility
- [ ] Reviewer view: a screen or report showing the rule trace and the ML score side by side for a human underwriter

### Hybrid and future-work ideas

- [ ] Rules as guardrails around an ML score: hard policy gates first, ML for ranking, rules to generate reasons
- [ ] Monitoring dashboard: approval rates by group over time, override rates and drift alerts
- [ ] Conflict-detection tooling that flags overlapping or contradictory rules whenever a new one is added

### Final deliverables and presentation

- [ ] README with setup, run and test instructions
- [ ] Demo script with 4 to 5 curated applicants: a clear approval, a clear denial, a boundary case, a referral, and a case where rules and ML disagree
- [ ] Architecture and data-flow diagrams
- [ ] Slides and final report, following the report outline above
- [ ] Viva or Q&A preparation: why rules instead of ML, how conflicts are resolved, and which fairness metric you chose and why
- [ ] Licensing and citations for every dataset and library used

## Document checklist for the coding agent

A coding agent can only be as precise as the documents it is given. Ticked items are drafted as v0.1 and linked; the rest are still to write. Draft the core set first, because every later document depends on it.

### Core set (write before any code)

- [x] [Software Requirements Specification (SRS)](https://claude.ai/artifact/X2rtZHK6nrx3KgmdxLtHWj)
- [x] [Credit Policy and Rule Catalog](https://claude.ai/artifact/DZamgas8Hcn8HammhPf7N4) (illustrative thresholds; replace or confirm)
- [x] [Predicate and Fact Schema](https://claude.ai/artifact/2W2wtr764ggqAYCeNG9nfH)
- [x] [Lending Calculations Specification](https://claude.ai/artifact/EyP7Gu9hfPDe1r19jHBuu6)
- [x] [Agent Instructions (AGENTS.md draft)](https://claude.ai/artifact/T6YwMoYM13v3brzi7E6d8Z)
- [x] [System Architecture and Design Document](https://claude.ai/artifact/NY4wq37Vw5DhKzYPRz8kiK) (includes ADR-001, awaiting your confirmation)
- [x] [Master Test Plan](https://claude.ai/artifact/2idwepziHXF6TuxuuTBFqu)

### Product and requirements

- [ ] Project Charter / Vision and Scope
- [ ] Use Case and User Story Document
- [ ] Requirements Traceability Matrix
- [ ] Glossary and Domain Dictionary (a first glossary sits in the SRS)
- [ ] Assumptions, Constraints and Out-of-Scope Register (a first version sits in the SRS)

### Domain, rules and compliance

- [ ] Decision Tables
- [x] Reason Code Catalog (section 3 of the Credit Policy and Rule Catalog)
- [ ] Regulatory Compliance Mapping (first table in the SRS, section 5)
- [x] Conflict Resolution and Default Policy (section 4 of the Credit Policy and Rule Catalog)

### Architecture and design

- [ ] High-Level and Low-Level Design
- [ ] Data Flow and Sequence Diagrams
- [x] Inference Engine and Explanation Trace Specification (trace schema in section 5 of the Predicate and Fact Schema)
- [ ] API / Interface Specification (OpenAPI)
- [ ] Data Dictionary and Database Schema
- [ ] UI/UX Specification and Wireframes
- [ ] Technology Stack and Architecture Decision Records (ADR-001: rule engine choice)

### Data and ML

- [x] [Dataset Mapping and Synthetic Data Specification](https://claude.ai/artifact/3MQLNPWaJ7pgAv4FTiiDBo): dataset selection and column-to-predicate mapping (sections 2 and 3)
- [ ] Datasheet for each dataset
- [x] Synthetic Data Generation Specification (section 4 of the [Dataset Mapping and Synthetic Data Specification](https://claude.ai/artifact/3MQLNPWaJ7pgAv4FTiiDBo))
- [x] Preprocessing and Data Split Specification (section 5 of the [Dataset Mapping and Synthetic Data Specification](https://claude.ai/artifact/3MQLNPWaJ7pgAv4FTiiDBo))
- [ ] ML Baseline Specification
- [ ] Model Card

### Evaluation and fairness

- [ ] Comparison Methodology
- [ ] Fairness Audit Plan
- [ ] Edge Case Catalog
- [ ] Test Case Specification
- [ ] Golden Test Set with Expected Outputs (nine vectors TV1 to TV9 are in the Lending Calculations Specification)
- [ ] Experiment Protocol and Reproducibility Guide

### Governance, privacy and risk

- [ ] Risk Register
- [ ] Data Privacy and Handling Statement
- [ ] Human Oversight and Override Policy
- [ ] Audit Log Specification
- [ ] Monitoring Plan

### Development process

- [x] [Implementation Plan and Work Breakdown](https://claude.ai/artifact/TEVuk2SAnm6EHBBrjUzw1h)
- [ ] Definition of Done (a first version sits in the AGENTS.md draft)
- [ ] Coding Standards and Conventions
- [ ] Repository Structure and Git Workflow (a proposed layout sits in the AGENTS.md draft)
- [ ] Environment and Setup Guide
- [ ] Change Log and Version History

### Delivery

- [ ] README
- [ ] Demo Script and User Manual
- [ ] Final Project Report
- [ ] Presentation Slides and Viva Q&A Sheet
- [ ] Licensing and Citations List

**Suggested writing order:** charter and SRS; credit policy, glossary, predicate schema, calculation spec and rule catalog; architecture, design, API and data schema; test plan, edge cases and golden set; data, ML, comparison and fairness plans; agent instructions and implementation plan; delivery documents last.

## Decision log and checkpoints

This section is the one place to see what has been decided and what is still open. Checkpoints are tied to the work packages in the [Implementation Plan](https://claude.ai/artifact/TEVuk2SAnm6EHBBrjUzw1h), so "needed by" means the work package that cannot be finished without the answer. If a checkpoint is still open when its work package starts, development continues with the stated default and the choice is recorded here.

**Reminders.** This doc cannot remind you by itself. At the start of each phase, ask "what is due" and I will list the open checkpoints for that phase and the next one.

### Decisions made on 2026-11-06 (defaults accepted)

| ID | Decision | Choice | Recorded in |
| --- | --- | --- | --- |
| D-01 | Rule engine (ADR-001) | SWI-Prolog for rules, Python for everything else. Fall back to a pure-Python evaluator that uses the same rule files and trace format if the WP-02 integration spike fails | System Architecture and Design, section 5 |
| D-02 | Policy thresholds | The values in the Credit Policy and Rule Catalog v0.1 are working values for development. They remain illustrative and must be labelled that way in the report | Credit Policy and Rule Catalog, section 1 |
| D-03 | Jurisdiction and lender | India (RBI framework) is primary; the lender is modelled as a bank or NBFC; US and EU rules are comparison points | SRS, section 2 |
| D-04 | Loan type | Unsecured personal loan in INR | SRS, section 1 |
| D-05 | Primary fairness metric | Equal opportunity difference on the public dataset D2: the gap in approval rates between groups among applicants who go on to repay. Reported alongside it as screening metrics for both systems: selection-rate ratio and difference, error-rate gaps and calibration by group. The four-fifths ratio is a screening signal only. On the synthetic population D3, which has no repayment truth, the headline is the selection-rate difference by group | Master Test Plan, section 6; Dataset Mapping, section 5 |
| D-06 | Minimum group size for fairness reporting | 100 applicants per group; smaller groups are flagged, not silently reported | Dataset Mapping, section 5 |

D-05 was not specified earlier, so I chose it. It is easy to change before any results are viewed, but not after, because the test plan requires the primary metric to be stated first.

### Open checkpoints, in order of when they are needed

| ID | Decision or task | Default if still open | Needed by | Status |
| --- | --- | --- | --- | --- |
| CP-01 | Project start date, team size and any hard deadline | Plan stays undated; phases are ordered only | Before WP-02 ends, so phases can be dated. Only you can answer this | Open |
| CP-02 | Is continuous integration available to run `make test` on every commit | No CI; run `make test` before every commit | WP-02 | Open |
| CP-03 | How Python and Prolog exchange data, and the final test tools | Settled by the WP-02 spike: a bridge library or a subprocess with JSON | WP-02 | Open |
| CP-04 | Keep experimental rules X01 and X02 | Keep them, disabled in the baseline rule set | WP-06, because the rule loader must support the switch | Open |
| CP-05 | Does GST on the processing fee enter the APR | Excluded | WP-04 | Open |
| CP-06 | Point rate inside each band instead of the midpoint | Midpoint | WP-09 | Open |
| CP-07 | Check the RBI Key Fact Statement APR method against the current annex | Use formula F9 and label the figure "indicative" | WP-12, and before any real-looking disclosure | Open |
| CP-08 | Optional review of the rule list by a credit professional | Record a self-review checklist instead | End of WP-10 (phase 2 gate) | Optional |
| CP-09 | API framework | FastAPI | Start of WP-14 | Open |
| CP-10 | Reviewer view: web page or generated report | Generated report | Start of WP-14 | Open |
| CP-11 | Public dataset: confirm Home Credit or switch to Give Me Some Credit; verify column names and licence | Home Credit, with Give Me Some Credit as the fallback | Start of WP-15 | Open |
| CP-12 | Which groups the chosen dataset supports | Whatever it supports; state the gaps | WP-15 | Open |
| CP-13 | Rescale dataset amounts to INR | No rescale; report how many rows fail the amount and income rules | WP-15 | Open |
| CP-14 | Set the synthetic generator's distributions; include a simulated outcome in D3 | Placeholders in the data specification; no simulated outcome | WP-16 | Open |
| CP-15 | Verify the regulatory texts you will cite: RBI Digital Lending Directions, EU AI Act dates, Regulation B | Cite with the caveat "as researched November 2026" | Before WP-19 (comparison) and before any citation in the report | Open |
| CP-16 | Replace the placeholder thresholds with a real policy source | Keep them, labelled illustrative | Before WP-21 (final report) | Open |
| CP-17 | Applicant text for the experimental reason codes | Not needed while the rules are disabled | Only if a rule is enabled in a real notice | Optional |

To close a checkpoint, change its status to Done and add the choice and date under the decision log.

## Handoff readiness: documents still needed

The coding agent can start WP-01 and WP-02 with the documents already written (SRS, Credit Policy and Rule Catalog, Predicate and Fact Schema, Lending Calculations Specification, Architecture and Design, Master Test Plan, Implementation Plan, Dataset Mapping, AGENTS.md draft). Four items in tier 1 should exist before it starts, because otherwise it will invent them. Everything in tier 2 can be written just before the work package that needs it. Tier 3 is written from finished work.

### Tier 1: write before the agent starts

- [ ] **Rule File and Parameter File Format Specification.** Rule syntax, the metadata fields, how rules refer to parameters by name, how layer and experimental files load, and how the rule-set version is computed. Needed for WP-03 and WP-06, the first things the agent builds. I recommend writing this first.
- [ ] **Machine-readable JSON Schemas** for the application input, the decision response and the trace, derived from the Predicate and Fact Schema. Needed for WP-05 and WP-11.
- [ ] **Golden test files.** TV1 to TV9 as input and expected-output files, with the extra vectors listed in the Master Test Plan. Needed for WP-04. The expected values in the Lending Calculations Specification are already verified, so this is a conversion job.
- [ ] **AGENTS.md, final version.** Update the draft for decisions D-01 to D-06, replace the proposed commands and layout once WP-02 settles them, and add coding standards: naming, formatting, linting and type checking.

### Tier 2: write just before the work package that needs it

| Document | Needed before | Why |
| --- | --- | --- |
| Decision Tables | WP-07 | Shows rule combinations and gaps on paper; feeds the completeness check |
| Audit Log Specification | WP-13 | Exact record fields, hash chain and replay contract |
| Data Dictionary and Database Schema | WP-13 | Tables for audit records and reviewer actions |
| Data Privacy and Handling Statement | WP-13 and WP-16 | Consent, minimisation and retention wording the code must follow |
| API / Interface Specification (OpenAPI) | WP-14 | Endpoints, errors and examples |
| Human Oversight and Override Policy | WP-14 | Which cases are referred and what a reviewer must record |
| Reviewer View Specification and wireframe | WP-14 | Depends on checkpoint CP-10 |
| Data Flow and Sequence Diagrams | WP-14 | Approve, deny and refer paths |
| Dataset datasheets | WP-15 | One per dataset, written during mapping |
| ML Baseline Specification | WP-17 | Models, metrics, seeds and explanation method |
| Experiment Protocol and Reproducibility Guide | WP-17 | Seeds, versions and the `make reproduce` contract |
| Edge Case Catalog | WP-18 | Turns section 6 of the Master Test Plan into cases |
| Comparison Methodology | WP-18 | Scoring rubric and hypotheses for the four criteria |
| Fairness Audit Plan | WP-20 | Groups, metrics, thresholds and mitigation options, stated before results are viewed |
| Regulatory Compliance Mapping, full version | WP-19 | Extends the SRS table once checkpoint CP-15 is done |
| Risk Register | End of phase 3 | Project and model risks with owners |
| Model Card | WP-17 | Intended use, performance and limits of the ML model |
| Monitoring Plan | WP-21 | Drift, override rates and fairness re-checks |

### Tier 3: written from finished work

- [ ] README, Environment and Setup Guide (produced by WP-02, finished by WP-21)
- [ ] Demo Script and User Manual
- [ ] Final Project Report
- [ ] Presentation Slides and Viva Q&A Sheet
- [ ] Licensing and Citations List
- [ ] Change Log and Version History (kept up to date through the build)
- [ ] Requirements Traceability Matrix (generated by a script from test names)
- [ ] Project Charter and Use Case document. The agent does not need them, but coursework submissions often do.

**Suggested order for me to write next:** the four tier 1 items first, then the tier 2 documents in the order of the work packages that need them.

## Coding agent playbook

The [Coding Agent Playbook: Risk-Driven Phases](https://claude.ai/artifact/CL7euKCiRuJ9Fdv5drCHDE) sets out seven phases (0 to 6), the documents to give the agent in each, a risk register, a paste-ready prompt per phase, and the review step with me after each one. A working expert system exists after Phase 3 and the project is complete after Phase 6. Before Phase 0 can start, the Tier 1 documents above still have to be written.

## Build order and progress

Work in this order, because each step feeds the next. Tick items off as they are done.

- [ ] 1\. Fix jurisdiction and loan type
- [ ] 2\. Write the policy and rule catalog on paper
- [ ] 3\. Encode the rules and build the explanation trace
- [ ] 4\. Create test data and the test suite
- [ ] 5\. Train the ML baseline
- [ ] 6\. Run the four-criterion comparison
- [ ] 7\. Run the fairness audit on both systems
- [ ] 8\. Write up findings, limits and future work

## Sources

Links below come from search results gathered on 2026-11-05; open the originals before citing them.

- [CFPB adverse action circular 2023-03](https://files.consumerfinance.gov/f/documents/cfpb_adverse_action_notice_circular_2023-09.pdf)
- [MoFo: CFPB guidance on AI in credit decisions](https://www.mofo.com/resources/insights/231002-cfpb-issues-guidance-on-ai-use-in-credit-decisions)
- [Consumer Finance Monitor: CFPB revisits adverse action](https://www.consumerfinancemonitor.com/2023/09/20/cfpb-revisits-adverse-action-notice-requirements-when-using-artificial-intelligence-or-complex-credit-models/)
- [Mondaq: RBI Digital Lending Directions 2025](https://www.mondaq.com/india/financial-services/1625008/rbi-notifies-reserve-bank-of-india-digital-lending-directions-2025)
- [Mondaq: RBI directions and transparency](https://www.mondaq.com/india/financial-services/1697900/rbis-digital-lending-directions-2025-enhancing-transparency-and-consumer-protection)
- [Taxguru: RBI digital lending guidelines](https://taxguru.in/?p=833624)
- [GKToday: RBI digital lending guidelines](https://www.gktoday.in/rbi-digital-lending-guidelines)
- [regulations.ai: credit scoring AI and the EU AI Act](https://regulations.ai/glossary/credit-scoring-ai)
- [Openlayer: EU AI Act credit scoring guide](https://www.openlayer.com/blog/credit-scoring-eu-ai-act-compliance-guide.md)
- [KNIME: EU AI Act for finance](https://www.knime.com/blog/eu-ai-act-finance-what-you-actually-have-do)
- [SR 11-7 overview](https://ryanoconnellfinance.com/?p=13970)
- [Fairlearn: common fairness metrics](https://fairlearn.org/v0.9/user_guide/assessment/common_fairness_metrics.html)
- [The four-fifths rule is not disparate impact (arXiv)](https://arxiv.org/pdf/2202.09519)
- [Fairness in Credit Scoring (arXiv)](https://arxiv.org/pdf/2103.01907)
- [Algorithmic Fairness Datasets: the Story so Far (arXiv)](https://arxiv.org/abs/2202.01711v2)
- [Exploration of a new fairness benchmark for Europe](https://ceur-ws.org/Vol-3908/paper_45.pdf)
- [Revisiting (Un)Fairness in Recourse (arXiv)](https://arxiv.org/pdf/2509.04128)
