"""Dataset splitting module for D2 and D3.

Implements: WP-17, FR-21, DR-04, DR-05.
Spec: docs/ml-baseline-spec.md §2, docs/experiment-protocol.md §1, 2.
Splits: 70% train, 15% validation, 15% test, stratified on the binary label.
"""

from __future__ import annotations

import argparse
import hashlib
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def derive_seed(master: int, name: str) -> int:
    """FR-21: deterministic per-name seed from master seed."""
    return int(hashlib.sha256(f"{master}:{name}".encode()).hexdigest(), 16) % (2**32)


def make_splits(
    dataset: str,
    input_csv_path: Path | str,
    output_csv_path: Path | str,
    exp_cfg: dict,
    decisions_csv_path: Path | str | None = None,
) -> pd.DataFrame:
    """Create 70/15/15 stratified train/val/test split and write split CSV."""
    master_seed = int(exp_cfg["seeds"]["master"])
    seed = derive_seed(master_seed, f"split_{dataset}")

    input_df = pd.read_csv(input_csv_path, dtype=str)

    if dataset == "d2":
        # Stratify on TARGET column in D2
        if "TARGET" not in input_df.columns:
            raise KeyError("TARGET column missing in D2 mapped data")
        y = input_df["TARGET"].astype(int)
    elif dataset == "d3":
        # Stratify on binary decision (eligible=1 vs not=0)
        dec_path = (
            Path(decisions_csv_path)
            if decisions_csv_path
            else Path("data/decisions/d3_decisions.csv")
        )
        dec_df = pd.read_csv(dec_path, dtype=str)
        merged = pd.merge(
            input_df[["applicant_id"]], dec_df[["applicant_id", "decision"]], on="applicant_id"
        )
        y = (merged["decision"] == "eligible").astype(int)
    else:
        raise ValueError(f"Unknown dataset: {dataset}")

    # First split: train (70%) vs temp (30%)
    train_idx, temp_idx = train_test_split(
        np.arange(len(input_df)),
        test_size=0.30,
        random_state=seed,
        stratify=y,
    )

    # Second split: validation (15% total) vs test (15% total) -> 50/50 of temp
    y_temp = y.iloc[temp_idx]
    val_sub_idx, test_sub_idx = train_test_split(
        np.arange(len(temp_idx)),
        test_size=0.50,
        random_state=seed,
        stratify=y_temp,
    )
    val_idx = temp_idx[val_sub_idx]
    test_idx = temp_idx[test_sub_idx]

    split_series = pd.Series(index=input_df.index, dtype="string")
    split_series.iloc[train_idx] = "train"
    split_series.iloc[val_idx] = "validation"
    split_series.iloc[test_idx] = "test"

    out_df = pd.DataFrame(
        {
            "applicant_id": input_df["applicant_id"],
            "split": split_series,
        }
    )

    out_p = Path(output_csv_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_p, index=False, lineterminator="\n")

    digest = hashlib.sha256(out_p.read_bytes()).hexdigest()
    print(f"Created split {dataset}: {out_p} (SHA-256: {digest})")
    print(f"Counts: {dict(out_df['split'].value_counts())}")

    return out_df


def main() -> None:
    """CLI to split datasets."""
    parser = argparse.ArgumentParser(description="Create train/val/test splits.")
    parser.add_argument("--dataset", choices=["d2", "d3", "all"], default="all")
    args = parser.parse_args()

    with open("config/experiment.toml", "rb") as fh:
        exp_cfg = tomllib.load(fh)

    if args.dataset in ("d2", "all"):
        make_splits(
            dataset="d2",
            input_csv_path=Path(exp_cfg["d2"]["mapped_path"]),
            output_csv_path=Path("data/splits/d2_split.csv"),
            exp_cfg=exp_cfg,
        )

    if args.dataset in ("d3", "all"):
        make_splits(
            dataset="d3",
            input_csv_path=Path(exp_cfg["d3"]["mapped_path"]),
            output_csv_path=Path("data/splits/d3_split.csv"),
            exp_cfg=exp_cfg,
            decisions_csv_path=Path("data/decisions/d3_decisions.csv"),
        )


if __name__ == "__main__":
    main()
