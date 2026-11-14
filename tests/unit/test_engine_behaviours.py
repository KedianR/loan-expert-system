"""
Engine behaviour unit tests.

Implements: docs/06-test-plan.md Lean mode, docs/decision-tables.md §1-4
Behaviours:
  1. null credit score (K04 not_evaluated, R01 fires, V01 does not)
  2. missing required field (V01 fires, dependent rule not_evaluated)
  3. derivation rules skipped after a blocking outcome
  4. default REFER with NO_RULE_APPLICABLE (test-only parameter set)
  5. request of 777,777 (recommended 775,000, no A04)
  6. A03 and A04 never both firing (TV6, TV8)
  7. DT-4: binding_limit is 'requested' when request equals the smallest cap (a04_tie_request_income)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.engine.engine import decide
from src.engine.rule_loader import RuleSet, load_rules

REPO_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = REPO_ROOT / "rules"
PARAMS_PATH = REPO_ROOT / "params" / "params.toml"

BASE_APPLICANT: dict[str, Any] = {
    "applicant_id": "tv1_base",
    "age": 34,
    "employment_type": "salaried",
    "employment_months": 48,
    "monthly_net_income": 80000,
    "monthly_obligations": 10000,
    "credit_score": 735,
    "enquiries_6m": 2,
    "severe_delinquency_36m": False,
    "written_off": False,
    "kyc_verified": True,
    "consent_given": True,
    "requested_amount": 700000,
    "requested_tenure_months": 36,
}


@pytest.fixture(scope="module")
def rule_set():
    rs = load_rules(RULES_DIR, PARAMS_PATH)
    assert rs is not None
    return rs


def get_step(res: dict[str, Any], rule_id: str) -> dict[str, Any]:
    for s in res["steps"]:
        if s["rule_id"] == rule_id:
            return s
    raise AssertionError(f"Step {rule_id} not in result steps")


class TestEngineBehaviours:
    def test_null_credit_score(self, rule_set):
        """Null credit score: K04 is not_evaluated (missing credit_score), R01 fires, V01 does not fire."""
        app = {**BASE_APPLICANT, "credit_score": None}
        res = decide(app, rule_set)

        assert res["decision"] == "refer"
        assert res["reason_codes"] == ["NO_CREDIT_HISTORY"]

        step_k04 = get_step(res, "K04")
        step_r01 = get_step(res, "R01")
        step_v01 = get_step(res, "V01")

        assert step_k04["status"] == "not_evaluated"
        assert step_k04["missing"] == "credit_score"
        assert step_r01["status"] == "fired"
        assert step_v01["status"] == "not_fired"

    def test_missing_required_field(self, rule_set):
        """Missing required field: V01 fires, dependent rule (V03 or K01) is not_evaluated."""
        app = {**BASE_APPLICANT, "requested_amount": None}
        res = decide(app, rule_set)

        assert res["decision"] == "refer"
        assert "INCOMPLETE_APPLICATION" in res["reason_codes"]

        step_v01 = get_step(res, "V01")
        step_v03 = get_step(res, "V03")

        assert step_v01["status"] == "fired"
        assert step_v03["status"] == "not_evaluated"
        assert step_v03["missing"] == "requested_amount"

    def test_derivations_skipped_after_blocking(self, rule_set):
        """Derivation rules E02, A01, A02, P01 skipped after a blocking outcome."""
        # Age 17 blocks in K01
        app = {**BASE_APPLICANT, "age": 17}
        res = decide(app, rule_set)

        assert res["decision"] == "ineligible"
        assert "LEGAL_CAPACITY_NOT_MET" in res["reason_codes"]

        for r_id in ("E02", "A01", "A02", "P01"):
            step = get_step(res, r_id)
            assert step["status"] == "skipped"
            assert step.get("skipped_reason") == "blocking outcome"

    def test_default_refer_no_rule_applicable(self, rule_set):
        """Default REFER with NO_RULE_APPLICABLE when no band can be derived."""
        # Test-only parameter set with band C removed
        bands_without_c = [b for b in rule_set.bands if b["id"] != "C"]
        test_rs = RuleSet(
            manifest=rule_set.manifest,
            params=rule_set.params,
            bands=bands_without_c,
            fields=rule_set.fields,
            reason_codes=rule_set.reason_codes,
            rules=rule_set.rules,
            rules_by_layer=rule_set.rules_by_layer,
        )

        # Applicant with score 650, FOIR 0.45: clears K04 and E01, but matches no band (A requires 750, B requires 700)
        app = {
            **BASE_APPLICANT,
            "credit_score": 650,
            "monthly_net_income": 100000,
            "monthly_obligations": 45000,
            "requested_amount": 50000,
            "requested_tenure_months": 24,
        }
        res = decide(app, test_rs)

        assert res["decision"] == "refer"
        assert res["reason_codes"] == ["NO_RULE_APPLICABLE"]
        assert get_step(res, "E02")["status"] == "not_fired"
        assert get_step(res, "A01")["status"] == "skipped"
        assert get_step(res, "A02")["status"] == "skipped"

    def test_request_777777_no_a04(self, rule_set):
        """A request of 777,777: recommended 775,000, shortfall 2,777 < amount_step (5,000), no A04."""
        app = {
            **BASE_APPLICANT,
            "requested_amount": 777777,
            "monthly_net_income": 150000,
            "monthly_obligations": 10000,
        }
        res = decide(app, rule_set)

        assert res["decision"] == "eligible"
        assert res["reason_codes"] == []
        assert res["offer"]["amount"] == 775000
        step_a04 = get_step(res, "A04")
        assert step_a04["status"] == "not_fired"

    def test_a03_and_a04_never_both_firing(self, rule_set):
        """Decision DT-1: A03 and A04 never both fire (tested on TV6 and TV8)."""
        # TV6: no EMI room
        tv6 = {
            "applicant_id": "tv6",
            "age": 34,
            "employment_type": "salaried",
            "employment_months": 48,
            "monthly_net_income": 100000,
            "monthly_obligations": 50000,
            "credit_score": 650,
            "enquiries_6m": 2,
            "severe_delinquency_36m": False,
            "written_off": False,
            "kyc_verified": True,
            "consent_given": True,
            "requested_amount": 300000,
            "requested_tenure_months": 24,
        }
        r6 = decide(tv6, rule_set)
        assert r6["decision"] == "ineligible"
        assert "INSUFFICIENT_REPAYMENT_CAPACITY" in r6["reason_codes"]
        assert get_step(r6, "A03")["status"] == "fired"
        assert get_step(r6, "A04")["status"] == "skipped"

        # TV8: capacity below 50,000
        tv8 = {
            "applicant_id": "tv8",
            "age": 34,
            "employment_type": "salaried",
            "employment_months": 48,
            "monthly_net_income": 15000,
            "monthly_obligations": 6500,
            "credit_score": 700,
            "enquiries_6m": 2,
            "severe_delinquency_36m": False,
            "written_off": False,
            "kyc_verified": True,
            "consent_given": True,
            "requested_amount": 100000,
            "requested_tenure_months": 12,
        }
        r8 = decide(tv8, rule_set)
        assert r8["decision"] == "ineligible"
        assert "INSUFFICIENT_REPAYMENT_CAPACITY" in r8["reason_codes"]
        assert get_step(r8, "A03")["status"] == "fired"
        assert get_step(r8, "A04")["status"] == "skipped"

    def test_dt4_binding_limit_requested_when_request_equals_cap(self, rule_set):
        """DT-4: when request equals the smallest cap, binding_limit is 'requested' and A04 must not fire.

        Case a04_tie_request_income: request 500,000, income 50,000 (10 x I = 500,000),
        capacity cap well above request. P* = 500,000 = R, so the full request is granted;
        A04 condition (recommended_amount + amount_step <= requested_amount) is false.
        docs/03-calculations.md F6 and docs/decision-tables.md §4 (DT-4): binding_limit is 'requested'.

        FR-08, docs/decision-tables.md §4 DT-4
        """
        app = {
            **BASE_APPLICANT,
            "applicant_id": "a04_tie_request_income",
            "monthly_net_income": 50000,
            "monthly_obligations": 0,
            "credit_score": 720,
            "requested_amount": 500000,
            "requested_tenure_months": 60,
        }
        res = decide(app, rule_set)

        assert res["decision"] == "eligible"
        assert res["reason_codes"] == []
        assert res["derived"]["binding_limit"] == "requested"
        assert res["offer"]["amount"] == 500000
        step_a04 = get_step(res, "A04")
        assert step_a04["status"] == "not_fired"

    def test_fr06_decision_precedence_and_recommendation(self, rule_set):
        """FR-06, FR-05: Exactly one decision returned; precedence INELIGIBLE over REFER over ELIGIBLE.

        Also recommends an amount and interest band for ELIGIBLE decisions.
        """
        # Case with both knockout (K01: age 17) and refer condition (R01: credit_score None)
        app_both = {**BASE_APPLICANT, "age": 17, "credit_score": None}
        res_both = decide(app_both, rule_set)
        assert res_both["decision"] == "ineligible", "INELIGIBLE must take precedence over REFER"

        # Eligible decision recommends amount and interest band
        res_elig = decide(BASE_APPLICANT, rule_set)
        assert res_elig["decision"] == "eligible"
        assert res_elig["offer"]["amount"] > 0
        assert res_elig["offer"]["band"] in ("A", "B", "C", "D")

    def test_fr19_deterministic_engine_evaluation(self, rule_set):
        """FR-19, NFR-01: Engine evaluation is deterministic and operates without audit writes.

        Repeated evaluation of the same applicant produces identical decisions, steps, and derived facts.
        """
        res1 = decide(BASE_APPLICANT, rule_set)
        res2 = decide(BASE_APPLICANT, rule_set)
        assert res1 == res2, "Repeated engine runs must produce byte-identical dictionaries"
