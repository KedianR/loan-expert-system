"""
Facts package.

Input validation, applicant fact building, and unknown fact handling.
Exact Decimal arithmetic; no floats permitted.
"""

from src.facts.fact_builder import (
    ApplicantFacts,
    SchemaValidationError,
    build_facts,
    validate_input,
)

__all__ = [
    "ApplicantFacts",
    "SchemaValidationError",
    "build_facts",
    "validate_input",
]
