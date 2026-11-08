"""
Unit tests for fact builder.

Implements: FR-01, FR-02, FR-03, WP-05
Spec: docs/04-predicates-and-facts.md
"""

from __future__ import annotations

import pytest

from src.facts.fact_builder import (
    ApplicantFacts,
    SchemaValidationError,
    build_facts,
    validate_input,
)


class TestFactsUnit:
    """Unit tests for ApplicantFacts and fact builder helpers."""

    def test_facts_container_methods(self):
        """ApplicantFacts is_unknown, get, to_prolog_facts."""
        from decimal import Decimal

        facts = ApplicantFacts(
            applicant_id="a001",
            facts={
                "age": 34,
                "employment_type": "salaried",
                "consent_given": True,
                "existing_foir": Decimal("0.3000"),
            },
            unknowns={"credit_score"},
        )
        assert facts.applicant_id == "a001"
        assert not facts.is_unknown("age")
        assert facts.is_unknown("credit_score")
        assert facts.get("age") == 34
        assert facts.get("credit_score") is None
        assert facts.get("credit_score", 700) == 700

        clauses = facts.to_prolog_facts()
        assert "age(a001, 34)." in clauses
        assert "consent_given(a001, true)." in clauses
        assert "existing_foir(a001, 0.3000)." in clauses
        assert "unknown(a001, credit_score)." in clauses

    def test_absent_obligations_makes_foir_unknown(self):
        """When obligations is absent, existing_foir is recorded as unknown."""
        base_valid = {
            "applicant_id": "a001",
            "age": 30,
            "employment_type": "salaried",
            "employment_months": 24,
            "monthly_net_income": 50000,
            "credit_score": 750,
            "enquiries_6m": 1,
            "severe_delinquency_36m": False,
            "written_off": False,
            "kyc_verified": True,
            "consent_given": True,
            "requested_amount": 300000,
            "requested_tenure_months": 24,
        }
        facts = build_facts(base_valid)
        assert facts.is_unknown("monthly_obligations")
        assert facts.is_unknown("existing_foir")

    def test_protected_attributes_rejected(self):
        """Gender, religion, caste in input are rejected by schema validator."""
        base_valid = {
            "applicant_id": "a001",
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

        for attr in ["gender", "religion", "caste"]:
            bad_inp = dict(base_valid, **{attr: "test_val"})
            errors = validate_input(bad_inp)
            assert len(errors) >= 1
            assert any("Additional properties are not allowed" in e for e in errors)
            with pytest.raises(SchemaValidationError):
                build_facts(bad_inp)
