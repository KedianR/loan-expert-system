# Regulatory Compliance Mapping (v1.0, full version)

Requirements: CR-01 to CR-06 (SRS section 5). Checkpoint CP-15 (verify the regulatory texts before citing them) was run on **13 November 2026** with the sources in section 1. **Every item marked "confirm" rests on a law-firm or news summary read through a fetch tool, not on the official text.** The owner confirms those items on the official site before the final report quotes them. The agent treats confirm items as open points, does not fill them in, and writes "see regulatory-mapping.md, confirm" in the report.

This mapping is a worked example for a coursework prototype. It is not legal advice and not a compliance opinion.

## 1. What CP-15 found

| Framework | Status on 13 Nov 2026 | Source read | Confirm on |
|---|---|---|---|
| RBI (Digital Lending) Directions, 2025 | In force since May 2025 (a summary gives 9 May 2025 as the effective date, with some provisions from 15 June and 1 November 2025). Requires a Key Fact Statement and APR disclosure before disbursal, explicit consent, data limited to what the loan needs, a cooling-off period, and grievance redressal with escalation to RBI if a complaint is unresolved after 30 days (summary figures). The RBI page itself could not be fetched | indialaw.in summary of the Directions | rbi.org.in, "Reserve Bank of India (Digital Lending) Directions, 2025" |
| EU AI Act, Annex III, point 5(b) | Creditworthiness systems for natural persons are high-risk. The Digital Omnibus on AI was published in the Official Journal on 24 July 2026 as Regulation (EU) 2026/1744 and entered into force 27 July 2026. Stand-alone Annex III high-risk obligations now apply from **2 December 2027** (previously 2 August 2026) | White & Case summary; Gibson Dunn summary (which described the earlier, pre-adoption stage) | eur-lex.europa.eu, Regulation (EU) 2026/1744 and Regulation (EU) 2024/1689 |
| US ECOA / Regulation B | A CFPB final rule published 22 April 2026, effective **21 July 2026**, removes the effects test and disparate-impact liability from Regulation B, narrows the discouragement provision, and restricts for-profit special purpose credit programs. The summaries read did **not** address the adverse-action notice and specific-reasons requirement, so this plan assumes it is unchanged (confirm). State fair-lending laws may still allow disparate-impact claims | Greenberg Traurig summary | consumerfinance.gov, 12 CFR part 1002, sections 1002.9 and 1002.6 and the final rule |
| DPDP Act (India) | **Not re-verified in this session** | none | meity.gov.in |
| RBI Fair Practices Code | **Not re-verified in this session** | none | rbi.org.in |
| SR 11-7 (US model risk) | **Not re-verified in this session**; used only as a documentation rubric | none | federalreserve.gov |

**Consequence for the fairness review.** Because the US federal rule no longer carries an effects test, the group-level review in this project is justified by the EU AI Act bias-testing duty, India-side fair-conduct expectations, state law and good practice, and **not** by a US federal disparate-impact requirement. The report says this once, with "confirm".

## 2. Requirement to feature to test

The agent fills the last two columns from the repository: the feature (a module, rule ID, reason code or file) and the **test name** that covers it, taken from the test names, not from memory. A row without a test is listed under Gaps. "Out of scope" rows need a reason.

| ID | Requirement | Source | Feature (agent fills) | Test (agent fills) | Status |
|---|---|---|---|---|---|
| CR-01 | Adverse-action reasons are specific and reflect the factors actually considered | ECOA / Reg B (confirm unchanged) | reason codes from fired rules; notice builder | trace-equals-fired-rules; reason-code test | |
| CR-02 | Offer summary discloses amount, instalment, fees, total cost and APR before any contract step | RBI Digital Lending Directions (KFS) | KFS-style offer summary | TV1 to TV9 offer figures | |
| CR-03 | Collect only the data needed, with a recorded consent flag | RBI Directions; DPDP (confirm) | 14-field schema; `consent_given`; audit stores an input hash | schema test; audit record test | |
| CR-04 | Human referral and review path, overrides logged | EU AI Act human oversight | REFER queue, override with reason | override-without-reason test | |
| CR-05 | Document model purpose, data, method, tests and approved use | SR 11-7 (rubric only) | `docs/model-card.md`, datasheets | document-to-code consistency check | |
| CR-06 | Document bias testing and results | EU AI Act; fairness review | fairness plan, `reports/fairness/` | planted-bias and control tests | |

Add one row for each of these RBI-framework points that the system touches, marked met, gap or out of scope: cooling-off period (out of scope: no disbursal); storage of personal data in India (out of scope: synthetic data only); a way for a denied applicant to ask for a review (gap: the notices do not say how to ask; fixing the text is a catalog change and is listed for a future version); grievance redressal and its escalation path (out of scope: no grievance officer in a prototype, the reviewer queue is the nearest feature); lending app reporting (out of scope).

## 3. Gaps

Listed as gaps, never filled in: the confirm items in section 1; denial notices do not say how to ask for a review; no real policy source (D-02); no independent validation (SR 11-7); SHAP faithfulness not run (lean mode); Fairlearn cross-check not run (lean mode); education and family status not analysed.

## 4. R-14 note

The EU dates changed twice in 2026. The final report repeats the dates in section 1 with the date of this check and says they must be re-verified before anyone relies on them.
