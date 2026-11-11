"""Unit tests for D3 synthetic generator (WP-16b, DR-05).

Lean mode requirements:
- Same seed gives identical SHA-256.
- Different seed gives different SHA-256.
- Bias switch off by default.
- Bias switch on shifts only the target group's income.
- No D3 field is a float (all int, bool, str, None).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from data.synthetic.d3_generator import generate_d3


def test_DR05_d3_same_seed_identical_hash(tmp_path: Path) -> None:
    """Verify that same seed produces byte-identical D3 output."""
    pop1 = tmp_path / "run1" / "d3_population.csv"
    prot1 = tmp_path / "run1" / "d3_protected.csv"
    generate_d3(size=200, master_seed=12345, out_population_path=pop1, out_protected_path=prot1)
    hash1 = hashlib.sha256(pop1.read_bytes()).hexdigest()
    prot_hash1 = hashlib.sha256(prot1.read_bytes()).hexdigest()

    pop2 = tmp_path / "run2" / "d3_population.csv"
    prot2 = tmp_path / "run2" / "d3_protected.csv"
    generate_d3(size=200, master_seed=12345, out_population_path=pop2, out_protected_path=prot2)
    hash2 = hashlib.sha256(pop2.read_bytes()).hexdigest()
    prot_hash2 = hashlib.sha256(prot2.read_bytes()).hexdigest()

    assert hash1 == hash2, "D3 population hash differs for identical seed"
    assert prot_hash1 == prot_hash2, "D3 protected store hash differs for identical seed"


def test_DR05_d3_different_seed_different_hash(tmp_path: Path) -> None:
    """Verify that different seed produces different D3 output."""
    pop1 = tmp_path / "seed1" / "d3_population.csv"
    prot1 = tmp_path / "seed1" / "d3_protected.csv"
    generate_d3(size=200, master_seed=11111, out_population_path=pop1, out_protected_path=prot1)
    hash1 = hashlib.sha256(pop1.read_bytes()).hexdigest()

    pop2 = tmp_path / "seed2" / "d3_population.csv"
    prot2 = tmp_path / "seed2" / "d3_protected.csv"
    generate_d3(size=200, master_seed=22222, out_population_path=pop2, out_protected_path=prot2)
    hash2 = hashlib.sha256(pop2.read_bytes()).hexdigest()

    assert hash1 != hash2, "D3 population hash should differ for different seeds"


def test_DR05_d3_no_float_fields(tmp_path: Path) -> None:
    """Verify that output fields are strictly int, bool, str or None (never float)."""
    pop = tmp_path / "d3_population.csv"
    prot = tmp_path / "d3_protected.csv"
    df_pop, df_prot = generate_d3(
        size=200, master_seed=99999, out_population_path=pop, out_protected_path=prot
    )

    for col in df_pop.columns:
        for val in df_pop[col]:
            if pd.isna(val) or val is None:
                continue
            assert not isinstance(val, (float, np.floating)), (
                f"Column {col} has float value {val!r}"
            )
            assert isinstance(val, (int, np.integer, bool, str)), (
                f"Column {col} has unexpected type {type(val)}: {val!r}"
            )


def test_DR05_d3_bias_switch(tmp_path: Path) -> None:
    """Verify that bias switch modifies income for female applicants only."""
    # Control run (bias off)
    pop_ctrl = tmp_path / "ctrl" / "pop.csv"
    prot_ctrl = tmp_path / "ctrl" / "prot.csv"
    df_pop_c, df_prot_c = generate_d3(
        size=500,
        master_seed=54321,
        bias_enabled=False,
        out_population_path=pop_ctrl,
        out_protected_path=prot_ctrl,
    )

    # Bias run (bias on)
    pop_bias = tmp_path / "bias" / "pop.csv"
    prot_bias = tmp_path / "bias" / "prot.csv"
    df_pop_b, df_prot_b = generate_d3(
        size=500,
        master_seed=54321,
        bias_enabled=True,
        out_population_path=pop_bias,
        out_protected_path=prot_bias,
    )

    merged_c = pd.merge(df_pop_c, df_prot_c[["applicant_id", "gender"]], on="applicant_id")
    merged_b = pd.merge(df_pop_b, df_prot_b[["applicant_id", "gender"]], on="applicant_id")

    # For Male applicants, incomes should be identical between control and bias runs
    males_c = merged_c[merged_c["gender"] == "M"]["monthly_net_income"].values
    males_b = merged_b[merged_b["gender"] == "M"]["monthly_net_income"].values
    assert (males_c == males_b).all(), (
        "Male applicant income changed unexpectedly under gender bias"
    )

    # For Female applicants, incomes should differ
    females_c = merged_c[merged_c["gender"] == "F"]["monthly_net_income"].values
    females_b = merged_b[merged_b["gender"] == "F"]["monthly_net_income"].values
    assert not (females_c == females_b).all(), (
        "Female applicant income did not change under gender bias"
    )
