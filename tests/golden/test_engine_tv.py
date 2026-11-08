"""
Golden vector end-to-end engine tests (TV1 to TV9).

Spec: docs/03-calculations.md section 3, docs/06-test-plan.md
Tests golden vectors through decide(application, rule_set).
Verifies:
- Final decision
- Reason codes (DT-2: winning outcome only)
- rules_must_fire
- rules_must_not_fire
- Band and binding limit
- Offer figures (amount, tenure, rate, emi, fee, total interest, apr within 0.01, post_loan_foir)
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.engine.engine import decide
from src.engine.rule_loader import load_rules

REPO_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = REPO_ROOT / "rules"
PARAMS_PATH = REPO_ROOT / "params" / "params.toml"
VECTORS_PATH = REPO_ROOT / "tests" / "golden" / "vectors.json"


@pytest.fixture(scope="module")
def rule_set():
    return load_rules(RULES_DIR, PARAMS_PATH)


@pytest.fixture(scope="module")
def vectors_data():
    content = VECTORS_PATH.read_text(encoding="utf-8")
    return json.loads(content)


def test_tv_vectors(rule_set, vectors_data):
    apr_tol = Decimal(vectors_data.get("apr_tolerance", "0.01"))

    for vec in vectors_data["vectors"]:
        v_id = vec["id"]
        inp = vec["input"]
        exp = vec["expected"]

        res = decide(inp, rule_set)

        # 1. Decision
        assert res["decision"] == exp["decision"], (
            f"{v_id}: expected decision {exp['decision']}, got {res['decision']}"
        )

        # 2. Reason codes
        assert res["reason_codes"] == exp["reason_codes"], (
            f"{v_id}: expected reason codes {exp['reason_codes']}, got {res['reason_codes']}"
        )

        # Step lookup map
        steps_by_id = {s["rule_id"]: s for s in res["steps"]}

        # 3. rules_must_fire
        for r_id in exp.get("rules_must_fire", []):
            step = steps_by_id.get(r_id)
            assert step is not None, f"{v_id}: rule {r_id} not in trace steps"
            assert step["status"] == "fired", (
                f"{v_id}: rule {r_id} expected fired, got {step['status']}"
            )

        # 4. rules_must_not_fire
        for r_id in exp.get("rules_must_not_fire", []):
            step = steps_by_id.get(r_id)
            if step is not None:
                assert step["status"] != "fired", f"{v_id}: rule {r_id} must not fire, but fired"

        # 5. Derived checks if present in expected
        if "band" in exp:
            assert res["derived"].get("band") == exp["band"], (
                f"{v_id}: expected band {exp['band']}, got {res['derived'].get('band')}"
            )

        if "binding_limit" in exp:
            assert res["derived"].get("binding_limit") == exp["binding_limit"], (
                f"{v_id}: expected binding_limit {exp['binding_limit']}, got {res['derived'].get('binding_limit')}"
            )

        # 6. Offer checks if present
        if exp.get("offer") is not None:
            exp_offer = exp["offer"]
            act_offer = res.get("offer")
            assert act_offer is not None, f"{v_id}: expected offer, got None"
            assert act_offer["amount"] == exp_offer["amount"]
            assert act_offer["tenure_months"] == exp_offer["tenure_months"]
            assert act_offer["indicative_rate"] == exp_offer["indicative_rate"]
            assert act_offer["emi"] == exp_offer["emi"]
            assert act_offer["fee"] == exp_offer["fee"]
            assert act_offer["total_interest"] == exp_offer["total_interest"]
            assert act_offer["post_loan_foir"] == exp_offer["post_loan_foir"]

            # APR tolerance
            exp_apr = Decimal(exp_offer["apr"])
            act_apr = Decimal(act_offer["apr"])
            diff = abs(act_apr - exp_apr)
            assert diff <= apr_tol, f"{v_id}: APR diff {diff} exceeds tolerance {apr_tol}"
        else:
            assert res.get("offer") is None, (
                f"{v_id}: unexpected offer present on non-eligible decision"
            )
