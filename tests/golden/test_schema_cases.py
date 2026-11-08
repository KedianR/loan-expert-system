"""
Schema acceptance tests.

Implements: FR-01, FR-02, WP-05
Spec: schemas/input.schema.json, docs/04-predicates-and-facts.md §1 & §2

Tests every case in tests/golden/schema_cases.json against the input validator
and fact builder, and verifies unknown-value handling for absent/null fields.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.facts.fact_builder import (
    SchemaValidationError,
    build_facts,
    validate_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_CASES_PATH = REPO_ROOT / "tests" / "golden" / "schema_cases.json"


@pytest.fixture(scope="module")
def schema_cases():
    text = SCHEMA_CASES_PATH.read_text(encoding="utf-8")
    return json.loads(text)["cases"]


class TestSchemaCases:
    """Validate all golden schema cases."""

    def test_all_schema_cases(self, schema_cases):
        """Test each case in schema_cases.json against its valid flag."""
        for case in schema_cases:
            name = case["name"]
            is_valid = case["valid"]
            inp = case["input"]

            errors = validate_input(inp)
            if is_valid:
                assert not errors, (
                    f"Case '{name}' was expected to be valid, but had errors: {errors}"
                )
                facts = build_facts(inp)
                assert facts.applicant_id == inp["applicant_id"]
            else:
                assert errors, f"Case '{name}' was expected to fail validation, but passed."
                with pytest.raises(SchemaValidationError):
                    build_facts(inp)

    def test_unknown_handling_for_null_and_absent_fields(self):
        """
        Verify absent or null credit score, absent income, null income
        are valid at the schema and become unknown in the fact builder.
        """
        base_input = {
            "applicant_id": "test_app",
            "age": 30,
            "employment_type": "salaried",
            "employment_months": 24,
            "monthly_net_income": 50000,
            "monthly_obligations": 10000,
            "credit_score": 750,
            "enquiries_6m": 1,
            "severe_delinquency_36m": False,
            "written_off": False,
            "kyc_verified": True,
            "consent_given": True,
            "requested_amount": 300000,
            "requested_tenure_months": 24,
        }

        # 1. Credit score null -> unknown
        inp_null_score = dict(base_input, credit_score=None)
        assert validate_input(inp_null_score) == []
        facts_null_score = build_facts(inp_null_score)
        assert facts_null_score.is_unknown("credit_score")
        assert "credit_score" not in facts_null_score.facts

        # 2. Credit score absent -> unknown
        inp_absent_score = dict(base_input)
        del inp_absent_score["credit_score"]
        assert validate_input(inp_absent_score) == []
        facts_absent_score = build_facts(inp_absent_score)
        assert facts_absent_score.is_unknown("credit_score")
        assert "credit_score" not in facts_absent_score.facts

        # 3. Income absent -> unknown, existing_foir also unknown
        inp_absent_income = dict(base_input)
        del inp_absent_income["monthly_net_income"]
        assert validate_input(inp_absent_income) == []
        facts_absent_income = build_facts(inp_absent_income)
        assert facts_absent_income.is_unknown("monthly_net_income")
        assert facts_absent_income.is_unknown("existing_foir")

        # 4. Income null -> unknown, existing_foir also unknown
        inp_null_income = dict(base_input, monthly_net_income=None)
        assert validate_input(inp_null_income) == []
        facts_null_income = build_facts(inp_null_income)
        assert facts_null_income.is_unknown("monthly_net_income")
        assert facts_null_income.is_unknown("existing_foir")

        # 5. Income of zero -> known income=0, but existing_foir is unknown (no div by zero)
        inp_zero_income = dict(base_input, monthly_net_income=0)
        assert validate_input(inp_zero_income) == []
        facts_zero_income = build_facts(inp_zero_income)
        assert not facts_zero_income.is_unknown("monthly_net_income")
        assert facts_zero_income.get("monthly_net_income") == 0
        assert facts_zero_income.is_unknown("existing_foir")
