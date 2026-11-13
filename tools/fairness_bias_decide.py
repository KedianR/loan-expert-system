"""Pre-compute engine decisions on the bias large dataset for fast test reuse (WP-20).

Runs the engine over data/synthetic/d3_bias_large.csv (100k rows) and writes
data/decisions/d3_bias_large_decisions.csv.

This avoids re-running 100k rows in every pytest invocation.

Usage: make fairness-bias-decide
       python tools/fairness_bias_decide.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.engine.engine import decide as engine_decide  # noqa: E402
from src.engine.rule_loader import load_rules  # noqa: E402

BIAS_POP = REPO_ROOT / "data" / "synthetic" / "d3_bias_large.csv"
OUTPUT = REPO_ROOT / "data" / "decisions" / "d3_bias_large_decisions.csv"


def main() -> None:
    if not BIAS_POP.exists():
        print(f"Bias population not found: {BIAS_POP}")
        print("Run: make data-d3-bias-large")
        sys.exit(1)

    print(f"Loading {BIAS_POP} ...")
    pop = pd.read_csv(BIAS_POP)
    print(f"  {len(pop)} rows")

    rules = load_rules(REPO_ROOT / "rules", REPO_ROOT / "params" / "params.toml")

    decisions = []
    start = time.time()
    for i, (_, row) in enumerate(pop.iterrows()):
        inp = {
            "applicant_id": str(row["applicant_id"]),
            "age": int(row["age"]),
            "employment_type": str(row["employment_type"]),
            "employment_months": int(row["employment_months"]),
            "monthly_net_income": int(row["monthly_net_income"]),
            "monthly_obligations": int(row["monthly_obligations"]),
            "credit_score": float(row["credit_score"])
            if pd.notna(row.get("credit_score"))
            else None,
            "enquiries_6m": int(row["enquiries_6m"]),
            "severe_delinquency_36m": bool(row.get("severe_delinquency_36m", False)),
            "written_off": bool(row.get("written_off", False)),
            "kyc_verified": bool(row.get("kyc_verified", True)),
            "consent_given": bool(row.get("consent_given", True)),
            "requested_amount": int(row["requested_amount"]),
            "requested_tenure_months": int(row["requested_tenure_months"]),
        }
        try:
            res = engine_decide(inp, rules)
            dec = res.get("decision", "error") if isinstance(res, dict) else "error"
        except Exception:
            dec = "error"
        decisions.append(dec)
        if (i + 1) % 10000 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            print(f"  {i + 1}/{len(pop)} rows ({rate:.1f} rows/s)")

    out_df = pop[["applicant_id"]].copy()
    out_df["decision"] = decisions
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUTPUT, index=False)
    elapsed = time.time() - start
    rate = len(pop) / elapsed
    print(f"Written {len(out_df)} decisions to {OUTPUT}")
    print(f"Rate: {rate:.1f} rows/s")
    counts = pd.Series(decisions).value_counts()
    print(counts.to_string())


if __name__ == "__main__":
    main()
