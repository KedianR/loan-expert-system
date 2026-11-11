"""D2 mapping module: maps Home Credit Default Risk raw tables to fact schema.

Implements: DR-01, DR-02, DR-04, DR-05, FR-21 to FR-24.
Assumptions: ASM-D1 to ASM-D13 (docs/08-datasets.md section 3).
Phase 4 refinements P4-3 (bureau_zero), P4-4 (age not an ML feature).

AGENTS.md hard rules:
- No policy number in code; every constant read from config/d2_mapping.toml.
- Money and ratios use Decimal / ROUND_HALF_UP. No float in this module.
- Protected attributes (CODE_GENDER, NAME_EDUCATION_TYPE, NAME_FAMILY_STATUS)
  only written to the protected store; never passed to the fact base.
- Output: LF line endings, fixed column order, no index, no timestamps.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import tomllib
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

import pandas as pd

from src.data.fallback import draw_fallback_obligations


def derive_seed(master: int, name: str) -> int:
    """FR-21: deterministic per-name seed from the master seed."""
    return int(hashlib.sha256(f"{master}:{name}".encode()).hexdigest(), 16) % (2**32)


def _age_band(age: int | None, edges: list[int]) -> str:
    """Return the age band label for a given age (config/d2_mapping.toml [protected_store])."""
    if age is None:
        return "unknown"
    if age < edges[0]:
        return "under-21"
    for i in range(len(edges) - 1):
        if edges[i] <= age < edges[i + 1]:
            lo = edges[i]
            hi = edges[i + 1] - 1
            return f"{lo}-{hi}"
    return f"{edges[-1]}+"


def _aggregate_bureau_balance(
    raw_dir: Path,
    mapping_cfg: dict[str, Any],
) -> tuple[set[int], set[int]]:
    """Scan bureau_balance.csv in chunks.

    Returns:
        all_balance_bureaus: set of all SK_ID_BUREAU in bureau_balance
        bad_bureaus: set of SK_ID_BUREAU with severe delinquency in window
    """
    bad_statuses = set(mapping_cfg["severe_delinquency_36m"]["bad_statuses"])
    window_months = int(mapping_cfg["severe_delinquency_36m"]["window_months"])

    all_balance_bureaus: set[int] = set()
    bad_bureaus: set[int] = set()

    bb_path = raw_dir / "bureau_balance.csv"
    for chunk in pd.read_csv(
        bb_path,
        chunksize=1_000_000,
        dtype={
            "SK_ID_BUREAU": "int32",
            "MONTHS_BALANCE": "int16",
            "STATUS": "string",
        },
    ):
        all_balance_bureaus.update(chunk["SK_ID_BUREAU"].unique())
        bad_mask = chunk["STATUS"].isin(bad_statuses) & (chunk["MONTHS_BALANCE"] >= -window_months)
        if bad_mask.any():
            bad_bureaus.update(chunk.loc[bad_mask, "SK_ID_BUREAU"])

    return all_balance_bureaus, bad_bureaus


def _aggregate_bureau(
    raw_dir: Path,
    mapping_cfg: dict[str, Any],
    all_balance_bureaus: set[int],
    bad_bureaus: set[int],
) -> dict[int, dict[str, Any]]:
    """Aggregate bureau.csv per SK_ID_CURR.

    Returns dict mapping sk_id_curr (int) to summary dict:
        has_active: bool
        active_ann_sum: Decimal
        active_ann_present: int
        active_ann_total: int
        written_off: bool
        has_bb: bool
        has_severe: bool
    """
    active_value = mapping_cfg["monthly_obligations"]["active_value"]
    bad_value = mapping_cfg["written_off"]["bad_value"]
    amount_col = mapping_cfg["monthly_obligations"]["bureau_amount_column"]

    bureau_path = raw_dir / "bureau.csv"
    df_b = pd.read_csv(
        bureau_path,
        usecols=["SK_ID_CURR", "SK_ID_BUREAU", "CREDIT_ACTIVE", amount_col],
        dtype={
            "SK_ID_CURR": "int32",
            "SK_ID_BUREAU": "int32",
            "CREDIT_ACTIVE": "string",
            amount_col: "string",
        },
    )

    curr_info: dict[int, dict[str, Any]] = {}
    for curr, bur, active, ann in zip(
        df_b["SK_ID_CURR"],
        df_b["SK_ID_BUREAU"],
        df_b["CREDIT_ACTIVE"],
        df_b[amount_col],
    ):
        info = curr_info.get(curr)
        if info is None:
            info = {
                "has_active": False,
                "active_ann_sum": Decimal("0"),
                "active_ann_present": 0,
                "active_ann_total": 0,
                "written_off": False,
                "has_bb": False,
                "has_severe": False,
            }
            curr_info[curr] = info

        if active == active_value:
            info["has_active"] = True
            info["active_ann_total"] += 1
            if pd.notna(ann) and str(ann).strip() not in ("", "nan"):
                info["active_ann_present"] += 1
                info["active_ann_sum"] += Decimal(str(ann).strip())
        elif active == bad_value:
            info["written_off"] = True

        if bur in all_balance_bureaus:
            info["has_bb"] = True
            if bur in bad_bureaus:
                info["has_severe"] = True

    return curr_info


def map_d2(
    raw_dir: Path | str,
    out_path: Path | str,
    protected_path: Path | str,
    mapping_cfg: dict[str, Any],
    exp_cfg: dict[str, Any],
    mapping_table_path: Path | str | None = None,
) -> None:
    """Map Home Credit Default Risk tables to the fact schema and write outputs."""
    raw_dir = Path(raw_dir)
    out_path = Path(out_path)
    protected_path = Path(protected_path)
    if mapping_table_path is None:
        table_p = Path(
            exp_cfg.get("d2", {}).get("mapping_table", "docs/datasheets/d2-mapping-table.md")
        )
    else:
        table_p = Path(mapping_table_path)

    days_per_year = Decimal(str(mapping_cfg["age"]["days_per_year"]))
    days_per_month = Decimal(str(mapping_cfg["employment_months"]["days_per_month"]))
    unknown_sentinel = int(mapping_cfg["employment_months"]["unknown_sentinel"])
    months_per_year = Decimal(str(mapping_cfg["monthly_net_income"]["months_per_year"]))
    salaried_values: list[str] = mapping_cfg["employment_type"]["salaried"]
    self_employed_values: list[str] = mapping_cfg["employment_type"]["self_employed"]
    other_default: str = mapping_cfg["employment_type"]["other_default"]
    cs_base = Decimal(str(mapping_cfg["credit_score"]["base"]))
    cs_span = Decimal(str(mapping_cfg["credit_score"]["span"]))
    kyc_verified_val: bool = bool(mapping_cfg["kyc_consent"]["kyc_verified"])
    consent_given_val: bool = bool(mapping_cfg["kyc_consent"]["consent_given"])
    id_prefix: str = mapping_cfg["applicant_id"]["prefix"]
    age_band_edges: list[int] = [int(e) for e in mapping_cfg["protected_store"]["age_band_edges"]]
    protected_cols: list[str] = mapping_cfg["protected_store"]["columns"]

    master_seed = int(exp_cfg["seeds"]["master"])
    fallback_base_seed = derive_seed(master_seed, "fallback_obligations")

    gen_cfg_path = Path("config/generator.toml")
    with open(gen_cfg_path, "rb") as fh:
        gen_cfg = tomllib.load(fh)
    fallback_zero_fraction = str(gen_cfg["obligations_fallback"]["zero_fraction"])
    fallback_alpha = str(gen_cfg["obligations_fallback"]["beta_alpha"])
    fallback_beta = str(gen_cfg["obligations_fallback"]["beta_beta"])

    print("Aggregating bureau_balance.csv ...", file=sys.stderr)
    all_bb, bad_bb = _aggregate_bureau_balance(raw_dir, mapping_cfg)

    print("Aggregating bureau.csv ...", file=sys.stderr)
    curr_info = _aggregate_bureau(raw_dir, mapping_cfg, all_bb, bad_bb)

    print("Reading application_train.csv ...", file=sys.stderr)
    app_df = pd.read_csv(raw_dir / "application_train.csv", dtype=str)

    output_rows: list[dict[str, Any]] = []
    protected_rows: list[dict[str, Any]] = []

    # Counters for coverage table
    observed_counts: dict[str, int] = {}
    derived_counts: dict[str, int] = {}
    fallback_counts: dict[str, int] = {}
    unknown_counts: dict[str, int] = {}

    def _record_flag(field: str, flag: str) -> None:
        if flag == "observed":
            observed_counts[field] = observed_counts.get(field, 0) + 1
        elif flag == "derived":
            derived_counts[field] = derived_counts.get(field, 0) + 1
        elif flag == "fallback":
            fallback_counts[field] = fallback_counts.get(field, 0) + 1
        elif flag == "unknown":
            unknown_counts[field] = unknown_counts.get(field, 0) + 1

    # Counts for rows that do not fit the product
    count_v03_fail = 0
    count_v04_fail = 0
    count_k05_fail = 0

    param_cfg_path = Path("params/params.toml")
    with open(param_cfg_path, "rb") as fh:
        params = tomllib.load(fh)
    min_amount = int(params["product"]["min_amount"])
    max_amount = int(params["product"]["max_amount"])
    min_tenure = int(params["product"]["min_tenure_months"])
    max_tenure = int(params["product"]["max_tenure_months"])
    min_income = int(params["eligibility"]["min_monthly_income"])

    print("Mapping rows ...", file=sys.stderr)
    for _, row in app_df.iterrows():
        sk_id_curr_str = str(row["SK_ID_CURR"]).strip()
        sk_id_curr_int = int(sk_id_curr_str)
        applicant_id = id_prefix + sk_id_curr_str
        target_raw = row.get("TARGET", None)
        target = None if pd.isna(target_raw) else int(target_raw)

        # age (ASM-D13 rounding, floor)
        days_birth_raw = row.get("DAYS_BIRTH", None)
        if pd.isna(days_birth_raw) or str(days_birth_raw).strip() == "":
            age = None
            age_flag = "unknown"
        else:
            age_d = Decimal(str(days_birth_raw).strip())
            age = int((-age_d / days_per_year).to_integral_value(rounding=ROUND_FLOOR))
            age_flag = "derived"
        _record_flag("age", age_flag)

        # employment_type (ASM-D1)
        nit_raw = row.get("NAME_INCOME_TYPE", None)
        name_income_type = str(nit_raw).strip() if not pd.isna(nit_raw) else ""
        if name_income_type in salaried_values:
            employment_type = "salaried"
            employment_type_flag = "observed"
        elif name_income_type in self_employed_values:
            employment_type = "self_employed"
            employment_type_flag = "observed"
        elif name_income_type:
            employment_type = other_default
            employment_type_flag = "observed"
        else:
            employment_type = None
            employment_type_flag = "unknown"
        _record_flag("employment_type", employment_type_flag)

        # employment_months (ASM-D2)
        days_employed_raw = row.get("DAYS_EMPLOYED", None)
        if pd.isna(days_employed_raw) or str(days_employed_raw).strip() == "":
            employment_months = None
            employment_months_flag = "unknown"
        else:
            days_emp = int(Decimal(str(days_employed_raw).strip()))
            if days_emp == unknown_sentinel:
                employment_months = None
                employment_months_flag = "unknown"
            else:
                employment_months = int(
                    (-Decimal(str(days_emp)) / days_per_month).to_integral_value(
                        rounding=ROUND_FLOOR
                    )
                )
                employment_months_flag = "derived"
        _record_flag("employment_months", employment_months_flag)

        # monthly_net_income (ASM-D3)
        amt_income_raw = row.get("AMT_INCOME_TOTAL", None)
        if pd.isna(amt_income_raw) or str(amt_income_raw).strip() == "":
            monthly_net_income = None
            monthly_net_income_flag = "unknown"
        else:
            income_d = Decimal(str(amt_income_raw).strip())
            monthly_net_income = int(
                (income_d / months_per_year).to_integral_value(rounding=ROUND_HALF_UP)
            )
            monthly_net_income_flag = "derived"
        _record_flag("monthly_net_income", monthly_net_income_flag)

        # credit_score (ASM-D5)
        ext_values: list[Decimal] = []
        for col in mapping_cfg["credit_score"]["sources"]:
            v = row.get(col, None)
            if not pd.isna(v) and str(v).strip() not in ("", "nan"):
                ext_values.append(Decimal(str(v).strip()))
        if ext_values:
            mean_ext = sum(ext_values) / Decimal(len(ext_values))
            cs_d = cs_base + cs_span * mean_ext
            credit_score = int(cs_d.to_integral_value(rounding=ROUND_HALF_UP))
            credit_score_flag = "derived"
        else:
            credit_score = None
            credit_score_flag = "unknown"
        _record_flag("credit_score", credit_score_flag)

        # enquiries_6m (ASM-D6)
        enq_sources = mapping_cfg["enquiries_6m"]["sources"]
        enq_values: list[int] = []
        for col in enq_sources:
            v = row.get(col, None)
            if not pd.isna(v) and str(v).strip() not in ("", "nan"):
                enq_values.append(int(Decimal(str(v).strip())))
        if enq_values:
            enquiries_6m = sum(enq_values)
            enquiries_6m_flag = "derived"
        elif all(
            pd.isna(row.get(col, None)) or str(row.get(col, "")).strip() in ("", "nan")
            for col in enq_sources
        ):
            enquiries_6m = None
            enquiries_6m_flag = "unknown"
        else:
            enquiries_6m = sum(enq_values)
            enquiries_6m_flag = "derived"
        _record_flag("enquiries_6m", enquiries_6m_flag)

        # monthly_obligations (ASM-D4)
        info = curr_info.get(sk_id_curr_int)
        if info is None:
            monthly_obligations = draw_fallback_obligations(
                sk_id_curr_int,
                monthly_net_income,
                fallback_base_seed,
                fallback_zero_fraction,
                fallback_alpha,
                fallback_beta,
            )
            obligations_source = "fallback_no_bureau"
            monthly_obligations_flag = "fallback"
        elif not info["has_active"]:
            monthly_obligations = 0
            obligations_source = "bureau_zero"
            monthly_obligations_flag = "derived"
        elif info["active_ann_present"] > 0:
            monthly_obligations = int(
                info["active_ann_sum"].to_integral_value(rounding=ROUND_HALF_UP)
            )
            if info["active_ann_present"] == info["active_ann_total"]:
                obligations_source = "bureau"
            else:
                obligations_source = "bureau_partial"
            monthly_obligations_flag = "derived"
        else:
            monthly_obligations = draw_fallback_obligations(
                sk_id_curr_int,
                monthly_net_income,
                fallback_base_seed,
                fallback_zero_fraction,
                fallback_alpha,
                fallback_beta,
            )
            obligations_source = "fallback_missing_annuity"
            monthly_obligations_flag = "fallback"
        _record_flag("monthly_obligations", monthly_obligations_flag)

        # severe_delinquency_36m (ASM-D7)
        if info is None or not info["has_bb"]:
            severe_delinquency_36m = None
            severe_delinquency_36m_flag = "unknown"
        else:
            severe_delinquency_36m = bool(info["has_severe"])
            severe_delinquency_36m_flag = "derived"
        _record_flag("severe_delinquency_36m", severe_delinquency_36m_flag)

        # written_off (ASM-D8)
        if info is None:
            written_off = None
            written_off_flag = "unknown"
        else:
            written_off = bool(info["written_off"])
            written_off_flag = "derived"
        _record_flag("written_off", written_off_flag)

        # kyc_verified, consent_given (ASM-D9)
        kyc_verified = kyc_verified_val
        kyc_verified_flag = "observed"
        consent_given = consent_given_val
        consent_given_flag = "observed"
        _record_flag("kyc_verified", kyc_verified_flag)
        _record_flag("consent_given", consent_given_flag)

        # requested_amount (ASM-D10, ASM-D13)
        amt_credit_raw = row.get("AMT_CREDIT", None)
        if pd.isna(amt_credit_raw) or str(amt_credit_raw).strip() == "":
            requested_amount = None
            requested_amount_flag = "unknown"
        else:
            requested_amount = int(
                Decimal(str(amt_credit_raw).strip()).to_integral_value(rounding=ROUND_HALF_UP)
            )
            requested_amount_flag = "derived"
        _record_flag("requested_amount", requested_amount_flag)

        # requested_tenure_months (ASM-D11, ASM-D13)
        amt_annuity_raw = row.get("AMT_ANNUITY", None)
        if (
            requested_amount is None
            or pd.isna(amt_annuity_raw)
            or str(amt_annuity_raw).strip() in ("", "nan", "0", "0.0")
        ):
            requested_tenure_months = None
            requested_tenure_months_flag = "unknown"
        else:
            ann_d = Decimal(str(amt_annuity_raw).strip())
            if ann_d == Decimal("0"):
                requested_tenure_months = None
                requested_tenure_months_flag = "unknown"
            else:
                tenure_d = Decimal(str(requested_amount)) / ann_d
                requested_tenure_months = int(tenure_d.to_integral_value(rounding=ROUND_HALF_UP))
                requested_tenure_months_flag = "derived"
        _record_flag("requested_tenure_months", requested_tenure_months_flag)

        # region_tier (ASM-D12)
        region_raw = row.get("REGION_RATING_CLIENT", None)
        if pd.isna(region_raw) or str(region_raw).strip() == "":
            region_tier = None
            region_tier_flag = "unknown"
        else:
            region_tier = int(Decimal(str(region_raw).strip()))
            region_tier_flag = "observed"
        _record_flag("region_tier", region_tier_flag)

        # Check policy rule fit (V03, V04, K05)
        if requested_amount is not None:
            if requested_amount < min_amount or requested_amount > max_amount:
                count_v03_fail += 1
        if requested_tenure_months is not None:
            if requested_tenure_months < min_tenure or requested_tenure_months > max_tenure:
                count_v04_fail += 1
        if monthly_net_income is not None:
            if monthly_net_income < min_income:
                count_k05_fail += 1

        # Protected store row (audit-only)
        age_band = _age_band(age, age_band_edges)
        prot_row: dict[str, Any] = {"applicant_id": applicant_id}
        for col in protected_cols:
            v = row.get(col, None)
            prot_row[col] = None if pd.isna(v) else str(v)
        prot_row["age_band"] = age_band
        protected_rows.append(prot_row)

        output_rows.append(
            {
                "applicant_id": applicant_id,
                "TARGET": target,
                "age": age,
                "employment_type": employment_type,
                "employment_months": employment_months,
                "monthly_net_income": monthly_net_income,
                "monthly_obligations": monthly_obligations,
                "credit_score": credit_score,
                "enquiries_6m": enquiries_6m,
                "severe_delinquency_36m": severe_delinquency_36m,
                "written_off": written_off,
                "kyc_verified": kyc_verified,
                "consent_given": consent_given,
                "requested_amount": requested_amount,
                "requested_tenure_months": requested_tenure_months,
                "region_tier": region_tier,
                "obligations_source": obligations_source,
                "age_flag": age_flag,
                "employment_type_flag": employment_type_flag,
                "employment_months_flag": employment_months_flag,
                "monthly_net_income_flag": monthly_net_income_flag,
                "monthly_obligations_flag": monthly_obligations_flag,
                "credit_score_flag": credit_score_flag,
                "enquiries_6m_flag": enquiries_6m_flag,
                "severe_delinquency_36m_flag": severe_delinquency_36m_flag,
                "written_off_flag": written_off_flag,
                "kyc_verified_flag": kyc_verified_flag,
                "consent_given_flag": consent_given_flag,
                "requested_amount_flag": requested_amount_flag,
                "requested_tenure_months_flag": requested_tenure_months_flag,
                "region_tier_flag": region_tier_flag,
            }
        )

    OUTPUT_COLUMNS = [
        "applicant_id",
        "TARGET",
        "age",
        "employment_type",
        "employment_months",
        "monthly_net_income",
        "monthly_obligations",
        "credit_score",
        "enquiries_6m",
        "severe_delinquency_36m",
        "written_off",
        "kyc_verified",
        "consent_given",
        "requested_amount",
        "requested_tenure_months",
        "region_tier",
        "obligations_source",
        "age_flag",
        "employment_type_flag",
        "employment_months_flag",
        "monthly_net_income_flag",
        "monthly_obligations_flag",
        "credit_score_flag",
        "enquiries_6m_flag",
        "severe_delinquency_36m_flag",
        "written_off_flag",
        "kyc_verified_flag",
        "consent_given_flag",
        "requested_amount_flag",
        "requested_tenure_months_flag",
        "region_tier_flag",
    ]
    result_df = pd.DataFrame(output_rows, columns=OUTPUT_COLUMNS)

    # Validate mapped facts with Phase 1 validator
    from src.facts.fact_builder import validate_input  # noqa: PLC0415

    FACT_FIELDS = [
        "age",
        "employment_type",
        "employment_months",
        "monthly_net_income",
        "monthly_obligations",
        "credit_score",
        "enquiries_6m",
        "severe_delinquency_36m",
        "written_off",
        "kyc_verified",
        "consent_given",
        "requested_amount",
        "requested_tenure_months",
        "region_tier",
    ]

    failure_counts: dict[str, int] = {}
    n_total = len(result_df)
    n_failed = 0

    print("Validating with schema validator ...", file=sys.stderr)
    for _, row_data in result_df.iterrows():
        input_dict: dict[str, Any] = {
            "applicant_id": row_data["applicant_id"],
        }
        for f in FACT_FIELDS:
            val = row_data[f]
            if pd.isna(val) if not isinstance(val, (bool, str)) else False:
                input_dict[f] = None
            else:
                input_dict[f] = val

        errors = validate_input(input_dict)
        if errors:
            n_failed += 1
            for err in errors:
                field_name = err.split(":")[0].strip()
                failure_counts[field_name] = failure_counts.get(field_name, 0) + 1

    if n_total > 0 and (n_failed * 100 > n_total):  # > 1% check without float
        print(
            f"STOP: {n_failed}/{n_total} rows failed input validation. Counts: {failure_counts}",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print(
            f"Validation passed: {n_failed}/{n_total} rows failed ({n_failed} failures).",
            file=sys.stderr,
        )

    # Write output files (LF line endings, no index)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    protected_path.parent.mkdir(parents=True, exist_ok=True)

    result_df.to_csv(out_path, index=False, lineterminator="\n")
    prot_df = pd.DataFrame(protected_rows)
    prot_df.to_csv(protected_path, index=False, lineterminator="\n")

    for fpath in (out_path, protected_path):
        digest = hashlib.sha256(fpath.read_bytes()).hexdigest()
        print(f"SHA-256 {fpath}: {digest}")

    # Write mapping table
    table_p.parent.mkdir(parents=True, exist_ok=True)

    # All unmapped columns from application_train
    used_app_cols = {
        "SK_ID_CURR",
        "TARGET",
        "DAYS_BIRTH",
        "NAME_INCOME_TYPE",
        "DAYS_EMPLOYED",
        "AMT_INCOME_TOTAL",
        "AMT_CREDIT",
        "AMT_ANNUITY",
        "REGION_RATING_CLIENT",
        "EXT_SOURCE_1",
        "EXT_SOURCE_2",
        "EXT_SOURCE_3",
        "AMT_REQ_CREDIT_BUREAU_MON",
        "AMT_REQ_CREDIT_BUREAU_QRT",
        "CODE_GENDER",
        "NAME_EDUCATION_TYPE",
        "NAME_FAMILY_STATUS",
    }
    all_raw_cols = set(app_df.columns)
    unused_cols = sorted(list(all_raw_cols - used_app_cols))

    table_lines = [
        "# D2 Mapping Table (Home Credit Default Risk)",
        "",
        "This table documents the mapping from Home Credit Default Risk to the loan expert system fact schema.",
        f"Total applicants mapped: {n_total}.",
        "",
        "## Policy Fit Counts",
        "",
        f"- Rows failing V03 (requested amount outside policy range [{min_amount}, {max_amount}]): {count_v03_fail}",
        f"- Rows failing V04 (requested tenure outside policy range [{min_tenure}, {max_tenure}]): {count_v04_fail}",
        f"- Rows failing K05 (monthly income below minimum threshold): {count_k05_fail}",
        "",
        "## Fact Mapping and Coverage",
        "",
        "| Fact | Source Columns | Transformation | Assumption | Strength | Observed | Derived | Fallback | Unknown |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    FACT_META = [
        ("age", "DAYS_BIRTH", "floor(-DAYS_BIRTH / 365.25)", "None", "Strong"),
        (
            "employment_type",
            "NAME_INCOME_TYPE",
            "salaried/self_employed/other mapping",
            "ASM-D1",
            "Medium",
        ),
        (
            "employment_months",
            "DAYS_EMPLOYED",
            "floor(-DAYS_EMPLOYED / 30.4); 365243 -> null",
            "ASM-D2",
            "Medium",
        ),
        (
            "monthly_net_income",
            "AMT_INCOME_TOTAL",
            "AMT_INCOME_TOTAL / 12 round half-up",
            "ASM-D3",
            "Medium",
        ),
        (
            "monthly_obligations",
            "bureau (AMT_ANNUITY, CREDIT_ACTIVE)",
            "Active annuities sum, 0 if no active, Beta fallback",
            "ASM-D4",
            "Weak",
        ),
        (
            "credit_score",
            "EXT_SOURCE_1, 2, 3",
            "300 + 600 * mean(ext sources) round half-up",
            "ASM-D5",
            "Weak",
        ),
        (
            "enquiries_6m",
            "AMT_REQ_CREDIT_BUREAU_MON, QRT",
            "Sum of monthly and quarterly enquiries",
            "ASM-D6",
            "Medium",
        ),
        (
            "severe_delinquency_36m",
            "bureau_balance (STATUS, MONTHS_BALANCE)",
            "Status 4/5 in last 36m -> true; false if balance rows; null if none",
            "ASM-D7",
            "Medium",
        ),
        (
            "written_off",
            "bureau (CREDIT_ACTIVE)",
            "'Bad debt' -> true; false if bureau rows; null if none",
            "ASM-D8",
            "Medium",
        ),
        ("kyc_verified", "None", "Constant true", "ASM-D9", "N/A"),
        ("consent_given", "None", "Constant true", "ASM-D9", "N/A"),
        ("requested_amount", "AMT_CREDIT", "AMT_CREDIT round half-up", "ASM-D10", "Medium"),
        (
            "requested_tenure_months",
            "AMT_CREDIT, AMT_ANNUITY",
            "AMT_CREDIT / AMT_ANNUITY round half-up",
            "ASM-D11",
            "Weak",
        ),
        ("region_tier", "REGION_RATING_CLIENT", "1-3 rating as int", "ASM-D12", "Medium"),
    ]

    for field, src, trans, asmp, strength in FACT_META:
        obs = observed_counts.get(field, 0)
        der = derived_counts.get(field, 0)
        fb = fallback_counts.get(field, 0)
        unk = unknown_counts.get(field, 0)
        table_lines.append(
            f"| `{field}` | {src} | {trans} | {asmp} | {strength} | {obs} | {der} | {fb} | {unk} |"
        )

    table_lines.extend(
        [
            "",
            "## Raw Columns Not Used",
            "",
            f"Total unused application_train columns: {len(unused_cols)}.",
            "",
            "```text",
            ", ".join(unused_cols),
            "```",
            "",
        ]
    )

    table_p.write_text("\n".join(table_lines), encoding="utf-8")
    print(f"Wrote mapping table: {table_p}")


def main() -> None:
    """Read configs and run the D2 mapping pipeline."""
    parser = argparse.ArgumentParser(description="Map D2 (Home Credit) to fact schema.")
    parser.add_argument("--raw-dir", default=None, help="Override raw data directory.")
    args = parser.parse_args()

    with open("config/d2_mapping.toml", "rb") as fh:
        mapping_cfg = tomllib.load(fh)
    with open("config/experiment.toml", "rb") as fh:
        exp_cfg = tomllib.load(fh)

    raw_dir = Path(args.raw_dir) if args.raw_dir else Path(exp_cfg["d2"]["raw_dir"])
    out_path = Path(exp_cfg["d2"]["mapped_path"])
    protected_path = Path(exp_cfg["d2"]["protected_path"])

    map_d2(raw_dir, out_path, protected_path, mapping_cfg, exp_cfg)


if __name__ == "__main__":
    main()
