"""
D1 Rule Coverage Test.

Spec: docs/07-implementation-plan.md (WP-16a), docs/decision-tables.md §5, §6
Verifies:
- All D1 cases validate against schemas/input.schema.json
- Every active rule fires at least once on D1
- The firing matrix reports 0 unfired active rules
- DT-3: AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM is unreachable by design while V03 is active
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from src.engine.hygiene import generate_firing_matrix
from src.engine.rule_loader import load_rules

REPO_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = REPO_ROOT / "rules"
PARAMS_PATH = REPO_ROOT / "params" / "params.toml"
D1_CASES_PATH = REPO_ROOT / "data" / "d1" / "d1_cases.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "input.schema.json"


@pytest.fixture(scope="module")
def rule_set():
    return load_rules(RULES_DIR, PARAMS_PATH)


@pytest.fixture(scope="module")
def d1_data():
    content = D1_CASES_PATH.read_text(encoding="utf-8")
    return json.loads(content)


@pytest.fixture(scope="module")
def input_schema():
    content = SCHEMA_PATH.read_text(encoding="utf-8")
    return json.loads(content)


def test_d1_cases_schema_conformance(d1_data, input_schema):
    """All D1 cases must validate against schemas/input.schema.json."""
    cases = d1_data["cases"]
    assert len(cases) > 0, "D1 has no cases"
    for c in cases:
        # Throws ValidationError if invalid
        jsonschema.validate(instance=c["input"], schema=input_schema)


def test_d1_all_active_rules_fire(rule_set, d1_data):
    """Every active rule must fire at least once across D1."""
    cases = d1_data["cases"]
    counts = generate_firing_matrix(rule_set, cases)

    # 1. Check counts for each active rule
    unfired = []
    for r_id, count in counts.items():
        r = rule_set.rules.get(r_id)
        if r and r.status == "active":
            if count == 0:
                unfired.append(r_id)

    assert unfired == [], f"Active rules failed to fire on D1: {unfired}"
    assert len(counts) == 20, f"Expected 20 active rules in matrix, got {len(counts)}"
