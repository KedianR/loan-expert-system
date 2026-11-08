"""
Calculation core package.

Formulas F1 to F9 and calculation registry.
Exact Decimal arithmetic; no floats permitted.
"""

from src.calc.formulas import (
    APRConvergenceError,
    LoanCostResult,
    RecommendedAmountResult,
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
    round_foir,
)
from src.calc.registry import CALCULATION_REGISTRY, get_calc_info, is_valid_calc_id

__all__ = [
    "APRConvergenceError",
    "CALCULATION_REGISTRY",
    "LoanCostResult",
    "RecommendedAmountResult",
    "calculate_apr",
    "calculate_emi",
    "calculate_existing_foir",
    "calculate_fee",
    "calculate_loan_costs",
    "calculate_max_affordable_emi",
    "calculate_max_principal",
    "calculate_monthly_rate",
    "calculate_post_loan_foir",
    "calculate_recommended_amount",
    "calculate_total_interest",
    "calculate_total_repayment",
    "find_band",
    "get_calc_info",
    "is_valid_calc_id",
    "round_foir",
]
