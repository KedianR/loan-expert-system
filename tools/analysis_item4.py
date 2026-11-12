"""Item 4 analysis: unknown facts among D2 eligible decisions."""

import pandas as pd

d2_dec = pd.read_csv("data/decisions/d2_decisions.csv", dtype=str)
d2_split = pd.read_csv("data/splits/d2_split.csv", dtype=str)
d2_map = pd.read_csv("data/mapped/d2_mapped.csv", dtype=str)

# Merge split info
d2 = pd.merge(d2_dec, d2_split[["applicant_id", "split"]], on="applicant_id")
d2_eval = d2[d2["split"].isin(["validation", "test"])].copy()

# Merge with mapped data flags
d2_map_eval = pd.merge(
    d2_eval[["applicant_id", "decision"]],
    d2_map[
        [
            "applicant_id",
            "severe_delinquency_36m_flag",
            "employment_months_flag",
        ]
    ],
    on="applicant_id",
)

# Eligible decisions
eligible = d2_map_eval[d2_map_eval["decision"] == "eligible"]
print(f"Eligible decisions (val+test): {len(eligible)}")
n_deliq_unk = (eligible["severe_delinquency_36m_flag"] == "unknown").sum()
n_emp_unk = (eligible["employment_months_flag"] == "unknown").sum()
n_either_unk = (
    (eligible["severe_delinquency_36m_flag"] == "unknown")
    | (eligible["employment_months_flag"] == "unknown")
).sum()
print(f"  severe_delinquency_36m unknown: {n_deliq_unk}")
print(f"  employment_months unknown: {n_emp_unk}")
print(f"  either unknown: {n_either_unk}")

# Decision share by severe_delinquency_36m unknown vs known
print()
print("Decision share by severe_delinquency_36m unknown (all evaluated rows):")
d2_map_eval["deliq_unknown"] = d2_map_eval["severe_delinquency_36m_flag"] == "unknown"
counts = d2_map_eval.groupby("deliq_unknown")["decision"].value_counts()
pcts = d2_map_eval.groupby("deliq_unknown")["decision"].value_counts(normalize=True).round(4)
print("Counts:")
print(counts.to_string())
print()
print("Shares:")
print(pcts.to_string())
