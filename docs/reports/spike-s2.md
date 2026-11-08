# Spike S2 Report: Data Feasibility for Home Credit

**Date:** 2026-11-08
**Phase:** 0 (WP-02)
**Requirement:** DR-04

## 1. Objective

Assess whether the Home Credit Default Risk dataset can be obtained, used under its licence, and mapped to the fact fields in docs/04-predicates-and-facts.md. Identify which fields can and cannot be filled, and state the fallback.

## 2. Data availability

- **No network access.** The sandbox environment does not have network access. The dataset at `https://kaggle.com/c/home-credit-default-risk` could not be downloaded or verified.
- **No files in `data/raw/`.** The directory is empty. No column names or data types could be inspected.
- **All column-name mappings below come from docs/08-datasets.md §3.** They are documented assumptions from public documentation, not verified. WP-15 must check every name against the actual files.

## 3. Licence and terms of use

Per docs/08-datasets.md §2:

- The dataset is hosted on Kaggle under competition terms. The entry notes: "Kaggle competition terms may restrict use."
- The terms of Kaggle competitions typically allow use for academic and non-commercial purposes but may restrict redistribution.
- **This must be verified in WP-15** by reading the actual competition rules page. Until then, no raw data is committed (AGENTS.md Hard Rule 9).

**Assessment:** Likely usable for this academic prototype, but licence terms must be confirmed before any data is downloaded.

## 4. Fact field coverage

Using the mapping table from docs/08-datasets.md §3 and the input facts from docs/04-predicates-and-facts.md §2:

| Fact field | Required | Can Home Credit fill it? | Source column(s) | Assumption ID | Strength | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `applicant_id` | Yes | ✅ Yes | `SK_ID_CURR` | — | Strong | Unique per application |
| `age` | Yes | ✅ Yes | `DAYS_BIRTH` | — | Strong | `floor(-DAYS_BIRTH / 365.25)` |
| `employment_type` | Yes | ✅ Yes | `NAME_INCOME_TYPE` | ASM-D1 | Medium | Mapping: Working/State servant → salaried, Commercial associate → self_employed, others → other |
| `employment_months` | Yes | ✅ Yes | `DAYS_EMPLOYED` | ASM-D2 | Medium | `floor(-DAYS_EMPLOYED / 30.4)`; sentinel 365243 → unknown |
| `monthly_net_income` | Yes | ⚠️ Partial | `AMT_INCOME_TOTAL` | ASM-D3 | Medium | Annual ÷ 12; **gross not net** — overstates disposable income |
| `monthly_obligations` | Yes | ⚠️ Weak | `bureau.AMT_ANNUITY` | ASM-D4 | **Weak** | Sum of active credits; many missing; fallback distribution needed |
| `credit_score` | No (nullable) | ⚠️ Weak | `EXT_SOURCE_1/2/3` | ASM-D5 | **Weak** | Mean of non-missing × 600 + 300; **not a real credit score** |
| `enquiries_6m` | Yes | ⚠️ Partial | `AMT_REQ_CREDIT_BUREAU_MON/QRT` | ASM-D6 | Medium | Sum covers ~3 months, not 6 |
| `severe_delinquency_36m` | Yes | ✅ Yes | `bureau_balance.STATUS` | ASM-D7 | Medium | Status 4/5 with `MONTHS_BALANCE ≥ -36` |
| `written_off` | Yes | ✅ Yes | `bureau.CREDIT_ACTIVE` | ASM-D8 | Medium | `Bad debt` value |
| `kyc_verified` | Yes | ❌ No | — | ASM-D9 | N/A | Always `true` (no KYC data in the dataset) |
| `consent_given` | Yes | ❌ No | — | ASM-D9 | N/A | Always `true` (no consent data in the dataset) |
| `requested_amount` | Yes | ✅ Yes | `AMT_CREDIT` | ASM-D10 | Medium | This is the approved credit amount, not the original request |
| `requested_tenure_months` | Yes | ⚠️ Weak | `AMT_CREDIT / AMT_ANNUITY` | ASM-D11 | **Weak** | Ignores interest, understates tenure |
| `region_tier` (X02 only) | No | ✅ Yes | `REGION_RATING_CLIENT` | ASM-D12 | Medium | 1-to-3 rating maps directly |

**Audit-only fields (fairness module only):**

| Field | Available? | Source |
| --- | --- | --- |
| `gender` | ✅ Yes | `CODE_GENDER` |
| `age band` | ✅ Yes | Derived from `age` |
| `education` | ✅ Yes | `NAME_EDUCATION_TYPE` |
| `family status` | ✅ Yes | `NAME_FAMILY_STATUS` |

## 5. Fields that CANNOT be filled

| Field | Why | Impact |
| --- | --- | --- |
| `kyc_verified` | Not in the dataset | Set to `true` for all rows; V02/K02 never fire on D2 data |
| `consent_given` | Not in the dataset | Set to `true` for all rows; V02 never fires on D2 data |

These are structural: no public credit dataset has KYC or consent fields. The rules V02 and K02 are tested via synthetic data (D1, D3) only.

## 6. Weak mappings requiring sensitivity checks

Three mappings are marked **Weak** in docs/08-datasets.md and materially affect results:

1. **ASM-D4 (monthly_obligations):** Missing for many applicants. Fallback distribution must be documented. Sensitivity check: run with bureau-only, fallback-only, and both.
2. **ASM-D5 (credit_score):** External scores are normalised 0–1, not bureau scores. The 300 + 600 × mean transformation is arbitrary. Sensitivity check: vary the scaling.
3. **ASM-D11 (requested_tenure_months):** Dividing credit by annuity ignores interest. Tenure is understated. Sensitivity check: add a typical interest allowance.

## 7. Currency and product-fit issues

- **Amounts are not in INR.** The dataset does not state a currency. Amounts are likely in the local currency of the originating market. No rescaling is applied by default.
- **Many rows will fail product-limit rules.** V03 (amount outside 50,000–25,00,000 INR) and V04 (tenure outside 12–60 months) may reject a large proportion of rows. docs/08-datasets.md §3 says: count and report these; optionally run a filtered analysis.

## 8. Fallback dataset

If Home Credit is impractical (licence, size, or mapping quality):

- **Give Me Some Credit** (Kaggle): Age, monthly income, debt ratio, past-due counts, repayment label. No gender (only age for fairness). No employment, enquiries, or requested loan amount. Suitable for outcome experiment only, not full rule coverage.
- **Synthetic population D3** for group-level fairness analysis, with the caveat that gender effects are then based on synthetic data only.

Per docs/08-datasets.md §2: "Use Home Credit for D2 and the fairness review. If its terms or size make it impractical, use Give Me Some Credit for the outcome experiment and D3 for group analysis."

## 9. Conclusion

Home Credit Default Risk is **feasible but requires documented assumptions** for every mapped field. Three mappings are weak and need sensitivity checks. Two fields (`kyc_verified`, `consent_given`) cannot be filled and are set to `true`. Column names and licence must be verified against the actual files in WP-15.

**No data was downloaded. No mapping code was written. No raw data is committed.**
