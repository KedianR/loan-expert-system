"""
Golden vector calculation tests (TV1 to TV9).

Implements: FR-03, FR-07, FR-08, FR-13, WP-04
Spec: docs/03-calculations.md section 3, docs/06-test-plan.md §4
Tests golden vectors against the calculation core pure functions.
All policy parameters are loaded from params/params.toml; none are hardcoded.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.calc.formulas import (
    calculate_apr,
    calculate_existing_foir,
    calculate_loan_costs,
    calculate_max_affordable_emi,
    calculate_max_principal,
    calculate_monthly_rate,
    calculate_post_loan_foir,
    calculate_recommended_amount,
    find_band,
    round_foir,
)
from src.engine.param_loader import load_params

REPO_ROOT = Path(__file__).resolve().parents[2]
VECTORS_PATH = REPO_ROOT / "tests" / "golden" / "vectors.json"
PARAMS_PATH = REPO_ROOT / "params" / "params.toml"


@pytest.fixture(scope="module")
def policy():
    """Load policy parameters and bands from params/params.toml."""
    res = load_params(PARAMS_PATH)
    assert res.ok, f"Failed to load params: {res.errors}"
    return res


@pytest.fixture(scope="module")
def golden_vectors():
    """Load golden test vectors TV1 to TV9."""
    text = VECTORS_PATH.read_text(encoding="utf-8")
    data = json.loads(text)
    return {v["id"]: v for v in data["vectors"]}


class TestGoldenVectorsCalculations:
    """Validate numerical expectations of TV1 to TV9."""

    def test_tv1_eligible_requested_binding(self, policy, golden_vectors):
        """TV1: Typical eligible case in band B; requested amount is binding."""
        tv = golden_vectors["TV1"]
        inp = tv["input"]
        exp = tv["expected"]
        offer = exp["offer"]

        # F1. Existing FOIR
        foir = calculate_existing_foir(inp["monthly_obligations"], inp["monthly_net_income"])
        assert round_foir(foir) == Decimal(exp["existing_foir"])

        # Band lookup
        band = find_band(inp["credit_score"], foir, policy.bands)
        assert band is not None
        assert band["id"] == exp["band"]

        # F2. Monthly rate
        monthly_rate = calculate_monthly_rate(band["indicative_rate"])

        # F4 & F5. Max affordable EMI and Max principal
        max_emi = calculate_max_affordable_emi(
            inp["monthly_net_income"], inp["monthly_obligations"], band["post_loan_foir_cap"]
        )
        max_p = calculate_max_principal(max_emi, monthly_rate, inp["requested_tenure_months"])

        # F6. Recommended amount
        rec = calculate_recommended_amount(
            inp["requested_amount"],
            max_p,
            inp["monthly_net_income"],
            policy.params["amount_step"],
            policy.params["income_multiple_cap"],
            policy.params["max_amount"],
        )
        assert rec.recommended_amount == offer["amount"]
        assert rec.binding_limit == exp["binding_limit"]

        # F7. Loan costs (EMI, fee, repayment, interest)
        costs = calculate_loan_costs(
            rec.recommended_amount,
            monthly_rate,
            offer["tenure_months"],
            policy.params["processing_fee_rate"],
        )
        assert costs.emi == Decimal(offer["emi"])
        assert costs.fee == Decimal(offer["fee"])
        assert costs.total_interest == Decimal(offer["total_interest"])

        # F8. Post-loan FOIR
        post_foir = calculate_post_loan_foir(
            inp["monthly_obligations"], costs.emi, inp["monthly_net_income"]
        )
        assert round_foir(post_foir) == Decimal(offer["post_loan_foir"])

        # F9. APR within 0.01 percentage points
        apr = calculate_apr(costs.net_disbursed, costs.emi, offer["tenure_months"])
        assert abs(apr - Decimal(offer["apr"])) <= Decimal("0.01")

    def test_tv2_boundary_capacity_binding(self, policy, golden_vectors):
        """TV2: Band A boundary (FOIR exactly 0.30), limited by repayment capacity."""
        tv = golden_vectors["TV2"]
        inp = tv["input"]
        exp = tv["expected"]
        offer = exp["offer"]

        foir = calculate_existing_foir(inp["monthly_obligations"], inp["monthly_net_income"])
        assert foir == Decimal("0.3")
        assert round_foir(foir) == Decimal(exp["existing_foir"])

        band = find_band(inp["credit_score"], foir, policy.bands)
        assert band is not None
        assert band["id"] == "A"

        monthly_rate = calculate_monthly_rate(band["indicative_rate"])
        max_emi = calculate_max_affordable_emi(
            inp["monthly_net_income"], inp["monthly_obligations"], band["post_loan_foir_cap"]
        )
        max_p = calculate_max_principal(max_emi, monthly_rate, inp["requested_tenure_months"])
        # P_EMI is approx 379739.59
        assert abs(max_p - Decimal("379739.59")) < Decimal("0.01")

        rec = calculate_recommended_amount(
            inp["requested_amount"],
            max_p,
            inp["monthly_net_income"],
            policy.params["amount_step"],
            policy.params["income_multiple_cap"],
            policy.params["max_amount"],
        )
        assert rec.recommended_amount == offer["amount"]
        assert rec.binding_limit == "capacity"

        costs = calculate_loan_costs(
            rec.recommended_amount,
            monthly_rate,
            offer["tenure_months"],
            policy.params["processing_fee_rate"],
        )
        assert costs.emi == Decimal(offer["emi"])
        assert costs.fee == Decimal(offer["fee"])
        assert costs.total_interest == Decimal(offer["total_interest"])

        post_foir = calculate_post_loan_foir(
            inp["monthly_obligations"], costs.emi, inp["monthly_net_income"]
        )
        assert round_foir(post_foir) == Decimal(offer["post_loan_foir"])

        apr = calculate_apr(costs.net_disbursed, costs.emi, offer["tenure_months"])
        assert abs(apr - Decimal(offer["apr"])) <= Decimal("0.01")

    def test_tv3_income_multiple_binding_zero_obligations(self, policy, golden_vectors):
        """TV3: Zero obligations, income multiple cap is binding."""
        tv = golden_vectors["TV3"]
        inp = tv["input"]
        exp = tv["expected"]
        offer = exp["offer"]

        foir = calculate_existing_foir(inp["monthly_obligations"], inp["monthly_net_income"])
        assert foir == Decimal(0)
        assert round_foir(foir) == Decimal(exp["existing_foir"])

        band = find_band(inp["credit_score"], foir, policy.bands)
        assert band is not None
        assert band["id"] == "B"

        monthly_rate = calculate_monthly_rate(band["indicative_rate"])
        max_emi = calculate_max_affordable_emi(
            inp["monthly_net_income"], inp["monthly_obligations"], band["post_loan_foir_cap"]
        )
        max_p = calculate_max_principal(max_emi, monthly_rate, inp["requested_tenure_months"])

        rec = calculate_recommended_amount(
            inp["requested_amount"],
            max_p,
            inp["monthly_net_income"],
            policy.params["amount_step"],
            policy.params["income_multiple_cap"],
            policy.params["max_amount"],
        )
        assert rec.recommended_amount == offer["amount"]
        assert rec.binding_limit == "income_multiple"

        costs = calculate_loan_costs(
            rec.recommended_amount,
            monthly_rate,
            offer["tenure_months"],
            policy.params["processing_fee_rate"],
        )
        assert costs.emi == Decimal(offer["emi"])
        assert costs.fee == Decimal(offer["fee"])
        assert costs.total_interest == Decimal(offer["total_interest"])

        post_foir = calculate_post_loan_foir(
            inp["monthly_obligations"], costs.emi, inp["monthly_net_income"]
        )
        assert round_foir(post_foir) == Decimal(offer["post_loan_foir"])

        apr = calculate_apr(costs.net_disbursed, costs.emi, offer["tenure_months"])
        assert abs(apr - Decimal(offer["apr"])) <= Decimal("0.01")

    def test_tv4_boundary_credit_score_700(self, policy, golden_vectors):
        """TV4: Credit score exactly 700 qualifies for Band B."""
        tv = golden_vectors["TV4"]
        inp = tv["input"]
        exp = tv["expected"]
        offer = exp["offer"]

        foir = calculate_existing_foir(inp["monthly_obligations"], inp["monthly_net_income"])
        assert round_foir(foir) == Decimal(exp["existing_foir"])

        band = find_band(inp["credit_score"], foir, policy.bands)
        assert band is not None
        assert band["id"] == "B"

        monthly_rate = calculate_monthly_rate(band["indicative_rate"])
        max_emi = calculate_max_affordable_emi(
            inp["monthly_net_income"], inp["monthly_obligations"], band["post_loan_foir_cap"]
        )
        max_p = calculate_max_principal(max_emi, monthly_rate, inp["requested_tenure_months"])

        rec = calculate_recommended_amount(
            inp["requested_amount"],
            max_p,
            inp["monthly_net_income"],
            policy.params["amount_step"],
            policy.params["income_multiple_cap"],
            policy.params["max_amount"],
        )
        assert rec.recommended_amount == offer["amount"]
        assert rec.binding_limit == "requested"

        costs = calculate_loan_costs(
            rec.recommended_amount,
            monthly_rate,
            offer["tenure_months"],
            policy.params["processing_fee_rate"],
        )
        assert costs.emi == Decimal(offer["emi"])
        assert costs.fee == Decimal(offer["fee"])
        assert costs.total_interest == Decimal(offer["total_interest"])

        post_foir = calculate_post_loan_foir(
            inp["monthly_obligations"], costs.emi, inp["monthly_net_income"]
        )
        assert round_foir(post_foir) == Decimal(offer["post_loan_foir"])

        apr = calculate_apr(costs.net_disbursed, costs.emi, offer["tenure_months"])
        assert abs(apr - Decimal(offer["apr"])) <= Decimal("0.01")

    def test_tv5_boundary_score_750_and_foir_030(self, policy, golden_vectors):
        """TV5: Exact score 750 and FOIR 0.30 qualify for Band A."""
        tv = golden_vectors["TV5"]
        inp = tv["input"]
        exp = tv["expected"]
        offer = exp["offer"]

        foir = calculate_existing_foir(inp["monthly_obligations"], inp["monthly_net_income"])
        assert foir == Decimal("0.3")
        assert round_foir(foir) == Decimal(exp["existing_foir"])

        band = find_band(inp["credit_score"], foir, policy.bands)
        assert band is not None
        assert band["id"] == "A"

        monthly_rate = calculate_monthly_rate(band["indicative_rate"])
        max_emi = calculate_max_affordable_emi(
            inp["monthly_net_income"], inp["monthly_obligations"], band["post_loan_foir_cap"]
        )
        max_p = calculate_max_principal(max_emi, monthly_rate, inp["requested_tenure_months"])

        rec = calculate_recommended_amount(
            inp["requested_amount"],
            max_p,
            inp["monthly_net_income"],
            policy.params["amount_step"],
            policy.params["income_multiple_cap"],
            policy.params["max_amount"],
        )
        assert rec.recommended_amount == offer["amount"]
        assert rec.binding_limit == "requested"

        costs = calculate_loan_costs(
            rec.recommended_amount,
            monthly_rate,
            offer["tenure_months"],
            policy.params["processing_fee_rate"],
        )
        assert costs.emi == Decimal(offer["emi"])
        assert costs.fee == Decimal(offer["fee"])
        assert costs.total_interest == Decimal(offer["total_interest"])

        post_foir = calculate_post_loan_foir(
            inp["monthly_obligations"], costs.emi, inp["monthly_net_income"]
        )
        assert round_foir(post_foir) == Decimal(offer["post_loan_foir"])

        apr = calculate_apr(costs.net_disbursed, costs.emi, offer["tenure_months"])
        assert abs(apr - Decimal(offer["apr"])) <= Decimal("0.01")

    def test_tv6_boundary_foir_050_negative_max_emi(self, policy, golden_vectors):
        """TV6: FOIR exactly 0.50 qualifies for Band C, but max EMI is negative (-5,000)."""
        tv = golden_vectors["TV6"]
        inp = tv["input"]
        exp = tv["expected"]

        foir = calculate_existing_foir(inp["monthly_obligations"], inp["monthly_net_income"])
        assert foir == Decimal("0.5")
        assert round_foir(foir) == Decimal(exp["existing_foir"])

        band = find_band(inp["credit_score"], foir, policy.bands)
        assert band is not None
        assert band["id"] == "C"

        monthly_rate = calculate_monthly_rate(band["indicative_rate"])
        max_emi = calculate_max_affordable_emi(
            inp["monthly_net_income"], inp["monthly_obligations"], band["post_loan_foir_cap"]
        )
        # Cap is 0.45 * 100,000 - 50,000 = -5,000
        assert max_emi == Decimal(-5000)

        # Max principal supported by negative EMI is zero
        max_p = calculate_max_principal(max_emi, monthly_rate, inp["requested_tenure_months"])
        assert max_p == Decimal(0)

        rec = calculate_recommended_amount(
            inp["requested_amount"],
            max_p,
            inp["monthly_net_income"],
            policy.params["amount_step"],
            policy.params["income_multiple_cap"],
            policy.params["max_amount"],
        )
        assert rec.recommended_amount == 0
        assert rec.binding_limit == "capacity"

    def test_tv7_boundary_foir_above_050_unrounded(self, policy, golden_vectors):
        """TV7: FOIR is 0.50001 (above 0.50); no band assigned."""
        tv = golden_vectors["TV7"]
        inp = tv["input"]
        exp = tv["expected"]

        foir = calculate_existing_foir(inp["monthly_obligations"], inp["monthly_net_income"])
        # Unrounded value is strictly greater than 0.50
        assert foir == Decimal("50001") / Decimal("100000")
        assert foir > Decimal("0.50")
        assert round_foir(foir) == Decimal(exp["existing_foir"])

        # No band should match because max_foir on band C is 0.50
        band = find_band(inp["credit_score"], foir, policy.bands)
        assert band is None

    def test_tv8_repayment_capacity_below_minimum(self, policy, golden_vectors):
        """TV8: Band C with small spare EMI (250); recommended amount floors to 0."""
        tv = golden_vectors["TV8"]
        inp = tv["input"]
        exp = tv["expected"]

        foir = calculate_existing_foir(inp["monthly_obligations"], inp["monthly_net_income"])
        assert round_foir(foir) == Decimal(exp["existing_foir"])

        band = find_band(inp["credit_score"], foir, policy.bands)
        assert band is not None
        assert band["id"] == "C"

        monthly_rate = calculate_monthly_rate(band["indicative_rate"])
        max_emi = calculate_max_affordable_emi(
            inp["monthly_net_income"], inp["monthly_obligations"], band["post_loan_foir_cap"]
        )
        assert max_emi == Decimal(250)

        max_p = calculate_max_principal(max_emi, monthly_rate, inp["requested_tenure_months"])
        assert abs(max_p - Decimal("2726.88")) < Decimal("0.01")

        rec = calculate_recommended_amount(
            inp["requested_amount"],
            max_p,
            inp["monthly_net_income"],
            policy.params["amount_step"],
            policy.params["income_multiple_cap"],
            policy.params["max_amount"],
        )
        # 2726.88 floored to 5,000 step is 0 (below min_amount of 50,000)
        assert rec.recommended_amount == 0
        assert rec.binding_limit == "capacity"

    def test_tv9_typical_band_c_offer(self, policy, golden_vectors):
        """TV9: Typical eligible case in Band C."""
        tv = golden_vectors["TV9"]
        inp = tv["input"]
        exp = tv["expected"]
        offer = exp["offer"]

        foir = calculate_existing_foir(inp["monthly_obligations"], inp["monthly_net_income"])
        assert round_foir(foir) == Decimal(exp["existing_foir"])

        band = find_band(inp["credit_score"], foir, policy.bands)
        assert band is not None
        assert band["id"] == "C"

        monthly_rate = calculate_monthly_rate(band["indicative_rate"])
        max_emi = calculate_max_affordable_emi(
            inp["monthly_net_income"], inp["monthly_obligations"], band["post_loan_foir_cap"]
        )
        max_p = calculate_max_principal(max_emi, monthly_rate, inp["requested_tenure_months"])

        rec = calculate_recommended_amount(
            inp["requested_amount"],
            max_p,
            inp["monthly_net_income"],
            policy.params["amount_step"],
            policy.params["income_multiple_cap"],
            policy.params["max_amount"],
        )
        assert rec.recommended_amount == offer["amount"]
        assert rec.binding_limit == "requested"

        costs = calculate_loan_costs(
            rec.recommended_amount,
            monthly_rate,
            offer["tenure_months"],
            policy.params["processing_fee_rate"],
        )
        assert costs.emi == Decimal(offer["emi"])
        assert costs.fee == Decimal(offer["fee"])
        assert costs.total_interest == Decimal(offer["total_interest"])

        post_foir = calculate_post_loan_foir(
            inp["monthly_obligations"], costs.emi, inp["monthly_net_income"]
        )
        assert round_foir(post_foir) == Decimal(offer["post_loan_foir"])

        apr = calculate_apr(costs.net_disbursed, costs.emi, offer["tenure_months"])
        assert abs(apr - Decimal(offer["apr"])) <= Decimal("0.01")
