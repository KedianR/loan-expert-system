# Phase 4 report

Date: 2026-11-12  
Commit hash: **a400b9c** (`git rev-parse --short HEAD`)  
Agent session: phase4-session  

---

## Step 0: Confirm the Base

1. **`make oracle-diff`**: 0 differences across all D1 cases. Status: MATCH.
2. **Hygiene grep**: `git grep -nwE "5000|50000|2500000|0\.02" -- src/engine` → empty (exit 1). Status: PASS.
3. **`make check`, `make check-rules`, `make test`**: All pass. Rule-set tag `rules-1.0.0+params-0.1.0`, SHA-256 `sha256:eb7073a388817e0a455997c0c2ea86ccb25524cdff07faf8bf5ca98bb267be5a` matches `tests/golden/rule_set_pin.json`.
4. **`docs/datasheets/home-credit-terms.md`**: Exists; states "use for coursework or non-commercial research: allowed." No placeholders. Status: PASS.
5. **Raw data**: `data/raw/` holds all three files. SHA-256 values equal `data/checksums/home_credit.sha256`. `git check-ignore -v data/raw/application_train.csv` → `.gitignore:30:data/raw/`. Status: PASS.
6. **Column header verification**: All 17 required columns match `config/d2_mapping.toml` exactly. 0 missing, 0 different. Status: PASS.
7. **Dependency dry-run**: `python -m pip install --dry-run pandas numpy scikit-learn joblib` → all already satisfied on Python 3.14.2. Status: PASS.
8. **Float ban configuration**: `Makefile` target `check-floats` runs `python tools/check_floats.py src/calc src/facts src/explain src/data/d2_map.py`. Covers four paths: `src/calc/`, `src/facts/`, `src/explain/`, and `src/data/d2_map.py` (9 files total).

---

## 1. Summary

Phase 4 deliverables complete: D2 data mapping of Home Credit Default Risk to the loan expert system fact schema, D3 synthetic population generation, stratified 70/15/15 splits, batch decision evaluations, ML baseline (Logistic Regression + HistGradientBoosting), group-size tables, datasheets, model card, and integrity manifest (WP-15, WP-16b, WP-17). `make phase4` runs all stages in order and passes all Phase 4 checks.

Zero policy values, rules, parameters, or schemas were altered. Rule-set hash unchanged.

---

## 2. `make phase4` — Last 15 Lines (commit a400b9c)

```text
OK: all hygiene checks passed with zero findings.
python tools/oracle_diff.py
Diff report written to …\data\d1\oracle_diff.md (0 differences).
python -m src.data.manifest
Manifest written to data\manifest.json
python -m src.data.group_sizes
Group sizes for d2 written to data\group_sizes\d2_group_sizes.csv:
  Total groups evaluated: 30, Groups < 100 on test: 4
Group sizes for d3 written to data\group_sizes\d3_group_sizes.csv:
  Total groups evaluated: 17, Groups < 100 on test: 1
"=== Phase 4 complete ==="
```

`make phase4` order (from `docs/experiment-protocol.md` §2):
1. `data-d2` → 2. `data-d3` → 3. `decide-d3` → 4. `split` → 5. `decide-d2` → 6. `baseline` → Phase 4 checks → `manifest` → `group_sizes`.

---

## 3. Reproducibility — SHA-256 Comparison (run 1 → run 2)

Both `make data-d2`, `make data-d3`, and `make baseline` were run twice. All hashes are identical.

| File | Run 1 SHA-256 | Run 2 SHA-256 | Equal? |
|---|---|---|---|
| `data/mapped/d2_mapped.csv` | `44de1b82…6eae4` | `44de1b82…6eae4` | ✅ |
| `data/protected/d2_protected.csv` | `d539e950…017f` | `d539e950…017f` | ✅ |
| `data/synthetic/d3_population.csv` | `2311690b…19ef` | `2311690b…19ef` | ✅ |
| `data/protected/d3_protected.csv` | `f2bbd239…c44` | `f2bbd239…c44` | ✅ |
| `reports/ml/metrics_d2_lr.json` | `d45e2ce0…e219` | `d45e2ce0…e219` | ✅ |
| `reports/ml/metrics_d2_gb.json` | `a58dc871…851` | `a58dc871…851` | ✅ |
| `reports/ml/metrics_d3_lr.json` | `c4fe5aff…e89` | `c4fe5aff…e89` | ✅ |
| `reports/ml/metrics_d3_gb.json` | `d74d93b2…c7` | `d74d93b2…c7` | ✅ |
| `reports/ml/metrics_d3_sim_lr.json` | `20acd369…e55` | `20acd369…e55` | ✅ |

**Full SHA-256 values:**
```
data/mapped/d2_mapped.csv:            44de1b821cd3c4831b485b39435998e53c3f10754c7a069046bbca0f0ca6eae4
data/protected/d2_protected.csv:      d539e950a8a340470788b827a16678efd8c3ecb8f70dcf1f50980f2a1189017f
data/synthetic/d3_population.csv:     2311690bfaf45d7e944f5e572bdd50d0f5a768494480d54d78a88b1b8ed619ef
data/protected/d3_protected.csv:      f2bbd239ee35022ab99c69f32343962c2e33f84173a471a7d07b1499cd673c44
reports/ml/metrics_d2_lr.json:        d45e2ce0f55b2359a6e1c3af3fc5fcf461f3025f64089f5011b8ef4610c7e219
reports/ml/metrics_d2_gb.json:        a58dc871cbd4257c70001e27d425b3c3e2f1cc8ac22eea9d220cb397190ba851
reports/ml/metrics_d3_lr.json:        c4fe5aff7ae57d316e42258fac721bac214c441b6f0ad8102e8b5942e199be89
reports/ml/metrics_d3_gb.json:        d74d93b2d707791f8d25342b55cba911ebfb993f46a53980c69da398c412b0c7
reports/ml/metrics_d3_sim_lr.json:    20acd369fb433eddbf8961e30d15c7a5f1af249a1b4dc94c80e01fae33f67e55
```

**`data/manifest.json`:**

```json
{
  "raw_files": {
    "data/raw/application_train.csv": "52e96b895b1112e1c853f670e58372719c8441c5ed1c57ac2f7fad559d784f5f",
    "data/raw/bureau.csv": "9d799143423f280720cf51c1bfbbab2a0422da8ff2763335bb30bf43155494f7",
    "data/raw/bureau_balance.csv": "33e09f06174c26f0be6b8b7398886c69e7bf0abbb29b4122f7841ffe545729a9"
  },
  "d2_mapped": {
    "path": "data/mapped/d2_mapped.csv",
    "sha256": "44de1b821cd3c4831b485b39435998e53c3f10754c7a069046bbca0f0ca6eae4"
  },
  "d3_population": {
    "path": "data/synthetic/d3_population.csv",
    "sha256": "2311690bfaf45d7e944f5e572bdd50d0f5a768494480d54d78a88b1b8ed619ef"
  },
  "splits": {
    "d2": {
      "path": "data/splits/d2_split.csv",
      "sha256": "b4d17251eb41042137be01ea4e2363fae78b206ccedc2d87bcc6b89a95e19f47"
    },
    "d3": {
      "path": "data/splits/d3_split.csv",
      "sha256": "6f3b92f0ff0fa837e335eb779eadcb47253c108954d007bab8ae2446d0c08c6e"
    }
  },
  "policy": {
    "params_sha256": "4c2698607ae7ea824fc62f39a84ac52fa69db1b59c0657ffeb152b0960885373",
    "rule_set_hash": "sha256:eb7073a388817e0a455997c0c2ea86ccb25524cdff07faf8bf5ca98bb267be5a",
    "rule_set_version": "rules-1.0.0+params-0.1.0"
  }
}
```

---

## 4. Decision Statistics

### 4.1 D2 Decisions (`data/decisions/d2_decisions.csv`)

> Evaluated rows: 92,254 (validation + test splits of the full 307,511 mapped rows).

**Decision share:**

| Decision | Count | Share |
|---|---|---|
| ineligible | 82,663 | 89.60% |
| refer | 8,046 | 8.72% |
| eligible | 1,545 | 1.67% |
| **Total** | **92,254** | **100%** |

**Reason-code frequency table** (a row may carry multiple codes; count = rows where code fired):

| Reason Code | Rule | Count | Share of evaluated |
|---|---|---|---|
| `CREDIT_SCORE_BELOW_MINIMUM` | K04 | 59,969 | 65.00% |
| `INCOME_BELOW_MINIMUM` | K05 | 57,057 | 61.85% |
| `HIGH_EXISTING_OBLIGATIONS` | E01 | 12,796 | 13.87% |
| `TENURE_OUTSIDE_PRODUCT_LIMITS` | V04 | 10,345 | 11.21% |
| `INCOMPLETE_APPLICATION` | V01 | 8,027 | 8.70% |
| `EMPLOYMENT_TENURE_TOO_SHORT` | K06 | 7,546 | 8.18% |
| `EMPLOYMENT_TYPE_REQUIRES_REVIEW` | R03 | 1,488 | 1.61% |
| `AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY` | A04 | 1,054 | 1.14% |
| `ADVERSE_REPAYMENT_HISTORY` | K03 | 541 | 0.59% |
| `AMOUNT_LIMITED_BY_INCOME_MULTIPLE` | A03 | 481 | 0.52% |
| `AMOUNT_OUTSIDE_PRODUCT_LIMITS` | V03 | 270 | 0.29% |
| `INSUFFICIENT_REPAYMENT_CAPACITY` | E01 | 127 | 0.14% |
| `HIGH_RECENT_ENQUIRIES` | R02 | 106 | 0.11% |
| `NO_CREDIT_HISTORY` | R01 | 13 | 0.01% |

**Rows failing V03, V04, K05** (in this evaluated set):

| Rule | Reason Code | Count | Share |
|---|---|---|---|
| V03 | `AMOUNT_OUTSIDE_PRODUCT_LIMITS` | 270 | 0.29% |
| V04 | `TENURE_OUTSIDE_PRODUCT_LIMITS` | 10,345 | 11.21% |
| K05 | `INCOME_BELOW_MINIMUM` | 57,057 | 61.85% |

> For context: across the full 307,511 mapped D2 rows, the mapping table reports V03: 922 rows (0.30%), V04: 34,671 rows (11.27%), K05: 190,865 rows (62.07%) — consistent with the validation/test sample.

**Refer decisions from V01 or R01** (experiment-protocol §3 requirement):

| Code | Rule | Refer count | % of all refer |
|---|---|---|---|
| `INCOMPLETE_APPLICATION` | V01 | 8,027 | 99.76% |
| `NO_CREDIT_HISTORY` | R01 | 13 | 0.16% |
| **V01 or R01 combined** | — | **8,031** | **99.81%** |

> **Interpretation**: 99.81% of D2 refer decisions come from unknown facts (V01: missing required facts, R01: no credit history). This means the comparison evidence is weak for the refer population: nearly all refer rows would need manual review precisely because a key fact is unknown, so treating them as either approved or denied introduces noise. The reviewer should factor this in when interpreting Treatment A vs. B results.

---

### 4.2 D3 Decisions (`data/decisions/d3_decisions.csv`)

> Evaluated rows: 20,000 (full synthetic population).

**Decision share:**

| Decision | Count | Share |
|---|---|---|
| eligible | 9,449 | **47.24%** |
| ineligible | 9,054 | 45.27% |
| refer | 1,497 | 7.49% |
| **Total** | **20,000** | **100%** |

**Reason-code frequency table:**

| Reason Code | Rule | Count | Share |
|---|---|---|---|
| `CREDIT_SCORE_BELOW_MINIMUM` | K04 | 4,426 | 22.13% |
| `AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY` | A04 | 3,481 | 17.41% |
| `EMPLOYMENT_TENURE_TOO_SHORT` | K06 | 2,813 | 14.06% |
| `AMOUNT_LIMITED_BY_INCOME_MULTIPLE` | A03 | 1,746 | 8.73% |
| `ADVERSE_REPAYMENT_HISTORY` | K03 | 1,650 | 8.25% |
| `INCOME_BELOW_MINIMUM` | K05 | 1,214 | 6.07% |
| `NO_CREDIT_HISTORY` | R01 | 737 | 3.69% |
| `EMPLOYMENT_TYPE_REQUIRES_REVIEW` | R03 | 641 | 3.21% |
| `INSUFFICIENT_REPAYMENT_CAPACITY` | E01 | 432 | 2.16% |
| `KYC_NOT_VERIFIED` | K02 | 367 | 1.84% |
| `HIGH_EXISTING_OBLIGATIONS` | E01 | 295 | 1.47% |
| `CONSENT_NOT_GIVEN` | V02 | 187 | 0.94% |
| `HIGH_RECENT_ENQUIRIES` | R02 | 181 | 0.91% |

**Rows failing V03, V04, K05:**

| Rule | Reason Code | Count | Share |
|---|---|---|---|
| V03 | `AMOUNT_OUTSIDE_PRODUCT_LIMITS` | 0 | 0.00% |
| V04 | `TENURE_OUTSIDE_PRODUCT_LIMITS` | 0 | 0.00% |
| K05 | `INCOME_BELOW_MINIMUM` | 1,214 | 6.07% |

> D3 generator respects product amount/tenure bounds (amounts drawn from `[min_amount, max_amount]`, tenures from allowed set), so V03 and V04 never fire. K05 fires for the low-income tail of the synthetic distribution.

**Refer decisions from V01 or R01:**

| Code | Rule | Refer count | % of all refer |
|---|---|---|---|
| `INCOMPLETE_APPLICATION` | V01 | 0 | 0.00% |
| `NO_CREDIT_HISTORY` | R01 | 737 | 49.23% |
| **V01 or R01 combined** | — | **737** | **49.23%** |

> D3 refer decisions split roughly 50/50 between R01 (no credit score) and other referral rules (R02: high enquiries, R03: other employment type). V01 never fires because the synthetic generator always produces complete inputs.

---

## 5. Mapping Coverage Table (D2, 307,511 rows)

ASM-D13 applies integer rounding (ROUND_HALF_UP for income/amounts, ROUND_FLOOR for age/months) whenever a Decimal division produces a non-integer.

| Fact | Source | Observed | Derived | Fallback | Unknown | ASM-D13 affected |
|---|---|---|---|---|---|---|
| `age` | DAYS_BIRTH | 0 (0.0%) | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 307,348 (99.95%) |
| `employment_type` | NAME_INCOME_TYPE | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | — |
| `employment_months` | DAYS_EMPLOYED | 0 (0.0%) | 252,137 (82.0%) | 0 (0.0%) | 55,374 (18.0%) | ~252,137 (all derived) |
| `monthly_net_income` | AMT_INCOME_TOTAL | 0 (0.0%) | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 5,729 (1.86%) |
| `monthly_obligations` | bureau AMT_ANNUITY | 0 (0.0%) | 107,687 (35.0%) | 199,824 (65.0%) | 0 (0.0%) | — (sum of integers) |
| `credit_score` | EXT_SOURCE_1,2,3 | 0 (0.0%) | 307,339 (99.9%) | 0 (0.0%) | 172 (0.1%) | 307,339 (all derived) |
| `enquiries_6m` | AMT_REQ_CREDIT_BUREAU_MON,QRT | 0 (0.0%) | 265,992 (86.5%) | 0 (0.0%) | 41,519 (13.5%) | — (integer sum) |
| `severe_delinquency_36m` | bureau_balance STATUS | 0 (0.0%) | 92,231 (30.0%) | 0 (0.0%) | 215,280 (70.0%) | — (boolean) |
| `written_off` | bureau CREDIT_ACTIVE | 0 (0.0%) | 263,491 (85.7%) | 0 (0.0%) | 44,020 (14.3%) | — (boolean) |
| `kyc_verified` | constant | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | — |
| `consent_given` | constant | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | — |
| `requested_amount` | AMT_CREDIT | 0 (0.0%) | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 29,807 (9.70%) |
| `requested_tenure_months` | AMT_CREDIT/AMT_ANNUITY | 0 (0.0%) | 307,499 (100.0%) | 0 (0.0%) | 12 (0.0%) | 278,157 (90.47%) |
| `region_tier` | REGION_RATING_CLIENT | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | — |

**ASM-D13 summary:** Integer rounding applies to age (floor, 99.95% of rows), employment_months (floor, all derived rows), monthly_net_income (round half-up, 1.86%), credit_score (round half-up, all derived rows), requested_amount (round half-up, 9.70%), and requested_tenure_months (round half-up, 90.47%). The rounding is documented in the mapping table header.

**Key coverage notes:**
- `monthly_obligations`: 65.0% (199,824 rows) rely on Beta-distribution fallback (ASM-D4) due to missing or non-active bureau records. This is the weakest link in the mapping.
- `severe_delinquency_36m`: 70.0% (215,280 rows) are unknown — applicants with no bureau_balance rows. The engine treats these as unknown and fires V01 (refer) for required fields, or leaves them unknown for non-required fields.
- `employment_months`: 18.0% (55,374 rows) unknown due to the DAYS_EMPLOYED = 365,243 sentinel (pensioners/not-employed).

---

## 6. Phase 4 Tests

### 6.1 Collected Tests (`pytest --collect-only -q` on Phase 4 files)

```
tests/unit/test_d2_map.py::test_DR04_float_ban_fails_when_float_added
tests/unit/test_d2_map.py::test_DR04_mapping_reproducibility_on_fixture
tests/unit/test_d2_map.py::test_ASM_D1_to_D13_documented_in_mapping_table
tests/unit/test_d2_map.py::test_bureau_fallback_rules
tests/unit/test_d2_map.py::test_sentinel_days_employed_becomes_none
tests/unit/test_d2_map.py::test_income_type_mapping
tests/unit/test_d3_generator.py::test_DR05_d3_same_seed_identical_hash
tests/unit/test_d3_generator.py::test_DR05_d3_different_seed_different_hash
tests/unit/test_d3_generator.py::test_DR05_d3_no_float_fields
tests/unit/test_d3_generator.py::test_DR05_d3_bias_switch
tests/unit/test_ml_features.py::test_DR02_no_protected_or_excluded_features
tests/unit/test_ml_features.py::test_DR02_every_feature_in_config
tests/unit/test_ml_features.py::test_pipeline_accepts_row_with_unknown_values
tests/unit/test_ml_metrics.py::test_five_metrics_files_exist_and_validate
tests/unit/test_ml_metrics.py::test_feature_list_file_exists
tests/unit/test_ml_split.py::test_split_leakage_shuffle_test_labels
tests/unit/test_ml_split.py::test_split_files_integrity
tests/unit/test_no_group_outcome.py::test_group_sizes_never_reads_decisions_or_outcomes
tests/unit/test_no_group_outcome.py::test_group_size_tables_have_no_outcome_columns
tests/unit/test_protected_store_isolation.py::test_protected_store_isolation_static_scan
```

**Total: 20 tests across 7 files. All pass.**

### 6.2 Coverage Against Required Tests

| Required test (spec ref) | Covering test(s) | Status |
|---|---|---|
| Feature-list: no protected attribute, no identifier, no label-derived column; every feature in config/ml.toml (§10) | `test_DR02_no_protected_or_excluded_features`, `test_DR02_every_feature_in_config` | ✅ |
| Same split for every model and rule system; test split never used for fitting (§10) | `test_split_leakage_shuffle_test_labels`, `test_split_files_integrity` | ✅ |
| Two models with metrics file and seed each, for D2 and D3 (§10) | `test_five_metrics_files_exist_and_validate`, `test_feature_list_file_exists` | ✅ |
| Protected store read by nothing under src/ except mapping/generator modules (§10) | `test_protected_store_isolation_static_scan` | ✅ |
| Tests use small synthetic fixtures; never need data/raw/ (§10) | All 7 fixture-based tests in test_d2_map.py and test_d3_generator.py | ✅ |
| Pipeline accepts a row with unknown values (§4) | `test_pipeline_accepts_row_with_unknown_values` | ✅ |
| No group outcome metric (experiment-protocol §5) | `test_group_sizes_never_reads_decisions_or_outcomes`, `test_group_size_tables_have_no_outcome_columns` | ✅ |
| Float ban covers d2_map.py; prove it fails when a float is added (DR-04) | `test_DR04_float_ban_fails_when_float_added` | ✅ |
| Mapping reproducibility: same hash on same fixture twice (experiment-protocol §6) | `test_DR04_mapping_reproducibility_on_fixture` | ✅ |
| D3: same seed → identical hash; different seed → different hash (experiment-protocol §6) | `test_DR05_d3_same_seed_identical_hash`, `test_DR05_d3_different_seed_different_hash` | ✅ |
| ASM-D1 to D13 documented in mapping table (docs/08-datasets.md §3) | `test_ASM_D1_to_D13_documented_in_mapping_table` | ✅ |
| ASM-D4 bureau fallback: 4 cases (no bureau, closed only, active with annuity, active with missing annuity) | `test_bureau_fallback_rules` | ✅ |
| ASM-D2 sentinel DAYS_EMPLOYED=365243 → null employment_months | `test_sentinel_days_employed_becomes_none` | ✅ |
| ASM-D1 NAME_INCOME_TYPE mapping (salaried/self_employed/other) | `test_income_type_mapping` | ✅ |
| D3: no float fields in output (P4-8) | `test_DR05_d3_no_float_fields` | ✅ |
| D3: bias switch changes output (config/generator.toml) | `test_DR05_d3_bias_switch` | ✅ |

**No required test is missing.** All 16 requirements from `docs/ml-baseline-spec.md` §10 and the Phase 4 prompt are covered by the 20 collected tests.

---

## 7. `src/data/fallback.py` and the Float Ban

**`src/data/fallback.py` is NOT under the static float ban.** The current `check-floats` command covers `src/data/d2_map.py` only, not the whole `src/data/` directory.

**Reason: its float use is permitted by decision P4-8.** The module draws a Beta-distributed random share using `numpy.random.Generator.beta()`, which unavoidably returns a Python `float`. This is the only way to call numpy's Beta distribution. Decision P4-8 states: *"The D3 generator may use floats inside random draws."* The obligations fallback draw is structurally identical — a random draw — and the same reasoning applies.

**The output is always an integer.** The float share is immediately converted:
```python
amount = Decimal(str(share)) * Decimal(str(monthly_net_income))
return int(amount.to_integral_value(rounding=ROUND_HALF_UP))
```
The final value returned is `int`, never `float`. The float exists only as an intermediate value inside the numpy RNG call.

**Extending the ban would break the module** without any real correctness benefit: numpy does not offer a Decimal-native Beta distribution, and the conversion to Decimal before the money multiplication preserves exact decimal arithmetic for the final result.

**Conclusion:** `src/data/fallback.py` is correctly excluded from the float ban because it uses floats only inside a random draw (permitted by P4-8) and its output is integer-only.

---

## 8. Group-Size Tables

### 8.1 D2 (Home Credit Default Risk)

> Groups with count_test < 100 are marked ⚠️ (too small for outcome analysis in Phase 5).

| Attribute | Group | Full set | Test split | Too small (test) |
|---|---|---|---|---|
| CODE_GENDER | F | 202,448 | 30,352 | — |
| CODE_GENDER | M | 105,059 | 15,774 | — |
| CODE_GENDER | XNA | 4 | 1 | ⚠️ |
| NAME_EDUCATION_TYPE | Academic degree | 164 | 28 | ⚠️ |
| NAME_EDUCATION_TYPE | Higher education | 74,863 | 11,205 | — |
| NAME_EDUCATION_TYPE | Incomplete higher | 10,277 | 1,538 | — |
| NAME_EDUCATION_TYPE | Lower secondary | 3,816 | 601 | — |
| NAME_EDUCATION_TYPE | Secondary / secondary special | 218,391 | 32,755 | — |
| NAME_FAMILY_STATUS | Civil marriage | 29,775 | 4,398 | — |
| NAME_FAMILY_STATUS | Married | 196,432 | 29,482 | — |
| NAME_FAMILY_STATUS | Separated | 19,770 | 2,995 | — |
| NAME_FAMILY_STATUS | Single / not married | 45,444 | 6,852 | — |
| NAME_FAMILY_STATUS | Unknown | 2 | 1 | ⚠️ |
| NAME_FAMILY_STATUS | Widow | 16,088 | 2,399 | — |
| REGION_RATING_CLIENT | 1 | 32,197 | 4,884 | — |
| REGION_RATING_CLIENT | 2 | 226,984 | 34,001 | — |
| REGION_RATING_CLIENT | 3 | 48,330 | 7,242 | — |
| age_band | under-21 | 1 | 0 | ⚠️ |
| age_band | 21-29 | 45,185 | 6,770 | — |
| age_band | 30-39 | 82,331 | 12,387 | — |
| age_band | 40-49 | 76,599 | 11,488 | — |
| age_band | 50-59 | 68,094 | 10,170 | — |
| age_band | 60+ | 35,301 | 5,312 | — |
| employment_type | other | 55,417 | 8,260 | — |
| employment_type | salaried | 180,477 | 27,146 | — |
| employment_type | self_employed | 71,617 | 10,721 | — |
| income_band | Q1_low | 100,578 | 14,956 | — |
| income_band | Q2_med_low | 53,055 | 7,999 | — |
| income_band | Q3_med_high | 82,340 | 12,392 | — |
| income_band | Q4_high | 71,538 | 10,780 | — |

**D2 groups too small on test: 4** — `CODE_GENDER=XNA` (1), `NAME_EDUCATION_TYPE=Academic degree` (28), `NAME_FAMILY_STATUS=Unknown` (1), `age_band=under-21` (0).

### 8.2 D3 (Synthetic Population)

> Groups with count_test < 100 are marked ⚠️.

| Attribute | Group | Full set | Test split | Too small (test) |
|---|---|---|---|---|
| gender | F | 9,953 | 1,487 | — |
| gender | M | 10,047 | 1,513 | — |
| region_tier | 1 | 6,026 | 938 | — |
| region_tier | 2 | 9,992 | 1,483 | — |
| region_tier | 3 | 3,982 | 579 | — |
| age_band | 21-29 | 4,491 | 670 | — |
| age_band | 30-39 | 5,072 | 723 | — |
| age_band | 40-49 | 5,076 | 776 | — |
| age_band | 50-59 | 4,890 | 760 | — |
| age_band | 60+ | 471 | 71 | ⚠️ |
| employment_type | other | 978 | 139 | — |
| employment_type | salaried | 13,990 | 2,102 | — |
| employment_type | self_employed | 5,032 | 759 | — |
| income_band | Q1_low | 5,007 | 735 | — |
| income_band | Q2_med_low | 5,045 | 762 | — |
| income_band | Q3_med_high | 4,965 | 782 | — |
| income_band | Q4_high | 4,983 | 721 | — |

**D3 groups too small on test: 1** — `age_band=60+` (71 on test). The D3 generator draws ages with the same distribution used for D2, where the 60+ tail is sparse.

---

## 9. Item 9 — `make baseline-filtered`

**Not implemented.** No answer B was given by the owner. This item is deferred.

---

## 10. Work Packages

| Work package | Done | Notes |
|---|---|---|
| **WP-15 D2 mapping** | Yes | `src/data/d2_map.py` & `src/data/fallback.py`. 307,511 rows mapped; 0/307,511 schema failures; 0 float violations. `data/mapped/d2_mapped.csv` SHA-256 `44de1b82…`. Mapping table regenerated to docs. |
| **WP-16b D3 synthetic population** | Yes | `data/synthetic/d3_generator.py`. 20,000 rows; `data/synthetic/d3_population.csv` SHA-256 `2311690b…`. D1 byte-identical (oracle-diff: 0 differences). |
| **Batch decisions & splits** | Yes | 70/15/15 stratified splits. D3: 20,000 rows at 1,626 rows/s. D2: 92,254 rows at 4,389 rows/s. |
| **WP-17 ML baseline** | Yes | LR + HistGradientBoosting on D2 and D3. Exact linear contributions for LR. 5 metrics files. All reproduce exactly. |
| **Group-size tables & Manifest** | Yes | 30 D2 groups (4 too small on test), 17 D3 groups (1 too small). Zero outcome metrics. `data/manifest.json` updated. |

---

## 11. Gate Command Results

| Command | Status | Notes |
|---|---|---|
| `python tools/oracle_diff.py` | PASS | 0 differences |
| `git grep -nwE "5000|50000|2500000|0\.02" -- src/engine` | PASS | 0 matches |
| `python tools/check_floats.py src/calc src/facts src/explain src/data/d2_map.py` | PASS | 9 files, 0 floats |
| `python -m src.engine.param_loader params/params.toml` | PASS | 18 params, 3 bands, 0 errors |
| `python -m src.engine.field_loader rules/fields.toml` | PASS | 27 fields, 0 errors |
| `python -m src.engine.rule_loader rules params/params.toml` | PASS | 22 rules, 21 reason codes |
| `python -m src.engine.hygiene` | PASS | Zero findings |
| `python -m ruff check src/ tests/ tools/` | PASS | All passed |
| `python -m ruff format --check src/ tests/ tools/` | PASS | 67 files formatted |
| `python -m pytest tests/ -v` | PASS | 151 passed, 0 failed in 22.71s |
| `mingw32-make phase4` | PASS | Full pipeline in protocol order; `=== Phase 4 complete ===` |
| `python -m src.ml.baseline` ×2 | PASS | All 5 metrics files byte-identical |
| `python -m src.data.d2_map` ×2 | PASS | d2_mapped.csv SHA-256 identical |
| `python data/synthetic/d3_generator.py` ×2 | PASS | d3_population.csv SHA-256 identical |

---

## 12. `make phase4` Full Output (last 15 lines)

```text
OK: all hygiene checks passed with zero findings.
python tools/oracle_diff.py
Diff report written to …\data\d1\oracle_diff.md (0 differences).
python -m src.data.manifest
Manifest written to data\manifest.json
python -m src.data.group_sizes
Group sizes for d2 written to data\group_sizes\d2_group_sizes.csv:
  Total groups evaluated: 30, Groups < 100 on test: 4
Group sizes for d3 written to data\group_sizes\d3_group_sizes.csv:
  Total groups evaluated: 17, Groups < 100 on test: 1
"=== Phase 4 complete ==="
```
