"""
Calculation registry mapping calculation IDs to formula specifications.

Implements: WP-04, AGENTS.md Layout, docs/09-file-formats.md §4
"""

from __future__ import annotations

from typing import Any

CALCULATION_REGISTRY: dict[str, dict[str, Any]] = {
    "F1": {
        "id": "F1",
        "name": "existing_foir",
        "description": "Existing FOIR: obligations divided by monthly net income",
        "formula": "FOIR_existing = O / I",
        "computes": ["existing_foir"],
    },
    "F2": {
        "id": "F2",
        "name": "monthly_rate",
        "description": "Monthly rate from annual percentage",
        "formula": "r = annual_rate / 1200",
        "computes": ["monthly_rate"],
    },
    "F3": {
        "id": "F3",
        "name": "emi",
        "description": "Equated Monthly Instalment for principal P",
        "formula": "EMI(P) = P * (r * (1+r)^n) / ((1+r)^n - 1)",
        "computes": ["emi"],
    },
    "F4": {
        "id": "F4",
        "name": "max_emi",
        "description": "Maximum affordable EMI under band cap",
        "formula": "EMI_max = cap_band * I - O",
        "computes": ["max_emi"],
    },
    "F5": {
        "id": "F5",
        "name": "max_principal_emi",
        "description": "Maximum principal supported by max affordable EMI",
        "formula": "P_EMI = EMI_max * ((1+r)^n - 1) / (r * (1+r)^n)",
        "computes": ["max_principal_emi"],
    },
    "F6": {
        "id": "F6",
        "name": "recommended_amount",
        "description": "Recommended loan amount and binding limit",
        "formula": "P* = amount_step * floor(min(R, P_EMI, income_multiple_cap * I, max_amount) / amount_step)",
        "computes": ["recommended_amount", "binding_limit"],
    },
    "F7": {
        "id": "F7",
        "name": "fee_and_interest",
        "description": "Processing fee, net disbursed amount, and total interest",
        "formula": "Fee = processing_fee_rate * P*, Net = P* - Fee, Total Repayment = n * EMI",
        "computes": ["fee", "net_disbursed", "total_repayment", "total_interest"],
    },
    "F8": {
        "id": "F8",
        "name": "post_loan_foir",
        "description": "Post-loan FOIR after adding new loan EMI",
        "formula": "FOIR_post = (O + EMI(P*)) / I",
        "computes": ["post_loan_foir"],
    },
    "F9": {
        "id": "F9",
        "name": "apr",
        "description": "Annualised internal rate of return including fee",
        "formula": "Net = sum(EMI / (1+i)^t), APR = 12 * i * 100%",
        "computes": ["apr"],
    },
    "band_lookup": {
        "id": "band_lookup",
        "name": "band_lookup",
        "description": "Assign band A, B or C using band table",
        "formula": "First band where score >= min_score and existing_foir <= max_foir",
        "computes": ["band"],
    },
    "rate_lookup": {
        "id": "rate_lookup",
        "name": "rate_lookup",
        "description": "Indicative rate and rate range from assigned band",
        "formula": "Midpoint indicative rate of band",
        "computes": ["indicative_rate"],
    },
}


def is_valid_calc_id(calc_id: str) -> bool:
    """Check whether a calc ID is known in the registry."""
    return calc_id in CALCULATION_REGISTRY


def get_calc_info(calc_id: str) -> dict[str, Any] | None:
    """Retrieve metadata for a calculation ID."""
    return CALCULATION_REGISTRY.get(calc_id)
