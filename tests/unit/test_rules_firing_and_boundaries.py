"""
Rule firing and threshold-boundary tests.

Implements: WP-07, WP-08, WP-09, FR-02, FR-04, FR-05, FR-07, FR-08, FR-09
Spec: docs/decision-tables.md section 5
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.engine.engine import decide
from src.engine.rule_loader import load_rules

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


def app_mod(mod: dict[str, Any]) -> dict[str, Any]:
    return {**BASE_APPLICANT, **mod}


def get_step(res: dict[str, Any], rule_id: str) -> dict[str, Any]:
    for s in res["steps"]:
        if s["rule_id"] == rule_id:
            return s
    raise AssertionError(f"Step {rule_id} not in result steps")


class TestValidationRules:
    def test_V01_firing_on_missing_income(self, rule_set):
        res = decide(app_mod({"monthly_net_income": None}), rule_set)
        assert res["decision"] == "refer"
        assert "INCOMPLETE_APPLICATION" in res["reason_codes"]
        step = get_step(res, "V01")
        assert step["status"] == "fired"

    def test_V01_no_fire_when_complete(self, rule_set):
        res = decide(BASE_APPLICANT, rule_set)
        step = get_step(res, "V01")
        assert step["status"] == "not_fired"

    def test_V02_firing_on_consent_false(self, rule_set):
        res = decide(app_mod({"consent_given": False}), rule_set)
        assert res["decision"] == "ineligible"
        assert "CONSENT_NOT_GIVEN" in res["reason_codes"]
        step = get_step(res, "V02")
        assert step["status"] == "fired"

    def test_V02_no_fire_on_consent_true(self, rule_set):
        res = decide(BASE_APPLICANT, rule_set)
        step = get_step(res, "V02")
        assert step["status"] == "not_fired"

    def test_V03_boundaries(self, rule_set):
        # 49,999: fires
        r_low = decide(app_mod({"requested_amount": 49999}), rule_set)
        assert r_low["decision"] == "ineligible"
        assert get_step(r_low, "V03")["status"] == "fired"

        # 50,000: does not fire
        r_min = decide(app_mod({"requested_amount": 50000}), rule_set)
        assert get_step(r_min, "V03")["status"] == "not_fired"

        # 2,500,000: does not fire
        r_max = decide(app_mod({"requested_amount": 2500000}), rule_set)
        assert get_step(r_max, "V03")["status"] == "not_fired"

        # 2,500,001: fires
        r_high = decide(app_mod({"requested_amount": 2500001}), rule_set)
        assert r_high["decision"] == "ineligible"
        assert get_step(r_high, "V03")["status"] == "fired"

    def test_V04_boundaries(self, rule_set):
        # 11: fires
        r_low = decide(app_mod({"requested_tenure_months": 11}), rule_set)
        assert r_low["decision"] == "ineligible"
        assert get_step(r_low, "V04")["status"] == "fired"

        # 12: does not fire
        r_min = decide(app_mod({"requested_tenure_months": 12}), rule_set)
        assert get_step(r_min, "V04")["status"] == "not_fired"

        # 60: does not fire
        r_max = decide(app_mod({"requested_tenure_months": 60}), rule_set)
        assert get_step(r_max, "V04")["status"] == "not_fired"

        # 61: fires
        r_high = decide(app_mod({"requested_tenure_months": 61}), rule_set)
        assert r_high["decision"] == "ineligible"
        assert get_step(r_high, "V04")["status"] == "fired"


class TestKnockoutRules:
    def test_K01_boundaries(self, rule_set):
        # Age 17: fires
        r17 = decide(app_mod({"age": 17}), rule_set)
        assert r17["decision"] == "ineligible"
        assert get_step(r17, "K01")["status"] == "fired"

        # Age 18: does not fire
        r18 = decide(app_mod({"age": 18}), rule_set)
        assert get_step(r18, "K01")["status"] == "not_fired"

    def test_K02_kyc(self, rule_set):
        r_false = decide(app_mod({"kyc_verified": False}), rule_set)
        assert r_false["decision"] == "ineligible"
        assert get_step(r_false, "K02")["status"] == "fired"

        r_true = decide(BASE_APPLICANT, rule_set)
        assert get_step(r_true, "K02")["status"] == "not_fired"

    def test_K03_adverse_history(self, rule_set):
        # Severe delinquency
        r_del = decide(app_mod({"severe_delinquency_36m": True}), rule_set)
        assert r_del["decision"] == "ineligible"
        assert get_step(r_del, "K03")["status"] == "fired"

        # Written off
        r_wo = decide(app_mod({"written_off": True}), rule_set)
        assert r_wo["decision"] == "ineligible"
        assert get_step(r_wo, "K03")["status"] == "fired"

        # Both false: not fired
        r_clean = decide(BASE_APPLICANT, rule_set)
        assert get_step(r_clean, "K03")["status"] == "not_fired"

    def test_K04_boundaries(self, rule_set):
        # 649: fires
        r649 = decide(app_mod({"credit_score": 649}), rule_set)
        assert r649["decision"] == "ineligible"
        assert get_step(r649, "K04")["status"] == "fired"

        # 650: does not fire
        r650 = decide(app_mod({"credit_score": 650}), rule_set)
        assert get_step(r650, "K04")["status"] == "not_fired"

    def test_K05_boundaries(self, rule_set):
        # 14,999: fires
        r14999 = decide(app_mod({"monthly_net_income": 14999, "monthly_obligations": 0}), rule_set)
        assert r14999["decision"] == "ineligible"
        assert get_step(r14999, "K05")["status"] == "fired"

        # 15,000: does not fire
        r15000 = decide(app_mod({"monthly_net_income": 15000, "monthly_obligations": 0}), rule_set)
        assert get_step(r15000, "K05")["status"] == "not_fired"

    def test_K06_boundaries(self, rule_set):
        # Salaried: 5 months (fires), 6 months (does not fire)
        rs5 = decide(app_mod({"employment_type": "salaried", "employment_months": 5}), rule_set)
        assert get_step(rs5, "K06")["status"] == "fired"
        rs6 = decide(app_mod({"employment_type": "salaried", "employment_months": 6}), rule_set)
        assert get_step(rs6, "K06")["status"] == "not_fired"

        # Self-employed: 23 months (fires), 24 months (does not fire)
        re23 = decide(
            app_mod({"employment_type": "self_employed", "employment_months": 23}), rule_set
        )
        assert get_step(re23, "K06")["status"] == "fired"
        re24 = decide(
            app_mod({"employment_type": "self_employed", "employment_months": 24}), rule_set
        )
        assert get_step(re24, "K06")["status"] == "not_fired"


class TestReferralRules:
    def test_R01_null_credit_score(self, rule_set):
        r_null = decide(app_mod({"credit_score": None}), rule_set)
        assert r_null["decision"] == "refer"
        assert "NO_CREDIT_HISTORY" in r_null["reason_codes"]
        assert get_step(r_null, "R01")["status"] == "fired"

        r_known = decide(BASE_APPLICANT, rule_set)
        assert get_step(r_known, "R01")["status"] == "not_fired"

    def test_R02_boundaries(self, rule_set):
        # 5 enquiries: not fired
        r5 = decide(app_mod({"enquiries_6m": 5}), rule_set)
        assert get_step(r5, "R02")["status"] == "not_fired"

        # 6 enquiries: fires
        r6 = decide(app_mod({"enquiries_6m": 6}), rule_set)
        assert r6["decision"] == "refer"
        assert "HIGH_RECENT_ENQUIRIES" in r6["reason_codes"]
        assert get_step(r6, "R02")["status"] == "fired"

    def test_R03_employment_type_other(self, rule_set):
        r_other = decide(app_mod({"employment_type": "other"}), rule_set)
        assert r_other["decision"] == "refer"
        assert "EMPLOYMENT_TYPE_REQUIRES_REVIEW" in r_other["reason_codes"]
        assert get_step(r_other, "R03")["status"] == "fired"

        r_sal = decide(BASE_APPLICANT, rule_set)
        assert get_step(r_sal, "R03")["status"] == "not_fired"


class TestEligibilityRules:
    def test_E01_boundaries(self, rule_set):
        # FOIR 0.50 (100k income, 50k obligations): does not fire E01
        r50 = decide(
            app_mod(
                {"monthly_net_income": 100000, "monthly_obligations": 50000, "credit_score": 650}
            ),
            rule_set,
        )
        assert get_step(r50, "E01")["status"] == "not_fired"

        # FOIR 0.50001 (100k income, 50001 obligations): fires E01
        r50001 = decide(
            app_mod({"monthly_net_income": 100000, "monthly_obligations": 50001}),
            rule_set,
        )
        assert r50001["decision"] == "ineligible"
        assert "HIGH_EXISTING_OBLIGATIONS" in r50001["reason_codes"]
        assert get_step(r50001, "E01")["status"] == "fired"

    def test_E02_band_assignments(self, rule_set):
        # Band A: score 750, FOIR 0.30
        ra = decide(
            app_mod(
                {
                    "credit_score": 750,
                    "monthly_net_income": 100000,
                    "monthly_obligations": 30000,
                    "requested_amount": 50000,
                    "requested_tenure_months": 24,
                }
            ),
            rule_set,
        )
        assert ra["derived"]["band"] == "A"
        assert get_step(ra, "E02")["status"] == "fired"

        # Band B: score 749, FOIR 0.30
        rb1 = decide(
            app_mod(
                {
                    "credit_score": 749,
                    "monthly_net_income": 100000,
                    "monthly_obligations": 30000,
                    "requested_amount": 50000,
                    "requested_tenure_months": 24,
                }
            ),
            rule_set,
        )
        assert rb1["derived"]["band"] == "B"

        # Band B: score 700, FOIR 0.40
        rb2 = decide(
            app_mod(
                {
                    "credit_score": 700,
                    "monthly_net_income": 100000,
                    "monthly_obligations": 40000,
                    "requested_amount": 50000,
                    "requested_tenure_months": 24,
                }
            ),
            rule_set,
        )
        assert rb2["derived"]["band"] == "B"

        # Band C: score 699, FOIR 0.40
        rc1 = decide(
            app_mod(
                {
                    "credit_score": 699,
                    "monthly_net_income": 100000,
                    "monthly_obligations": 40000,
                    "requested_amount": 50000,
                    "requested_tenure_months": 24,
                }
            ),
            rule_set,
        )
        assert rc1["derived"]["band"] == "C"


class TestAmountAndPricingRules:
    def test_A01_and_A02_derivations(self, rule_set):
        res = decide(BASE_APPLICANT, rule_set)
        s_a01 = get_step(res, "A01")
        s_a02 = get_step(res, "A02")
        assert s_a01["status"] == "fired"
        assert "max_emi" in s_a01["derived"]
        assert s_a02["status"] == "fired"
        assert s_a02["derived"]["recommended_amount"] == 700000
        assert s_a02["derived"]["binding_limit"] == "requested"

    def test_A03_insufficient_repayment_capacity(self, rule_set):
        # TV8 inputs: recommended amount 0 or < 50,000 -> A03 fires
        tv8_app = {
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
        res = decide(tv8_app, rule_set)
        assert res["decision"] == "ineligible"
        assert "INSUFFICIENT_REPAYMENT_CAPACITY" in res["reason_codes"]
        assert get_step(res, "A03")["status"] == "fired"

    def test_A04_step_boundary(self, rule_set):
        # TV2 applicant inputs: rec 375,000
        # Request 379,999: shortfall is 4,999 (< 5,000 step) -> A04 does not fire
        r_379 = decide(
            app_mod(
                {
                    "monthly_net_income": 40000,
                    "monthly_obligations": 12000,
                    "credit_score": 760,
                    "requested_amount": 379999,
                    "requested_tenure_months": 48,
                }
            ),
            rule_set,
        )
        assert get_step(r_379, "A04")["status"] == "not_fired"
        assert r_379["reason_codes"] == []

        # Request 380,000: shortfall is 5,000 (== 5,000 step) -> A04 fires
        r_380 = decide(
            app_mod(
                {
                    "monthly_net_income": 40000,
                    "monthly_obligations": 12000,
                    "credit_score": 760,
                    "requested_amount": 380000,
                    "requested_tenure_months": 48,
                }
            ),
            rule_set,
        )
        assert get_step(r_380, "A04")["status"] == "fired"
        assert "AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY" in r_380["reason_codes"]

    def test_P01_pricing_derivation(self, rule_set):
        res = decide(BASE_APPLICANT, rule_set)
        s_p01 = get_step(res, "P01")
        assert s_p01["status"] == "fired"
        assert s_p01["derived"]["indicative_rate"] == "14.5"
        assert s_p01["derived"]["fee"] == "14000.00"
        assert "offer" in res
