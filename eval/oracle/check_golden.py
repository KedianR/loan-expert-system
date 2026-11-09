"""Self-check script to verify oracle against golden test vectors TV1 to TV9."""

import json
import sys
import tomllib
from decimal import Decimal
from pathlib import Path

from eval.oracle.oracle import evaluate


def load_params() -> dict:
    params_path = Path("params/params.toml")
    with open(params_path, "rb") as f:
        return tomllib.load(f)


def load_vectors() -> dict:
    vectors_path = Path("tests/golden/vectors.json")
    with open(vectors_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_checks() -> bool:
    params = load_params()
    vectors_data = load_vectors()
    vectors = vectors_data["vectors"]
    apr_tol = Decimal(str(vectors_data.get("apr_tolerance", "0.01")))

    all_passed = True
    rows = []

    for vec in vectors:
        v_id = vec["id"]
        inp = vec["input"]
        exp = vec["expected"]

        res = evaluate(inp, params)

        checks = []

        # 1. Decision
        dec_ok = (res["decision"] == exp["decision"])
        checks.append(("Decision", dec_ok, res["decision"], exp["decision"]))

        # 2. Reason codes
        rc_ok = (res["reason_codes"] == exp["reason_codes"])
        checks.append(("Reason Codes", rc_ok, res["reason_codes"], exp["reason_codes"]))

        # 3. Existing FOIR
        if "existing_foir" in exp:
            foir_ok = (res["existing_foir"] == exp["existing_foir"])
            checks.append(("Existing FOIR", foir_ok, res["existing_foir"], exp["existing_foir"]))

        # 4. Rules must fire
        for r in exp.get("rules_must_fire", []):
            fired = r in res["all_fired_rules"]
            checks.append((f"Fired {r}", fired, fired, True))

        # 5. Rules must not fire
        for r in exp.get("rules_must_not_fire", []):
            not_fired = r not in res["all_fired_rules"]
            checks.append((f"Not Fired {r}", not_fired, not not_fired, False))

        # 6. Band
        if "band" in exp:
            band_ok = (res["band"] == exp["band"])
            checks.append(("Band", band_ok, res["band"], exp["band"]))

        # 7. Binding limit
        if "binding_limit" in exp:
            bl_ok = (res["binding_limit"] == exp["binding_limit"])
            checks.append(("Binding Limit", bl_ok, res["binding_limit"], exp["binding_limit"]))

        # 8. Offer
        if exp["offer"] is None:
            off_ok = (res["offer"] is None)
            checks.append(("Offer is None", off_ok, res["offer"] is None, True))
        else:
            exp_off = exp["offer"]
            res_off = res["offer"]
            if res_off is None:
                checks.append(("Offer exists", False, None, "Expected dict"))
            else:
                checks.append(("Offer Amount", res_off["amount"] == exp_off["amount"], res_off["amount"], exp_off["amount"]))
                checks.append(("Offer Tenure", res_off["tenure_months"] == exp_off["tenure_months"], res_off["tenure_months"], exp_off["tenure_months"]))
                checks.append(("Offer Rate", res_off["indicative_rate"] == exp_off["indicative_rate"], res_off["indicative_rate"], exp_off["indicative_rate"]))
                checks.append(("Offer EMI", res_off["emi"] == exp_off["emi"], res_off["emi"], exp_off["emi"]))
                checks.append(("Offer Fee", res_off["fee"] == exp_off["fee"], res_off["fee"], exp_off["fee"]))
                checks.append(("Offer Total Interest", res_off["total_interest"] == exp_off["total_interest"], res_off["total_interest"], exp_off["total_interest"]))
                checks.append(("Offer Post FOIR", res_off["post_loan_foir"] == exp_off["post_loan_foir"], res_off["post_loan_foir"], exp_off["post_loan_foir"]))

                # APR tolerance
                apr_res = Decimal(str(res_off["apr"]))
                apr_exp = Decimal(str(exp_off["apr"]))
                apr_diff = abs(apr_res - apr_exp)
                apr_ok = apr_diff <= apr_tol
                checks.append(("Offer APR", apr_ok, str(apr_res), f"{apr_exp} (+/- {apr_tol})"))

        vec_passed = all(c[1] for c in checks)
        if not vec_passed:
            all_passed = False

        status = "PASS" if vec_passed else "FAIL"
        rows.append((v_id, status, checks))

    # Print summary table
    print(f"{'Vector':<8} | {'Status':<6} | {'Details'}")
    print("-" * 70)
    for v_id, status, checks in rows:
        failed = [f"{c[0]} (got {c[2]}, exp {c[3]})" for c in checks if not c[1]]
        if failed:
            detail = "; ".join(failed)
        else:
            detail = "All checks passed"
        print(f"{v_id:<8} | {status:<6} | {detail}")

    print("-" * 70)
    overall = "ALL VECTORS PASSED" if all_passed else "SOME VECTORS FAILED"
    print(f"Result: {overall}")
    return all_passed


if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)

