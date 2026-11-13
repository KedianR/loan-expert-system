# Lending Calculations Specification (v0.1)

Nov 5, 2026 · @Kulvinder

## 1. Conventions

These formulas implement the parameters in the Credit Policy and Rule Catalog. Where a value below disagrees with that document, the Credit Policy wins and this document must be corrected.

**Units and types**

- Money is INR. Use exact decimal arithmetic (for example Python `Decimal`), never binary floating point, for every amount, EMI and fee.
- Rates are annual percentages in inputs (14.5 means 14.5%); the monthly rate is r = annual / 1200.
- Tenure n is a whole number of months. Ratios such as FOIR are decimals (0.30 means 30%).

**Rounding**

- EMI and fees round half up to 2 decimal places.
- The recommended amount is rounded down to the nearest 5,000 and never rounded up.
- Ratios are kept unrounded in comparisons (so FOIR of exactly 0.30 qualifies for band A) and shown to 4 decimals in output.
- APR is shown to 2 decimals. Tests allow a tolerance of 0.01 percentage points on APR only.

**Parameters used** (names must match the parameter file)

| Name | Value |
| --- | --- |
| `min_amount`, `max_amount`, `amount_step` | 50,000; 25,00,000; 5,000 |
| `min_tenure_months`, `max_tenure_months` | 12; 60 |
| `income_multiple_cap` | 10 |
| `processing_fee_rate` | 0.02 of the sanctioned amount, GST excluded |
| `band_rate_A`, `band_rate_B`, `band_rate_C` | 12.0; 14.5; 18.0 (band midpoints) |
| `foir_cap_A`, `foir_cap_B`, `foir_cap_C` | 0.55; 0.50; 0.45 (post-loan) |

## 2. Formulas

Let I = monthly net income, O = existing monthly obligations, R = requested amount, n = tenure in months, and band-specific rate and cap as defined in the Credit Policy.

**F1. Existing FOIR**

```latex
\mathrm{FOIR}_{\mathrm{existing}} = \frac{O}{I}
```

**F2. Monthly rate**

```latex
r = \frac{\text{annual rate in percent}}{1200}
```

**F3. EMI for principal P**

```latex
\mathrm{EMI}(P) = P \cdot \frac{r\,(1+r)^{n}}{(1+r)^{n}-1}
```

**F4. Maximum affordable EMI** (the post-loan FOIR cap belongs to the applicant's band)

```latex
\mathrm{EMI}_{\max} = \mathrm{cap}_{\mathrm{band}} \cdot I - O
```

If EMI\_max is zero or negative, the maximum principal is zero, which makes the recommended amount fall below the minimum and fires rule A03.

**F5. Maximum principal supported by that EMI**

```latex
P_{\mathrm{EMI}} = \mathrm{EMI}_{\max} \cdot \frac{(1+r)^{n}-1}{r\,(1+r)^{n}}
```

**F6. Recommended amount**

```latex
P^{*} = 5000 \cdot \left\lfloor \frac{\min\left(R,\; P_{\mathrm{EMI}},\; 10\,I,\; 2500000\right)}{5000} \right\rfloor
```

If P\* is below 50,000, the decision is INELIGIBLE with INSUFFICIENT\_REPAYMENT\_CAPACITY. If P\* is below R, the binding limit is the smallest of the three caps; report it as the matching AMOUNT\_LIMITED\_BY code. If two caps tie, report capacity first, then income multiple, then product maximum. If the request is equal to or smaller than all three caps, the whole request fits: the binding limit is requested, even when a cap equals the request exactly.

**F7. Fee, net disbursed amount and repayment**

```latex
\mathrm{Fee} = 0.02\,P^{*},\qquad \mathrm{Net} = P^{*} - \mathrm{Fee},\qquad \mathrm{Total\ repayment} = n\cdot\mathrm{EMI}(P^{*})
```

Total interest is total repayment minus P\*. Total cost of credit is total interest plus the fee. The last-instalment adjustment is ignored in this prototype.

**F8. Post-loan FOIR**

```latex
\mathrm{FOIR}_{\mathrm{post}} = \frac{O + \mathrm{EMI}(P^{*})}{I}
```

**F9. APR (annualised internal rate of return including the fee)**

```latex
\mathrm{Net} = \sum_{t=1}^{n} \frac{\mathrm{EMI}(P^{*})}{(1+i)^{t}},\qquad \mathrm{APR} = 12\,i \times 100\%
```

Solve for the monthly rate i numerically (bisection is sufficient). The RBI Key Fact Statement prescribes its own APR method; confirm it against the current official annex before using these figures in any real disclosure.

## 3. Test vectors

These nine applicants were computed with exact decimal arithmetic and a bisection solver for APR, following the formulas above and the rule order in the Credit Policy. Use them as the first golden tests. All inputs not listed are assumed valid: KYC verified, consent given, no adverse history, enquiries under 6, salaried with enough tenure.

| ID | Income, obligations, score, requested, tenure | Band | Binding limit | Recommended | EMI | Fee | APR | Expected decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TV1 | 80,000; 10,000; 735; 7,00,000; 36 | B | Requested amount | 7,00,000 | 24,094.68 | 14,000.00 | 15.93% | ELIGIBLE. Post-loan FOIR 0.4262 |
| TV2 | 40,000; 12,000; 760; 8,00,000; 48 | A (FOIR exactly 0.30) | Repayment capacity: P\_EMI is 3,79,739.59 | 3,75,000 | 9,875.19 | 7,500.00 | 13.09% | ELIGIBLE on reduced terms, AMOUNT\_LIMITED\_BY\_REPAYMENT\_CAPACITY. Post-loan FOIR 0.5469 |
| TV3 | 50,000; 0; 720; 9,00,000; 60 | B | Income multiple cap: 5,00,000 | 5,00,000 | 11,764.14 | 10,000.00 | 15.42% | ELIGIBLE on reduced terms, AMOUNT\_LIMITED\_BY\_INCOME\_MULTIPLE. Post-loan FOIR 0.2353 |
| TV4 | 1,00,000; 20,000; 700; 5,00,000; 24 | B (score exactly 700) | Requested amount | 5,00,000 | 24,124.71 | 10,000.00 | 16.57% | ELIGIBLE. Post-loan FOIR 0.4412 |
| TV5 | 1,00,000; 30,000; 750; 3,00,000; 24 | A (score 750 and FOIR 0.30, both exact) | Requested amount | 3,00,000 | 14,122.04 | 6,000.00 | 14.05% | ELIGIBLE. Post-loan FOIR 0.4412 |
| TV6 | 1,00,000; 50,000; 650; 3,00,000; 24 | C (FOIR exactly 0.50) | EMI\_max is -5,000 | none | none | none | none | INELIGIBLE, INSUFFICIENT\_REPAYMENT\_CAPACITY (rule A03) |
| TV7 | 1,00,000; 50,001; 700; 3,00,000; 24 | none (FOIR just above 0.50) | none | none | none | none | none | INELIGIBLE, HIGH\_EXISTING\_OBLIGATIONS (rule E01) |
| TV8 | 15,000; 6,500; 700; 1,00,000; 12 | C (FOIR 0.4333 is above 0.40) | EMI\_max is 250; P\_EMI is 2,726.88 | none | none | none | none | INELIGIBLE, INSUFFICIENT\_REPAYMENT\_CAPACITY (rule A03) |
| TV9 | 60,000; 5,000; 680; 2,50,000; 36 | C | Requested amount | 2,50,000 | 9,038.10 | 5,000.00 | 19.46% | ELIGIBLE. Post-loan FOIR 0.2340 |

TV2, TV4, TV5, TV6 and TV7 sit exactly on policy boundaries, so they catch off-by-one comparison errors (at or above versus above). Total repayment and total interest for each eligible vector are EMI times n, and EMI times n minus the recommended amount.

## 4. Edge cases and implementation notes

**Edge cases the code must handle**

- [ ] Income missing: stop before any division and return REFER through V01. Income of zero: do not divide; record existing\_foir as unknown and let K05 fire INELIGIBLE, which takes precedence; never divide by zero
- [ ] Obligations of zero: FOIR is 0 and the band depends on score alone
- [ ] Negative EMI\_max: treat the maximum principal as zero, never as a negative loan amount
- [ ] Requested amount that is not a multiple of 5,000: floor to 5,000 as in F6 and report a reduced offer only if the result is below the request by at least one step
- [ ] Requested amount at exactly 50,000 or 25,00,000 and tenure at exactly 12 or 60: accepted, not rejected
- [ ] Recommended amount exactly 50,000: accepted; 49,999 after rounding down means below minimum
- [ ] A cap tie in F6: apply the stated tie order (capacity, income multiple, product maximum)
- [ ] Very small monthly rate: if r is zero, EMI is P divided by n (not expected with the bands here, but guard it)
- [ ] APR solver failure to converge: return an explicit error and log it, never a guessed value

**Implementation notes**

- Implement each formula as a pure function with its own unit tests; the rule engine calls these functions rather than recomputing.
- Store every intermediate (existing FOIR, EMI\_max, P\_EMI, each cap, binding limit, EMI, fee, APR) in the decision trace, so the reason text and the audit log use the same numbers.
- Parameters come from the parameter file by name. Changing a value there must change both the rules and the calculations.
- Property tests to add: P\* never exceeds R, P\_EMI, 10 I or 2,500,000; EMI(P\_EMI) is within one rupee of EMI\_max; P\* is always a multiple of 5,000; APR is at least the band rate for any positive fee.

**Open items**

- [ ] Confirm the RBI KFS APR method and update F9 if it differs
- [ ] Decide whether GST on the processing fee enters the APR
- [ ] Decide whether to pick a point rate inside the band instead of the midpoint
