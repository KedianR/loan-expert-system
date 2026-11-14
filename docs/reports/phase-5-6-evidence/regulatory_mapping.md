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

| ID | Requirement | Source | Feature | Test | Status |
|---|---|---|---|---|---|
| CR-01 | Adverse-action reasons are specific and reflect the factors actually considered | ECOA / Reg B (confirm unchanged) | Reason codes from fired rules (`rules/reason_codes.toml`); trace builder (`src/explain/trace.py`); notice builder (`src/explain/notice.py`) | `test_fr11_golden_notice_cases_exact_match`, `test_fr10_fr11_d1_traces_notices_and_latency` | Met |
| CR-02 | Offer summary discloses amount, instalment, fees, total cost and APR before any contract step | RBI Digital Lending Directions (KFS) | Key Fact Statement calculations: `src/calc/f3_offer_summary.py` (F3), `src/calc/f4_apr.py` (F4) | `test_tv1_eligible_requested_binding` to `test_tv9_typical_band_c_offer` in `tests/golden/test_calculations_tv.py` | Met |
| CR-03 | Collect only the data needed, with a recorded consent flag | RBI Directions; DPDP (confirm) | 14-field strict input schema (`schemas/input.schema.json`); consent validation rule VA002 (`rules/validation.toml`); SHA-256 canonical input hash in audit log (`src/audit/canonical.py`) | `test_all_schema_cases`, `test_V02_firing_on_consent_false`, `test_fr15_nfr02_audit_records_and_immutable_triggers` | Met |
| CR-04 | Human referral and review path, overrides logged | EU AI Act human oversight | REFER routing in `src/engine/engine.py`; reviewer queue report (`reports/reviewer/queue.html`); audit store reviewer action logging (`src/audit/store.py` `reviewer_actions` table) | `test_reviewer_view_smoke`, `test_fr15_nfr02_audit_records_and_immutable_triggers` | Met |
| CR-05 | Document model purpose, data, method, tests and approved use | SR 11-7 (rubric only) | `docs/model-card.md`, `docs/datasheets/d2-mapping-table.md`, `docs/datasheets/d3-synthetic-data.md`, `tools/check_docs.py` | `test_all_scorecard_artifacts_exist_on_disk`, `tools/check_docs.py` (via `make check-docs`) | Met |
| CR-06 | Document bias testing and results | EU AI Act; fairness review | Pinned fairness audit plan (`docs/fairness-audit-plan.md`, `reports/fairness/plan_pin.json`), evaluation module (`src/eval/fairness.py`), reports (`reports/fairness/`) | `test_planted_bias_gender_flagged`, `test_control_gender_not_flagged`, `test_guard_refuses_changed_plan` | Met |
| — | Cooling-off period | RBI Digital Lending Directions | None (system decides eligibility only; no contract execution or disbursal step) | None | Out of scope: prototype produces eligibility decisions, not loan agreements or funds transfer |
| — | Storage of personal data in India | RBI Directions / DPDP (confirm) | Synthetic data (D3) and anonymized public benchmark (D2) only; no PII collected | `test_protected_store_isolation_static_scan` | Out of scope: academic prototype with synthetic/mapped data; no live personal data handled |
| — | Way for denied applicant to ask for a review | RBI Fair Practices Code | Adverse action notice in `src/explain/notice.py` | None | Gap: notices state reason codes and explanatory text but do not currently include instructions on requesting manual review; catalog enhancement scheduled for future release |
| — | Grievance redressal and escalation path | RBI Directions | Reviewer queue and human override logging (`src/api/review_report.py`, `src/audit/store.py`) | `test_reviewer_view_smoke` | Out of scope: no institutional grievance officer or 30-day escalation ombudsman path in academic coursework; reviewer queue is the nearest operational feature |
| — | Lending app reporting / DL app store listing | RBI Directions | Decision API and local demo UI (`src/ui/app.py`) | `test_index_page_200_and_banner` | Out of scope: prototype is an internal service and local evaluation interface, not a public commercial app |

## 3. Gaps

Listed as gaps, never filled in: the confirm items in section 1; denial notices do not say how to ask for a review; no real policy source (D-02); no independent validation (SR 11-7); SHAP faithfulness not run (lean mode); Fairlearn cross-check not run (lean mode); education and family status not analysed.

## 4. R-14 note

The EU dates changed twice in 2026. The final report repeats the dates in section 1 with the date of this check and says they must be re-verified before anyone relies on them.
