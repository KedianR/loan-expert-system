"""
Calculation core: pure functions implementing formulas F1 to F9.

Implements: FR-03, FR-07, FR-08, FR-13, WP-04
Spec: docs/03-calculations.md sections 1, 2, 4
AGENTS.md: Hard rules 1 (no policy numbers in code) and 2 (exact Decimal arithmetic, no floats).

Conventions:
- Money and ratios use exact decimals (Decimal) or ints. Never floats.
- Monthly rate r = annual_rate_pct / 1200.
- Guard r = 0: when r is zero, EMI is P / n.
- Rounding: EMI and fees round half up to 2 decimal places.
- Recommended amount floors to amount_step.
- APR solver raises APRConvergenceError if bisection does not converge.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal
from typing import Any

# Rounding quantizers
_TWO_PLACES = Decimal("0.01")
_FOUR_PLACES = Decimal("0.0001")


class APRConvergenceError(Exception):
    """Raised when the numerical APR bisection solver fails to converge."""


@dataclass(frozen=True)
class RecommendedAmountResult:
    """Result of Formula F6 (recommended amount and binding limit)."""

    recommended_amount: int
    binding_limit: str  # "requested" | "capacity" | "income_multiple" | "product_maximum"
    cap_capacity: Decimal
    cap_income_multiple: Decimal
    cap_product_max: Decimal


@dataclass(frozen=True)
class LoanCostResult:
    """Result of Formula F7 (fee, repayment, total interest)."""

    recommended_amount: int
    fee: Decimal
    net_disbursed: Decimal
    emi: Decimal
    total_repayment: Decimal
    total_interest: Decimal


def calculate_existing_foir(
    monthly_obligations: int | Decimal,
    monthly_net_income: int | Decimal,
) -> Decimal:
    """
    Formula F1: Existing FOIR = O / I.

    Kept unrounded in comparisons.
    Raises ZeroDivisionError if income is zero or negative.
    """
    income = Decimal(monthly_net_income)
    if income <= Decimal(0):
        raise ZeroDivisionError("Monthly net income must be greater than zero to compute FOIR")
    return Decimal(monthly_obligations) / income


def calculate_monthly_rate(annual_rate_pct: Decimal | str | int) -> Decimal:
    """
    Formula F2: Monthly rate r = annual_rate_pct / 1200.

    1200 = 12 months * 100 percent.
    """
    return Decimal(str(annual_rate_pct)) / Decimal(1200)


def calculate_emi(
    principal: int | Decimal,
    monthly_rate: Decimal,
    tenure_months: int,
) -> Decimal:
    """
    Formula F3: EMI for principal P at monthly rate r over tenure n.

    EMI(P) = P * (r * (1+r)^n) / ((1+r)^n - 1)
    Guard r = 0: if r is zero, EMI is P / n.
    Round half up to 2 decimal places.
    """
    p = Decimal(principal)
    n = tenure_months
    if n <= 0:
        raise ValueError(f"Tenure must be positive, got {n}")

    if p <= Decimal(0):
        return Decimal("0.00")

    if monthly_rate == Decimal(0):
        emi = p / Decimal(n)
        return emi.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

    r = monthly_rate
    factor = (Decimal(1) + r) ** n
    emi = p * (r * factor) / (factor - Decimal(1))
    return emi.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_max_affordable_emi(
    monthly_net_income: int | Decimal,
    monthly_obligations: int | Decimal,
    post_loan_foir_cap: Decimal | str,
) -> Decimal:
    """
    Formula F4: Maximum affordable EMI = cap_band * I - O.

    If EMI_max is zero or negative, maximum principal is zero.
    """
    cap = Decimal(str(post_loan_foir_cap))
    income = Decimal(monthly_net_income)
    obligations = Decimal(monthly_obligations)
    return cap * income - obligations


def calculate_max_principal(
    max_emi: Decimal,
    monthly_rate: Decimal,
    tenure_months: int,
) -> Decimal:
    """
    Formula F5: Maximum principal supported by that EMI.

    P_EMI = EMI_max * ((1+r)^n - 1) / (r * (1+r)^n)
    If max_emi <= 0: return 0.
    Guard r = 0: if r is zero, P_EMI = max_emi * n.
    """
    if max_emi <= Decimal(0):
        return Decimal(0)

    n = tenure_months
    if n <= 0:
        raise ValueError(f"Tenure must be positive, got {n}")

    if monthly_rate == Decimal(0):
        return max_emi * Decimal(n)

    r = monthly_rate
    factor = (Decimal(1) + r) ** n
    p_emi = max_emi * (factor - Decimal(1)) / (r * factor)
    return p_emi


def calculate_recommended_amount(
    requested_amount: int | Decimal,
    max_principal_emi: Decimal,
    monthly_net_income: int | Decimal,
    amount_step: int,
    income_multiple_cap: int,
    max_amount: int,
) -> RecommendedAmountResult:
    """
    Formula F6: Recommended amount and binding limit.

    P* = amount_step * floor(min(R, P_EMI, income_multiple_cap * I, max_amount) / amount_step)

    The three caps are:
      - capacity: P_EMI
      - income_multiple: income_multiple_cap * I
      - product_maximum: max_amount

    If P* is below R, the binding limit is the smallest of the three caps.
    Tie order: capacity first, then income multiple, then product maximum.
    If requested amount is <= all caps, binding limit is 'requested'.
    """
    r_amount = Decimal(requested_amount)
    cap_capacity = max_principal_emi if max_principal_emi > Decimal(0) else Decimal(0)
    cap_income = Decimal(income_multiple_cap) * Decimal(monthly_net_income)
    cap_product = Decimal(max_amount)
    step = Decimal(amount_step)

    # Determine smallest of the three caps with tie order:
    # capacity first, then income multiple, then product maximum
    if cap_capacity <= cap_income and cap_capacity <= cap_product:
        smallest_cap_name = "capacity"
        smallest_cap_val = cap_capacity
    elif cap_income <= cap_product:
        smallest_cap_name = "income_multiple"
        smallest_cap_val = cap_income
    else:
        smallest_cap_name = "product_maximum"
        smallest_cap_val = cap_product

    # The effective ceiling before flooring
    effective_limit = min(r_amount, cap_capacity, cap_income, cap_product)

    if effective_limit <= Decimal(0):
        rec_amount = 0
    else:
        rec_amount = int((effective_limit / step).quantize(Decimal(1), rounding=ROUND_FLOOR)) * int(
            step
        )

    # Binding limit determination:
    # If request is less than or equal to all three caps, the request was the binding factor.
    if r_amount <= smallest_cap_val:
        binding_limit = "requested"
    else:
        binding_limit = smallest_cap_name

    return RecommendedAmountResult(
        recommended_amount=rec_amount,
        binding_limit=binding_limit,
        cap_capacity=cap_capacity,
        cap_income_multiple=cap_income,
        cap_product_max=cap_product,
    )


def calculate_fee(
    recommended_amount: int | Decimal,
    processing_fee_rate: Decimal | str,
) -> Decimal:
    """
    Formula F7: Processing fee = processing_fee_rate * P*.

    Rounded half up to 2 decimal places.
    """
    rate = Decimal(str(processing_fee_rate))
    fee = Decimal(recommended_amount) * rate
    return fee.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_total_repayment(emi: Decimal, tenure_months: int) -> Decimal:
    """
    Formula F7: Total repayment = n * EMI(P*).
    """
    total = Decimal(tenure_months) * Decimal(emi)
    return total.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_total_interest(
    total_repayment: Decimal,
    recommended_amount: int | Decimal,
) -> Decimal:
    """
    Formula F7: Total interest = total_repayment - P*.
    """
    return total_repayment - Decimal(recommended_amount)


def calculate_loan_costs(
    recommended_amount: int,
    monthly_rate: Decimal,
    tenure_months: int,
    processing_fee_rate: Decimal | str,
) -> LoanCostResult:
    """
    Compute all formula F7 values given a recommended amount and band rate.
    """
    emi = calculate_emi(recommended_amount, monthly_rate, tenure_months)
    fee = calculate_fee(recommended_amount, processing_fee_rate)
    net = Decimal(recommended_amount) - fee
    repayment = calculate_total_repayment(emi, tenure_months)
    interest = calculate_total_interest(repayment, recommended_amount)

    return LoanCostResult(
        recommended_amount=recommended_amount,
        fee=fee,
        net_disbursed=net,
        emi=emi,
        total_repayment=repayment,
        total_interest=interest,
    )


def calculate_post_loan_foir(
    monthly_obligations: int | Decimal,
    emi: Decimal,
    monthly_net_income: int | Decimal,
) -> Decimal:
    """
    Formula F8: Post-loan FOIR = (O + EMI(P*)) / I.

    Kept unrounded in comparisons, formatted to 4 decimals in output.
    Raises ZeroDivisionError if income is zero or negative.
    """
    income = Decimal(monthly_net_income)
    if income <= Decimal(0):
        raise ZeroDivisionError("Monthly net income must be greater than zero to compute FOIR")
    obligations = Decimal(monthly_obligations)
    return (obligations + Decimal(emi)) / income


def round_foir(foir: Decimal) -> Decimal:
    """Format FOIR to 4 decimal places with half-up rounding."""
    return foir.quantize(_FOUR_PLACES, rounding=ROUND_HALF_UP)


def calculate_apr(
    net_disbursed: Decimal,
    emi: Decimal,
    tenure_months: int,
    max_iterations: int = 200,
    tolerance: Decimal = Decimal("1e-9"),
) -> Decimal:
    """
    Formula F9: APR (annualised internal rate of return including the fee).

    Net = sum_{t=1}^n EMI / (1+i)^t
    APR = 12 * i * 100%

    Solved for monthly rate i by bisection.
    Raises APRConvergenceError if the solver fails to converge.
    Returns APR in percent rounded half up to 2 decimal places.
    """
    net = Decimal(net_disbursed)
    c = Decimal(emi)
    n = tenure_months

    if net <= Decimal(0) or c <= Decimal(0) or n <= 0:
        raise ValueError(f"Invalid parameters for APR: net={net}, emi={c}, tenure={n}")

    # If net equals total payments exactly, rate is 0
    if net == Decimal(n) * c:
        return Decimal("0.00")

    def pv(rate: Decimal) -> Decimal:
        # PV = sum_{t=1}^n c / (1+rate)^t
        total = Decimal(0)
        base = Decimal(1) + rate
        current_pow = base
        for _ in range(1, n + 1):
            total += c / current_pow
            current_pow *= base
        return total

    # Root finding for f(i) = pv(i) - net = 0
    # At i = 0, pv(0) = n * c > net, so f(0) > 0.
    low = Decimal(0)
    high = Decimal(1)  # 100% monthly rate

    # Ensure f(high) < 0
    for _ in range(20):
        if pv(high) < net:
            break
        high *= Decimal(2)
    else:
        raise APRConvergenceError(
            f"APR solver could not bracket the rate: pv({high}) >= net ({net})"
        )

    converged = False
    mid = low
    for _ in range(max_iterations):
        mid = (low + high) / Decimal(2)
        val = pv(mid)
        diff = val - net
        if abs(diff) < tolerance or (high - low) < tolerance:
            converged = True
            break
        if diff > Decimal(0):
            low = mid
        else:
            high = mid

    if not converged:
        raise APRConvergenceError(f"APR solver did not converge after {max_iterations} iterations")

    apr = (mid * Decimal(12) * Decimal(100)).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    return apr


def find_band(
    credit_score: int | None,
    existing_foir: Decimal,
    bands: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Assign pricing band A, B or C using the band table.

    Order in table is order tried (best first). First match wins.
    If credit_score is None, or no band matches, returns None.
    """
    if credit_score is None:
        return None

    for b in bands:
        min_score = b["min_score"]
        max_foir = Decimal(str(b["max_foir"]))
        if credit_score >= min_score and existing_foir <= max_foir:
            return b

    return None
