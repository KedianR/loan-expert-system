"""Group-size tables for fairness evaluation preparation.

Implements: WP-17, D-06, docs/experiment-protocol.md §5.
Counts applicants per group on full set and test split.
Marks groups < 100 as "too_small".

HARD RULE:
- Does NOT compute any outcome metric by group (no approval rate, no default rate, no score).
- Does NOT read decisions, TARGET, or any label column.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd


def compute_group_sizes(
    dataset_name: str,
    protected_csv_path: Path | str,
    mapped_csv_path: Path | str,
    split_csv_path: Path | str,
    output_csv_path: Path | str,
    min_group_size: int = 100,
) -> pd.DataFrame:
    """Build group-size table for full set and test split."""
    prot_df = pd.read_csv(protected_csv_path, dtype=str)
    mapped_df = pd.read_csv(mapped_csv_path, dtype=str)
    split_df = pd.read_csv(split_csv_path, dtype=str)

    # Merge on applicant_id ONLY needed demographic/proxy columns
    # We DO NOT merge TARGET or decision
    cols_to_use = ["applicant_id"]
    for col in ("employment_type", "monthly_net_income"):
        if col in mapped_df.columns:
            cols_to_use.append(col)

    merged = pd.merge(prot_df, mapped_df[cols_to_use], on="applicant_id")
    merged = pd.merge(merged, split_df[["applicant_id", "split"]], on="applicant_id")

    # Compute income quartiles on the train split only (docs/experiment-protocol.md §5)
    train_incomes = pd.to_numeric(
        merged.loc[merged["split"] == "train", "monthly_net_income"],
        errors="coerce",
    ).dropna()
    q25, q50, q75 = train_incomes.quantile([0.25, 0.50, 0.75])

    def _income_band(v: Any) -> str:
        try:
            val = float(v)
            if val <= q25:
                return "Q1_low"
            if val <= q50:
                return "Q2_med_low"
            if val <= q75:
                return "Q3_med_high"
            return "Q4_high"
        except (ValueError, TypeError):
            return "unknown"

    merged["income_band"] = merged["monthly_net_income"].apply(_income_band)

    # Determine group attributes to count
    ignore_cols = {"applicant_id", "split", "monthly_net_income"}
    attr_cols = [c for c in merged.columns if c not in ignore_cols]

    rows: list[dict[str, Any]] = []

    test_df = merged[merged["split"] == "test"]

    for attr in attr_cols:
        unique_vals = sorted([str(x) for x in merged[attr].dropna().unique()])
        for val in unique_vals:
            count_full = int((merged[attr] == val).sum())
            count_test = int((test_df[attr] == val).sum())
            too_small_full = count_full < min_group_size
            too_small_test = count_test < min_group_size

            rows.append(
                {
                    "dataset": dataset_name,
                    "attribute": attr,
                    "group_value": val,
                    "count_full": count_full,
                    "too_small_full": too_small_full,
                    "count_test": count_test,
                    "too_small_test": too_small_test,
                }
            )

    out_df = pd.DataFrame(rows)
    out_p = Path(output_csv_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_p, index=False, lineterminator="\n")

    print(f"Group sizes for {dataset_name} written to {out_p}:")
    n_small = (out_df["too_small_test"]).sum()
    print(f"  Total groups evaluated: {len(out_df)}, Groups < {min_group_size} on test: {n_small}")

    return out_df


def main() -> None:
    """CLI for building group size tables."""
    parser = argparse.ArgumentParser(description="Build group size tables.")
    parser.add_argument("--dataset", choices=["d2", "d3", "all"], default="all")
    args = parser.parse_args()

    out_dir = Path("data/group_sizes")

    if args.dataset in ("d2", "all"):
        compute_group_sizes(
            dataset_name="d2",
            protected_csv_path="data/protected/d2_protected.csv",
            mapped_csv_path="data/mapped/d2_mapped.csv",
            split_csv_path="data/splits/d2_split.csv",
            output_csv_path=out_dir / "d2_group_sizes.csv",
        )

    if args.dataset in ("d3", "all"):
        compute_group_sizes(
            dataset_name="d3",
            protected_csv_path="data/protected/d3_protected.csv",
            mapped_csv_path="data/synthetic/d3_population.csv",
            split_csv_path="data/splits/d3_split.csv",
            output_csv_path=out_dir / "d3_group_sizes.csv",
        )


if __name__ == "__main__":
    main()
