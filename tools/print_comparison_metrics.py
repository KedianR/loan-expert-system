"""Print key metrics from comparison JSON files for the report."""

import json
from pathlib import Path

for fname in ["comparison_main.json", "comparison_f1.json", "comparison_f2.json"]:
    d = json.loads(Path("reports/ml", fname).read_text())
    print(f"=== {fname} ===")
    print(f"  subset: {d['subset']}")
    print(f"  rows: val={d['row_counts']['validation']}, test={d['row_counts']['test']}")

    ra = d["rule_system"]["treatment_A"]
    ci = ra["default_rate_among_approved_ci"]
    print(
        f"  Rule A: approval={ra['approval_rate']}, "
        f"def_rate={ra['default_rate_among_approved']}, "
        f"CI=[{ci['ci_lower']},{ci['ci_upper']}], n_app={ra['n_approved']}"
    )
    rb = d["rule_system"]["treatment_B"]
    ci_b = rb["default_rate_among_approved_ci"]
    print(
        f"  Rule B: approval={rb['approval_rate']}, "
        f"def_rate={rb['default_rate_among_approved']}, "
        f"CI=[{ci_b['ci_lower']},{ci_b['ci_upper']}], n_app={rb['n_approved']}, "
        f"n_excl_refer={rb.get('n_excluded_refer', 'N/A')}"
    )

    for model_key, label in [("logistic_regression", "LR"), ("gradient_boosting", "GB")]:
        m = d[model_key]
        op_m = m["operating_points"]["matched_approval_rate"]
        op_c = m["operating_points"]["cost_based_primary"]
        ci_m = op_m["default_rate_among_approved_ci"]
        ci_c = op_c["default_rate_among_approved_ci"]
        print(
            f"  {label} matched: approval={op_m['approval_rate']}, "
            f"def_rate={op_m['default_rate_among_approved']}, "
            f"CI=[{ci_m['ci_lower']},{ci_m['ci_upper']}], n_app={op_m['n_approved']}, "
            f"auc={m['test_auc']}"
        )
        print(
            f"  {label} cost:    approval={op_c['approval_rate']}, "
            f"def_rate={op_c['default_rate_among_approved']}, "
            f"CI=[{ci_c['ci_lower']},{ci_c['ci_upper']}], n_app={op_c['n_approved']}"
        )
    print()
