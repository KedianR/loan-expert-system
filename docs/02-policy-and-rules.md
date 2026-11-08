# Credit Policy and Rule Catalog (v0.1, illustrative)

Nov 5, 2026 · @Kulvinder

## 1. Product and policy parameters

This is an illustrative policy for an unsecured personal loan in India, written so the rules have something concrete to encode. It is not any real lender's policy. Replace any value here and the matching rule changes in one place. All amounts are in INR.

| Ref | Parameter | Value |
| --- | --- | --- |
| CP-1.1 | Loan amount range | 50,000 to 25,00,000 |
| CP-1.2 | Amount step | 5,000 |
| CP-1.3 | Tenure range | 12 to 60 months, whole months |
| CP-2.1 | Minimum age | 18 years (legal capacity only) |
| CP-2.2 | Minimum monthly net income | 15,000 |
| CP-2.3 | Minimum credit score | 650 on a 300 to 900 scale |
| CP-2.4 | Minimum employment tenure | Salaried 6 months; self-employed 24 months |
| CP-2.5 | Adverse repayment history | Any 90+ days past due in the last 36 months, or any written-off account |
| CP-3.1 | Income multiple cap | 10 times monthly net income |
| CP-3.2 | Maximum existing FOIR to be considered | 0.50 |
| CP-5.1 | Referral: recent enquiries | More than 5 in the last 6 months |
| CP-6.1 | Processing fee | 2% of the sanctioned amount |

**Pricing bands (CP-4).** Band is the best one where both conditions hold, checked in order A, B, C. Existing FOIR means existing monthly obligations divided by monthly net income, before the new loan.

| Band | Credit score at least | Existing FOIR at most | Rate range (annual) | Indicative rate | Post-loan FOIR cap |
| --- | --- | --- | --- | --- | --- |
| A | 750 | 0.30 | 11.0% to 13.0% | 12.0% | 0.55 |
| B | 700 | 0.40 | 13.0% to 16.0% | 14.5% | 0.50 |
| C | 650 | 0.50 | 16.0% to 20.0% | 18.0% | 0.45 |

The indicative rate is the midpoint of the band's range. Post-loan FOIR cap limits the new EMI plus existing obligations as a share of income.

## 2. Rule catalog

The system has 20 active rules and 2 experimental rules. Layers run in this order: Validation (V), Knock-out (K), Referral (R), Eligibility (E), Amount (A), Pricing (P). Within a layer, rules run in ID order. Rule IDs are permanent: retire a rule, never reuse its ID.

| ID | Layer | Condition | Outcome | Reason code | Clause | Status |
| --- | --- | --- | --- | --- | --- | --- |
| V01 | Validation | Any required fact is missing (a null credit score is handled by R01) | REFER | INCOMPLETE\_APPLICATION | CP-7.1 | Active |
| V02 | Validation | Consent is not recorded | INELIGIBLE | CONSENT\_NOT\_GIVEN | CP-7.2 | Active |
| V03 | Validation | Requested amount is outside 50,000 to 25,00,000 | INELIGIBLE | AMOUNT\_OUTSIDE\_PRODUCT\_LIMITS | CP-1.1 | Active |
| V04 | Validation | Requested tenure is outside 12 to 60 months | INELIGIBLE | TENURE\_OUTSIDE\_PRODUCT\_LIMITS | CP-1.3 | Active |
| K01 | Knock-out | Age is under 18 | INELIGIBLE | LEGAL\_CAPACITY\_NOT\_MET | CP-2.1 | Active |
| K02 | Knock-out | KYC is not verified | INELIGIBLE | KYC\_NOT\_VERIFIED | CP-2.6 | Active |
| K03 | Knock-out | Any 90+ days past due in 36 months, or a written-off account | INELIGIBLE | ADVERSE\_REPAYMENT\_HISTORY | CP-2.5 | Active |
| K04 | Knock-out | Credit score is known and below 650 | INELIGIBLE | CREDIT\_SCORE\_BELOW\_MINIMUM | CP-2.3 | Active |
| K05 | Knock-out | Monthly net income is below 15,000 | INELIGIBLE | INCOME\_BELOW\_MINIMUM | CP-2.2 | Active |
| K06 | Knock-out | Salaried with under 6 months, or self-employed with under 24 months, in current employment | INELIGIBLE | EMPLOYMENT\_TENURE\_TOO\_SHORT | CP-2.4 | Active |
| R01 | Referral | Credit score is null (no bureau history) | REFER | NO\_CREDIT\_HISTORY | CP-5.2 | Active |
| R02 | Referral | More than 5 credit enquiries in the last 6 months | REFER | HIGH\_RECENT\_ENQUIRIES | CP-5.1 | Active |
| R03 | Referral | Employment type is "other" | REFER | EMPLOYMENT\_TYPE\_REQUIRES\_REVIEW | CP-5.3 | Active |
| E01 | Eligibility | Existing FOIR is above 0.50 | INELIGIBLE | HIGH\_EXISTING\_OBLIGATIONS | CP-3.2 | Active |
| E02 | Eligibility | Assign band A, B or C using the band table; no band if no row matches | Derives band | none | CP-4 | Active |
| A01 | Amount | Compute the EMI-based maximum principal at the indicative rate and requested tenure | Derives value | none | CP-4, Calc Spec | Active |
| A02 | Amount | Recommended amount is the lowest of requested, EMI-based maximum, income multiple cap and product maximum, rounded down to 5,000 | Derives amount | none | CP-1.1, 1.2, 3.1 | Active |
| A03 | Amount | Recommended amount is below 50,000 | INELIGIBLE | INSUFFICIENT\_REPAYMENT\_CAPACITY | CP-1.1, CP-4 | Active |
| A04 | Amount | Recommended amount is below the requested amount by at least one amount step (5,000) | Offer on reduced terms | AMOUNT\_LIMITED\_BY\_REPAYMENT\_CAPACITY, AMOUNT\_LIMITED\_BY\_INCOME\_MULTIPLE or AMOUNT\_LIMITED\_BY\_PRODUCT\_MAXIMUM, whichever cap was lowest | CP-3.1, CP-4, CP-1.1 | Active |
| P01 | Pricing | Attach indicative rate, rate range and 2% processing fee of the band | Derives price | none | CP-4, CP-6.1 | Active |
| X01 | Experimental | Age at loan maturity is above 65 | INELIGIBLE | AGE\_AT\_MATURITY\_LIMIT | Experiment only | Disabled |
| X02 | Experimental | Region tier is 3: move the band down one step; band C becomes INELIGIBLE | Derives band or INELIGIBLE | REGIONAL\_RISK\_ADJUSTMENT | Experiment only | Disabled |

**Notes**

- Rules E02, A01, A02 and P01 derive values and fire only when no INELIGIBLE or REFER outcome has been recorded for the applicant. Trace entries still list the rules that were skipped and why.
- X01 and X02 exist so the fairness review can show how an age-linked rule and a proxy rule change group outcomes. They stay disabled in the baseline rule set.

**Procedural clauses referenced above**

| Clause | Text |
| --- | --- |
| CP-2.6 | KYC verification is required before any decision |
| CP-5.2 | An applicant with no credit score is referred to a human reviewer |
| CP-5.3 | An applicant whose employment type is not salaried or self-employed is referred |
| CP-7.1 | An application must be complete before it is scored |
| CP-7.2 | Applicant consent must be recorded before processing |
| CP-8.1 | If no rule determines an outcome, the application is referred to a human reviewer |

## 3. Reason code catalog

Each reason code appears in an applicant notice only when its rule fired for that applicant. The text must stay specific: say what was found and, where possible, what would change the outcome. Do not substitute generic wording.

| Code | Applicant-facing text (template) | Rule |
| --- | --- | --- |
| INCOMPLETE\_APPLICATION | We could not decide because these details are missing: {missing\_fields}. | V01 |
| CONSENT\_NOT\_GIVEN | We cannot process your application without your recorded consent to use your data. | V02 |
| AMOUNT\_OUTSIDE\_PRODUCT\_LIMITS | The amount requested ({requested\_amount}) is outside our limits of 50,000 to 25,00,000. | V03 |
| TENURE\_OUTSIDE\_PRODUCT\_LIMITS | The tenure requested ({requested\_tenure} months) is outside our range of 12 to 60 months. | V04 |
| LEGAL\_CAPACITY\_NOT\_MET | Applicants must be at least 18 years old. | K01 |
| KYC\_NOT\_VERIFIED | Your identity verification is not complete. | K02 |
| ADVERSE\_REPAYMENT\_HISTORY | Your credit record shows a payment 90 or more days overdue in the last 36 months, or a written-off account. | K03 |
| CREDIT\_SCORE\_BELOW\_MINIMUM | Your credit score ({credit\_score}) is below our minimum of 650. | K04 |
| INCOME\_BELOW\_MINIMUM | Your monthly net income ({income}) is below our minimum of 15,000. | K05 |
| EMPLOYMENT\_TENURE\_TOO\_SHORT | Your time in current employment ({employment\_months} months) is below our minimum of {min\_months} months for your employment type. | K06 |
| NO\_CREDIT\_HISTORY | We found no credit score for you, so a reviewer will assess your application. | R01 |
| HIGH\_RECENT\_ENQUIRIES | You have {enquiries\_6m} credit enquiries in the last 6 months, above our limit of 5, so a reviewer will assess your application. | R02 |
| EMPLOYMENT\_TYPE\_REQUIRES\_REVIEW | Your employment type needs a reviewer's assessment. | R03 |
| HIGH\_EXISTING\_OBLIGATIONS | Your existing monthly loan payments are {existing\_foir\_pct}% of your income, above our limit of 50%. | E01 |
| INSUFFICIENT\_REPAYMENT\_CAPACITY | Based on your income and existing payments, the most we can offer is {recommended\_amount}, below our minimum loan of 50,000. | A03 |
| AMOUNT\_LIMITED\_BY\_REPAYMENT\_CAPACITY | We can offer {recommended\_amount} instead of {requested\_amount} because your income and existing payments limit the monthly instalment you can afford. | A04 |
| AMOUNT\_LIMITED\_BY\_INCOME\_MULTIPLE | We can offer {recommended\_amount} instead of {requested\_amount} because our limit is 10 times your monthly income. | A04 |
| AMOUNT\_LIMITED\_BY\_PRODUCT\_MAXIMUM | We can offer {recommended\_amount} instead of {requested\_amount} because 25,00,000 is the maximum for this loan. | A04 |
| AGE\_AT\_MATURITY\_LIMIT | Experimental rule X01 only. Text to be drafted if the rule is ever enabled in a real notice. | X01 |
| REGIONAL\_RISK\_ADJUSTMENT | Experimental rule X02 only. Text to be drafted if the rule is ever enabled in a real notice. | X02 |
| NO\_RULE\_APPLICABLE | A reviewer will assess your application. | Default (CP-8.1) |

Template fields in braces are filled from the trace's recorded facts, never from a separate calculation.

## 4. Decision precedence, conflict resolution and defaults

The decision is INELIGIBLE if any ineligible-outcome rule fired, otherwise REFER if any referral rule fired, otherwise ELIGIBLE. This precedence is fixed and tested.

| Situation | Behaviour |
| --- | --- |
| Several INELIGIBLE rules fire | Decision is INELIGIBLE; every fired rule's reason code is reported |
| INELIGIBLE and REFER rules both fire | INELIGIBLE wins; referral reasons stay in the trace for the reviewer |
| A rule needs a fact that is missing | The rule is not evaluated; the trace records "not evaluated: missing {fact}"; V01 fires |
| Band conditions overlap | Bands are checked in order A, B, C and the first match wins |
| ELIGIBLE with a lower amount than requested | Decision stays ELIGIBLE with rule A04 fired; the notice treats it as an offer on reduced terms |
| Derivation rules (E02, A01, A02, P01) | Run only when no INELIGIBLE or REFER outcome has been recorded |
| No rule determines an outcome | Default REFER with reason code NO\_RULE\_APPLICABLE, per CP-8.1. Applicant text: "A reviewer will assess your application." A test must fail if this default is reached on any golden test case |
| Experimental rules X01, X02 | Evaluated only when switched on in the rule-set configuration; the switch is part of the rule-set version |

**Hygiene checks the rule loader must run (FR-18)**

- Completeness: every combination of outcome-relevant facts reaches a defined outcome
- Contradiction: no two active rules give opposite outcomes for the same facts without a stated precedence
- Redundancy: no rule is subsumed by another rule with the same outcome
- Cycles: derived facts do not depend on themselves
- Orphans: every reason code in a rule exists in the catalog, and every catalog code has a rule

## 5. Rule file requirements and open items

**Rule file requirements for the coding agent**

- One rule per entry, in plain text under version control, grouped into one file per layer: `validation`, `knockout`, `referral`, `eligibility`, `amount`, `pricing`, `experimental`.
- Every rule carries these metadata fields: `id`, `layer`, `description`, `clause`, `outcome`, `reason_code`, `owner`, `effective_date`, `version`, `status`.
- Thresholds and bands live in one parameter file, never inside rule text. Rules refer to parameters by name, for example `min_credit_score`.
- The rule-set version is a hash or tag of all rule and parameter files together, and is stored with every audit record.
- Each rule ID has a matching unit test file entry and at least one boundary test (just below, at, just above each threshold).
- Every rule description and reason code text must be understandable by someone who has not read the code.

**Open items**

- [ ] Confirm or replace the illustrative thresholds in section 1 with a real policy source
- [x] Add NO\_RULE\_APPLICABLE to the reason code catalog
- [ ] Decide whether the 2% fee should include GST for APR purposes
- [ ] Decide whether to draw a point rate inside the band (for example by score) instead of using the midpoint
- [ ] Review the rule list with a credit professional if one is available, and record the review
- [ ] Draft applicant text for experimental codes if they are ever used in a notice
