"""
Decision trace builder and validator.

Implements: FR-10, WP-11
Spec: docs/04-predicates-and-facts.md §5, docs/decision-tables.md §1-4, schemas/trace.schema.json
AGENTS.md: Hard rule 2 (no floats), Hard rule 5 (trace built only from engine result).
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from src.engine.rule_loader import RuleSet

DEFAULT_TRACE_SCHEMA_PATH = Path("schemas/trace.schema.json")
_CACHED_TRACE_VALIDATOR: Draft202012Validator | None = None


def get_trace_validator(
    schema_path: Path | str | None = None,
) -> Draft202012Validator:
    global _CACHED_TRACE_VALIDATOR
    path = Path(schema_path) if schema_path else DEFAULT_TRACE_SCHEMA_PATH
    if _CACHED_TRACE_VALIDATOR is None:
        schema_text = path.read_text(encoding="utf-8")
        schema = json.loads(schema_text)
        Draft202012Validator.check_schema(schema)
        _CACHED_TRACE_VALIDATOR = Draft202012Validator(schema)
    return _CACHED_TRACE_VALIDATOR


def validate_trace(trace: dict[str, Any], schema_path: Path | str | None = None) -> None:
    validator = get_trace_validator(schema_path)
    errors = list(validator.iter_errors(trace))
    if errors:
        msg = "; ".join(f"{e.json_path}: {e.message}" for e in errors)
        raise ValueError(f"Trace validation failed: {msg}")


def _clean_fact_value(v: Any) -> Any:
    if isinstance(v, float):
        raise TypeError(f"Floats forbidden in trace facts: {v!r}")
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, list):
        return [_clean_fact_value(item) for item in v]
    return v


def build_trace(
    engine_result: dict[str, Any],
    rule_set: RuleSet,
    applicant_ref: str,
    input_hash: str,
    rule_set_version: str,
    rule_set_hash: str,
    decision_id: str | None = None,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    """
    Build a decision trace from engine_result.
    Does not evaluate rules or raw input; transforms engine result to conform
    to schemas/trace.schema.json.
    """
    decision = engine_result["decision"]
    reason_codes = list(engine_result.get("reason_codes", []))

    # Build clean steps
    trace_steps: list[dict[str, Any]] = []
    engine_steps = engine_result.get("steps", [])

    for s in engine_steps:
        r_id = s["rule_id"]
        rule_def = rule_set.rules.get(r_id)
        rule_version = s.get("rule_version", rule_def.version if rule_def else "0.1.0")
        layer = s.get("layer", rule_def.layer if rule_def else "validation")

        step_dict: dict[str, Any] = {
            "order": s["order"],
            "rule_id": r_id,
            "rule_version": str(rule_version),
            "layer": layer,
            "status": s["status"],
        }

        status = s["status"]
        if status == "fired":
            step_dict["outcome"] = s["outcome"]
            if "reason_code" in s and s["reason_code"]:
                step_dict["reason_code"] = s["reason_code"]
            if "derived" in s and s["derived"]:
                step_dict["derived"] = {k: _clean_fact_value(v) for k, v in s["derived"].items()}
            if "facts_used" in s and s["facts_used"]:
                step_dict["facts_used"] = {
                    k: _clean_fact_value(v) for k, v in s["facts_used"].items()
                }

        elif status == "not_fired":
            if "facts_used" in s and s["facts_used"]:
                step_dict["facts_used"] = {
                    k: _clean_fact_value(v) for k, v in s["facts_used"].items()
                }

        elif status == "not_evaluated":
            missing = s.get("missing", [])
            if isinstance(missing, str):
                missing = [missing]
            step_dict["missing"] = list(missing)

        elif status == "skipped":
            step_dict["skipped_reason"] = s.get("skipped_reason", "blocking outcome")

        trace_steps.append(step_dict)

    # Derived values
    derived_in = engine_result.get("derived", {})
    trace_derived: dict[str, Any] = {k: _clean_fact_value(v) for k, v in derived_in.items()}

    # Offer
    offer_in = engine_result.get("offer")
    trace_offer = None
    if decision == "eligible" and offer_in:
        trace_offer = {
            "amount": int(offer_in["amount"]),
            "tenure_months": int(offer_in["tenure_months"]),
            "band": str(offer_in["band"]),
            "rate_range": str(offer_in["rate_range"]),
            "indicative_rate": str(offer_in["indicative_rate"]),
            "emi": str(offer_in["emi"]),
            "fee": str(offer_in["fee"]),
            "total_interest": str(offer_in["total_interest"]),
            "apr": str(offer_in["apr"]),
        }
        if "post_loan_foir" in offer_in:
            trace_offer["post_loan_foir"] = str(offer_in["post_loan_foir"])

    trace: dict[str, Any] = {
        "applicant_ref": applicant_ref,
        "input_hash": input_hash,
        "rule_set_version": rule_set_version,
        "rule_set_hash": rule_set_hash,
        "decision": decision,
        "steps": trace_steps,
        "derived": trace_derived,
        "reason_codes": reason_codes,
        "offer": trace_offer,
    }

    if decision_id is not None:
        trace["decision_id"] = decision_id
    if evaluated_at is not None:
        trace["evaluated_at"] = evaluated_at

    return trace
