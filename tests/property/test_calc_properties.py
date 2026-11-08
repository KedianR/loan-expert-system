"""
Property-based tests for calculation module invariants.

Implements: WP-04, FR-03, FR-07, docs/06-test-plan.md §4, Lean mode
Fixed random seeds: 20261108

Invariants tested:
1. Recommended amount never exceeds requested amount, capacity cap, 10x income, or max product limit.
2. Recommended amount is always a multiple of amount_step (5,000).
3. EMI at the maximum principal is within one rupee of the maximum affordable EMI.
4. APR is at least the band's indicative rate whenever the fee is positive.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given, seed, settings
from hypothesis import strategies as st

from src.calc.formulas import (
    calculate_apr,
    calculate_emi,
    calculate_fee,
    calculate_max_affordable_emi,
    calculate_max_principal,
    calculate_monthly_rate,
    calculate_recommended_amount,
)
from src.engine.param_loader import load_params

REPO_ROOT = Path(__file__).resolve().parents[2]
PARAMS_PATH = REPO_ROOT / "params" / "params.toml"
PROPERTY_SEED = 20261108


@pytest.fixture(scope="module")
def policy():
    res = load_params(PARAMS_PATH)
    assert res.ok
    return res


class TestCalculationProperties:
    """Hypothesis property tests with fixed seed."""

    @seed(PROPERTY_SEED)
    @settings(max_examples=100)
    @given(
        requested_amount=st.integers(min_value=10000, max_value=5000000),
        income=st.integers(min_value=15000, max_value=500000),
        obligations=st.integers(min_value=0, max_value=250000),
        tenure=st.integers(min_value=12, max_value=60),
        band_idx=st.integers(min_value=0, max_value=2),
    )
    def test_property_recommended_amount_caps_and_step(
        self,
        requested_amount: int,
        income: int,
        obligations: int,
        tenure: int,
        band_idx: int,
    ):
        """
        Invariant 1 & 2:
        - Recommended amount never exceeds requested amount, capacity limit,
          income multiple limit, or product maximum.
        - Recommended amount is always an integer multiple of amount_step.
        """
        policy_res = load_params(PARAMS_PATH)
        params = policy_res.params
        band = policy_res.bands[band_idx]

        monthly_rate = calculate_monthly_rate(band["indicative_rate"])
        max_emi = calculate_max_affordable_emi(income, obligations, band["post_loan_foir_cap"])
        max_p = calculate_max_principal(max_emi, monthly_rate, tenure)

        rec = calculate_recommended_amount(
            requested_amount=requested_amount,
            max_principal_emi=max_p,
            monthly_net_income=income,
            amount_step=params["amount_step"],
            income_multiple_cap=params["income_multiple_cap"],
            max_amount=params["max_amount"],
        )

        amount = rec.recommended_amount
        step = params["amount_step"]

        # Multiple of amount_step
        assert amount % step == 0

        # Non-negative
        assert amount >= 0

        # Never exceeds requested amount
        assert amount <= requested_amount

        # Never exceeds capacity cap (P_EMI)
        assert Decimal(amount) <= max_p or amount == 0

        # Never exceeds income multiple cap
        assert amount <= params["income_multiple_cap"] * income

        # Never exceeds product maximum
        assert amount <= params["max_amount"]

    @seed(PROPERTY_SEED)
    @settings(max_examples=100)
    @given(
        income=st.integers(min_value=20000, max_value=500000),
        obligations=st.integers(min_value=0, max_value=10000),
        tenure=st.integers(min_value=12, max_value=60),
        band_idx=st.integers(min_value=0, max_value=2),
    )
    def test_property_emi_at_max_principal_matches_max_emi(
        self,
        income: int,
        obligations: int,
        tenure: int,
        band_idx: int,
    ):
        """
        Invariant 3:
        EMI computed on the unrounded maximum principal (P_EMI) is within
        one rupee of the maximum affordable EMI (max_emi).
        """
        policy_res = load_params(PARAMS_PATH)
        band = policy_res.bands[band_idx]

        monthly_rate = calculate_monthly_rate(band["indicative_rate"])
        max_emi = calculate_max_affordable_emi(income, obligations, band["post_loan_foir_cap"])
        if max_emi <= Decimal(0):
            return  # Skip when no capacity

        max_p = calculate_max_principal(max_emi, monthly_rate, tenure)
        emi_at_max_p = calculate_emi(max_p, monthly_rate, tenure)

        diff = abs(emi_at_max_p - max_emi)
        assert diff <= Decimal(1), (
            f"EMI diff {diff} exceeds 1 rupee: emi={emi_at_max_p}, max_emi={max_emi}"
        )

    @seed(PROPERTY_SEED)
    @settings(max_examples=100)
    @given(
        amount=st.integers(min_value=50000, max_value=1500000).filter(lambda x: x % 5000 == 0),
        tenure=st.integers(min_value=12, max_value=60),
        band_idx=st.integers(min_value=0, max_value=2),
    )
    def test_property_apr_at_least_band_rate_for_positive_fee(
        self,
        amount: int,
        tenure: int,
        band_idx: int,
    ):
        """
        Invariant 4:
        APR is at least the band's indicative rate whenever the processing fee is positive.
        """
        policy_res = load_params(PARAMS_PATH)
        params = policy_res.params
        band = policy_res.bands[band_idx]

        rate_pct = Decimal(str(band["indicative_rate"]))
        monthly_rate = calculate_monthly_rate(rate_pct)
        emi = calculate_emi(amount, monthly_rate, tenure)
        fee = calculate_fee(amount, params["processing_fee_rate"])
        net_disbursed = Decimal(amount) - fee

        # With positive fee, Net < amount, so IRR must be strictly higher than nominal interest rate
        apr = calculate_apr(net_disbursed, emi, tenure)

        # Allow 0.01 tolerance for bisection / rounding
        assert apr >= rate_pct - Decimal("0.01"), f"APR {apr} < band rate {rate_pct}"
