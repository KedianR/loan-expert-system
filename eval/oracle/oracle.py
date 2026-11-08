"""Reference Oracle implementation of the personal loan credit policy.

An independent, standalone evaluator written in plain Python with exact Decimal
arithmetic. Evaluates an application against the credit policy parameters without
using any rule engine, Prolog, or condition DSL.
"""

from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Any, Dict, List, Optional, Tuple

# Set global decimal precision high enough for exact calculation
getcontext().prec = 50

# Required fields per docs/04-predicates-and-facts.md section 2
REQUIRED_FIELDS = (
    "age",
    "employment_type",
    "employment_months",
    "monthly_net_income",
    "monthly_obligations",
    "enquiries_6m",
    "severe_delinquency_36m",
    "written_off",
    "kyc_verified",
    "consent_given",
    "requested_amount",
    "requested_tenure_months",
)


def _solve_apr(p_star: int, fee: Decimal, emi: Decimal, n: int) -> Decimal:
    """Solve for APR using bisection method per Formula F9."""
    net = Decimal(p_star) - fee
    low = Decimal("0.0000000001")
    high = Decimal("1.0")  # 1200% annual
    for _ in range(100):
        mid = (low + high) / Decimal(2)
        # Present value of n payments of emi discounted at monthly rate mid
        # PV = emi * (1 - (1 + mid)^(-n)) / mid
        pv = emi * (Decimal(1) - (Decimal(1) + mid) ** (-n)) / mid
        if pv > net:
            low = mid
        else:
            high = mid
    # APR = 12 * i * 100% = 1200 * i
    return (low * Decimal(1200)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def evaluate(application: dict, params: dict) -> dict:
    """Evaluate a loan application against credit policy parameters.

    Args:
        application: Dictionary with input facts matching docs/04 schema.
        params: Dictionary loaded from params/params.toml.

    Returns:
        Dictionary with decision, reason_codes, fired_rules, band,
        recommended_amount, binding_limit, indicative_rate, emi, fee,
        total_interest, apr, post_loan_foir, and offer details.
    """
    prod_params = params["product"]
    elig_params = params["eligibility"]
    exp_params = params.get("experimental", {})
    bands = params.get("band", [])

    min_amount = prod_params["min_amount"]
    max_amount = prod_params["max_amount"]
    amount_step = prod_params["amount_step"]
    min_tenure = prod_params["min_tenure_months"]
    max_tenure = prod_params["max_tenure_months"]
    processing_fee_rate = Decimal(str(prod_params["processing_fee_rate"]))
    income_multiple_cap = prod_params["income_multiple_cap"]

    min_age = elig_params["min_age"]
    min_monthly_income = elig_params["min_monthly_income"]
    min_credit_score = elig_params["min_credit_score"]
    min_emp_salaried = elig_params["min_employment_months_salaried"]
    min_emp_self_employed = elig_params["min_employment_months_self_employed"]
    max_existing_foir = Decimal(str(elig_params["max_existing_foir"]))
    max_enquiries_6m = elig_params["max_enquiries_6m"]

    # Fired rules tracking
    fired_ineligible: List[Tuple[str, str]] = []  # (rule_id, reason_code)
    fired_refer: List[Tuple[str, str]] = []  # (rule_id, reason_code)
    all_fired_rules: List[str] = []

    # -------------------------------------------------------------
    # Layer V: Validation Rules (V01 - V04)
    # -------------------------------------------------------------

    # V01: Any required fact is missing (null credit score is handled by R01)
    missing_required = any(
        field not in application or application[field] is None
        for field in REQUIRED_FIELDS
    )
    if missing_required:
        fired_refer.append(("V01", "INCOMPLETE_APPLICATION"))
        all_fired_rules.append("V01")

    # V02: Consent is not recorded
    consent_given = application.get("consent_given")
    if consent_given is not None:
        if consent_given is False:
            fired_ineligible.append(("V02", "CONSENT_NOT_GIVEN"))
            all_fired_rules.append("V02")

    # V03: Requested amount outside product limits
    requested_amount = application.get("requested_amount")
    if requested_amount is not None:
        if requested_amount < min_amount or requested_amount > max_amount:
            fired_ineligible.append(("V03", "AMOUNT_OUTSIDE_PRODUCT_LIMITS"))
            all_fired_rules.append("V03")

    # V04: Requested tenure outside product limits
    requested_tenure = application.get("requested_tenure_months")
    if requested_tenure is not None:
        if requested_tenure < min_tenure or requested_tenure > max_tenure:
            fired_ineligible.append(("V04", "TENURE_OUTSIDE_PRODUCT_LIMITS"))
            all_fired_rules.append("V04")

    # -------------------------------------------------------------
    # Layer K: Knock-out Rules (K01 - K06)
    # -------------------------------------------------------------

    # K01: Age under 18
    age = application.get("age")
    if age is not None:
        if age < min_age:
            fired_ineligible.append(("K01", "LEGAL_CAPACITY_NOT_MET"))
            all_fired_rules.append("K01")

    # K02: KYC not verified
    kyc_verified = application.get("kyc_verified")
    if kyc_verified is not None:
        if kyc_verified is False:
            fired_ineligible.append(("K02", "KYC_NOT_VERIFIED"))
            all_fired_rules.append("K02")

    # K03: Adverse repayment history
    severe_delinquency = application.get("severe_delinquency_36m")
    written_off = application.get("written_off")
    if severe_delinquency is True or written_off is True:
        fired_ineligible.append(("K03", "ADVERSE_REPAYMENT_HISTORY"))
        all_fired_rules.append("K03")

    # K04: Credit score is known and below minimum (650)
    credit_score = application.get("credit_score")
    if credit_score is not None:
        if credit_score < min_credit_score:
            fired_ineligible.append(("K04", "CREDIT_SCORE_BELOW_MINIMUM"))
            all_fired_rules.append("K04")

    # K05: Monthly net income below minimum (15,000)
    monthly_income = application.get("monthly_net_income")
    if monthly_income is not None:
        if monthly_income < min_monthly_income:
            fired_ineligible.append(("K05", "INCOME_BELOW_MINIMUM"))
            all_fired_rules.append("K05")

    # K06: Employment tenure too short
    emp_type = application.get("employment_type")
    emp_months = application.get("employment_months")
    if emp_type is not None and emp_months is not None:
        if emp_type == "salaried" and emp_months < min_emp_salaried:
            fired_ineligible.append(("K06", "EMPLOYMENT_TENURE_TOO_SHORT"))
            all_fired_rules.append("K06")
        elif emp_type == "self_employed" and emp_months < min_emp_self_employed:
            fired_ineligible.append(("K06", "EMPLOYMENT_TENURE_TOO_SHORT"))
            all_fired_rules.append("K06")

    # -------------------------------------------------------------
    # Layer R: Referral Rules (R01 - R03)
    # -------------------------------------------------------------

    # R01: Credit score null (no bureau history)
    if "credit_score" not in application or application.get("credit_score") is None:
        fired_refer.append(("R01", "NO_CREDIT_HISTORY"))
        all_fired_rules.append("R01")

    # R02: More than 5 credit enquiries in last 6 months
    enquiries_6m = application.get("enquiries_6m")
    if enquiries_6m is not None:
        if enquiries_6m > max_enquiries_6m:
            fired_refer.append(("R02", "HIGH_RECENT_ENQUIRIES"))
            all_fired_rules.append("R02")

    # R03: Employment type is "other"
    if emp_type is not None:
        if emp_type == "other":
            fired_refer.append(("R03", "EMPLOYMENT_TYPE_REQUIRES_REVIEW"))
            all_fired_rules.append("R03")

    # -------------------------------------------------------------
    # Layer E: Eligibility Rules (E01, E02)
    # -------------------------------------------------------------

    # Existing FOIR calculation (Formula F1)
    monthly_obligations = application.get("monthly_obligations")
    existing_foir: Optional[Decimal] = None
    existing_foir_str: Optional[str] = None
    if (
        monthly_income is not None
        and monthly_income > 0
        and monthly_obligations is not None
    ):
        existing_foir = Decimal(monthly_obligations) / Decimal(monthly_income)
        existing_foir_str = str(
            existing_foir.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        )

    # E01: Existing FOIR is above 0.50
    if existing_foir is not None:
        if existing_foir > max_existing_foir:
            fired_ineligible.append(("E01", "HIGH_EXISTING_OBLIGATIONS"))
            all_fired_rules.append("E01")

    # Derivations (E02, A01, A02, P01) run ONLY when NO ineligible or refer outcome has been recorded
    has_prior_adverse = bool(fired_ineligible or fired_refer)

    derived_band: Optional[str] = None
    matched_band_info: Optional[dict] = None

    if not has_prior_adverse and credit_score is not None and existing_foir is not None:
        # E02: Assign band A, B or C
        for b in bands:
            b_score = b["min_score"]
            b_foir = Decimal(str(b["max_foir"]))
            if credit_score >= b_score and existing_foir <= b_foir:
                derived_band = b["id"]
                matched_band_info = b
                all_fired_rules.append("E02")
                break

    # -------------------------------------------------------------
    # Layer A: Amount Rules (A01 - A04)
    # -------------------------------------------------------------

    p_star: Optional[int] = None
    binding_limit: Optional[str] = None
    a04_reason_code: Optional[str] = None
    a04_fired = False

    if (
        not has_prior_adverse
        and derived_band is not None
        and matched_band_info is not None
        and monthly_income is not None
        and monthly_obligations is not None
        and requested_amount is not None
        and requested_tenure is not None
    ):
        # A01: Compute EMI-based maximum principal (Formulas F4, F5)
        post_loan_cap = Decimal(str(matched_band_info["post_loan_foir_cap"]))
        indicative_rate_dec = Decimal(str(matched_band_info["indicative_rate"]))
        emi_max = post_loan_cap * Decimal(monthly_income) - Decimal(monthly_obligations)

        if emi_max <= Decimal(0):
            p_emi = Decimal(0)
        else:
            r = indicative_rate_dec / Decimal(1200)
            n = requested_tenure
            p_emi = emi_max * ((Decimal(1) + r) ** n - Decimal(1)) / (r * (Decimal(1) + r) ** n)
        all_fired_rules.append("A01")

        # A02: Recommended amount (Formula F6)
        r_req = Decimal(requested_amount)
        cap_capacity = p_emi
        cap_income_multiple = Decimal(income_multiple_cap * monthly_income)
        cap_product_max = Decimal(max_amount)

        min_val = min(r_req, cap_capacity, cap_income_multiple, cap_product_max)
        p_star = int((min_val // Decimal(amount_step)) * Decimal(amount_step))

        # Binding limit selection with stated tie-breaking order
        caps = [
            ("capacity", cap_capacity),
            ("income_multiple", cap_income_multiple),
            ("product_maximum", cap_product_max),
        ]
        lowest_cap_name, lowest_cap_val = min(caps, key=lambda x: x[1])
        if r_req < lowest_cap_val:
            binding_limit = "requested"
        else:
            binding_limit = lowest_cap_name

        all_fired_rules.append("A02")

        # A03: Recommended amount is below 50,000
        if p_star < min_amount:
            fired_ineligible.append(("A03", "INSUFFICIENT_REPAYMENT_CAPACITY"))
            all_fired_rules.append("A03")
        else:
            # A04: Reduced offer
            # Fires only when no INELIGIBLE or REFER outcome recorded,
            # and p_star + amount_step <= requested_amount
            if p_star + amount_step <= requested_amount:
                a04_fired = True
                if binding_limit == "capacity":
                    a04_reason_code = "AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY"
                elif binding_limit == "income_multiple":
                    a04_reason_code = "AMOUNT_LIMITED_BY_INCOME_MULTIPLE"
                elif binding_limit == "product_maximum":
                    a04_reason_code = "AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM"
                all_fired_rules.append("A04")

    # -------------------------------------------------------------
    # Layer P: Pricing Rules (P01)
    # -------------------------------------------------------------

    indicative_rate_str: Optional[str] = None
    emi_str: Optional[str] = None
    fee_str: Optional[str] = None
    total_interest_str: Optional[str] = None
    apr_str: Optional[str] = None
    post_loan_foir_str: Optional[str] = None
    offer: Optional[dict] = None

    # P01 runs only if eligible
    is_eligible = (
        not fired_ineligible
        and not fired_refer
        and p_star is not None
        and p_star >= min_amount
        and matched_band_info is not None
        and requested_tenure is not None
        and monthly_income is not None
        and monthly_obligations is not None
    )

    if is_eligible:
        indicative_rate_dec = Decimal(str(matched_band_info["indicative_rate"]))
        indicative_rate_str = str(indicative_rate_dec)
        n = requested_tenure
        r = indicative_rate_dec / Decimal(1200)

        # Formula F3: EMI
        num = r * (Decimal(1) + r) ** n
        den = (Decimal(1) + r) ** n - Decimal(1)
        emi_dec = (Decimal(p_star) * num / den).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        emi_str = str(emi_dec)

        # Formula F7: Fee and Total interest
        fee_dec = (Decimal(p_star) * processing_fee_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fee_str = str(fee_dec)
        total_repayment = Decimal(n) * emi_dec
        total_interest_dec = (total_repayment - Decimal(p_star)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_interest_str = str(total_interest_dec)

        # Formula F8: Post-loan FOIR
        post_foir_dec = (Decimal(monthly_obligations) + emi_dec) / Decimal(monthly_income)
        post_loan_foir_str = str(post_foir_dec.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))

        # Formula F9: APR
        apr_dec = _solve_apr(p_star, fee_dec, emi_dec, n)
        apr_str = str(apr_dec)

        all_fired_rules.append("P01")

        offer = {
            "amount": p_star,
            "tenure_months": n,
            "indicative_rate": indicative_rate_str,
            "emi": emi_str,
            "fee": fee_str,
            "total_interest": total_interest_str,
            "apr": apr_str,
            "post_loan_foir": post_loan_foir_str,
        }

    # -------------------------------------------------------------
    # Final Decision, Reason Codes, and Fired Rules
    # -------------------------------------------------------------

    # Fired rules that have outcome ineligible, refer, or reduced_offer, in rule order
    fired_outcome_rules: List[str] = []
    for r_id, _ in fired_ineligible:
        if r_id not in fired_outcome_rules:
            fired_outcome_rules.append(r_id)
    for r_id, _ in fired_refer:
        if r_id not in fired_outcome_rules:
            fired_outcome_rules.append(r_id)
    if a04_fired:
        if "A04" not in fired_outcome_rules:
            fired_outcome_rules.append("A04")

    # Order fired_outcome_rules by canonical rule order
    rule_order = [
        "V01", "V02", "V03", "V04",
        "K01", "K02", "K03", "K04", "K05", "K06",
        "R01", "R02", "R03",
        "E01",
        "A03", "A04",
    ]
    fired_outcome_rules.sort(key=lambda x: rule_order.index(x) if x in rule_order else 999)

    if fired_ineligible:
        decision = "ineligible"
        # Reason codes of winning outcome only, deduplicated, in rule order
        seen = set()
        reason_codes = []
        # Sort fired_ineligible by rule_order
        sorted_ineligible = sorted(
            fired_ineligible,
            key=lambda x: rule_order.index(x[0]) if x[0] in rule_order else 999
        )
        for _, code in sorted_ineligible:
            if code not in seen:
                seen.add(code)
                reason_codes.append(code)
    elif fired_refer:
        decision = "refer"
        seen = set()
        reason_codes = []
        sorted_refer = sorted(
            fired_refer,
            key=lambda x: rule_order.index(x[0]) if x[0] in rule_order else 999
        )
        for _, code in sorted_refer:
            if code not in seen:
                seen.add(code)
                reason_codes.append(code)
    elif is_eligible:
        decision = "eligible"
        reason_codes = [a04_reason_code] if a04_reason_code else []
    else:
        # Default CP-8.1: No rule determines an outcome
        decision = "refer"
        reason_codes = ["NO_RULE_APPLICABLE"]

    # When there is no offer, financial fields are null
    rec_amt_out = p_star if is_eligible else None
    binding_limit_out = binding_limit if is_eligible else None
    indicative_rate_out = indicative_rate_str if is_eligible else None
    emi_out = emi_str if is_eligible else None
    fee_out = fee_str if is_eligible else None
    total_interest_out = total_interest_str if is_eligible else None
    apr_out = apr_str if is_eligible else None
    post_loan_foir_out = post_loan_foir_str if is_eligible else None

    return {
        "decision": decision,
        "reason_codes": reason_codes,
        "fired_rules": fired_outcome_rules,
        "all_fired_rules": all_fired_rules,
        "band": derived_band,
        "recommended_amount": rec_amt_out,
        "binding_limit": binding_limit_out,
        "indicative_rate": indicative_rate_out,
        "emi": emi_out,
        "fee": fee_out,
        "total_interest": total_interest_out,
        "apr": apr_out,
        "post_loan_foir": post_loan_foir_out,
        "existing_foir": existing_foir_str,
        "offer": offer,
    }
