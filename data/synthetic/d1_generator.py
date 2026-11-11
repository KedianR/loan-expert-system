"""
D1 rule-coverage dataset generator.

Implements: WP-16a, DR-05, docs/08-datasets.md §4, docs/decision-tables.md §5
Deterministic, no randomness, no clock.
Writes to data/d1/d1_cases.json.
Format: {"version": 1, "cases": [{"case_id": "...", "tests": "...", "input": {...}}]}
Every input validates against schemas/input.schema.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.facts.fact_builder import validate_input

SCHEMA_PATH = Path("schemas/input.schema.json")
OUTPUT_PATH = Path("data/d1/d1_cases.json")

# Clean base applicant (TV1)
BASE_APPLICANT: dict[str, Any] = {
    "applicant_id": "tv1",
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


def make_case(case_id: str, tests: str, modifications: dict[str, Any]) -> dict[str, Any]:
    app = dict(BASE_APPLICANT)
    app["applicant_id"] = case_id
    for k, v in modifications.items():
        if v is None and k in app:
            # None means missing field if specified, or explicit None
            app[k] = None
        elif v == "__DELETE__":
            app.pop(k, None)
        else:
            app[k] = v
    return {
        "case_id": case_id,
        "tests": tests,
        "input": app,
    }


def build_d1_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    # -----------------------------------------------------------------------
    # 1. Decision Tables Section 5 baseline rows
    # -----------------------------------------------------------------------
    cases.append(make_case("b0_tv1_base", "Base applicant (TV1 eligible band B)", {}))

    # V01 cases
    cases.append(
        make_case("v01_a_income_missing", "V01: Income missing", {"monthly_net_income": None})
    )
    cases.append(
        make_case(
            "v01_b_requested_amount_missing",
            "V01: Requested amount missing",
            {"requested_amount": None},
        )
    )
    cases.append(
        make_case("v01_c_consent_missing", "V01: Consent missing", {"consent_given": None})
    )

    # V02 case
    cases.append(make_case("v02_a_consent_false", "V02: Consent false", {"consent_given": False}))

    # V03 amount limits
    cases.append(
        make_case(
            "v03_49999",
            "V03: Requested amount 49,999 below min_amount",
            {"requested_amount": 49999},
        )
    )
    cases.append(
        make_case("v03_50000", "V03: Requested amount exactly 50,000", {"requested_amount": 50000})
    )
    cases.append(
        make_case(
            "v03_50001",
            "V03: Requested amount 50,001 just above min_amount",
            {"requested_amount": 50001},
        )
    )
    cases.append(
        make_case(
            "v03_2499999",
            "V03: Requested amount 2,499,999 just below max_amount",
            {"requested_amount": 2499999},
        )
    )
    cases.append(
        make_case(
            "v03_2500000",
            "V03: Requested amount 2,500,000 at max_amount",
            {"requested_amount": 2500000},
        )
    )
    cases.append(
        make_case(
            "v03_2500001",
            "V03: Requested amount 2,500,001 above max_amount",
            {"requested_amount": 2500001},
        )
    )

    # V04 tenure limits
    cases.append(
        make_case(
            "v04_11",
            "V04: Tenure 11 months below min_tenure_months",
            {"requested_tenure_months": 11},
        )
    )
    cases.append(
        make_case(
            "v04_12", "V04: Tenure 12 months at min_tenure_months", {"requested_tenure_months": 12}
        )
    )
    cases.append(
        make_case(
            "v04_13",
            "V04: Tenure 13 months just above min_tenure_months",
            {"requested_tenure_months": 13},
        )
    )
    cases.append(
        make_case(
            "v04_59",
            "V04: Tenure 59 months just below max_tenure_months",
            {"requested_tenure_months": 59},
        )
    )
    cases.append(
        make_case(
            "v04_60", "V04: Tenure 60 months at max_tenure_months", {"requested_tenure_months": 60}
        )
    )
    cases.append(
        make_case(
            "v04_61",
            "V04: Tenure 61 months above max_tenure_months",
            {"requested_tenure_months": 61},
        )
    )

    # K01 age
    cases.append(make_case("k01_17", "K01: Age 17 below min_age", {"age": 17}))
    cases.append(make_case("k01_18", "K01: Age 18 at min_age", {"age": 18}))
    cases.append(make_case("k01_19", "K01: Age 19 just above min_age", {"age": 19}))

    # K02 KYC
    cases.append(make_case("k02_a_kyc_false", "K02: KYC not verified", {"kyc_verified": False}))

    # K03 adverse history
    cases.append(
        make_case(
            "k03_a_delinquency_true",
            "K03: Severe delinquency true",
            {"severe_delinquency_36m": True},
        )
    )
    cases.append(
        make_case("k03_b_written_off_true", "K03: Written off true", {"written_off": True})
    )

    # K04 credit score
    cases.append(
        make_case("k04_649", "K04: Credit score 649 below min_credit_score", {"credit_score": 649})
    )
    cases.append(
        make_case("k04_650", "K04: Credit score 650 at min_credit_score", {"credit_score": 650})
    )
    cases.append(
        make_case(
            "k04_651", "K04: Credit score 651 just above min_credit_score", {"credit_score": 651}
        )
    )

    # K05 income
    cases.append(
        make_case(
            "k05_14999",
            "K05: Income 14,999 below min_monthly_income",
            {"monthly_net_income": 14999, "monthly_obligations": 0},
        )
    )
    cases.append(
        make_case(
            "k05_15000",
            "K05: Income 15,000 at min_monthly_income",
            {"monthly_net_income": 15000, "monthly_obligations": 0},
        )
    )
    cases.append(
        make_case(
            "k05_15001",
            "K05: Income 15,001 just above min_monthly_income",
            {"monthly_net_income": 15001, "monthly_obligations": 0},
        )
    )
    cases.append(
        make_case("k05_0", "K05: Income 0", {"monthly_net_income": 0, "monthly_obligations": 0})
    )

    # K06 employment tenure
    cases.append(
        make_case(
            "k06_s5",
            "K06: Salaried 5 months below min_employment_months_salaried",
            {"employment_type": "salaried", "employment_months": 5},
        )
    )
    cases.append(
        make_case(
            "k06_s6",
            "K06: Salaried 6 months at min_employment_months_salaried",
            {"employment_type": "salaried", "employment_months": 6},
        )
    )
    cases.append(
        make_case(
            "k06_s7",
            "K06: Salaried 7 months just above min_employment_months_salaried",
            {"employment_type": "salaried", "employment_months": 7},
        )
    )
    cases.append(
        make_case(
            "k06_e23",
            "K06: Self-employed 23 months below min_employment_months_self_employed",
            {"employment_type": "self_employed", "employment_months": 23},
        )
    )
    cases.append(
        make_case(
            "k06_e24",
            "K06: Self-employed 24 months at min_employment_months_self_employed",
            {"employment_type": "self_employed", "employment_months": 24},
        )
    )
    cases.append(
        make_case(
            "k06_e25",
            "K06: Self-employed 25 months just above min_employment_months_self_employed",
            {"employment_type": "self_employed", "employment_months": 25},
        )
    )

    # R01 credit score null
    cases.append(
        make_case(
            "r01_a_null_score", "R01: Credit score null (no bureau history)", {"credit_score": None}
        )
    )

    # R02 enquiries
    cases.append(make_case("r02_4", "R02: 4 enquiries below max_enquiries_6m", {"enquiries_6m": 4}))
    cases.append(make_case("r02_5", "R02: 5 enquiries at max_enquiries_6m", {"enquiries_6m": 5}))
    cases.append(make_case("r02_6", "R02: 6 enquiries above max_enquiries_6m", {"enquiries_6m": 6}))

    # R03 employment type other
    cases.append(
        make_case("r03_a_other", "R03: Employment type other", {"employment_type": "other"})
    )

    # E01 FOIR boundary
    cases.append(
        make_case(
            "e01_a_foir_exact_050",
            "E01: FOIR exactly 0.50 (100k inc, 50k obl, score 650)",
            {"monthly_net_income": 100000, "monthly_obligations": 50000, "credit_score": 650},
        )
    )
    cases.append(
        make_case(
            "e01_b_foir_above_050",
            "E01: FOIR 0.50001 (100k inc, 50001 obl)",
            {"monthly_net_income": 100000, "monthly_obligations": 50001},
        )
    )

    # E02 Band lookups
    cases.append(
        make_case(
            "e02_a_750_30000",
            "E02: Band A boundary: score 750, FOIR 0.30",
            {
                "credit_score": 750,
                "monthly_net_income": 100000,
                "monthly_obligations": 30000,
                "requested_amount": 50000,
                "requested_tenure_months": 24,
            },
        )
    )
    cases.append(
        make_case(
            "e02_b_749_30000",
            "E02: Band B boundary: score 749, FOIR 0.30",
            {
                "credit_score": 749,
                "monthly_net_income": 100000,
                "monthly_obligations": 30000,
                "requested_amount": 50000,
                "requested_tenure_months": 24,
            },
        )
    )
    cases.append(
        make_case(
            "e02_b_750_30001",
            "E02: Band B boundary: score 750, FOIR 0.30001",
            {
                "credit_score": 750,
                "monthly_net_income": 100000,
                "monthly_obligations": 30001,
                "requested_amount": 50000,
                "requested_tenure_months": 24,
            },
        )
    )
    cases.append(
        make_case(
            "e02_b_700_40000",
            "E02: Band B boundary: score 700, FOIR 0.40",
            {
                "credit_score": 700,
                "monthly_net_income": 100000,
                "monthly_obligations": 40000,
                "requested_amount": 50000,
                "requested_tenure_months": 24,
            },
        )
    )
    cases.append(
        make_case(
            "e02_c_699_40000",
            "E02: Band C boundary: score 699, FOIR 0.40",
            {
                "credit_score": 699,
                "monthly_net_income": 100000,
                "monthly_obligations": 40000,
                "requested_amount": 50000,
                "requested_tenure_months": 24,
            },
        )
    )
    cases.append(
        make_case(
            "e02_c_700_40001",
            "E02: Band C boundary: score 700, FOIR 0.40001",
            {
                "credit_score": 700,
                "monthly_net_income": 100000,
                "monthly_obligations": 40001,
                "requested_amount": 50000,
                "requested_tenure_months": 24,
            },
        )
    )
    cases.append(
        make_case(
            "e02_c_650_50000",
            "E02: Band C boundary: score 650, FOIR 0.50",
            {
                "credit_score": 650,
                "monthly_net_income": 100000,
                "monthly_obligations": 50000,
                "requested_amount": 50000,
                "requested_tenure_months": 24,
            },
        )
    )

    # Additional Band boundaries: just-below, at, just-above
    cases.append(
        make_case(
            "band_a_score_751",
            "Band A: score 751 just above threshold",
            {"credit_score": 751, "monthly_net_income": 100000, "monthly_obligations": 25000},
        )
    )
    cases.append(
        make_case(
            "band_a_foir_29999",
            "Band A: FOIR 0.29999 just below 0.30",
            {"credit_score": 760, "monthly_net_income": 100000, "monthly_obligations": 29999},
        )
    )
    cases.append(
        make_case(
            "band_b_score_701",
            "Band B: score 701 just above 700",
            {"credit_score": 701, "monthly_net_income": 100000, "monthly_obligations": 35000},
        )
    )
    cases.append(
        make_case(
            "band_b_foir_39999",
            "Band B: FOIR 0.39999 just below 0.40",
            {"credit_score": 720, "monthly_net_income": 100000, "monthly_obligations": 39999},
        )
    )
    cases.append(
        make_case(
            "band_c_foir_49999",
            "Band C: FOIR 0.49999 just below 0.50",
            {"credit_score": 660, "monthly_net_income": 100000, "monthly_obligations": 49999},
        )
    )

    # Amount layer cases: A02, A03, A04
    cases.append(
        make_case(
            "a02_cap_tv2",
            "A02/A04: Capacity limit binding (TV2)",
            {
                "monthly_net_income": 40000,
                "monthly_obligations": 12000,
                "credit_score": 760,
                "requested_amount": 800000,
                "requested_tenure_months": 48,
            },
        )
    )
    cases.append(
        make_case(
            "a02_inc_tv3",
            "A02/A04: Income multiple limit binding (TV3)",
            {
                "monthly_net_income": 50000,
                "monthly_obligations": 0,
                "credit_score": 720,
                "requested_amount": 900000,
                "requested_tenure_months": 60,
            },
        )
    )
    cases.append(
        make_case(
            "a03_a_tv8",
            "A03: Recommended amount below 50,000 (TV8)",
            {
                "monthly_net_income": 15000,
                "monthly_obligations": 6500,
                "credit_score": 700,
                "requested_amount": 100000,
                "requested_tenure_months": 12,
            },
        )
    )
    cases.append(
        make_case(
            "a03_b_tv6",
            "A03: No EMI room at all (TV6)",
            {
                "monthly_net_income": 100000,
                "monthly_obligations": 50000,
                "credit_score": 650,
                "requested_amount": 300000,
                "requested_tenure_months": 24,
            },
        )
    )
    cases.append(
        make_case(
            "a04_777777",
            "A04: Request 777,777 (rec 775,000, shortfall 2,777 < 5,000, no A04)",
            {
                "requested_amount": 777777,
                "monthly_net_income": 150000,
                "monthly_obligations": 10000,
            },
        )
    )
    cases.append(
        make_case(
            "a04_379999",
            "A04: TV2 inputs, request 379,999 (rec 375,000, shortfall 4,999 < 5,000, no A04)",
            {
                "monthly_net_income": 40000,
                "monthly_obligations": 12000,
                "credit_score": 760,
                "requested_amount": 379999,
                "requested_tenure_months": 48,
            },
        )
    )
    cases.append(
        make_case(
            "a04_380000",
            "A04: TV2 inputs, request 380,000 (rec 375,000, shortfall exactly 5,000, A04 fires)",
            {
                "monthly_net_income": 40000,
                "monthly_obligations": 12000,
                "credit_score": 760,
                "requested_amount": 380000,
                "requested_tenure_months": 48,
            },
        )
    )
    cases.append(
        make_case(
            "a04_tie_request_income",
            "A04: Request equals 10 x income (500,000), capacity higher, no A04",
            {
                "monthly_net_income": 50000,
                "monthly_obligations": 0,
                "credit_score": 720,
                "requested_amount": 500000,
                "requested_tenure_months": 60,
            },
        )
    )

    # Multi-rule combinations
    cases.append(
        make_case(
            "x_multi_k03_k04_k05",
            "Multi-failure: severe delinquency, score 600, income 10,000",
            {
                "severe_delinquency_36m": True,
                "credit_score": 600,
                "monthly_net_income": 10000,
                "monthly_obligations": 0,
            },
        )
    )
    cases.append(
        make_case(
            "x_ref_inel_r02_k04",
            "Precedence: score 600 (inel) and 7 enquiries (refer) -> INELIGIBLE wins",
            {"credit_score": 600, "enquiries_6m": 7},
        )
    )
    cases.append(
        make_case(
            "x_refonly_r02_r03",
            "REFER only: 7 enquiries and employment other -> REFER",
            {"enquiries_6m": 7, "employment_type": "other"},
        )
    )
    cases.append(
        make_case(
            "x_inc_consent_v01_v02",
            "V01 + V02: Income missing and consent false -> INELIGIBLE wins",
            {"monthly_net_income": None, "consent_given": False},
        )
    )
    cases.append(
        make_case(
            "x_null_score_amt_tv2",
            "Null score on TV2 applicant: REFER, no derivation",
            {
                "monthly_net_income": 40000,
                "monthly_obligations": 12000,
                "credit_score": None,
                "requested_amount": 800000,
                "requested_tenure_months": 48,
            },
        )
    )

    # Missing each required field in turn (for V01)
    missing_fields_to_test = [
        ("age", "k01_age"),
        ("employment_type", "k06_r03_emptype"),
        ("employment_months", "k06_empmonths"),
        ("monthly_obligations", "e01_obligations"),
        ("enquiries_6m", "r02_enquiries"),
        ("severe_delinquency_36m", "k03_delinquency"),
        ("written_off", "k03_writtenoff"),
        ("kyc_verified", "k02_kyc"),
        ("requested_tenure_months", "v04_tenure"),
    ]
    for field_name, tag in missing_fields_to_test:
        cases.append(
            make_case(
                f"v01_missing_{field_name}", f"V01: {field_name} missing/null", {field_name: None}
            )
        )

    # Cap tie cases for F6
    # 1. Capacity limit ties with 10 x income (both 500,000, request 600,000) -> tie goes to capacity
    # To get P_EMI = 500,000: with band A (cap 0.55, rate 12%, tenure 24, monthly rate 0.01)
    # P_EMI = EMI_max * ((1.01^24 - 1)/(0.01 * 1.01^24)) = EMI_max * 21.243387...
    # We can craft capacity == income multiple by choosing income and obligations
    # Or test binding limit tie logic: income = 50,000 -> 10 x I = 500,000
    # 2. 10 x income ties with product maximum (income = 250,000, 10 x I = 2,500,000, request = 2,500,000)
    cases.append(
        make_case(
            "cap_tie_income_prodmax",
            "F6 tie: 10 x income (2,500,000) equals product maximum",
            {
                "monthly_net_income": 250000,
                "monthly_obligations": 10000,
                "credit_score": 760,
                "requested_amount": 2500000,
                "requested_tenure_months": 48,
            },
        )
    )
    cases.append(
        make_case(
            "cap_tie_capacity_prodmax",
            "F6 tie: capacity equals product maximum (2,500,000)",
            {
                "monthly_net_income": 300000,
                "monthly_obligations": 47000,
                "credit_score": 760,
                "requested_amount": 2500000,
                "requested_tenure_months": 48,
            },
        )
    )

    # Requests not multiples of 5,000
    cases.append(
        make_case(
            "req_not_mult_5000_54321",
            "Requested amount 54,321 not a multiple of 5,000",
            {"requested_amount": 54321},
        )
    )
    cases.append(
        make_case(
            "req_not_mult_5000_123456",
            "Requested amount 123,456 not a multiple of 5,000",
            {"requested_amount": 123456},
        )
    )
    cases.append(
        make_case(
            "req_not_mult_5000_999999",
            "Requested amount 999,999 not a multiple of 5,000",
            {"requested_amount": 999999},
        )
    )

    return cases


def generate_d1(output_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    cases = build_d1_cases()

    # Validate each case against input schema
    for c in cases:
        errors = validate_input(c["input"], SCHEMA_PATH)
        if errors:
            raise ValueError(f"D1 case '{c['case_id']}' failed schema validation: {errors}")

    dataset = {
        "version": 1,
        "cases": cases,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    return dataset


if __name__ == "__main__":
    ds = generate_d1()
    print(f"Generated D1 dataset with {len(ds['cases'])} cases into {OUTPUT_PATH}")
