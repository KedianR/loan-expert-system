"""
Fact builder: input validation and fact base creation.

Implements: FR-01, FR-02, FR-03, WP-05
Spec: docs/04-predicates-and-facts.md sections 1, 2, 3; docs/03-calculations.md §4
AGENTS.md: Hard rule 4 (protected attributes never entered into fact base).

Rules:
- Validate input against schemas/input.schema.json (Draft 2020-12).
- Malformed value or unknown key (including protected attributes): SchemaValidationError.
- Absent or null field: record as unknown; never guess or default.
- Compute existing_foir (F1) when income and obligations are known and income > 0.
- If income is missing or zero: record existing_foir as unknown (never divide by zero).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from src.calc.formulas import calculate_existing_foir

# Default schema path relative to project root
DEFAULT_SCHEMA_PATH = Path("schemas/input.schema.json")

# Input fields defined in docs/04 §2 and schemas/input.schema.json (excluding applicant_id)
INPUT_FACT_FIELDS = (
    "age",
    "employment_type",
    "employment_months",
    "monthly_net_income",
    "monthly_obligations",
    "credit_score",
    "enquiries_6m",
    "severe_delinquency_36m",
    "written_off",
    "kyc_verified",
    "consent_given",
    "requested_amount",
    "requested_tenure_months",
    "region_tier",
)

# Predicate name mapping for fields where predicate differs from field name
PREDICATE_NAME_MAP = {
    "requested_tenure_months": "requested_tenure",
}


class SchemaValidationError(Exception):
    """Raised when an application input fails schema validation."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__(f"Schema validation failed: {'; '.join(errors)}")
        self.errors = errors


@dataclass
class ApplicantFacts:
    """The fact base for a single applicant."""

    applicant_id: str
    facts: dict[str, Any] = field(default_factory=dict)
    unknowns: set[str] = field(default_factory=set)

    def is_unknown(self, field_name: str) -> bool:
        """Return True if the field is recorded as unknown."""
        return field_name in self.unknowns

    def get(self, field_name: str, default: Any = None) -> Any:
        """Get known fact value or default if unknown/absent."""
        if field_name in self.unknowns:
            return default
        return self.facts.get(field_name, default)

    def to_prolog_facts(self) -> list[str]:
        """Format the known facts and unknowns as Prolog assertions."""
        clauses: list[str] = []
        aid = self.applicant_id

        # Known facts
        for name, val in sorted(self.facts.items()):
            pred = PREDICATE_NAME_MAP.get(name, name)
            if isinstance(val, bool):
                val_str = "true" if val else "false"
            elif isinstance(val, Decimal):
                val_str = f"{val:.4f}"
            elif isinstance(val, (int, str)):
                val_str = str(val)
            else:
                val_str = str(val)
            clauses.append(f"{pred}({aid}, {val_str}).")

        # Unknowns
        for unk in sorted(self.unknowns):
            clauses.append(f"unknown({aid}, {unk}).")

        return clauses


_CACHED_VALIDATOR: Draft202012Validator | None = None
_CACHED_SCHEMA_PATH: Path | None = None


def get_validator(schema_path: Path | str | None = None) -> Draft202012Validator:
    """Load and cache the Draft 2020-12 validator."""
    global _CACHED_VALIDATOR, _CACHED_SCHEMA_PATH
    path = Path(schema_path) if schema_path else DEFAULT_SCHEMA_PATH
    if _CACHED_VALIDATOR is None or _CACHED_SCHEMA_PATH != path:
        schema_text = path.read_text(encoding="utf-8")
        schema = json.loads(schema_text)
        Draft202012Validator.check_schema(schema)
        _CACHED_VALIDATOR = Draft202012Validator(schema)
        _CACHED_SCHEMA_PATH = path
    return _CACHED_VALIDATOR


def validate_input(
    data: dict[str, Any],
    schema_path: Path | str | None = None,
) -> list[str]:
    """
    Validate raw input dict against the input JSON Schema.
    Returns a list of human-readable error strings (empty if valid).
    """
    validator = get_validator(schema_path)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: e.path):
        loc = ".".join(str(p) for p in err.path) if err.path else "(root)"
        errors.append(f"{loc}: {err.message}")
    return errors


def build_facts(
    data: dict[str, Any],
    schema_path: Path | str | None = None,
) -> ApplicantFacts:
    """
    Validate application input and build ApplicantFacts.

    - Validates against schemas/input.schema.json.
    - Captures absent or null fields into unknowns.
    - Computes existing_foir (F1) when obligations and income are known and income > 0.
    - If income is missing or zero, existing_foir is recorded as unknown.
    - Never reads gender, religion, caste or keys outside the schema.
    """
    errors = validate_input(data, schema_path)
    if errors:
        raise SchemaValidationError(errors)

    applicant_id = str(data["applicant_id"])
    facts: dict[str, Any] = {}
    unknowns: set[str] = set()

    for fld in INPUT_FACT_FIELDS:
        if fld not in data or data[fld] is None:
            unknowns.add(fld)
        else:
            val = data[fld]
            facts[fld] = val

    # Derive existing_foir (Formula F1)
    # Docs/03 §4: If income is missing: stop before division.
    # If income is 0: do not divide; record existing_foir as unknown.
    if "monthly_net_income" in unknowns or facts.get("monthly_net_income") == 0:
        unknowns.add("existing_foir")
    elif "monthly_obligations" in unknowns:
        unknowns.add("existing_foir")
    else:
        obligations = facts["monthly_obligations"]
        income = facts["monthly_net_income"]
        foir = calculate_existing_foir(obligations, income)
        facts["existing_foir"] = foir

    return ApplicantFacts(
        applicant_id=applicant_id,
        facts=facts,
        unknowns=unknowns,
    )
