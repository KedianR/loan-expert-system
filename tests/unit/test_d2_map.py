"""Unit tests for D2 mapping (WP-15, DR-04, ASM-D1 to ASM-D13).

Lean mode requirements:
- Same hash twice on fixture.
- Every mapped fact has an assumption recorded.
- Float ban failure proof.
- Bureau fallback rules (4 cases).
- Sentinel DAYS_EMPLOYED handling.
- NAME_INCOME_TYPE mapping.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pandas as pd

from src.data.d2_map import map_d2
from tools.check_floats import check_file


def test_DR04_float_ban_fails_when_float_added(tmp_path: Path) -> None:
    """Prove that check_file fails when a float is added."""
    # 1. src/data/d2_map.py has 0 violations
    clean_violations = check_file(Path("src/data/d2_map.py"))
    assert len(clean_violations) == 0, f"d2_map.py has float violations: {clean_violations}"

    # 2. Temporary file with float literal fails
    bad_code = "x: float = 1.23\n"
    bad_file = tmp_path / "bad.py"
    bad_file.write_text(bad_code, encoding="utf-8")
    violations = check_file(bad_file)
    assert len(violations) > 0
    assert any("float literal" in desc for _, _, desc in violations)

    # 3. Temporary file with float() call fails
    bad_code_call = "y = float('456')\n"
    bad_file_call = tmp_path / "bad_call.py"
    bad_file_call.write_text(bad_code_call, encoding="utf-8")
    violations_call = check_file(bad_file_call)
    assert len(violations_call) > 0
    assert any("call to float()" in desc for _, _, desc in violations_call)


def test_DR04_mapping_reproducibility_on_fixture(tmp_path: Path) -> None:
    """Verify that mapping produces identical SHA-256 on same fixture twice."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    # Create minimal 3-row application_train.csv
    app_csv = (
        "SK_ID_CURR,TARGET,DAYS_BIRTH,NAME_INCOME_TYPE,DAYS_EMPLOYED,AMT_INCOME_TOTAL,"
        "AMT_CREDIT,AMT_ANNUITY,REGION_RATING_CLIENT,EXT_SOURCE_1,EXT_SOURCE_2,EXT_SOURCE_3,"
        "AMT_REQ_CREDIT_BUREAU_MON,AMT_REQ_CREDIT_BUREAU_QRT,CODE_GENDER,NAME_EDUCATION_TYPE,NAME_FAMILY_STATUS\n"
        "100001,0,-12000,Working,-1000,120000,100000,5000,2,0.5,0.6,0.7,1,0,F,Higher education,Married\n"
        "100002,1,-15000,Commercial associate,-2000,240000,200000,10000,1,0.4,0.5,,0,1,M,Secondary / secondary special,Single / not married\n"
        "100003,0,-18000,Pensioner,365243,60000,50000,2500,3,,,0.8,,,F,Secondary / secondary special,Civil marriage\n"
    )
    (raw_dir / "application_train.csv").write_text(app_csv, encoding="utf-8")

    # bureau.csv
    bureau_csv = (
        "SK_ID_CURR,SK_ID_BUREAU,CREDIT_ACTIVE,AMT_ANNUITY\n"
        "100001,500001,Active,2000\n"
        "100002,500002,Closed,1500\n"
    )
    (raw_dir / "bureau.csv").write_text(bureau_csv, encoding="utf-8")

    # bureau_balance.csv
    bb_csv = "SK_ID_BUREAU,MONTHS_BALANCE,STATUS\n500001,-12,0\n500002,-40,5\n"
    (raw_dir / "bureau_balance.csv").write_text(bb_csv, encoding="utf-8")

    with open("config/d2_mapping.toml", "rb") as fh:
        mapping_cfg = tomllib.load(fh)
    with open("config/experiment.toml", "rb") as fh:
        exp_cfg = tomllib.load(fh)

    out1 = tmp_path / "run1" / "mapped.csv"
    prot1 = tmp_path / "run1" / "protected.csv"
    map_d2(
        raw_dir,
        out1,
        prot1,
        mapping_cfg,
        exp_cfg,
        mapping_table_path=tmp_path / "run1" / "table.md",
    )

    import hashlib

    hash1 = hashlib.sha256(out1.read_bytes()).hexdigest()
    prot_hash1 = hashlib.sha256(prot1.read_bytes()).hexdigest()

    out2 = tmp_path / "run2" / "mapped.csv"
    prot2 = tmp_path / "run2" / "protected.csv"
    map_d2(
        raw_dir,
        out2,
        prot2,
        mapping_cfg,
        exp_cfg,
        mapping_table_path=tmp_path / "run2" / "table.md",
    )

    hash2 = hashlib.sha256(out2.read_bytes()).hexdigest()
    prot_hash2 = hashlib.sha256(prot2.read_bytes()).hexdigest()

    assert hash1 == hash2, "Mapped CSV SHA-256 differs between runs"
    assert prot_hash1 == prot_hash2, "Protected CSV SHA-256 differs between runs"


def test_ASM_D1_to_D13_documented_in_mapping_table() -> None:
    """Verify that every mapped fact has an assumption ID in docs/datasheets/d2-mapping-table.md."""
    mapping_table = Path("docs/datasheets/d2-mapping-table.md")
    assert mapping_table.exists(), "docs/datasheets/d2-mapping-table.md is missing"
    content = mapping_table.read_text(encoding="utf-8")

    expected_facts = [
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
    for fact in expected_facts:
        assert f"`{fact}`" in content, f"Fact `{fact}` not found in mapping table"


def test_bureau_fallback_rules(tmp_path: Path) -> None:
    """Verify 4 cases of ASM-D4:

    1. No bureau rows -> fallback_no_bureau
    2. Bureau rows, no active -> bureau_zero
    3. Active with annuity -> bureau / bureau_partial
    4. Active with missing annuity -> fallback_missing_annuity
    """
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    app_csv = (
        "SK_ID_CURR,TARGET,DAYS_BIRTH,NAME_INCOME_TYPE,DAYS_EMPLOYED,AMT_INCOME_TOTAL,"
        "AMT_CREDIT,AMT_ANNUITY,REGION_RATING_CLIENT,EXT_SOURCE_1,EXT_SOURCE_2,EXT_SOURCE_3,"
        "AMT_REQ_CREDIT_BUREAU_MON,AMT_REQ_CREDIT_BUREAU_QRT,CODE_GENDER,NAME_EDUCATION_TYPE,NAME_FAMILY_STATUS\n"
        "200001,0,-12000,Working,-1000,120000,100000,5000,2,0.5,0.6,0.7,0,0,F,Higher education,Single\n"
        "200002,0,-12000,Working,-1000,120000,100000,5000,2,0.5,0.6,0.7,0,0,F,Higher education,Single\n"
        "200003,0,-12000,Working,-1000,120000,100000,5000,2,0.5,0.6,0.7,0,0,F,Higher education,Single\n"
        "200004,0,-12000,Working,-1000,120000,100000,5000,2,0.5,0.6,0.7,0,0,F,Higher education,Single\n"
    )
    (raw_dir / "application_train.csv").write_text(app_csv, encoding="utf-8")

    # 200001: no bureau rows
    # 200002: closed only
    # 200003: active with annuity
    # 200004: active with missing annuity
    bureau_csv = (
        "SK_ID_CURR,SK_ID_BUREAU,CREDIT_ACTIVE,AMT_ANNUITY\n"
        "200002,600002,Closed,1000\n"
        "200003,600003,Active,3500\n"
        "200004,600004,Active,\n"
    )
    (raw_dir / "bureau.csv").write_text(bureau_csv, encoding="utf-8")

    bb_csv = "SK_ID_BUREAU,MONTHS_BALANCE,STATUS\n"
    (raw_dir / "bureau_balance.csv").write_text(bb_csv, encoding="utf-8")

    with open("config/d2_mapping.toml", "rb") as fh:
        mapping_cfg = tomllib.load(fh)
    with open("config/experiment.toml", "rb") as fh:
        exp_cfg = tomllib.load(fh)

    out_csv = tmp_path / "out.csv"
    prot_csv = tmp_path / "prot.csv"
    map_d2(
        raw_dir, out_csv, prot_csv, mapping_cfg, exp_cfg, mapping_table_path=tmp_path / "table.md"
    )

    df = pd.read_csv(out_csv)
    row1 = df[df["applicant_id"] == "hc-200001"].iloc[0]
    row2 = df[df["applicant_id"] == "hc-200002"].iloc[0]
    row3 = df[df["applicant_id"] == "hc-200003"].iloc[0]
    row4 = df[df["applicant_id"] == "hc-200004"].iloc[0]

    assert row1["obligations_source"] == "fallback_no_bureau"
    assert row2["obligations_source"] == "bureau_zero"
    assert row2["monthly_obligations"] == 0
    assert row3["obligations_source"] == "bureau"
    assert row3["monthly_obligations"] == 3500
    assert row4["obligations_source"] == "fallback_missing_annuity"


def test_sentinel_days_employed_becomes_none(tmp_path: Path) -> None:
    """Verify that sentinel 365243 maps to null employment_months."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    app_csv = (
        "SK_ID_CURR,TARGET,DAYS_BIRTH,NAME_INCOME_TYPE,DAYS_EMPLOYED,AMT_INCOME_TOTAL,"
        "AMT_CREDIT,AMT_ANNUITY,REGION_RATING_CLIENT,EXT_SOURCE_1,EXT_SOURCE_2,EXT_SOURCE_3,"
        "AMT_REQ_CREDIT_BUREAU_MON,AMT_REQ_CREDIT_BUREAU_QRT,CODE_GENDER,NAME_EDUCATION_TYPE,NAME_FAMILY_STATUS\n"
        "300001,0,-12000,Pensioner,365243,120000,100000,5000,2,0.5,0.6,0.7,0,0,F,Higher education,Single\n"
    )
    (raw_dir / "application_train.csv").write_text(app_csv, encoding="utf-8")
    (raw_dir / "bureau.csv").write_text(
        "SK_ID_CURR,SK_ID_BUREAU,CREDIT_ACTIVE,AMT_ANNUITY\n", encoding="utf-8"
    )
    (raw_dir / "bureau_balance.csv").write_text(
        "SK_ID_BUREAU,MONTHS_BALANCE,STATUS\n", encoding="utf-8"
    )

    with open("config/d2_mapping.toml", "rb") as fh:
        mapping_cfg = tomllib.load(fh)
    with open("config/experiment.toml", "rb") as fh:
        exp_cfg = tomllib.load(fh)

    out_csv = tmp_path / "out.csv"
    prot_csv = tmp_path / "prot.csv"
    map_d2(
        raw_dir, out_csv, prot_csv, mapping_cfg, exp_cfg, mapping_table_path=tmp_path / "table.md"
    )

    df = pd.read_csv(out_csv)
    row = df.iloc[0]
    assert pd.isna(row["employment_months"])
    assert row["employment_months_flag"] == "unknown"


def test_income_type_mapping(tmp_path: Path) -> None:
    """Verify NAME_INCOME_TYPE mapping (ASM-D1)."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    app_csv = (
        "SK_ID_CURR,TARGET,DAYS_BIRTH,NAME_INCOME_TYPE,DAYS_EMPLOYED,AMT_INCOME_TOTAL,"
        "AMT_CREDIT,AMT_ANNUITY,REGION_RATING_CLIENT,EXT_SOURCE_1,EXT_SOURCE_2,EXT_SOURCE_3,"
        "AMT_REQ_CREDIT_BUREAU_MON,AMT_REQ_CREDIT_BUREAU_QRT,CODE_GENDER,NAME_EDUCATION_TYPE,NAME_FAMILY_STATUS\n"
        "400001,0,-12000,Working,-1000,120000,100000,5000,2,0.5,0.6,0.7,0,0,F,Higher education,Single\n"
        "400002,0,-12000,Commercial associate,-1000,120000,100000,5000,2,0.5,0.6,0.7,0,0,F,Higher education,Single\n"
        "400003,0,-12000,Maternity leave,-1000,120000,100000,5000,2,0.5,0.6,0.7,0,0,F,Higher education,Single\n"
    )
    (raw_dir / "application_train.csv").write_text(app_csv, encoding="utf-8")
    (raw_dir / "bureau.csv").write_text(
        "SK_ID_CURR,SK_ID_BUREAU,CREDIT_ACTIVE,AMT_ANNUITY\n", encoding="utf-8"
    )
    (raw_dir / "bureau_balance.csv").write_text(
        "SK_ID_BUREAU,MONTHS_BALANCE,STATUS\n", encoding="utf-8"
    )

    with open("config/d2_mapping.toml", "rb") as fh:
        mapping_cfg = tomllib.load(fh)
    with open("config/experiment.toml", "rb") as fh:
        exp_cfg = tomllib.load(fh)

    out_csv = tmp_path / "out.csv"
    prot_csv = tmp_path / "prot.csv"
    map_d2(
        raw_dir, out_csv, prot_csv, mapping_cfg, exp_cfg, mapping_table_path=tmp_path / "table.md"
    )

    df = pd.read_csv(out_csv)
    assert df.loc[df["applicant_id"] == "hc-400001", "employment_type"].values[0] == "salaried"
    assert df.loc[df["applicant_id"] == "hc-400002", "employment_type"].values[0] == "self_employed"
    assert df.loc[df["applicant_id"] == "hc-400003", "employment_type"].values[0] == "other"
