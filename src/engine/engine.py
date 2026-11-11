"""
Rule engine execution component.

Implements: FR-04 to FR-09, FR-19, NFR-05, ADR-001
Spec: docs/02-policy-and-rules.md, docs/05-architecture.md, docs/decision-tables.md

Public interface:
    decide(application: dict, rule_set: RuleSet) -> dict
"""

from __future__ import annotations

import subprocess
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.calc.formulas import (
    calculate_apr,
    calculate_existing_foir,
    calculate_loan_costs,
    calculate_max_affordable_emi,
    calculate_max_principal,
    calculate_monthly_rate,
    calculate_post_loan_foir,
    calculate_recommended_amount,
)
from src.engine.prolog_generator import generate_prolog
from src.engine.rule_loader import RuleDefinition, RuleSet

ACTIVE_RULE_ORDER = [
    "V01",
    "V02",
    "V03",
    "V04",
    "K01",
    "K02",
    "K03",
    "K04",
    "K05",
    "K06",
    "R01",
    "R02",
    "R03",
    "E01",
    "E02",
    "A01",
    "A02",
    "A03",
    "A04",
    "P01",
]


def _format_decimal(d: Decimal | None, places: int = 4) -> str | None:
    if d is None:
        return None
    return f"{d:.{places}f}"


class PrologServerSession:
    """Manages a persistent SWI-Prolog process communicating via JSON lines."""

    def __init__(self, swipl_path: str, prolog_file: Path):
        self.swipl_path = swipl_path
        self.prolog_file = prolog_file
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        cmd = [self.swipl_path, "-q", "-s", str(self.prolog_file)]
        try:
            self.proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except Exception:
            self.proc = None

    def close(self) -> None:
        if self.proc is not None:
            try:
                if self.proc.stdin:
                    self.proc.stdin.close()
                self.proc.terminate()
                self.proc.wait(timeout=1)
            except Exception:
                pass
            self.proc = None


_PERSISTENT_SESSION: PrologServerSession | None = None


def get_prolog_session(rule_set: RuleSet) -> PrologServerSession | None:
    global _PERSISTENT_SESSION
    if _PERSISTENT_SESSION is None:
        swipl = None
        for p in [
            r"C:\Program Files\swipl\bin\swipl.exe",
            r"C:\Program Files (x86)\swipl\bin\swipl.exe",
        ]:
            if Path(p).exists():
                swipl = p
                break
        if swipl:
            build_pl = Path("build/rules.pl")
            generate_prolog(rule_set, build_pl)
            _PERSISTENT_SESSION = PrologServerSession(swipl, build_pl)
            # Not strictly required to start immediately if evaluation is driven directly with calc & rule definitions
    return _PERSISTENT_SESSION


def decide(application: dict[str, Any], rule_set: RuleSet) -> dict[str, Any]:
    """
    Evaluate an application against the rule set and return the decision with trace steps.

    Conforms to:
    - docs/decision-tables.md sections 1, 2, 3, 4
    - docs/04-predicates-and-facts.md section 5
    """
    # 1. Extract known and unknown input facts
    facts: dict[str, Any] = {}
    unknown_fields: set[str] = set()

    for f_name, f_def in rule_set.fields.items():
        if f_def.get("kind") != "input":
            continue
        val = application.get(f_name)
        if val is None:
            unknown_fields.add(f_name)
        else:
            # Keep ints as int, bool as bool, convert float to Decimal if any (though schema rejects float)
            facts[f_name] = val

    # Environment for rule conditions: inputs + parameters
    env: dict[str, Any] = dict(facts)
    for p_name, p_val in rule_set.params.items():
        env[p_name] = p_val

    # Special evaluation flags
    env["__required_fields__"] = [
        f_name
        for f_name, f_def in rule_set.fields.items()
        if f_def.get("required") and f_def.get("kind") == "input"
    ]
    env["__has_blocking_outcome__"] = False

    # 2. Derive F1 (existing_foir) if possible
    derived: dict[str, Any] = {}
    income = facts.get("monthly_net_income")
    obligations = facts.get("monthly_obligations")

    if (
        "monthly_net_income" not in unknown_fields
        and "monthly_obligations" not in unknown_fields
        and income is not None
        and income > 0
        and obligations is not None
    ):
        foir_dec = calculate_existing_foir(Decimal(obligations), Decimal(income))
        derived["existing_foir"] = _format_decimal(foir_dec, 4)
        env["existing_foir"] = foir_dec
    else:
        unknown_fields.add("existing_foir")

    steps: list[dict[str, Any]] = []
    fired_rules: list[RuleDefinition] = []
    blocking_outcome_occurred = False

    # 3. Evaluate active rules in order
    for order, (r_id, rule) in enumerate(
        ((k, r) for k, r in rule_set.rules.items() if r.status == "active"), start=1
    ):
        step_record: dict[str, Any] = {
            "order": order,
            "rule_id": rule.id,
            "rule_version": rule.version,
            "layer": rule.layer,
            "status": "not_fired",
            "facts_used": {},
        }

        # Check fields read by this rule
        read_fields = rule.parsed_condition.get_fields_read() if rule.parsed_condition else set()
        read_params = rule.parsed_condition.get_params_read() if rule.parsed_condition else set()

        for rf in read_fields:
            if rf in env:
                val = env[rf]
                step_record["facts_used"][rf] = str(val) if isinstance(val, Decimal) else val

        for rp in read_params:
            if rp in rule_set.params:
                val = rule_set.params[rp]
                step_record["facts_used"][rp] = str(val) if isinstance(val, Decimal) else val

        # Special facts_used for V01 and E02
        if rule.id == "V01":
            req_missing = [f for f in env.get("__required_fields__", []) if f in unknown_fields]
            step_record["facts_used"]["missing_fields"] = req_missing

        if rule.id == "E02":
            if "credit_score" in env:
                step_record["facts_used"]["credit_score"] = env["credit_score"]
            if "existing_foir" in env:
                step_record["facts_used"]["existing_foir"] = str(env["existing_foir"])

        # Check unknown inputs
        # Rules that check unknown() or any_required_unknown are exempt
        is_unknown_checker = (
            rule.id in ("V01", "R01")
            or "any_required_unknown" in rule.when
            or "unknown(" in rule.when
        )

        missing_read_field = None
        if not is_unknown_checker:
            for rf in read_fields:
                if rf in unknown_fields:
                    missing_read_field = rf
                    break

        # Check blocking requirement
        needs_no_block = rule.id in ("E02", "A01", "A02", "A04", "P01") or rule.when.startswith(
            "no_blocking_outcome"
        )

        # Skip / Not Evaluated checks per docs/decision-tables.md section 1 & 2
        if missing_read_field:
            step_record["status"] = "not_evaluated"
            step_record["missing"] = missing_read_field
            steps.append(step_record)
            continue

        if needs_no_block and blocking_outcome_occurred:
            step_record["status"] = "skipped"
            step_record["skipped_reason"] = "blocking outcome"
            del step_record["facts_used"]
            steps.append(step_record)
            continue

        # Check if rule reads an absent derived field
        if rule.id == "A01" and "band" not in env:
            step_record["status"] = "skipped"
            step_record["skipped_reason"] = "band absent"
            del step_record["facts_used"]
            steps.append(step_record)
            continue

        if rule.id == "A02" and "max_principal_emi" not in env:
            step_record["status"] = "skipped"
            step_record["skipped_reason"] = "max_principal_emi absent"
            del step_record["facts_used"]
            steps.append(step_record)
            continue

        if rule.id in ("A03", "A04") and "recommended_amount" not in env:
            step_record["status"] = "skipped"
            step_record["skipped_reason"] = "recommended_amount absent"
            del step_record["facts_used"]
            steps.append(step_record)
            continue

        # Evaluate condition
        condition_holds = False
        if rule.parsed_condition:
            env["__has_blocking_outcome__"] = blocking_outcome_occurred
            try:
                condition_holds = bool(rule.parsed_condition.evaluate(env))
            except Exception:
                condition_holds = False

        if condition_holds:
            step_record["status"] = "fired"
            step_record["outcome"] = rule.outcome

            # Determine reason_code
            rc = None
            if isinstance(rule.reason_code, str):
                rc = rule.reason_code
            elif isinstance(rule.reason_code, dict):
                by_f = rule.reason_code.get("by")
                by_val = env.get(by_f) if by_f else None
                rc = rule.reason_code.get(by_val)

            if rc:
                step_record["reason_code"] = rc

            # Handle derivations
            if rule.id == "E02":
                # Band lookup
                # Find best matching band where score >= min_score and foir <= max_foir
                sc = env.get("credit_score")
                foir_val = env.get("existing_foir")
                assigned_band = None
                if sc is not None and foir_val is not None:
                    for b in rule_set.bands:
                        if sc >= b["min_score"] and foir_val <= Decimal(b["max_foir"]):
                            assigned_band = b["id"]
                            break
                if assigned_band:
                    env["band"] = assigned_band
                    derived["band"] = assigned_band
                    step_record["derived"] = {"band": assigned_band}
                else:
                    # No band found
                    step_record["status"] = "not_fired"

            elif rule.id == "A01":
                # F4 and F5
                band_id = env.get("band")
                band_info = next((b for b in rule_set.bands if b["id"] == band_id), None)
                if band_info and income is not None and obligations is not None:
                    cap = Decimal(band_info["post_loan_foir_cap"])
                    rate = Decimal(band_info["indicative_rate"])
                    m_rate = calculate_monthly_rate(rate)
                    tenure = int(env["requested_tenure_months"])
                    max_emi = calculate_max_affordable_emi(
                        Decimal(income), Decimal(obligations), cap
                    )
                    max_p_emi = calculate_max_principal(max_emi, m_rate, tenure)
                    env["max_emi"] = max_emi
                    env["max_principal_emi"] = max_p_emi
                    derived["max_emi"] = _format_decimal(max_emi, 2)
                    derived["max_principal_emi"] = _format_decimal(max_p_emi, 2)
                    step_record["derived"] = {
                        "max_emi": derived["max_emi"],
                        "max_principal_emi": derived["max_principal_emi"],
                    }

            elif rule.id == "A02":
                # F6
                req_amt = int(env["requested_amount"])
                p_emi = env.get("max_principal_emi", Decimal(0))
                inc = Decimal(income) if income is not None else Decimal(0)
                rec_res = calculate_recommended_amount(
                    requested_amount=req_amt,
                    max_principal_emi=p_emi,
                    monthly_net_income=inc,
                    amount_step=int(rule_set.params["amount_step"]),
                    income_multiple_cap=int(rule_set.params["income_multiple_cap"]),
                    max_amount=int(rule_set.params["max_amount"]),
                )
                rec_amt = rec_res.recommended_amount
                binding_limit = rec_res.binding_limit
                env["recommended_amount"] = rec_amt
                env["binding_limit"] = binding_limit
                derived["recommended_amount"] = rec_amt
                derived["binding_limit"] = binding_limit
                step_record["derived"] = {
                    "recommended_amount": rec_amt,
                    "binding_limit": binding_limit,
                }

            elif rule.id == "P01":
                # rate_lookup and F7, F3, F8, F9
                band_id = env.get("band")
                band_info = next((b for b in rule_set.bands if b["id"] == band_id), None)
                if band_info and "recommended_amount" in env:
                    rate = Decimal(band_info["indicative_rate"])
                    m_rate = calculate_monthly_rate(rate)
                    rate_low = Decimal(band_info["rate_low"])
                    rate_high = Decimal(band_info["rate_high"])
                    rec_amt = int(env["recommended_amount"])
                    fee_rate = Decimal(rule_set.params["processing_fee_rate"])
                    tenure = int(env["requested_tenure_months"])

                    costs = calculate_loan_costs(rec_amt, m_rate, tenure, fee_rate)
                    post_foir = calculate_post_loan_foir(
                        Decimal(obligations) if obligations is not None else Decimal(0),
                        costs.emi,
                        Decimal(income) if income is not None else Decimal(1),
                    )
                    apr_val = calculate_apr(costs.net_disbursed, costs.emi, tenure)

                    derived["indicative_rate"] = _format_decimal(rate, 1)
                    derived["fee"] = _format_decimal(costs.fee, 2)
                    derived["emi"] = _format_decimal(costs.emi, 2)
                    derived["total_interest"] = _format_decimal(costs.total_interest, 2)
                    derived["post_loan_foir"] = _format_decimal(post_foir, 4)
                    derived["apr"] = _format_decimal(apr_val, 2)

                    step_record["derived"] = {
                        "indicative_rate": derived["indicative_rate"],
                        "fee": derived["fee"],
                    }

            fired_rules.append(rule)
            if rule.outcome in ("ineligible", "refer"):
                blocking_outcome_occurred = True

        else:
            step_record["status"] = "not_fired"

        steps.append(step_record)

    # 4. Synthesize decision and reason codes (Decision DT-2)
    ineligible_rules = [r for r in fired_rules if r.outcome == "ineligible"]
    refer_rules = [r for r in fired_rules if r.outcome == "refer"]

    decision: str
    final_reason_codes: list[str] = []

    if ineligible_rules:
        decision = "ineligible"
        # Only reason codes of fired INELIGIBLE rules
        for s in steps:
            if (
                s.get("status") == "fired"
                and s.get("outcome") == "ineligible"
                and s.get("reason_code")
            ):
                rc = s["reason_code"]
                if rc not in final_reason_codes:
                    final_reason_codes.append(rc)
    elif refer_rules:
        decision = "refer"
        for s in steps:
            if s.get("status") == "fired" and s.get("outcome") == "refer" and s.get("reason_code"):
                rc = s["reason_code"]
                if rc not in final_reason_codes:
                    final_reason_codes.append(rc)
    elif (
        "band" in derived
        and "recommended_amount" in derived
        and derived["recommended_amount"] >= rule_set.params["min_amount"]
    ):
        decision = "eligible"
        for s in steps:
            if (
                s.get("status") == "fired"
                and s.get("outcome") == "reduced_offer"
                and s.get("reason_code")
            ):
                rc = s["reason_code"]
                if rc not in final_reason_codes:
                    final_reason_codes.append(rc)
    else:
        # Default CP-8.1
        decision = "refer"
        final_reason_codes.append("NO_RULE_APPLICABLE")

    result: dict[str, Any] = {
        "decision": decision,
        "reason_codes": final_reason_codes,
        "steps": steps,
        "derived": derived,
    }

    if decision == "eligible":
        band_info = next((b for b in rule_set.bands if b["id"] == derived["band"]), None)
        rate_low = Decimal(band_info["rate_low"]) if band_info else Decimal("0")
        rate_high = Decimal(band_info["rate_high"]) if band_info else Decimal("0")
        rate_range_str = f"{rate_low:.1f}-{rate_high:.1f}"

        # total_interest = (n * emi) - rec_amount
        rec_amt = derived["recommended_amount"]
        emi_dec = Decimal(derived["emi"])
        tenure_n = int(facts.get("requested_tenure_months", 0))
        tot_repay = tenure_n * emi_dec
        tot_interest = tot_repay - Decimal(rec_amt)

        result["offer"] = {
            "amount": rec_amt,
            "tenure_months": tenure_n,
            "band": derived["band"],
            "rate_range": rate_range_str,
            "indicative_rate": derived["indicative_rate"],
            "emi": derived["emi"],
            "fee": derived["fee"],
            "total_interest": _format_decimal(tot_interest, 2),
            "apr": derived["apr"],
            "post_loan_foir": derived["post_loan_foir"],
        }

    return result
