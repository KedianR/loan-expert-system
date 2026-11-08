"""
Unit tests for calculation core formulas F1 to F9.

Implements: FR-03, FR-07, FR-08, FR-13, WP-04
Spec: docs/03-calculations.md
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.calc.formulas import (
    APRConvergenceError,
    calculate_apr,
    calculate_emi,
    calculate_existing_foir,
    calculate_fee,
    calculate_loan_costs,
    calculate_max_affordable_emi,
    calculate_max_principal,
    calculate_monthly_rate,
    calculate_post_loan_foir,
    calculate_recommended_amount,
    calculate_total_interest,
    calculate_total_repayment,
    find_band,
)
from src.calc.registry import get_calc_info, is_valid_calc_id


class TestCalcUnitFormulas:
    """Unit tests for individual formulas and edge cases."""

    def test_f1_existing_foir_zero_division(self):
        """Zero or negative income raises ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            calculate_existing_foir(10000, 0)
        with pytest.raises(ZeroDivisionError):
            calculate_existing_foir(10000, -100)

    def test_f2_monthly_rate(self):
        """Monthly rate is annual / 1200."""
        r = calculate_monthly_rate("12.0")
        assert r == Decimal("0.01")
        r_zero = calculate_monthly_rate(0)
        assert r_zero == Decimal(0)

    def test_f3_emi_guard_r_zero(self):
        """When r = 0, EMI is principal / n."""
        emi = calculate_emi(120000, Decimal(0), 12)
        assert emi == Decimal("10000.00")
        assert calculate_emi(0, Decimal(0), 12) == Decimal("0.00")

    def test_f3_emi_invalid_tenure(self):
        """Tenure <= 0 raises ValueError."""
        with pytest.raises(ValueError):
            calculate_emi(100000, Decimal("0.01"), 0)

    def test_f5_max_principal_invalid_tenure(self):
        """Tenure <= 0 raises ValueError."""
        with pytest.raises(ValueError):
            calculate_max_principal(Decimal(1000), Decimal("0.01"), 0)

    def test_f4_max_affordable_emi_negative(self):
        """Negative EMI_max when obligations exceed cap * income."""
        max_emi = calculate_max_affordable_emi(100000, 60000, "0.50")
        assert max_emi == Decimal(-10000)

    def test_f5_max_principal_guard_r_zero(self):
        """When r = 0, P_EMI = max_emi * n."""
        p_emi = calculate_max_principal(Decimal(5000), Decimal(0), 12)
        assert p_emi == Decimal(60000)

    def test_f5_max_principal_negative_emi(self):
        """When max_emi <= 0, max principal is 0."""
        p_emi = calculate_max_principal(Decimal(-500), Decimal("0.01"), 12)
        assert p_emi == Decimal(0)

    def test_f6_cap_tie_order(self):
        """
        Tie order: capacity first, then income multiple, then product maximum.
        """
        # Capacity and income multiple tie at 400,000, below requested 500,000
        res = calculate_recommended_amount(
            requested_amount=500000,
            max_principal_emi=Decimal(400000),
            monthly_net_income=40000,  # 10 * 40,000 = 400,000
            amount_step=5000,
            income_multiple_cap=10,
            max_amount=2500000,
        )
        assert res.recommended_amount == 400000
        assert res.binding_limit == "capacity"

        # Income multiple and product max tie at 500,000, capacity is higher
        res2 = calculate_recommended_amount(
            requested_amount=600000,
            max_principal_emi=Decimal(800000),
            monthly_net_income=50000,  # 10 * 50,000 = 500,000
            amount_step=5000,
            income_multiple_cap=10,
            max_amount=500000,
        )
        assert res2.recommended_amount == 500000
        assert res2.binding_limit == "income_multiple"

    def test_f7_loan_costs_and_helpers(self):
        """F7 fee, repayment, total interest calculation."""
        fee = calculate_fee(100000, "0.02")
        assert fee == Decimal("2000.00")
        repay = calculate_total_repayment(Decimal("9000.00"), 12)
        assert repay == Decimal("108000.00")
        interest = calculate_total_interest(repay, 100000)
        assert interest == Decimal("8000.00")

        costs = calculate_loan_costs(100000, Decimal("0.01"), 12, "0.02")
        assert costs.fee == Decimal("2000.00")
        assert costs.net_disbursed == Decimal("98000.00")

    def test_f8_post_loan_foir_zero_division(self):
        """Zero income raises ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            calculate_post_loan_foir(1000, Decimal(500), 0)

    def test_f9_apr_invalid_inputs(self):
        """Invalid inputs to APR solver raise ValueError."""
        with pytest.raises(ValueError):
            calculate_apr(Decimal(0), Decimal(1000), 12)
        with pytest.raises(ValueError):
            calculate_apr(Decimal(10000), Decimal(0), 12)
        with pytest.raises(ValueError):
            calculate_apr(Decimal(10000), Decimal(1000), 0)

    def test_f9_apr_zero_interest(self):
        """When net equals total repayment, APR is 0.00."""
        apr = calculate_apr(Decimal(12000), Decimal(1000), 12)
        assert apr == Decimal("0.00")

    def test_f9_apr_convergence_error(self):
        """Unbracketable rates raise APRConvergenceError."""
        with pytest.raises(APRConvergenceError):
            # Net is vastly larger than repayment -> negative rate bracketing fails
            calculate_apr(Decimal(1000000), Decimal(10), 12, max_iterations=5)

    def test_band_lookup_none_score(self):
        """Score of None returns None band."""
        assert find_band(None, Decimal("0.20"), []) is None

    def test_calc_registry_lookups(self):
        """Calculation registry checks."""
        assert is_valid_calc_id("F1")
        assert is_valid_calc_id("F9")
        assert not is_valid_calc_id("F99")
        info = get_calc_info("F6")
        assert info is not None
        assert info["computes"] == ["recommended_amount", "binding_limit"]
