# Phase 4 report

Date: 2026-11-12  
Commit hash: a84fa6b  
Agent session: phase4-closeout  

---

## 1. Step 0: Confirm the Base

1. **`make oracle-diff`**: 0 differences across all D1 cases against oracle expectations. Status: MATCH.
2. **Hygiene analyser grep**: `git grep -nwE "5000|50000|2500000|0\.02" -- src/engine` output is empty (0 matches, exit code 1). Status: PASS.
3. **`make check`, `make check-rules`, `make test`**: Pass cleanly; rule-set tag equals `rules-1.0.0+params-0.1.0` and SHA-256 hash equals `sha256:eb7073a388817e0a455997c0c2ea86ccb25524cdff07faf8bf5ca98bb267be5a` (matching `tests/golden/rule_set_pin.json`). Status: PASS.
4. **`docs/datasheets/home-credit-terms.md`**: Exists and confirms use for coursework or non-commercial research is allowed without placeholders. Status: PASS.
5. **Raw data check**: `data/raw/` holds `application_train.csv`, `bureau.csv`, and `bureau_balance.csv`. SHA-256 checksums match `data/checksums/home_credit.sha256` exactly. `git check-ignore -v data/raw/application_train.csv` reports `.gitignore:30:data/raw/`. Status: PASS.
6. **Column header verification**: All 17 required columns across `application_train.csv`, `bureau.csv`, and `bureau_balance.csv` match `config/d2_mapping.toml` exactly. 0 missing, 0 different. Status: PASS.
7. **Dependency dry-run**: `python -m pip install --dry-run pandas numpy scikit-learn joblib` confirmed all wheels install cleanly on Python 3.14.2. Status: PASS.
8. **Float ban configuration**: Configured in `Makefile` under target `check-floats` invoking `tools/check_floats.py`, covering directories `src/calc`, `src/facts`, `src/explain`, and module `src/data/d2_map.py` (9 files total). Status: PASS.

---

## 2. Summary

Phase 4 deliverables complete:
- **WP-15 D2 mapping**: Home Credit Default Risk (307,511 rows) mapped to fact schema in `data/mapped/d2_mapped.csv` and `data/protected/d2_protected.csv` via `src/data/d2_map.py` and `src/data/fallback.py`. Zero validation failures (0/307,511). Extended static float ban confirmed with 0 floats.
- **WP-16b D3 synthetic population**: 20,000 synthetic applicants generated in `data/synthetic/d3_population.csv` and `data/protected/d3_protected.csv` via `data/synthetic/d3_generator.py`. D1 generation remains byte-identical (`make oracle-diff` reports 0 differences).
- **Batch decisions & splits**: Stratified 70/15/15 splits generated for D2 and D3 via `src/data/split.py`. Direct engine evaluation in `src/data/batch_decide.py` for full D3 (20,000 rows) and D2 validation/test splits (92,254 rows) without audit logging overhead.
- **WP-17 ML baseline**: Logistic Regression and HistGradientBoosting trained on D2 and D3 via `src/ml/baseline.py`. Operating points selected on validation; exact linear contributions computed for LR. 5 metrics files and `feature_list.json` written to `reports/ml/`.
- **Filtered subset comparisons (F1 & F2)**: Implemented `src/ml/baseline_filtered.py` (`make baseline-filtered`) evaluating rule system Treatments A and B, LR, and HistGB across filtered subsets F1 (no V03/V04/K05) and F2 (F1 without K04) without retraining. Operating points chosen on filtered validation rows. 95% bootstrap confidence intervals computed over 1,000 resamples for default rate among approved.
- **Datasheets & documentation**: `docs/datasheets/home-credit.md`, `docs/datasheets/d3-synthetic.md`, `docs/datasheets/d2-mapping-table.md`, `docs/model-card.md`, and `data/manifest.json`.

Zero policy values, rules, parameters, or schemas were altered. Exact decimal arithmetic (`Decimal` and whole rupee `int`) is strictly enforced in mapping code. Protected attributes are strictly isolated to `data/protected/` and never accessed by the fact base, rule engine, or ML baseline features.

---

## 3. Pass/Fail Table with Lean Test Names

All 29 Phase 4 tests pass under `pytest` (full project test suite: 160 passed, 0 failed in 22.10s).

| Test Name | File | Spec Requirement / Purpose | Status |
|---|---|---|---|
| `test_DR04_float_ban_fails_when_float_added` | `tests/unit/test_d2_map.py` | DR-04: Static float ban covers d2_map.py; fails when float added | PASS |
| `test_DR04_mapping_reproducibility_on_fixture` | `tests/unit/test_d2_map.py` | DR-04: D2 mapping deterministic on identical fixture | PASS |
| `test_ASM_D1_to_D13_documented_in_mapping_table` | `tests/unit/test_d2_map.py` | docs/08-datasets.md §3: All assumptions ASM-D1 to D13 in mapping table | PASS |
| `test_bureau_fallback_rules` | `tests/unit/test_d2_map.py` | ASM-D4: Bureau fallback covers all 4 cases | PASS |
| `test_sentinel_days_employed_becomes_none` | `tests/unit/test_d2_map.py` | ASM-D2: Sentinel DAYS_EMPLOYED=365243 maps to null/unknown | PASS |
| `test_income_type_mapping` | `tests/unit/test_d2_map.py` | ASM-D1: Income type correctly categorized into salaried/self_employed/other | PASS |
| `test_DR05_d3_same_seed_identical_hash` | `tests/unit/test_d3_generator.py` | DR-05: D3 generator produces identical SHA-256 with same seed | PASS |
| `test_DR05_d3_different_seed_different_hash` | `tests/unit/test_d3_generator.py` | DR-05: D3 generator produces different output with different seed | PASS |
| `test_DR05_d3_no_float_fields` | `tests/unit/test_d3_generator.py` | P4-8: D3 output fields are int, bool, str, null only (no floats) | PASS |
| `test_DR05_d3_bias_switch` | `tests/unit/test_d3_generator.py` | config/generator.toml: Planted bias switch alters data when enabled | PASS |
| `test_DR02_no_protected_or_excluded_features` | `tests/unit/test_ml_features.py` | DR-02: ML feature list contains no protected or excluded attributes | PASS |
| `test_DR02_every_feature_in_config` | `tests/unit/test_ml_features.py` | DR-02: Every model feature is explicitly declared in config/ml.toml | PASS |
| `test_pipeline_accepts_row_with_unknown_values` | `tests/unit/test_ml_features.py` | docs/ml-baseline-spec.md §4: Pipeline handles missing values gracefully | PASS |
| `test_five_metrics_files_exist_and_validate` | `tests/unit/test_ml_metrics.py` | WP-17: All 5 baseline metrics JSON files exist and match schema | PASS |
| `test_feature_list_file_exists` | `tests/unit/test_ml_metrics.py` | WP-17: `reports/ml/feature_list.json` exists with complete groups | PASS |
| `test_split_leakage_shuffle_test_labels` | `tests/unit/test_ml_split.py` | docs/ml-baseline-spec.md §10: Zero leakage; test split never used in training | PASS |
| `test_split_files_integrity` | `tests/unit/test_ml_split.py` | WP-16b: D2 and D3 split ratios match 70/15/15 target | PASS |
| `test_group_sizes_never_reads_decisions_or_outcomes` | `tests/unit/test_no_group_outcome.py` | D-06: Group sizing never imports or reads decisions or labels | PASS |
| `test_group_size_tables_have_no_outcome_columns` | `tests/unit/test_no_group_outcome.py` | D-06: Group size output tables contain no outcome columns | PASS |
| `test_protected_store_isolation_static_scan` | `tests/unit/test_protected_store_isolation.py` | DR-02: `src/` modules (except mappers) never reference protected store | PASS |
| `test_DR05_filtered_comparison_files_exist` | `tests/unit/test_baseline_filtered.py` | P4-14: `comparison_main.json`, `comparison_f1.json`, `comparison_f2.json` exist | PASS |
| `test_filtered_no_group_outcome_metrics` | `tests/unit/test_baseline_filtered.py` | D-06: Filtered comparisons compute no outcome metric by group | PASS |
| `test_filtered_lr_and_gb_note_no_retrain` | `tests/unit/test_baseline_filtered.py` | P4-14: Model entries state no retraining occurred | PASS |
| `test_filtered_f1_f2_subsets_labelled` | `tests/unit/test_baseline_filtered.py` | P4-14: Filtered outputs explicitly labeled as "filtered subset" | PASS |
| `test_filtered_rule_note_mechanical_approval` | `tests/unit/test_baseline_filtered.py` | P4-14: Rule system notes mechanical increase in approval rate | PASS |
| `test_filtered_bootstrap_ci_present` | `tests/unit/test_baseline_filtered.py` | P4-13: 95% bootstrap CIs present on all approval operating points | PASS |
| `test_DR05_filtered_comparison_reproducible` | `tests/unit/test_baseline_filtered.py` | DR-05: Filtered comparisons reproduce byte-identical across runs | PASS |
| `test_filter_mask_f1_excludes_correct_codes` | `tests/unit/test_baseline_filtered.py` | P4-14: F1 mask correctly excludes V03, V04, K05 | PASS |
| `test_filter_mask_f2_also_excludes_k04` | `tests/unit/test_baseline_filtered.py` | P4-14: F2 mask correctly excludes V03, V04, K05, K04 | PASS |

---

## 4. Engine and Source Changes

In accordance with AGENTS.md, **zero changes were made** to existing engine, calculation, explanation, or rule modules:
- `src/engine/`: Untouched.
- `src/calc/`: Untouched.
- `src/explain/`: Untouched.
- `src/audit/`: Untouched.
- `src/api/`: Untouched.
- `rules/`: Untouched.
- `params/`: Untouched.
- `schemas/`: Untouched.
- `tests/golden/`: Untouched.

**New source and tool modules added in Phase 4:**
- `src/data/d2_map.py`: Home Credit raw CSV chunked processor and fact mapper.
- `src/data/fallback.py`: Obligations fallback draw via Beta distribution.
- `data/synthetic/d3_generator.py`: Synthetic population generator.
- `src/data/split.py`: Stratified 70/15/15 train/validation/test splitter.
- `src/data/batch_decide.py`: Batch evaluation engine runner for D2 and D3.
- `src/data/manifest.py`: Cryptographic hash manifest builder (`data/manifest.json`).
- `src/data/group_sizes.py`: Demographic subgroup census builder (`data/group_sizes/`).
- `src/ml/features.py`: Feature engineering pipeline with ColumnTransformer.
- `src/ml/baseline.py`: ML baseline trainer, validator, and evaluator.
- `src/ml/baseline_filtered.py`: Filtered subset comparison engine with bootstrap CIs.

---

## 5. Dependencies

Pinned in `requirements.txt`:
- `pandas==3.1.1`
- `numpy==2.5.4`
- `scikit-learn==1.9.1`
- `joblib==1.6.0`
- `scipy==1.18.1`
- `narwhals==2.28.0`
- `threadpoolctl==3.8.0`
- `cloudpickle==3.1.2`

---

## 6. Reproducibility Hashes and Manifest

All generated datasets, models, metrics, and comparison files were generated across two independent runs. SHA-256 hashes are identical.

| Artifact File | Run 1 SHA-256 | Run 2 SHA-256 | Equal? |
|---|---|---|---|
| `data/mapped/d2_mapped.csv` | `44de1b821cd3c4831b485b39435998e53c3f10754c7a069046bbca0f0ca6eae4` | `44de1b821cd3c4831b485b39435998e53c3f10754c7a069046bbca0f0ca6eae4` | ✅ |
| `data/protected/d2_protected.csv` | `d539e950a8a340470788b827a16678efd8c3ecb8f70dcf1f50980f2a1189017f` | `d539e950a8a340470788b827a16678efd8c3ecb8f70dcf1f50980f2a1189017f` | ✅ |
| `data/synthetic/d3_population.csv` | `2311690bfaf45d7e944f5e572bdd50d0f5a768494480d54d78a88b1b8ed619ef` | `2311690bfaf45d7e944f5e572bdd50d0f5a768494480d54d78a88b1b8ed619ef` | ✅ |
| `data/protected/d3_protected.csv` | `f2bbd239ee35022ab99c69f32343962c2e33f84173a471a7d07b1499cd673c44` | `f2bbd239ee35022ab99c69f32343962c2e33f84173a471a7d07b1499cd673c44` | ✅ |
| `reports/ml/metrics_d2_lr.json` | `d45e2ce0f55b2359a6e1c3af3fc5fcf461f3025f64089f5011b8ef4610c7e219` | `d45e2ce0f55b2359a6e1c3af3fc5fcf461f3025f64089f5011b8ef4610c7e219` | ✅ |
| `reports/ml/metrics_d2_gb.json` | `a58dc871cbd4257c70001e27d425b3c3e2f1cc8ac22eea9d220cb397190ba851` | `a58dc871cbd4257c70001e27d425b3c3e2f1cc8ac22eea9d220cb397190ba851` | ✅ |
| `reports/ml/metrics_d3_lr.json` | `c4fe5aff7ae57d316e42258fac721bac214c441b6f0ad8102e8b5942e199be89` | `c4fe5aff7ae57d316e42258fac721bac214c441b6f0ad8102e8b5942e199be89` | ✅ |
| `reports/ml/metrics_d3_gb.json` | `d74d93b2d707791f8d25342b55cba911ebfb993f46a53980c69da398c412b0c7` | `d74d93b2d707791f8d25342b55cba911ebfb993f46a53980c69da398c412b0c7` | ✅ |
| `reports/ml/metrics_d3_sim_lr.json` | `20acd369fb433eddbf8961e30d15c7a5f1af249a1b4dc94c80e01fae33f67e55` | `20acd369fb433eddbf8961e30d15c7a5f1af249a1b4dc94c80e01fae33f67e55` | ✅ |
| `reports/ml/comparison_main.json` | `dd151b5b022b276770334283e9135abafc10f811d96ac9235211d28431e66aa6` | `dd151b5b022b276770334283e9135abafc10f811d96ac9235211d28431e66aa6` | ✅ |
| `reports/ml/comparison_f1.json` | `c53ee2b171077e3b6457469d43d38799bd4e0bc87df1ed03e42abf21047769b7` | `c53ee2b171077e3b6457469d43d38799bd4e0bc87df1ed03e42abf21047769b7` | ✅ |
| `reports/ml/comparison_f2.json` | `c639023c3138feb6a9255e567457396226d594c4d6a9f34d7563544968fa515a` | `c639023c3138feb6a9255e567457396226d594c4d6a9f34d7563544968fa515a` | ✅ |

### `data/manifest.json`

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

## 7. Decision Statistics

### 7.1 D2 Decisions (`data/decisions/d2_decisions.csv`)

Evaluated rows: 92,254 (validation and test splits).

**Decision share:**

| Decision | Count | Share |
|---|---|---|
| ineligible | 82,663 | 89.60% |
| refer | 8,046 | 8.72% |
| eligible | 1,545 | 1.67% |
| **Total** | **92,254** | **100.00%** |

**Reason-code frequency table:**

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

**Counts failing V03, V04, K05:**

| Rule | Reason Code | Count | Share |
|---|---|---|---|
| V03 | `AMOUNT_OUTSIDE_PRODUCT_LIMITS` | 270 | 0.29% |
| V04 | `TENURE_OUTSIDE_PRODUCT_LIMITS` | 10,345 | 11.21% |
| K05 | `INCOME_BELOW_MINIMUM` | 57,057 | 61.85% |

**Refer decisions originating from V01 or R01:**

| Code | Rule | Refer count | % of all refer |
|---|---|---|---|
| `INCOMPLETE_APPLICATION` | V01 | 8,027 | 99.76% |
| `NO_CREDIT_HISTORY` | R01 | 13 | 0.16% |
| **V01 or R01 combined** | — | **8,031** | **99.81%** |

### 7.2 D3 Decisions (`data/decisions/d3_decisions.csv`)

Evaluated rows: 20,000 (all synthetic applicants).

**Decision share:**

| Decision | Count | Share |
|---|---|---|
| eligible | 9,449 | 47.24% |
| ineligible | 9,054 | 45.27% |
| refer | 1,497 | 7.49% |
| **Total** | **20,000** | **100.00%** |

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

**Counts failing V03, V04, K05:**

| Rule | Reason Code | Count | Share |
|---|---|---|---|
| V03 | `AMOUNT_OUTSIDE_PRODUCT_LIMITS` | 0 | 0.00% |
| V04 | `TENURE_OUTSIDE_PRODUCT_LIMITS` | 0 | 0.00% |
| K05 | `INCOME_BELOW_MINIMUM` | 1,214 | 6.07% |

*(In D3, requests are generated within product parameters, so V03 and V04 never fire).*

**Refer decisions originating from V01 or R01:**

| Code | Rule | Refer count | % of all refer |
|---|---|---|---|
| `INCOMPLETE_APPLICATION` | V01 | 0 | 0.00% |
| `NO_CREDIT_HISTORY` | R01 | 737 | 49.23% |
| **V01 or R01 combined** | — | **737** | **49.23%** |

---

## 8. Mapping Coverage and Limitations

### 8.1 D2 Mapping Coverage (307,511 rows)

| Fact | Source | Observed | Derived | Fallback | Unknown | ASM-D13 affected |
|---|---|---|---|---|---|---|
| `age` | DAYS_BIRTH | 0 (0.0%) | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 307,348 (99.95%) |
| `employment_type` | NAME_INCOME_TYPE | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | — |
| `employment_months` | DAYS_EMPLOYED | 0 (0.0%) | 252,137 (82.0%) | 0 (0.0%) | 55,374 (18.0%) | 252,137 (82.00%) |
| `monthly_net_income` | AMT_INCOME_TOTAL | 0 (0.0%) | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 5,729 (1.86%) |
| `monthly_obligations` | bureau AMT_ANNUITY | 0 (0.0%) | 107,687 (35.0%) | 199,824 (65.0%) | 0 (0.0%) | — |
| `credit_score` | EXT_SOURCE_1,2,3 | 0 (0.0%) | 307,339 (99.9%) | 0 (0.0%) | 172 (0.1%) | 307,339 (99.94%) |
| `enquiries_6m` | AMT_REQ_CREDIT_BUREAU_MON,QRT | 0 (0.0%) | 265,992 (86.5%) | 0 (0.0%) | 41,519 (13.5%) | — |
| `severe_delinquency_36m` | bureau_balance STATUS | 0 (0.0%) | 92,231 (30.0%) | 0 (0.0%) | 215,280 (70.0%) | — |
| `written_off` | bureau CREDIT_ACTIVE | 0 (0.0%) | 263,491 (85.7%) | 0 (0.0%) | 44,020 (14.3%) | — |
| `kyc_verified` | constant | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | — |
| `consent_given` | constant | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | — |
| `requested_amount` | AMT_CREDIT | 0 (0.0%) | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 29,807 (9.70%) |
| `requested_tenure_months` | AMT_CREDIT/AMT_ANNUITY | 0 (0.0%) | 307,499 (100.0%) | 0 (0.0%) | 12 (0.0%) | 278,157 (90.47%) |
| `region_tier` | REGION_RATING_CLIENT | 307,511 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | — |

### 8.2 Mapping Limitations

1. **65.0% fallback obligations (ASM-D4)**: 199,824 rows lack active bureau loan annuities and receive a synthetic obligation drawn from a Beta distribution parameterized on net income. This is the primary mapping uncertainty.
2. **70.0% unknown severe delinquency**: 215,280 rows have no matching `bureau_balance` history. The engine treats missing required fields as unknown and triggers rule V01 (`INCOMPLETE_APPLICATION`), routing 99.81% of all D2 refer decisions through V01/R01.
3. **K04 effect of ASM-D5**: External source ratings (EXT_SOURCE_1, 2, 3) are mapped to credit score range [300, 900]. Because Home Credit applicants have low average external scores, 65.00% (59,969 of 92,254 evaluated rows) fall below the 650 threshold, causing rule K04 to fire.
4. **ASM-D13 integer rounding**: Applied where exact decimal division produces fractional values for integer facts (floor for age and employment months; round-half-up for income, credit score, amount, and tenure).
5. **Float-ban status of `src/data/fallback.py`**: Not under static float ban. Per decision P4-8, floating-point arithmetic is permitted inside random draws (`numpy.random.Generator.beta`). The output is converted to `Decimal` and rounded to whole-rupee `int` before returning.

---

## 9. ML Metrics for Main and Filtered Comparisons with CIs

### 9.1 Main Comparison (All Evaluated Rows, Test $N = 46,127$)

| System / Model | Operating Point | Approval Rate | Approvals ($N$) | Default Rate among Approved | 95% Bootstrap CI | AUC | Brier Score |
|---|---|---|---|---|---|---|---|
| **Rule System (Treatment A)** | Policy (refer denied) | 1.68% | 776 | 3.35% | [2.14%, 4.70%] | — | — |
| **Rule System (Treatment B)** | Policy (refer excluded, $N_{\text{excl}}=4055$) | 1.84% | 776 | 3.35% | [2.12%, 4.67%] | — | — |
| **Logistic Regression** | Matched ($\tau = 0.1479$) | 1.56% | 720 | 1.39% | [0.56%, 2.42%] | 0.7248 | 0.2105 |
| **Logistic Regression** | Cost-based primary ($\tau = 0.6684$) | 87.60% | 40,406 | 6.06% | [5.84%, 6.31%] | 0.7248 | 0.2105 |
| **HistGradientBoosting** | Matched ($\tau = 0.0680$) | 1.71% | 787 | 1.27% | [0.58%, 2.12%] | 0.7378 | 0.1951 |
| **HistGradientBoosting** | Cost-based primary ($\tau = 0.6889$) | 89.12% | 41,110 | 6.11% | [5.86%, 6.33%] | 0.7378 | 0.1951 |

### 9.2 Filtered Subset F1 (No V03, V04, K05; Test $N = 15,798$, Val $N = 15,858$)

*Note: No retraining. Operating points selected on filtered validation rows.*

| System / Model | Operating Point | Approval Rate | Approvals ($N$) | Default Rate among Approved | 95% Bootstrap CI | AUC | Brier Score |
|---|---|---|---|---|---|---|---|
| **Rule System (Treatment A)** | Policy (refer denied) | 4.91% | 776 | 3.35% | [2.15%, 4.68%] | — | — |
| **Rule System (Treatment B)** | Policy (refer excluded, $N_{\text{excl}}=4055$) | 6.61% | 776 | 3.35% | [2.22%, 4.72%] | — | — |
| **Logistic Regression** | Matched ($\tau = 0.2163$) | 4.61% | 728 | 2.20% | [1.22%, 3.40%] | 0.7417 | 0.2144 |
| **Logistic Regression** | Cost-based primary ($\tau = 0.6586$) | 90.85% | 14,353 | 5.89% | [5.51%, 6.29%] | 0.7417 | 0.2144 |
| **HistGradientBoosting** | Matched ($\tau = 0.1030$) | 5.04% | 796 | 1.76% | [0.88%, 2.70%] | 0.7495 | 0.2003 |
| **HistGradientBoosting** | Cost-based primary ($\tau = 0.6791$) | 91.46% | 14,449 | 5.80% | [5.42%, 6.20%] | 0.7495 | 0.2003 |

### 9.3 Filtered Subset F2 (F1 without K04; Test $N = 5,995$, Val $N = 5,990$)

*Note: No retraining. Operating points selected on filtered validation rows.*

| System / Model | Operating Point | Approval Rate | Approvals ($N$) | Default Rate among Approved | 95% Bootstrap CI | AUC | Brier Score |
|---|---|---|---|---|---|---|---|
| **Rule System (Treatment A)** | Policy (refer denied) | 12.94% | 776 | 3.35% | [2.08%, 4.63%] | — | — |
| **Rule System (Treatment B)** | Policy (refer excluded, $N_{\text{excl}}=4055$) | 40.00% | 776 | 3.35% | [2.11%, 4.67%] | — | — |
| **Logistic Regression** | Matched ($\tau = 0.2929$) | 12.14% | 728 | 2.34% | [1.35%, 3.47%] | 0.5925 | 0.0898 |
| **Logistic Regression** | Cost-based primary ($\tau = 0.6033$) | 99.97% | 5,993 | 2.75% | [2.34%, 3.17%] | 0.5925 | 0.0898 |
| **HistGradientBoosting** | Matched ($\tau = 0.1419$) | 13.06% | 783 | 1.79% | [0.89%, 2.73%] | 0.6295 | 0.0886 |
| **HistGradientBoosting** | Cost-based primary ($\tau = 0.6416$) | 99.88% | 5,988 | 2.76% | [2.34%, 3.17%] | 0.6295 | 0.0886 |

**Mechanical approval rate observation**: Filtering on rule outcomes mechanically raises the rule system's approval rate: rows that the rule system rejected or referred for V03, V04, K05 (and K04 in F2) are removed, leaving a higher concentration of eligible decisions (from 1.68% in main to 4.91% in F1 to 12.94% in F2 under Treatment A, and up to 40.00% under Treatment B).

### 9.4 D3 Policy Imitation Evaluation (Test Split $N = 3,000$)

| Model | Operating Point ($\tau = 0.50$) | Agreement with Policy | Precision | Recall | F1 | Test AUC | Brier Score |
|---|---|---|---|---|---|---|---|
| **Logistic Regression** | 0.50 | 80.97% | 0.7768 | 0.8377 | 0.8061 | 0.8852 | 0.1346 |
| **HistGradientBoosting** | 0.50 | 98.53% | 0.9744 | 0.9951 | 0.9846 | 0.9902 | 0.0134 |

---

## 10. Unknown Facts Analysis (Item 4)

### 10.1 Unknown Facts Among D2 Eligible Decisions

Among all 1,545 D2 eligible decisions in the evaluated validation and test sets:
- `severe_delinquency_36m` unknown: **0 (0.00%)**
- `employment_months` unknown: **0 (0.00%)**
- Either unknown: **0 (0.00%)**

### 10.2 Decision Share by Delinquency Fact Availability

Across all 92,254 evaluated D2 rows:

| `severe_delinquency_36m` Status | Count | Ineligible | Eligible | Refer |
|---|---|---|---|---|
| **Known** (`False`) | 27,721 (30.05%) | 25,808 (93.10%) | 1,545 (5.57%) | 368 (1.33%) |
| **Unknown** (`True`) | 64,533 (69.95%) | 56,855 (88.10%) | 0 (0.00%) | 7,678 (11.90%) |

### 10.3 Engine Treatment of Unknown K03 and K06 Inputs

In `rules/fields.toml`, `severe_delinquency_36m`, `written_off`, and `employment_months` are marked `required = true`; when any required input is unknown, rule V01 in `rules/validation.toml` fires first with `when = "any_required_unknown"`, resulting in a `refer` decision (`INCOMPLETE_APPLICATION`). Because boolean and arithmetic conditions on unknown facts evaluate to false, knockout rules K03 (`when = "severe_delinquency_36m or written_off"`) and K06 (`when = "(employment_type == salaried and employment_months < min_employment_months_salaried) or (employment_type == self_employed and employment_months < min_employment_months_self_employed)"`) do not fire when their inputs are missing.

---

## 11. Group-Size Tables

### 11.1 D2 (Home Credit Default Risk)

> Groups with test split count < 100 are marked ⚠️ (too small for outcome analysis in Phase 5).

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

**D2 groups too small on test: 4** (`CODE_GENDER=XNA` [1], `NAME_EDUCATION_TYPE=Academic degree` [28], `NAME_FAMILY_STATUS=Unknown` [1], `age_band=under-21` [0]).

### 11.2 D3 (Synthetic Population)

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

**D3 age statement correction**: In D3, ages are generated uniformly from 21 to 60 (inclusive), per `config/generator.toml`. The `60+` age band therefore contains only applicants of exact age 60 (1 of 40 integer ages, or ~2.5% of the population), resulting in 471 applicants in the full population and 71 on the 15% test split (marked ⚠️ < 100). It does not reflect a sparse tail of an older distribution.

---

## 12. Gate Command Outputs (Last 15 Lines Each, Unedited)

### `python tools/oracle_diff.py`
```text
Diff report written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\data\d1\oracle_diff.md (0 differences).
```

### `git grep -nwE "5000|50000|2500000|0\.02" -- src/engine`
```text
(empty output, exit code 1)
```

### `python tools/check_floats.py src/calc src/facts src/explain src/data/d2_map.py`
```text
FLOAT_BAN OK: no floats in src\calc, src\facts, src\explain, src\data\d2_map.py (9 file(s) checked).
```

### `python -m src.engine.param_loader params/params.toml`
```text
OK: params/params.toml loaded with 0 warning(s) and no errors.
    18 scalar parameters, 3 band(s).
```

### `python -m src.engine.field_loader rules/fields.toml`
```text
OK: rules\fields.toml loaded with 0 warning(s) and no errors.
    27 fields (15 input, 12 derived).
```

### `python -m src.engine.rule_loader rules params/params.toml`
```text
OK: rules loaded successfully (22 rules across 7 layers, 21 reason codes).
```

### `python -m src.engine.hygiene`
```text
K03        | 3            | OK                            
K04        | 3            | OK                            
K05        | 3            | OK                            
K06        | 2            | OK                            
P01        | 42           | OK                            
R01        | 2            | OK                            
R02        | 3            | OK                            
R03        | 2            | OK                            
V01        | 16           | OK                            
V02        | 2            | OK                            
V03        | 2            | OK                            
V04        | 2            | OK                            
AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM | 0            | Unreachable by design (DT-3)  
----------------------------------------

OK: all hygiene checks passed with zero findings.
```

### `python -m ruff check src/ tests/ tools/`
```text
All checks passed!
```

### `python -m ruff format --check src/ tests/ tools/`
```text
71 files already formatted
```

### `python -m pytest tests/ -v`
```text
tests\unit\test_facts_unit.py ...                                        [ 43%]
tests\unit\test_field_loader.py .....                                    [ 46%]
tests\unit\test_fields_registry_vs_schema.py .....                       [ 50%]
tests\unit\test_float_ban.py .......                                     [ 54%]
tests\unit\test_hygiene.py .....                                         [ 57%]
tests\unit\test_ml_features.py ...                                       [ 59%]
tests\unit\test_ml_metrics.py ..                                         [ 60%]
tests\unit\test_ml_split.py ..                                           [ 61%]
tests\unit\test_no_group_outcome.py ..                                   [ 63%]
tests\unit\test_param_loader.py ..............................           [ 81%]
tests\unit\test_protected_store_isolation.py .                           [ 82%]
tests\unit\test_rule_loader.py .......                                   [ 86%]
tests\unit\test_rules_firing_and_boundaries.py .....................     [100%]

======================= 160 passed, 1 warning in 22.10s =======================
```

### `git check-ignore -v data/raw/application_train.csv`
```text
.gitignore:30:data/raw/	data/raw/application_train.csv
```

### `mingw32-make phase4`
```text
V04        | 2            | OK                            
AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM | 0            | Unreachable by design (DT-3)  
----------------------------------------

OK: all hygiene checks passed with zero findings.
python tools/oracle_diff.py
Diff report written to C:\Users\asus\Documents\Learning\AI_Class_Project\loan-expert-system\data\d1\oracle_diff.md (0 differences).
python -m src.data.manifest
Manifest written to data\manifest.json
python -m src.data.group_sizes
Group sizes for d2 written to data\group_sizes\d2_group_sizes.csv:
  Total groups evaluated: 30, Groups < 100 on test: 4
Group sizes for d3 written to data\group_sizes\d3_group_sizes.csv:
  Total groups evaluated: 17, Groups < 100 on test: 1
"=== Phase 4 complete ==="
```

### `python -m src.ml.baseline_filtered`
```text
--- Subset: MAIN ---
  val rows: 46127, test rows: 46127
  Wrote reports\ml\comparison_main.json

--- Subset: F1 ---
  val rows: 15858, test rows: 15798
  Wrote reports\ml\comparison_f1.json

--- Subset: F2 ---
  val rows: 5990, test rows: 5995
  Wrote reports\ml\comparison_f2.json

All filtered comparison files written.
```

---

## 13. Amendments

| ID | Date | What Changed | Reason |
|---|---|---|---|
| P4-1 | 2026-11-12 | D2 dataset defined as Home Credit Default Risk (`application_train.csv`, `bureau.csv`, `bureau_balance.csv`). | Experiment protocol §8 |
| P4-2 | 2026-11-12 | D3 binary label is policy decision (`eligible` vs `ineligible`/`refer`). | Experiment protocol §8 |
| P4-3 | 2026-11-12 | ASM-D4 obligations fallback refinement using applicant-keyed Beta draw. | Experiment protocol §8 |
| P4-4 | 2026-11-12 | Missing `written_off` and `severe_delinquency_36m` treated as unknown facts. | Experiment protocol §8 |
| P4-5 | 2026-11-12 | `age` excluded from ML baseline features (DR-02). | Experiment protocol §8 |
| P4-6 | 2026-11-12 | Approval threshold matched to rule approval rate on validation split. | Experiment protocol §8 |
| P4-7 | 2026-11-12 | Rule system evaluated under Treatments A (refer denied) and B (refer excluded). | Experiment protocol §8 |
| P4-8 | 2026-11-12 | Floating-point operations permitted inside random generators and ML models; mapping output remains integer/decimal. | Experiment protocol §8 |
| P4-9 | 2026-11-12 | Direct engine calls used for batch evaluation without audit store overhead. | Experiment protocol §8 |
| P4-10 | 2026-11-12 | Constants loaded exclusively from `config/d2_mapping.toml`. | Experiment protocol §8 |
| P4-11 | 2026-11-12 | Linear contributions for Logistic Regression computed as exact SHAP-equivalent values. | Experiment protocol §8 |
| P4-12 | 2026-11-12 | Outcome metrics by protected group strictly prohibited in Phase 4. | Experiment protocol §8 |
| P4-13 | 2026-11-12 | Added seed name `"bootstrap"` to `config/experiment.toml` and section `[bootstrap]` with `resamples = 1000` and `ci = 0.95`. | Phase 4 close-out item 1 (owner answered B). |
| P4-14 | 2026-11-12 | Filtered subsets F1 and F2 pre-registered after viewing reason-code frequencies and before viewing any filtered outcome result. | Phase 4 close-out item 1 (owner answered B). |

---

## 14. Open Questions

| ID | Status | Resolution / Current State |
|---|---|---|
| OQ-001 | Waiting | SWI-Prolog environment fallback (pure Python evaluator active). |
| OQ-002 | Resolved | Raw data verified in Phase 4 Step 0; SHA-256 matched. |
| OQ-003 | Resolved | Parameter and rule file line-end hashing verified. |
| OQ-004 | Resolved | Nullability difference between schema and fields registry handled. |
| OQ-005 | Resolved | Subprocess communication architecture established. |
| OQ-006 | Waiting | Policy cap tie-break priority when requested amount ties a limit. |
| OQ-007 | Resolved | 422 Validation error response codes mapped to standardized schema. |
| OQ-008 | Resolved | Hygiene analyzer literals derived from named parameters. |
| OQ-009 | Resolved | Terms record renamed to `home-credit-terms.md`; placeholders cleared. |
| OQ-010 | Resolved | Reviewer report ML block skipped to preserve test backwards compatibility. |
| OQ-011 | Resolved | All 17 raw columns verified against `config/d2_mapping.toml`. |
