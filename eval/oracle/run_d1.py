"""Run D1 cases through the reference oracle and produce oracle_expected.json."""

import json
import tomllib
from pathlib import Path

from eval.oracle.oracle import evaluate


def load_params() -> dict:
    params_path = Path("params/params.toml")
    with open(params_path, "rb") as f:
        return tomllib.load(f)


def run_d1() -> int:
    params = load_params()
    d1_path = Path("data/d1/d1_cases.json")
    with open(d1_path, "r", encoding="utf-8") as f:
        d1_data = json.load(f)

    cases = d1_data["cases"]
    results = {}

    for c in cases:
        case_id = c["case_id"]
        inp = c["input"]
        eval_res = evaluate(inp, params)

        entry = {
            "decision": eval_res["decision"],
            "reason_codes": eval_res["reason_codes"],
            "fired_rules": eval_res["fired_rules"],
            "band": eval_res["band"],
            "recommended_amount": eval_res["recommended_amount"],
            "binding_limit": eval_res["binding_limit"],
            "indicative_rate": eval_res["indicative_rate"],
            "emi": eval_res["emi"],
            "fee": eval_res["fee"],
            "total_interest": eval_res["total_interest"],
            "apr": eval_res["apr"],
            "post_loan_foir": eval_res["post_loan_foir"],
        }
        results[case_id] = entry

    output_data = {
        "version": 1,
        "cases": results,
    }

    out_path = Path("data/d1/oracle_expected.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Processed {len(cases)} cases from {d1_path}")
    print(f"Wrote oracle expected results to {out_path}")
    return len(cases)


if __name__ == "__main__":
    run_d1()
