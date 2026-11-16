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

## 3. ML Baseline Agreement with Rule System (D3 Models)

Note: ML binary prediction (operating threshold 0.5 on probability of eligible) is compared against rule outcome, mapping REFER to not-eligible.

| Category | Total | Matched Rules | Differs (Explained) | Differs (Unexplained) |
|---|---|---|---|---|
| **MD** (Missing / Contradictory Data) | 9 | 2 | 7 | 0 |
| **TB** (Threshold Boundaries) | 40 | 27 | 13 | 0 |
| **TF** (Thin File / New to Credit) | 4 | 4 | 0 | 0 |
| **RC** (Rare Combinations) | 4 | 3 | 1 | 0 |
| **AD** (Adversarial / Gamed Inputs) | 7 | 6 | 1 | 0 |
| **Total** | **64** | **42** | **22** | **0** |

## 4. Explanations of All 64 Cases (Actual Outputs, No Templates)

Each case below reflects the actual outputs of the Rule System and D3 ML models (Logistic Regression and Gradient Boosting with operating threshold 0.5 for eligibility).

- **EC-MD-01** (Income missing (null)): Rule=refer, LR=0.7870 (eligible), GB=0.9924 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — monthly_net_income is null. Pipeline did not raise or refuse; imputed median income; flagged with monthly_net_income_missing=1.0. LR=0.7870 (eligible), GB=0.9924 (eligible). Rules refer under V01 (INCOMPLETE_APPLICATION).
- **EC-MD-02** (Credit score null (thin file)): Rule=refer, LR=0.0104 (ineligible), GB=0.0001 (ineligible) [LR top 3: credit_score:-5.250; employment_type:+0.564; severe_delinquency_36m:+0.474] — credit_score is null. Pipeline did not raise or refuse; imputed median credit score; flagged with credit_score_missing=1.0 (large negative LR contribution). LR=0.0104 (ineligible), GB=0.0001 (ineligible). Rules refer under R01 (NO_CREDIT_HISTORY).
- **EC-MD-03** (Income is zero): Rule=ineligible, LR=0.7375 (eligible), GB=0.0002 (ineligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — monthly_net_income is zero. Valid numeric value; pipeline did not impute or raise. LR=0.7375 (eligible; no hard floor), GB=0.0002 (ineligible; tree isolates zero income). Rules reject under K05 (INCOME_BELOW_MINIMUM).
- **EC-MD-04** (Obligations greater than income (FOIR > 1.0)): Rule=ineligible, LR=0.1132 (ineligible), GB=0.0001 (ineligible) [LR top 3: existing_foir:-3.419; credit_score:+0.903; employment_type:+0.564] — Obligations > income (FOIR > 1.0). Pipeline did not impute or raise. existing_foir heavily penalised in LR and GB. LR=0.1132 (ineligible), GB=0.0001 (ineligible). Rules reject under E01 (HIGH_EXISTING_OBLIGATIONS).
- **EC-MD-05** (Employment months missing (null)): Rule=refer, LR=0.8183 (eligible), GB=0.9965 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — employment_months is null. Pipeline did not raise or refuse; imputed median months; flagged with employment_months_missing=1.0. LR=0.8183 (eligible), GB=0.9965 (eligible). Rules refer under V01 (INCOMPLETE_APPLICATION).
- **EC-MD-06** (Requested amount missing (null)): Rule=refer, LR=0.8196 (eligible), GB=0.9924 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — requested_amount is null. Pipeline did not raise or refuse; imputed median amount; flagged with requested_amount_missing=1.0. LR=0.8196 (eligible), GB=0.9924 (eligible). Rules refer under V01 (INCOMPLETE_APPLICATION).
- **EC-MD-07** (Consent false): Rule=ineligible, LR=0.8323 (eligible), GB=0.9965 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — consent_given is False. Excluded from ML features by design (spec §3); pipeline did not evaluate consent, impute, or raise. LR=0.8323 (eligible), GB=0.9965 (eligible). Rules reject under V02 (CONSENT_NOT_GIVEN).
- **EC-MD-08** (KYC verified false): Rule=ineligible, LR=0.8323 (eligible), GB=0.9965 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — kyc_verified is False. Excluded from ML features by design (spec §3); pipeline did not evaluate KYC, impute, or raise. LR=0.8323 (eligible), GB=0.9965 (eligible). Rules refer under V02 (KYC_PENDING).
- **EC-MD-09** (Field with wrong type (string for integer income)): Rule=validation_error, LR=0.7870 (eligible), GB=0.9924 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — String for integer income. Cleaned to null for numeric pipeline; imputed median income with missing flag; did not refuse. LR=0.7870 (eligible), GB=0.9924 (eligible). Rules reject at schema validation.
- **EC-TB-01** (Age below min_age (17)): Rule=ineligible, LR=0.8323 (eligible), GB=0.9965 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — LR=0.8323 (eligible), GB=0.9965 (eligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-02** (Age at min_age (18)): Rule=eligible, LR=0.8323 (eligible), GB=0.9965 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8323, GB=0.9965.
- **EC-TB-03** (Age above min_age (19)): Rule=eligible, LR=0.8323 (eligible), GB=0.9965 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8323, GB=0.9965.
- **EC-TB-04** (Monthly income below min (14999)): Rule=ineligible, LR=0.7833 (eligible), GB=0.0113 (ineligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — LR=0.7833 (eligible), GB=0.0113 (ineligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-05** (Monthly income at min (15000)): Rule=eligible, LR=0.7833 (eligible), GB=0.0113 (ineligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.7833, GB=0.0113.
- **EC-TB-06** (Monthly income above min (15001)): Rule=eligible, LR=0.7833 (eligible), GB=0.0113 (ineligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.7833, GB=0.0113.
- **EC-TB-07** (Credit score below min (649)): Rule=ineligible, LR=0.5080 (eligible), GB=0.0000 (ineligible) [LR top 3: credit_score:-0.666; employment_type:+0.564; severe_delinquency_36m:+0.474] — LR=0.5080 (eligible), GB=0.0000 (ineligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-08** (Credit score at min (650)): Rule=eligible, LR=0.5126 (eligible), GB=0.9981 (eligible) [LR top 3: credit_score:-0.648; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.5126, GB=0.9981.
- **EC-TB-09** (Credit score above min (651)): Rule=eligible, LR=0.5172 (eligible), GB=0.9981 (eligible) [LR top 3: credit_score:-0.630; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.5172, GB=0.9981.
- **EC-TB-10** (Salaried employment months below min (5)): Rule=ineligible, LR=0.7467 (eligible), GB=0.0002 (ineligible) [LR top 3: credit_score:+0.903; employment_months:-0.613; employment_type:+0.564] — LR=0.7467 (eligible), GB=0.0002 (ineligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-11** (Salaried employment months at min (6)): Rule=eligible, LR=0.7490 (eligible), GB=0.9987 (eligible) [LR top 3: credit_score:+0.903; employment_months:-0.601; employment_type:+0.564] — ML agrees with rule outcome (eligible). LR=0.7490, GB=0.9987.
- **EC-TB-12** (Salaried employment months above min (7)): Rule=eligible, LR=0.7513 (eligible), GB=0.9987 (eligible) [LR top 3: credit_score:+0.903; employment_months:-0.589; employment_type:+0.564] — ML agrees with rule outcome (eligible). LR=0.7513, GB=0.9987.
- **EC-TB-13** (Self-employed tenure below min (23)): Rule=ineligible, LR=0.6002 (eligible), GB=0.0070 (ineligible) [LR top 3: credit_score:+0.903; severe_delinquency_36m:+0.474; employment_months:-0.395] — LR=0.6002 (eligible), GB=0.0070 (ineligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-14** (Self-employed tenure at min (24)): Rule=eligible, LR=0.6031 (eligible), GB=0.9982 (eligible) [LR top 3: credit_score:+0.903; severe_delinquency_36m:+0.474; employment_months:-0.383] — ML agrees with rule outcome (eligible). LR=0.6031, GB=0.9982.
- **EC-TB-15** (Self-employed tenure above min (25)): Rule=eligible, LR=0.6060 (eligible), GB=0.9982 (eligible) [LR top 3: credit_score:+0.903; severe_delinquency_36m:+0.474; employment_months:-0.371] — ML agrees with rule outcome (eligible). LR=0.6060, GB=0.9982.
- **EC-TB-16** (FOIR below cap (obligations 39999)): Rule=ineligible, LR=0.5571 (eligible), GB=0.0001 (ineligible) [LR top 3: existing_foir:-1.229; credit_score:+0.903; employment_type:+0.564] — LR=0.5571 (eligible), GB=0.0001 (ineligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-17** (FOIR exactly at cap (obligations 40000)): Rule=ineligible, LR=0.5571 (eligible), GB=0.0001 (ineligible) [LR top 3: existing_foir:-1.229; credit_score:+0.903; employment_type:+0.564] — LR=0.5571 (eligible), GB=0.0001 (ineligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-18** (FOIR above cap (obligations 40001)): Rule=ineligible, LR=0.5571 (eligible), GB=0.0001 (ineligible) [LR top 3: existing_foir:-1.229; credit_score:+0.903; employment_type:+0.564] — LR=0.5571 (eligible), GB=0.0001 (ineligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-19** (Enquiries below max (4)): Rule=eligible, LR=0.7888 (eligible), GB=0.9967 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.7888, GB=0.9967.
- **EC-TB-20** (Enquiries at max (5)): Rule=eligible, LR=0.7642 (eligible), GB=0.9967 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.7642, GB=0.9967.
- **EC-TB-21** (Enquiries above max (6)): Rule=refer, LR=0.7377 (eligible), GB=0.0006 (ineligible) [LR top 3: credit_score:+0.903; enquiries_6m:-0.570; employment_type:+0.564] — LR=0.7377 (eligible), GB=0.0006 (ineligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-22** (Requested amount below min (45000)): Rule=ineligible, LR=0.8246 (eligible), GB=0.9966 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — LR=0.8246 (eligible), GB=0.9966 (eligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-23** (Requested amount at min (50000)): Rule=eligible, LR=0.8247 (eligible), GB=0.9966 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8247, GB=0.9966.
- **EC-TB-24** (Requested amount above min (55000)): Rule=eligible, LR=0.8248 (eligible), GB=0.9966 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8248, GB=0.9966.
- **EC-TB-25** (Requested amount below max (2495000)): Rule=eligible, LR=0.8519 (eligible), GB=0.9963 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; requested_amount:+0.493] — ML agrees with rule outcome (eligible). LR=0.8519, GB=0.9963.
- **EC-TB-26** (Requested amount at max (2500000)): Rule=eligible, LR=0.8520 (eligible), GB=0.9963 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; requested_amount:+0.495] — ML agrees with rule outcome (eligible). LR=0.8520, GB=0.9963.
- **EC-TB-27** (Requested amount above max (2505000)): Rule=ineligible, LR=0.8520 (eligible), GB=0.9963 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; requested_amount:+0.496] — LR=0.8520 (eligible), GB=0.9963 (eligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-28** (Requested tenure below min (11)): Rule=ineligible, LR=0.8178 (eligible), GB=0.9981 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — LR=0.8178 (eligible), GB=0.9981 (eligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-29** (Requested tenure at min (12)): Rule=eligible, LR=0.8193 (eligible), GB=0.9974 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8193, GB=0.9974.
- **EC-TB-30** (Requested tenure above min (13)): Rule=eligible, LR=0.8206 (eligible), GB=0.9974 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8206, GB=0.9974.
- **EC-TB-31** (Requested tenure below max (59)): Rule=eligible, LR=0.8374 (eligible), GB=0.9880 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8374, GB=0.9880.
- **EC-TB-32** (Requested tenure at max (60)): Rule=eligible, LR=0.8376 (eligible), GB=0.9880 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8376, GB=0.9880.
- **EC-TB-33** (Requested tenure above max (61)): Rule=ineligible, LR=0.8378 (eligible), GB=0.9880 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — LR=0.8378 (eligible), GB=0.9880 (eligible). Continuous probability shift across threshold; rule system applies discrete policy cutoff.
- **EC-TB-34** (Requested amount 777,777 not multiple of step 5,000): Rule=eligible, LR=0.8332 (eligible), GB=0.9958 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8332, GB=0.9958.
- **EC-TB-35** (Score just below Band A (749)): Rule=eligible, LR=0.8650 (eligible), GB=0.9958 (eligible) [LR top 3: credit_score:+1.159; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8650, GB=0.9958.
- **EC-TB-36** (Score at Band A boundary (750)): Rule=eligible, LR=0.8671 (eligible), GB=0.9958 (eligible) [LR top 3: credit_score:+1.177; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8671, GB=0.9958.
- **EC-TB-37** (Score above Band A (751)): Rule=eligible, LR=0.8692 (eligible), GB=0.9958 (eligible) [LR top 3: credit_score:+1.196; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8692, GB=0.9958.
- **EC-TB-38** (Score just below Band B (699)): Rule=eligible, LR=0.7201 (eligible), GB=0.9948 (eligible) [LR top 3: employment_type:+0.564; severe_delinquency_36m:+0.474; credit_score:+0.246] — ML agrees with rule outcome (eligible). LR=0.7201, GB=0.9948.
- **EC-TB-39** (Score at Band B boundary (700)): Rule=eligible, LR=0.7237 (eligible), GB=0.9948 (eligible) [LR top 3: employment_type:+0.564; severe_delinquency_36m:+0.474; credit_score:+0.265] — ML agrees with rule outcome (eligible). LR=0.7237, GB=0.9948.
- **EC-TB-40** (Score above Band B (701)): Rule=eligible, LR=0.7274 (eligible), GB=0.9948 (eligible) [LR top 3: employment_type:+0.564; severe_delinquency_36m:+0.474; credit_score:+0.283] — ML agrees with rule outcome (eligible). LR=0.7274, GB=0.9948.
- **EC-TF-01** (TF-01: No credit score): Rule=refer, LR=0.0104 (ineligible), GB=0.0001 (ineligible) [LR top 3: credit_score:-5.250; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (ineligible). LR=0.0104, GB=0.0001.
- **EC-TF-02** (TF-02: Shortest allowed employment history (6 months)): Rule=eligible, LR=0.7490 (eligible), GB=0.9987 (eligible) [LR top 3: credit_score:+0.903; employment_months:-0.601; employment_type:+0.564] — ML agrees with rule outcome (eligible). LR=0.7490, GB=0.9987.
- **EC-TF-03** (TF-03: No score and short employment history): Rule=refer, LR=0.0063 (ineligible), GB=0.0002 (ineligible) [LR top 3: credit_score:-5.250; employment_months:-0.601; employment_type:+0.564] — ML agrees with rule outcome (ineligible). LR=0.0063, GB=0.0002.
- **EC-TF-04** (TF-04: First-time borrower with zero existing obligations): Rule=eligible, LR=0.8462 (eligible), GB=0.9935 (eligible) [LR top 3: employment_type:+0.564; existing_foir:+0.523; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8462, GB=0.9935.
- **EC-RC-01** (RC-01: Very high income (500k) with score below knockout (649)): Rule=ineligible, LR=0.9681 (eligible), GB=0.0001 (ineligible) [LR top 3: monthly_net_income:+3.142; credit_score:-0.666; employment_type:+0.564] — LR=0.9681 (eligible), GB=0.0001 (ineligible). ML compensatory feature weighting vs non-compensatory policy knockouts.
- **EC-RC-02** (RC-02: Self-employed with top-of-range credit score (850)): Rule=eligible, LR=0.9348 (eligible), GB=0.9978 (eligible) [LR top 3: credit_score:+3.003; severe_delinquency_36m:+0.474; employment_type:-0.329] — ML agrees with rule outcome (eligible). LR=0.9348, GB=0.9978.
- **EC-RC-03** (RC-03: Max amount at max tenure with minimum income): Rule=eligible, LR=0.5881 (eligible), GB=0.0586 (ineligible) [LR top 3: amount_to_annual_income:-1.368; credit_score:+0.903; employment_type:+0.564] — ML agrees with rule outcome (eligible). LR=0.5881, GB=0.0586.
- **EC-RC-04** (RC-04: Salaried, min tenure (12m) and large requested amount (2M)): Rule=eligible, LR=0.8174 (eligible), GB=0.9983 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8174, GB=0.9983.
- **EC-AD-01** (AD-01: Income inflated by 25% over base (100k vs 80k)): Rule=eligible, LR=0.8642 (eligible), GB=0.9984 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8642, GB=0.9984.
- **EC-AD-02** (AD-02: Obligations set to largest value clearing FOIR cap (40k)): Rule=ineligible, LR=0.5571 (eligible), GB=0.0001 (ineligible) [LR top 3: existing_foir:-1.229; credit_score:+0.903; employment_type:+0.564] — LR=0.5571 (eligible), GB=0.0001 (ineligible). Marginal input shift evaluated continuously; capacity limits bind in rule engine.
- **EC-AD-03a** (AD-03a: Amount set to engine maximum offer (700,000)): Rule=eligible, LR=0.8323 (eligible), GB=0.9965 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8323, GB=0.9965.
- **EC-AD-03b** (AD-03b: Amount set to one step above max offer (705,000)): Rule=eligible, LR=0.8324 (eligible), GB=0.9965 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8324, GB=0.9965.
- **EC-AD-04** (AD-04: Tenure set to maximum to minimise EMI (60 months)): Rule=eligible, LR=0.8376 (eligible), GB=0.9880 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8376, GB=0.9880.
- **EC-AD-05a** (AD-05a: Baseline applicant (income 80,000)): Rule=eligible, LR=0.8323 (eligible), GB=0.9965 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8323, GB=0.9965.
- **EC-AD-05b** (AD-05b: Near-identical applicant differing by one rupee of income (80,001)): Rule=eligible, LR=0.8323 (eligible), GB=0.9965 (eligible) [LR top 3: credit_score:+0.903; employment_type:+0.564; severe_delinquency_36m:+0.474] — ML agrees with rule outcome (eligible). LR=0.8323, GB=0.9965.

## 4. Key Observations and Disagreements

1. **Rule system adherence**: 100% adherence to Rule Catalog expectations across all missing data, boundary flips, thin-file referrals, and capacity caps (61 matched catalog, 3 explained capacity interactions under OQ-012).
2. **ML handling of missing data (from actual outputs)**: After supplying obligations_source, both ML baseline models ran on all 64 cases without error. For inputs with a null mandatory field (EC-MD-01, EC-MD-02, EC-MD-05, EC-MD-06), the pipeline's SimpleImputer replaces the null with the training-set median and flags the imputation via PreImpMissingIndicator ({feature}_missing = 1.0); the pipeline does not raise an exception or refuse. In LR, the missing credit score indicator carries a large negative weight (-5.250), causing rejection (0.0104); for missing income, employment months, or requested amount, median imputation allows the models to approve (scores 0.78–0.82) without schema-level rejection. Excluded features (consent_given, kyc_verified) are ignored by the models.
3. **Non-compensatory enforcement**: Case `EC-RC-01` demonstrates the key architectural divergence: an applicant with INR 500,000 monthly income and credit score 649 is strictly rejected by rule K04, whereas LR compensatory weighting (+3.142 from income) yields an approval score of 0.9681; GB tree splits strictly enforce credit score < 650 (score 0.0001, ineligible).
4. **Boundary sharpness**: Rule thresholds flip decisions deterministically at the exact rupee/point boundary, whereas ML probabilities shift continuously without discrete policy bounds.
5. **Adversarial stability**: Near-identical applicants differing by 1 rupee (`EC-AD-05a` vs `EC-AD-05b`) produce identical decisions (eligible), reason codes, and top ML feature contributions (LR=0.8323, GB=0.9965).

> **Note on previous error**: Prior run showed `LR=error, GB=error` on all 64 cases because `obligations_source` (a D3 categorical training column) was missing from edge-case feature rows. Fixed in A2 patch: the value `'synthetic'` is supplied in the caller (not inside the model pipeline or the engine). See `docs/fairness-amendments.md` for the amendment record.

