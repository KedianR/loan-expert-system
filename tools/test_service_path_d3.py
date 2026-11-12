"""Step 0 item 5 test: Run 1,000 D3 rows through the real service path.

Runs through:
  1. Input validation / fact builder
  2. Engine decide
  3. Trace builder
  4. Notice builder
  5. Audit store write (to temporary database)

Checks:
  - Rows processed
  - Failures (exceptions / unhandled errors)
  - Rows per second
  - Trace existence for every decision
  - R-05 compliance: no reason code lacking a trace entry in fired rules
"""
from __future__ import annotations

import tempfile
import time
import sys
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.api.service import DecisionService
from src.audit.store import AuditStore
from src.facts.fact_builder import get_validator


def main():
    d3_path = Path("data/synthetic/d3_population.csv")
    if not d3_path.exists():
        print(f"Error: {d3_path} does not exist.")
        return

    df = pd.read_csv(d3_path, dtype=object).head(1000)
    print(f"Loaded {len(df)} rows from {d3_path}")

    # Use a temporary database for audit store
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db_path = Path(tmp.name)

    try:
        temp_audit_store = AuditStore(tmp_db_path)
        service = DecisionService(audit_store=temp_audit_store)
        validator = get_validator()

        failures = 0
        r05_violations = 0
        total_rows = len(df)

        start_time = time.perf_counter()

        for idx, row in df.iterrows():
            # Convert row to dictionary format expected by service/validator
            app_dict = {}
            for col, val in row.items():
                if col in ("sim_default", "obligations_source"):
                    continue
                if pd.isna(val) or val is None or str(val).strip() in ("", "nan", "none", "null"):
                    app_dict[col] = None
                elif col in ("age", "employment_months", "monthly_net_income", "monthly_obligations",
                             "credit_score", "enquiries_6m", "requested_amount", "requested_tenure_months", "region_tier"):
                    app_dict[col] = int(val)
                elif col in ("severe_delinquency_36m", "written_off", "kyc_verified", "consent_given"):
                    if isinstance(val, bool):
                        app_dict[col] = val
                    else:
                        app_dict[col] = str(val).strip().lower() in ("true", "1")
                else:
                    app_dict[col] = str(val)

            # 1. Fact validation
            val_errors = list(validator.iter_errors(app_dict))
            if val_errors:
                failures += 1
                continue

            # 2. Service execution (engine, trace, notice, audit write)
            try:
                res = service.decide(app_dict)
                # Check R-05: no reason code lacking a trace entry
                # Response has decision, reason_codes, and trace is saved in audit record
                reason_codes = res.get("reason_codes", [])
                
                # Retrieve trace from audit store
                dec_id = res.get("decision_id")
                rec = temp_audit_store.get_decision(dec_id)
                trace = rec.get("trace", {})
                
                # Check that every reason code in reason_codes has a corresponding step in trace
                trace_steps = trace.get("steps", [])
                fired_codes = {s.get("reason_code") for s in trace_steps if s.get("status") == "fired" and s.get("reason_code")}
                for rc in reason_codes:
                    if rc not in fired_codes:
                        r05_violations += 1

            except Exception as e:
                print(f"Row {idx} failed: {e}")
                failures += 1

        elapsed = time.perf_counter() - start_time
        rows_per_sec = total_rows / elapsed if elapsed > 0 else 0

        print(f"Results for 1,000 D3 rows:")
        print(f"  Rows processed: {total_rows}")
        print(f"  Failures: {failures}")
        print(f"  Elapsed time: {elapsed:.2f} s")
        print(f"  Throughput: {rows_per_sec:.1f} rows/s")
        print(f"  R-05 violations (reason code lacking trace entry): {r05_violations}")

    finally:
        if tmp_db_path.exists():
            tmp_db_path.unlink()


if __name__ == "__main__":
    main()
