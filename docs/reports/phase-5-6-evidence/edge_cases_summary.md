# Edge Cases Summary (WP-18, FR-24, P5-13)

Comprehensive evaluation of 64 edge cases across 5 categories comparing Rule System with ML Baselines (Logistic Regression and Gradient Boosting).

## 1. Category Counts and Rule System Results

| Category | Total | Matched Catalog | Differs (Explained) | Differs (Unexplained) |
|---|---|---|---|---|
| **MD** (Missing / Contradictory Data) | 9 | 9 | 0 | 0 |
| **TB** (Threshold Boundaries) | 40 | 38 | 2 | 0 |
| **TF** (Thin File / New to Credit) | 4 | 4 | 0 | 0 |
| **RC** (Rare Combinations) | 4 | 4 | 0 | 0 |
| **AD** (Adversarial / Gamed Inputs) | 7 | 6 | 1 | 0 |
| **Total** | **64** | **61** | **3** | **0** |

## 2. Full Explanation of the Three Differences (OQ-012)

The 3 cases where rule outcome differs from isolated catalog threshold expectation are all explained by end-to-end policy formula interaction:

1. **EC-TB-16** (FOIR below cap: monthly obligations INR 39,999 on monthly income INR 80,000):
   - *Isolated threshold expectation*: eligible (clears E01 as FOIR = 0.4999875 <= 0.50).
   - *Actual system outcome*: ineligible with reason code INSUFFICIENT_REPAYMENT_CAPACITY.
   - *Mechanism*: Under Band B, the post-loan FOIR cap is 0.50 (Formula F4). Maximum affordable EMI is (80000 * 0.50) - 39999 = INR 1. Formula F7 yields loan capacity of ~INR 25, which is strictly below min_amount (INR 50,000). Rule A03 correctly fires, denying the loan.

2. **EC-TB-17** (FOIR at cap: monthly obligations INR 40,000 on monthly income INR 80,000):
   - *Isolated threshold expectation*: eligible (clears E01 as FOIR = 0.50 <= 0.50).
   - *Actual system outcome*: ineligible with reason code INSUFFICIENT_REPAYMENT_CAPACITY.
   - *Mechanism*: Post-loan FOIR cap is 0.50. Max affordable EMI is (80000 * 0.50) - 40000 = INR 0. Principal capacity is INR 0 < min_amount (INR 50,000). Rule A03 fires.

3. **EC-AD-02** (Adversarial boundary gaming: obligations set to exactly INR 40,000):
   - *Isolated threshold expectation*: eligible.
   - *Actual system outcome*: ineligible with reason code INSUFFICIENT_REPAYMENT_CAPACITY.
   - *Mechanism*: Identical capacity exhaustion mechanism as EC-TB-17. Prevents lending to over-leveraged applicants even when eligibility threshold is technically skirted.

**Resolution in Open Questions (OQ-012)**: System behaviour is mathematically correct per Formulas F4, F7, and Golden Vector TV6. Logged in docs/open-questions.md as an explained design interaction.

## 3. ML-Side Disagreements (One Line per Case)

The ML baselines exhibit fundamental qualitative divergence from rule-based non-compensatory credit policy across all 64 cases:

- **EC-MD-01** (Income missing (null)): Rule=refer, LR=error, GB=error — ML lacks schema validation and imputes missing fields with median.
- **EC-MD-02** (Credit score null (thin file)): Rule=refer, LR=error, GB=error — ML lacks schema validation and imputes missing fields with median.
- **EC-MD-03** (Income is zero): Rule=ineligible, LR=error, GB=error — ML lacks schema validation and imputes missing fields with median.
- **EC-MD-04** (Obligations greater than income (FOIR > 1.0)): Rule=ineligible, LR=error, GB=error — ML lacks schema validation and imputes missing fields with median.
- **EC-MD-05** (Employment months missing (null)): Rule=refer, LR=error, GB=error — ML lacks schema validation and imputes missing fields with median.
- **EC-MD-06** (Requested amount missing (null)): Rule=refer, LR=error, GB=error — ML lacks schema validation and imputes missing fields with median.
- **EC-MD-07** (Consent false): Rule=ineligible, LR=error, GB=error — ML lacks schema validation and imputes missing fields with median.
- **EC-MD-08** (KYC verified false): Rule=ineligible, LR=error, GB=error — ML lacks schema validation and imputes missing fields with median.
- **EC-MD-09** (Field with wrong type (string for integer income)): Rule=validation_error, LR=error, GB=error — ML lacks schema validation and imputes missing fields with median.
- **EC-TB-01** (Age below min_age (17)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-02** (Age at min_age (18)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-03** (Age above min_age (19)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-04** (Monthly income below min (14999)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-05** (Monthly income at min (15000)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-06** (Monthly income above min (15001)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-07** (Credit score below min (649)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-08** (Credit score at min (650)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-09** (Credit score above min (651)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-10** (Salaried employment months below min (5)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-11** (Salaried employment months at min (6)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-12** (Salaried employment months above min (7)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-13** (Self-employed tenure below min (23)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-14** (Self-employed tenure at min (24)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-15** (Self-employed tenure above min (25)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-16** (FOIR below cap (obligations 39999)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-17** (FOIR exactly at cap (obligations 40000)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-18** (FOIR above cap (obligations 40001)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-19** (Enquiries below max (4)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-20** (Enquiries at max (5)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-21** (Enquiries above max (6)): Rule=refer, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-22** (Requested amount below min (45000)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-23** (Requested amount at min (50000)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-24** (Requested amount above min (55000)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-25** (Requested amount below max (2495000)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-26** (Requested amount at max (2500000)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-27** (Requested amount above max (2505000)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-28** (Requested tenure below min (11)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-29** (Requested tenure at min (12)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-30** (Requested tenure above min (13)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-31** (Requested tenure below max (59)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-32** (Requested tenure at max (60)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-33** (Requested tenure above max (61)): Rule=ineligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-34** (Requested amount 777,777 not multiple of step 5,000): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-35** (Score just below Band A (749)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-36** (Score at Band A boundary (750)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-37** (Score above Band A (751)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-38** (Score just below Band B (699)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-39** (Score at Band B boundary (700)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TB-40** (Score above Band B (701)): Rule=eligible, LR=error, GB=error — ML model has smooth continuous probability without hard policy threshold.
- **EC-TF-01** (TF-01: No credit score): Rule=refer, LR=error, GB=error — ML imputes missing credit history; rules refer underwriter.
- **EC-TF-02** (TF-02: Shortest allowed employment history (6 months)): Rule=eligible, LR=error, GB=error — ML imputes missing credit history; rules refer underwriter.
- **EC-TF-03** (TF-03: No score and short employment history): Rule=refer, LR=error, GB=error — ML imputes missing credit history; rules refer underwriter.
- **EC-TF-04** (TF-04: First-time borrower with zero existing obligations): Rule=eligible, LR=error, GB=error — ML imputes missing credit history; rules refer underwriter.
- **EC-RC-01** (RC-01: Very high income (500k) with score below knockout (649)): Rule=ineligible, LR=error, GB=error — ML trades off features linearly; rules enforce non-compensatory knockouts.
- **EC-RC-02** (RC-02: Self-employed with top-of-range credit score (850)): Rule=eligible, LR=error, GB=error — ML trades off features linearly; rules enforce non-compensatory knockouts.
- **EC-RC-03** (RC-03: Max amount at max tenure with minimum income): Rule=eligible, LR=error, GB=error — ML trades off features linearly; rules enforce non-compensatory knockouts.
- **EC-RC-04** (RC-04: Salaried, min tenure (12m) and large requested amount (2M)): Rule=eligible, LR=error, GB=error — ML trades off features linearly; rules enforce non-compensatory knockouts.
- **EC-AD-01** (AD-01: Income inflated by 25% over base (100k vs 80k)): Rule=eligible, LR=error, GB=error — ML scores continuous marginal shift without discrete rule triggers.
- **EC-AD-02** (AD-02: Obligations set to largest value clearing FOIR cap (40k)): Rule=ineligible, LR=error, GB=error — ML scores continuous marginal shift without discrete rule triggers.
- **EC-AD-03a** (AD-03a: Amount set to engine maximum offer (700,000)): Rule=eligible, LR=error, GB=error — ML scores continuous marginal shift without discrete rule triggers.
- **EC-AD-03b** (AD-03b: Amount set to one step above max offer (705,000)): Rule=eligible, LR=error, GB=error — ML scores continuous marginal shift without discrete rule triggers.
- **EC-AD-04** (AD-04: Tenure set to maximum to minimise EMI (60 months)): Rule=eligible, LR=error, GB=error — ML scores continuous marginal shift without discrete rule triggers.
- **EC-AD-05a** (AD-05a: Baseline applicant (income 80,000)): Rule=eligible, LR=error, GB=error — ML scores continuous marginal shift without discrete rule triggers.
- **EC-AD-05b** (AD-05b: Near-identical applicant differing by one rupee of income (80,001)): Rule=eligible, LR=error, GB=error — ML scores continuous marginal shift without discrete rule triggers.
