"""
Applicant notice builder and counterfactual guidance.

Implements: FR-11, FR-12, FR-13, CR-01, CR-02, WP-12
Spec: docs/data-dictionary.md §4, §6; config/notice_frame.toml
AGENTS.md: Hard rule 2 (no floats anywhere in src/explain), Hard rule 5 (trace is only source).
"""

from __future__ import annotations

import re
import tomllib
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from src.engine.engine import decide
from src.engine.rule_loader import RuleSet

DEFAULT_NOTICE_FRAME_PATH = Path("config/notice_frame.toml")


class NoticeError(Exception):
    """Raised when a notice template cannot be rendered due to missing values."""


def format_indian_rupees(val: int | str | Decimal) -> str:
    """
    Format whole rupees using Indian numbering system:
    last three digits, then groups of two.
    Example: 800000 -> '8,00,000', 1234567 -> '12,34,567'.
    """
    d = Decimal(str(val))
    n = int(d)
    s = str(abs(n))
    sign = "-" if n < 0 else ""
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        formatted = ",".join(parts) + "," + last3
    return sign + formatted


def format_indian_currency_with_paise(val: str | Decimal | int) -> str:
    """
    Format money with paise: Indian grouping on the whole part, '.' and 2 digits.
    Example: '10000.00' -> '10,000.00', '379739.59' -> '3,79,739.59'.
    """
    d = Decimal(str(val))
    whole = int(d)
    whole_str = format_indian_rupees(whole)
    cents = f"{abs(d - whole):.2f}".split(".")[1]
    return f"{whole_str}.{cents}"


def format_percent(val: Decimal | str, ceiling: bool = False) -> str:
    """
    Format percent: multiply exact decimal by 100, round to 2 decimal places,
    strip trailing zeros and trailing dot.
    ceiling=True uses ROUND_CEILING (for HIGH_EXISTING_OBLIGATIONS).
    """
    d = Decimal(str(val)) * Decimal("100")
    rounding_mode = ROUND_CEILING if ceiling else ROUND_HALF_UP
    d_rounded = d.quantize(Decimal("0.01"), rounding=rounding_mode)
    s = f"{d_rounded:.2f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def load_notice_frame(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_NOTICE_FRAME_PATH
    return tomllib.loads(p.read_text(encoding="utf-8"))


def _extract_fact(
    key: str,
    step: dict[str, Any] | None,
    trace: dict[str, Any],
    params: dict[str, Any],
    code: str,
) -> str | None:
    """Retrieve and format a placeholder value."""
    # Special param placeholders: {param.<name>}
    if key.startswith("param."):
        param_name = key[len("param.") :]
        if param_name == "max_existing_foir_pct":
            return format_percent(params["max_existing_foir"])
        if param_name in ("min_amount", "max_amount", "min_monthly_income"):
            return format_indian_rupees(params[param_name])
        if param_name in params:
            return str(params[param_name])
        return None

    facts_used = step.get("facts_used", {}) if step else {}
    step_derived = step.get("derived", {}) if step else {}
    trace_derived = trace.get("derived", {})

    if key == "missing_fields":
        missing_list = facts_used.get("missing_fields", [])
        formatted_names = [f.replace("_", " ") for f in missing_list]
        return ", ".join(formatted_names)

    if key == "min_months":
        emp_type = facts_used.get("employment_type")
        if emp_type == "self_employed":
            val = facts_used.get(
                "min_employment_months_self_employed",
                params.get("min_employment_months_self_employed"),
            )
        else:
            val = facts_used.get(
                "min_employment_months_salaried", params.get("min_employment_months_salaried")
            )
        return str(val) if val is not None else None

    if key == "existing_foir_pct":
        # Check step facts_used, then derived
        raw_foir = facts_used.get("existing_foir", trace_derived.get("existing_foir"))
        if raw_foir is not None:
            is_ceil = code == "HIGH_EXISTING_OBLIGATIONS"
            return format_percent(raw_foir, ceiling=is_ceil)
        return None

    if key in ("requested_amount", "recommended_amount", "income", "monthly_net_income"):
        val = facts_used.get(key)
        if val is None:
            val = step_derived.get(key)
        if val is None:
            val = trace_derived.get(key)
        if val is None and key == "income":
            val = facts_used.get("monthly_net_income", trace_derived.get("monthly_net_income"))
        if val is not None:
            return format_indian_rupees(val)
        return None

    if key in (
        "requested_tenure",
        "requested_tenure_months",
        "credit_score",
        "enquiries_6m",
        "employment_months",
    ):
        val = facts_used.get(key)
        if val is None:
            val = step_derived.get(key)
        if val is None:
            val = trace_derived.get(key)
        if val is None and key == "requested_tenure":
            val = facts_used.get("requested_tenure_months")
        if val is not None:
            return str(val)
        return None

    # Check facts_used, step_derived, trace_derived directly
    if key in facts_used:
        return str(facts_used[key])
    if key in step_derived:
        return str(step_derived[key])
    if key in trace_derived:
        return str(trace_derived[key])

    return None


def compute_counterfactual_guidance(
    application: dict[str, Any],
    rule_set: RuleSet,
    reason_codes: list[str],
    notice_frame: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Compute counterfactual guidance (docs/data-dictionary.md §6).
    Applies only when reason_codes has exactly one code:
    HIGH_EXISTING_OBLIGATIONS or INSUFFICIENT_REPAYMENT_CAPACITY.
    """
    if len(reason_codes) != 1:
        return []

    code = reason_codes[0]
    if code not in ("HIGH_EXISTING_OBLIGATIONS", "INSUFFICIENT_REPAYMENT_CAPACITY"):
        return []

    obligations = application.get("monthly_obligations")
    if obligations is None or obligations <= 0:
        return []

    low = 1
    high = obligations
    best_r = None

    while low <= high:
        mid = (low + high) // 2
        probe_app = dict(application, monthly_obligations=obligations - mid)
        res = decide(probe_app, rule_set)
        if res.get("decision") == "eligible":
            best_r = mid
            high = mid - 1
        else:
            low = mid + 1

    if best_r is None:
        return []

    # Monotonicity verification
    # Probe at best_r must be eligible; probe at best_r - 1 must NOT be eligible
    if best_r > 1:
        probe_minus_1 = dict(application, monthly_obligations=obligations - (best_r - 1))
        res_minus_1 = decide(probe_minus_1, rule_set)
        if res_minus_1.get("decision") == "eligible":
            return []

    reduction_str = format_indian_rupees(best_r)
    new_obl_str = format_indian_rupees(obligations - best_r)

    tmpl = notice_frame.get("guidance", {}).get(code)
    if not tmpl:
        return []

    text = tmpl.replace("{reduction}", reduction_str).replace("{new_obligations}", new_obl_str)
    if "{" in text or "}" in text:
        raise NoticeError(f"Unfilled placeholder in guidance text: {text}")

    return [
        {
            "code": code,
            "text": text,
            "verified_decision": "eligible",
        }
    ]


def build_notice(
    trace: dict[str, Any],
    rule_set: RuleSet,
    application: dict[str, Any] | None = None,
    notice_frame_path: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build notice from the trace and notice frame configuration.
    Conforms to docs/data-dictionary.md §4.
    """
    frame = load_notice_frame(notice_frame_path)
    notice_version = str(frame.get("meta", {}).get("version", "1.0.0"))
    decision = trace["decision"]
    reason_codes = list(trace.get("reason_codes", []))
    steps = trace.get("steps", [])

    # Map fired steps by reason code
    fired_step_by_code: dict[str, dict[str, Any]] = {}
    has_reduced_offer = False
    credit_score_val = None

    for s in steps:
        if s.get("status") == "fired":
            if s.get("outcome") == "reduced_offer":
                has_reduced_offer = True
            rc = s.get("reason_code")
            if rc and rc not in fired_step_by_code:
                fired_step_by_code[rc] = s
        fu = s.get("facts_used", {})
        if "credit_score" in fu and credit_score_val is None:
            credit_score_val = fu["credit_score"]

    # 1. Headline
    headline_config = frame.get("headline", {})
    if decision == "eligible" and has_reduced_offer:
        headline = headline_config.get("eligible_reduced")
    else:
        headline = headline_config.get(decision)
    if not headline:
        headline = f"Your application is {decision}."

    # 2. Reasons
    reasons: list[dict[str, str]] = []
    placeholder_pattern = re.compile(r"\{([^}]+)\}")

    for code in reason_codes:
        rc_def = rule_set.reason_codes.get(code)
        if not rc_def:
            raise NoticeError(f"Reason code '{code}' not found in reason code definitions")

        raw_template = rc_def.text
        step = fired_step_by_code.get(code)

        def replace_match(m: re.Match) -> str:
            ph = m.group(1)
            val = _extract_fact(ph, step, trace, rule_set.params, code)
            if val is None:
                raise NoticeError(f"Missing placeholder value for '{ph}' in reason code '{code}'")
            return val

        rendered_text = placeholder_pattern.sub(replace_match, raw_template)
        if "{" in rendered_text or "}" in rendered_text:
            raise NoticeError(f"Unfilled placeholder in reason text: {rendered_text}")

        reasons.append({"code": code, "text": rendered_text})

    # 3. Guidance (counterfactual)
    guidance: list[dict[str, Any]] = []
    if application is not None:
        guidance = compute_counterfactual_guidance(application, rule_set, reason_codes, frame)

    # 4. Basis (eligible only)
    basis: list[dict[str, str]] = []
    if decision == "eligible":
        basis_config = frame.get("basis", {})
        basis_binding_config = frame.get("basis_binding", {})
        derived = trace.get("derived", {})

        # band line
        band_val = derived.get("band")
        foir_val = derived.get("existing_foir")
        if band_val and foir_val is not None and credit_score_val is not None:
            band_tmpl = basis_config.get("band")
            if band_tmpl:
                txt = (
                    band_tmpl.replace("{band}", str(band_val))
                    .replace("{credit_score}", str(credit_score_val))
                    .replace("{existing_foir_pct}", format_percent(foir_val))
                )
                if not ("{" in txt or "}" in txt):
                    basis.append({"label": "band", "text": txt})

        # instalment_limit line
        max_emi_val = derived.get("max_emi")
        max_p_emi_val = derived.get("max_principal_emi")
        if max_emi_val is not None and max_p_emi_val is not None:
            inst_tmpl = basis_config.get("instalment_limit")
            if inst_tmpl:
                txt = inst_tmpl.replace(
                    "{max_emi}", format_indian_currency_with_paise(max_emi_val)
                ).replace(
                    "{max_principal_emi}",
                    format_indian_currency_with_paise(max_p_emi_val),
                )
                if not ("{" in txt or "}" in txt):
                    basis.append({"label": "instalment_limit", "text": txt})

        # after_loan line
        post_foir_val = derived.get("post_loan_foir")
        if post_foir_val is not None:
            after_tmpl = basis_config.get("after_loan")
            if after_tmpl:
                txt = after_tmpl.replace("{post_loan_foir_pct}", format_percent(post_foir_val))
                if not ("{" in txt or "}" in txt):
                    basis.append({"label": "after_loan", "text": txt})

        # binding_limit line
        bl = derived.get("binding_limit")
        if bl and bl in basis_binding_config:
            basis.append({"label": "binding_limit", "text": basis_binding_config[bl]})

    # 5. Offer summary (eligible only)
    offer_summary = None
    if decision == "eligible" and trace.get("offer"):
        off = trace["offer"]
        labels = frame.get("offer_summary", {}).get("labels", {})
        disclaimer = frame.get("offer_summary", {}).get(
            "disclaimer",
            "This is an indicative summary from an illustrative prototype that uses synthetic data. It is not a loan offer or a contract.",
        )

        rate_low, rate_high = off["rate_range"].split("-")
        rate_band_display = f"{off['band']}: {rate_low}% to {rate_high}%"

        rows = [
            {
                "label": labels.get("amount", "Loan amount"),
                "value": f"INR {format_indian_rupees(off['amount'])}",
            },
            {"label": labels.get("tenure", "Tenure"), "value": f"{off['tenure_months']} months"},
            {
                "label": labels.get("rate_band", "Interest band and yearly range"),
                "value": rate_band_display,
            },
            {
                "label": labels.get("indicative_rate", "Indicative interest rate (yearly)"),
                "value": f"{off['indicative_rate']}%",
            },
            {
                "label": labels.get("emi", "Monthly instalment (EMI)"),
                "value": f"INR {format_indian_currency_with_paise(off['emi'])}",
            },
            {
                "label": labels.get("fee", "Processing fee"),
                "value": f"INR {format_indian_currency_with_paise(off['fee'])}",
            },
            {
                "label": labels.get("total_interest", "Total interest over the tenure"),
                "value": f"INR {format_indian_currency_with_paise(off['total_interest'])}",
            },
            {
                "label": labels.get("apr", "Annual percentage rate (APR), including the fee"),
                "value": f"{off['apr']}%",
            },
        ]
        offer_summary = {
            "rows": rows,
            "disclaimer": disclaimer,
        }

    return {
        "notice_version": notice_version,
        "headline": headline,
        "reasons": reasons,
        "guidance": guidance,
        "basis": basis,
        "offer_summary": offer_summary,
    }
