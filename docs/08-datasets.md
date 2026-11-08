# Dataset Mapping and Synthetic Data Specification (v0.1)

Nov 5, 2026 · @Kulvinder

## 1. Data roles and strategy

No public dataset has the fields the rules need (credit score, requested tenure, KYC, consent, existing obligations), so the project uses three datasets, each with one job. This is the main design decision of the data work: it lets the rules be tested exactly while the comparison and fairness work still rests on real-world data.

| Dataset | Source | Purpose | Label | Used by |
| --- | --- | --- | --- | --- |
| D1. Rule-coverage set | Synthetic, deterministic | Exercise every rule and every threshold boundary; feed the golden and boundary tests | Expected decision from the reference oracle (section 4) | WP-07 to WP-11 |
| D2. Mapped public set | One public credit dataset mapped to the fact schema | Real-world comparison of rules and ML, and the group-level fairness review | Observed repayment outcome in the dataset | WP-15, WP-17, WP-18, WP-20 |
| D3. Synthetic population | Synthetic, seeded | Large, controlled population for the policy-label experiment and for validating the fairness pipeline | Policy decision (oracle), with an optional simulated outcome | WP-16, WP-17, WP-20 |

**Why two kinds of label.** The SRS leaves open what "eligible" means. The plan answers it by running two experiments, and the report must keep them apart:

- **Outcome experiment (D2).** Compare each system's approvals with observed repayment. This tests whether the policy and the ML model pick good borrowers. It cannot test policy compliance.
- **Policy experiment (D3).** Train the ML model to imitate the policy decision, then study where it disagrees with the rules. This tests transparency, auditability and edge cases. It is partly circular by design, because the rules define the label, and must be described that way.

**Limits to state in the report.** Mapped public data needs documented assumptions for every field the dataset lacks. Results from D2 therefore describe this policy on this mapped data, not lending in general. Repayment outcomes exist only for applicants who were approved, so selection bias applies.

## 2. Public dataset candidates

**Home Credit Default Risk is the recommended D2 dataset**, because it is the only one of the four that has gender, age, income, employment, bureau enquiries, an external score and a repayment label together. The column details below come from the dataset's public documentation as recalled when this spec was written; WP-15 must check every name against the actual files before any code relies on it.

| Dataset | Source | Useful for | Sensitive attributes | Main limits | Recommended role |
| --- | --- | --- | --- | --- | --- |
| [Home Credit Default Risk](https://kaggle.com/c/home-credit-default-risk) | Kaggle | Income, employment, requested credit amount and annuity, external scores, bureau enquiries, repayment label | Gender, age, education, family status, region rating | Large and heavy to preprocess; several tables; amounts have no stated currency; Kaggle competition terms may restrict use | Primary D2 |
| [Give Me Some Credit](https://kaggle.com/c/givemesomecredit) | Kaggle | Age, monthly income, debt ratio, past-due counts, repayment label | Age only | No gender; no employment, enquiries or requested loan; about 20% of income values missing | Secondary: check that ML baseline results hold on a second set |
| [German Credit](<https://archive.ics.uci.edu/ml/datasets/statlog+(german+credit+data)>) | UCI | Credit amount, duration, employment length, age, repayment label | Age; sex mixed with marital status in one field | 1,000 rows from 1994; currency is Deutsche Mark; one study cited in the Development Reference says its protected attribute cannot be reliably retrieved | Optional small sanity set; not for fairness conclusions |
| [Taiwan credit-card default](https://archive.ics.uci.edu/ml/datasets/default+of+credit+card+clients) | UCI | Payment history across months, credit limit, repayment label | Sex, age, education, marital status | No income and no loan request; credit-card context, not instalment loans | Not used; rules cannot run on it without inventing most inputs |

**Recommendation and fallback**

- Use Home Credit for D2 and the fairness review. If its terms or size make it impractical, use Give Me Some Credit for the outcome experiment and the synthetic population D3 for group analysis, and say in the report that gender is then covered only by synthetic data.
- Check each dataset's licence and terms of use in WP-15 and record them in its datasheet. Do not redistribute raw data in the repository; store download scripts and checksums instead.
- Do not mix datasets into one table. Each is mapped, split and reported separately.

## 3. Column-to-fact mapping (Home Credit)

Each row maps one fact in the Predicate and Fact Schema to dataset columns. The "Assumption" column is what the report must disclose. Rows marked **weak** change results materially and need a sensitivity check (section 5). Column names are from public documentation and must be verified in WP-15.

| Fact | Source columns | Transformation | Assumption ID | Strength |
| --- | --- | --- | --- | --- |
| `age` | `DAYS_BIRTH` (days before application, negative) | Whole years: floor of `-DAYS_BIRTH / 365.25` | none | Strong |
| `employment_type` | `NAME_INCOME_TYPE` | `Working` and `State servant` become `salaried`; `Commercial associate` becomes `self_employed`; all other values become `other` | ASM-D1 | Medium |
| `employment_months` | `DAYS_EMPLOYED` | Floor of `-DAYS_EMPLOYED / 30.4`; the sentinel value 365243 (not employed or pensioner) becomes unknown | ASM-D2 | Medium |
| `monthly_net_income` | `AMT_INCOME_TOTAL` (annual total income) | Divide by 12; this is gross, not net | ASM-D3 | Medium |
| `monthly_obligations` | Not in the main table; `bureau` table `AMT_ANNUITY` for active credits | Sum for each applicant; where the bureau value is missing, draw from the fallback distribution in section 4, flagged per row | ASM-D4 | **Weak** |
| `credit_score` | `EXT_SOURCE_1`, `EXT_SOURCE_2`, `EXT_SOURCE_3` (normalised external scores, 0 to 1) | Mean of the non-missing values, then `300 + 600 * mean`; unknown if all three are missing | ASM-D5 | **Weak** |
| `enquiries_6m` | `AMT_REQ_CREDIT_BUREAU_MON`, `AMT_REQ_CREDIT_BUREAU_QRT` | Sum, which covers about 3 months; the 6-month window is not available | ASM-D6 | Medium |
| `severe_delinquency_36m` | `bureau_balance` `STATUS` and `MONTHS_BALANCE` | True if any status of 4 or 5 (90+ days past due) with `MONTHS_BALANCE` of -36 or later; false if the applicant has records but none match; unknown if no bureau history | ASM-D7 | Medium |
| `written_off` | `bureau` `CREDIT_ACTIVE` | True if any credit has the value `Bad debt` | ASM-D8 | Medium |
| `kyc_verified` | none | True for every row | ASM-D9 | Not applicable |
| `consent_given` | none | True for every row | ASM-D9 | Not applicable |
| `requested_amount` | `AMT_CREDIT` | Use as is | ASM-D10 | Medium |
| `requested_tenure_months` | `AMT_CREDIT`, `AMT_ANNUITY` | Round `AMT_CREDIT / AMT_ANNUITY`; ignores interest, so tenure is understated | ASM-D11 | **Weak** |
| `region_tier` (only for X02) | `REGION_RATING_CLIENT` | Use the 1 to 3 rating as is | ASM-D12 | Medium |

**Audit-only fields (never in the fact base):** `CODE_GENDER`, age band (derived from `age`), `NAME_EDUCATION_TYPE`, `NAME_FAMILY_STATUS`. They are stored by `applicant_ref` for the fairness module. `REGION_RATING_CLIENT`, occupation and education are also proxy candidates and appear in the proxy review list for the ML model.

**Handling of rows that do not fit the product**

- Amounts are not rescaled to INR by default. Count and report how many rows fail V03 (amount limit), V04 (tenure limit) and K05 (minimum income), as a measure of how well the product matches the data.
- Optionally, run a second analysis on rows that pass V03 and V04 only, and state that this is a filtered subset.
- Each fact gets a flag column recording whether its value is observed, derived or filled from a fallback, so reports can separate them.

## 4. Synthetic data generator

One generator package in `data/synthetic/` produces D1 and D3. It reads the parameter file and a generator configuration, takes a seed, and writes the same output every time for the same inputs. All distribution values below are **placeholders** to be fixed in WP-16 and recorded in the generator configuration; they are not claims about real borrowers.

**D1. Rule-coverage set (deterministic, no randomness)**

- Start from one clean base applicant who passes every rule (similar to TV1).
- For every threshold read from the parameter file, add three applicants that change only that field to just below, exactly at and just above the threshold. Thresholds cover amount limits, tenure limits, minimum age, income, credit score, employment months by type, existing FOIR, enquiries, and each band boundary.
- For every boolean rule input (severe delinquency, written off, KYC, consent), add an applicant with the adverse value.
- Add multi-failure applicants (for example K03, K04 and K05 together), applicants that trigger only REFER rules, applicants that trigger both REFER and INELIGIBLE rules, and applicants with each required field missing in turn, plus a null credit score.
- Add cap-tie applicants for formula F6, and requested amounts that are not multiples of 5,000.
- Name each applicant by what it tests, for example `k04_score_below_min`, so failures read clearly.

**D3. Synthetic population (seeded)**

| Field | Placeholder distribution |
| --- | --- |
| `age` | Between 21 and 60, roughly uniform |
| `employment_type` | 70% salaried, 25% self-employed, 5% other |
| `employment_months` | Skewed towards shorter tenures; longer for older applicants |
| `monthly_net_income` | Log-normal with a median near 40,000 and a wide spread; floor of 8,000 |
| `monthly_obligations` | Income times a share drawn from a distribution with mean near 0.2; zero for about 25% of applicants |
| `credit_score` | Normal with mean near 700 and standard deviation near 70, clipped to 300 to 900; null for about 5% |
| `enquiries_6m` | Poisson with mean near 2 |
| `severe_delinquency_36m` | About 6% true; more likely at low scores |
| `written_off` | About 1% true |
| `kyc_verified`, `consent_given` | About 98% and 99% true |
| `requested_amount` | A multiple of monthly income between about 2 and 15, rounded to 5,000, clipped to the product range |
| `requested_tenure_months` | Chosen from 12, 24, 36, 48 or 60 |

Default size is 20,000 applicants. Make the correlations simple and documented (income with age and tenure, score with delinquency) rather than elaborate.

**Protected attributes in D3.** Assign `gender`, an age band and a region tier in the audit-only store. By default they are drawn independently of every other field, so no group effect exists except through rules that use age or region.

**Bias-injection mode (validates the fairness pipeline).** A switch applies a known, documented gap, for example shifting income for one group by a stated percentage. Running the fairness review on that data must detect the gap and report it with a confidence interval. If it does not, the fairness pipeline is broken. Keep this mode off in the reported experiments.

**Reference oracle.** Write a small, separate implementation of the policy in plain Python, without rule files or the engine, used only by tests. It computes the expected decision, reason codes, amount and band for any applicant. Tests compare the engine with the oracle on all of D1 and D3 and report every difference. Differences mean a bug in the engine, the oracle or the documents, and each one must be resolved, not waved away. The oracle is written by following the Credit Policy and Calculations documents directly, not by reading the engine code.

**Simulated outcome (optional)**

- For D3 only, simulate repayment as a random draw from a logistic function of score, existing FOIR and delinquency, with coefficients stored in the generator configuration.
- Use it only to check that the pipeline runs on a dataset with an outcome label. Never present simulated outcomes as evidence about real lending.

## 5. Labels, splits, preprocessing, documentation and open items

**Labels**

| Dataset | Positive class | Notes |
| --- | --- | --- |
| D1 | Not used for ML | Expected decision from the oracle, for tests only |
| D2 | Observed payment difficulty or default in the dataset's target column | Policy approvals are compared against it; ML trains on it |
| D3 | Policy decision `eligible` versus not, from the oracle | Three-way (`eligible`, `ineligible`, `refer`) kept for analysis; the ML baseline predicts eligible versus not |

The `refer` outcome has no ML equivalent. Report it separately and do not count it as a denial or an approval when comparing approval rates, or show both treatments.

**Splits (D2 and D3)**

- Train 70%, validation 15%, test 15%, stratified on the label, with a fixed seed stored in configuration.
- Split by applicant, and for D2 by `SK_ID_CURR` so that no applicant appears in two splits.
- Fit all preprocessing on the training split only. Save the split indices so every run uses identical data.
- The rule system needs no training, but it is evaluated on the same test split as the ML model.

**ML preprocessing**

- Features: the mapped fact fields plus derived ratios. No protected attributes as features.
- Review and list proxy features (region rating, occupation, education, income type) and report results with and without them.
- Impute and encode inside a pipeline fit on the training split. Keep the missing-value flags as features, since missingness is informative here.
- Record class balance and handle imbalance in one documented way (class weights by default).

**Sensitivity checks for the weak mappings**

- [ ] Vary the credit-score transformation (ASM-D5), for example a different scaling, and show how approvals and group gaps move
- [ ] Vary the obligations source (ASM-D4): bureau-derived only, fallback only, and both
- [ ] Vary the tenure assumption (ASM-D11) by adding a typical interest allowance
- [ ] Report results on rows with observed values only, as well as on all rows

**Documentation required for every dataset**

- [ ] Datasheet with motivation, composition, collection process, known issues, licence and terms of use, and intended use
- [ ] Mapping table with the assumption IDs above and the row counts affected by each
- [ ] Download script and checksums; no raw data committed
- [ ] Row counts after each filter, so the report can show how many applicants were dropped and why

**Requirements covered:** DR-01, DR-02, DR-04, DR-05, FR-21 to FR-24.

**Open items**

- [ ] Confirm Home Credit as D2, or choose Give Me Some Credit as the fallback
- [ ] Verify every column name and the licence in WP-15
- [ ] Decide whether to rescale amounts to INR, and by what rule
- [ ] Set the generator's placeholder distributions in WP-16
- [x] Minimum group size for fairness reporting set to 100 applicants per group (default accepted 2026-11-06)
- [ ] Decide whether D3 includes the simulated outcome
