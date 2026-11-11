"""Batch decision runner for expert system evaluation.

Implements: WP-15, WP-16b, WP-17, docs/08-datasets.md §5, docs/ml-baseline-spec.md §1, 6.
Calls engine directly without audit store, notice builder, or trace builder.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tomllib
from pathlib import Path
from typing import Any

import pandas as pd

from src.engine.engine import decide as engine_decide
from src.engine.rule_loader import load_rules
from src.engine.ruleset_hash import compute_hash_from_root


def _parse_bool_or_none(val: Any) -> bool | None:
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip().lower()
    if s in ("true", "1", "1.0"):
        return True
    if s in ("false", "0", "0.0"):
        return False
    return None


def _parse_int_or_none(val: Any) -> int | None:
    if pd.isna(val) or val is None or str(val).strip() in ("", "nan", "none", "null"):
        return None
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return None


def _parse_str_or_none(val: Any) -> str | None:
    if pd.isna(val) or val is None or str(val).strip() in ("", "nan", "none", "null"):
        return None
    return str(val).strip()


def run_batch_decisions(
    dataset_name: str,
    input_csv_path: Path | str,
    decisions_csv_path: Path | str,
    split_csv_path: Path | str | None = None,
    allowed_splits: list[str] | None = None,
    repo_root: Path | str = ".",
) -> dict[str, Any]:
    """Run engine directly on batch of rows."""
    root = Path(repo_root)
    input_path = Path(input_csv_path)
    output_path = Path(decisions_csv_path)

    rules_dir = root / "rules"
    params_path = root / "params" / "params.toml"
    rule_set = load_rules(rules_dir, params_path)
    if rule_set is None:
        raise RuntimeError("Failed to load rule set")

    rule_set_hash = compute_hash_from_root(root)
    rule_set_tag = f"rules-{rule_set.manifest.rules_version}+params-{rule_set.params.get('params_version', '0.1.0')}"

    print(f"Reading input dataset: {input_path} ...", file=sys.stderr)
    df = pd.read_csv(input_path, dtype=str)

    if allowed_splits is not None and split_csv_path is not None:
        split_p = Path(split_csv_path)
        if not split_p.exists():
            raise FileNotFoundError(f"Split file not found: {split_p}")
        split_df = pd.read_csv(split_p, dtype=str)
        # Filter df to applicants in allowed splits
        valid_ids = set(split_df[split_df["split"].isin(allowed_splits)]["applicant_id"])
        df = df[df["applicant_id"].isin(valid_ids)].copy()
        print(
            f"Filtered to {len(df)} applicants in splits: {allowed_splits}",
            file=sys.stderr,
        )

    t0 = time.time()
    rows: list[dict[str, Any]] = []

    for _, r in df.iterrows():
        app_id = str(r["applicant_id"]).strip()
        body: dict[str, Any] = {
            "applicant_id": app_id,
            "age": _parse_int_or_none(r.get("age")),
            "employment_type": _parse_str_or_none(r.get("employment_type")),
            "employment_months": _parse_int_or_none(r.get("employment_months")),
            "monthly_net_income": _parse_int_or_none(r.get("monthly_net_income")),
            "monthly_obligations": _parse_int_or_none(r.get("monthly_obligations")),
            "credit_score": _parse_int_or_none(r.get("credit_score")),
            "enquiries_6m": _parse_int_or_none(r.get("enquiries_6m")),
            "severe_delinquency_36m": _parse_bool_or_none(r.get("severe_delinquency_36m")),
            "written_off": _parse_bool_or_none(r.get("written_off")),
            "kyc_verified": _parse_bool_or_none(r.get("kyc_verified")),
            "consent_given": _parse_bool_or_none(r.get("consent_given")),
            "requested_amount": _parse_int_or_none(r.get("requested_amount")),
            "requested_tenure_months": _parse_int_or_none(r.get("requested_tenure_months")),
            "region_tier": _parse_int_or_none(r.get("region_tier")),
        }

        res = engine_decide(body, rule_set)
        decision = res["decision"]
        reason_codes = ";".join(res.get("reason_codes", []))
        rec_amt = (
            res.get("derived", {}).get("recommended_amount") if decision == "eligible" else None
        )
        band = res.get("derived", {}).get("band") if decision == "eligible" else None

        rows.append(
            {
                "applicant_id": app_id,
                "decision": decision,
                "reason_codes": reason_codes,
                "recommended_amount": rec_amt,
                "band": band,
            }
        )

    elapsed = time.time() - t0
    n_rows = len(rows)
    rps = n_rows / elapsed if elapsed > 0 else 0.0

    print(
        f"Evaluated {n_rows} rows for {dataset_name} in {elapsed:.2f}s ({rps:.1f} rows/s)",
        file=sys.stderr,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df = pd.DataFrame(rows)
    out_df.to_csv(output_path, index=False, lineterminator="\n")

    meta = {
        "dataset": dataset_name,
        "n_rows": n_rows,
        "elapsed_seconds": round(elapsed, 4),
        "rows_per_second": round(rps, 2),
        "rule_set_tag": rule_set_tag,
        "rule_set_hash": rule_set_hash,
    }
    meta_path = Path(f"{output_path}.meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    import hashlib

    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    print(f"SHA-256 {output_path}: {digest}")

    return meta


def main() -> None:
    """CLI for batch decision runner."""
    parser = argparse.ArgumentParser(description="Batch decision runner.")
    parser.add_argument(
        "--dataset",
        required=True,
        choices=["d2", "d3"],
        help="Dataset name (d2 or d3).",
    )
    parser.add_argument("--repo-root", default=".", help="Project repo root.")
    args = parser.parse_args()

    with open("config/experiment.toml", "rb") as fh:
        exp_cfg = tomllib.load(fh)

    out_dir = Path(exp_cfg["decisions"]["output_dir"])

    if args.dataset == "d3":
        input_csv = Path(exp_cfg["d3"]["mapped_path"])
        out_csv = out_dir / "d3_decisions.csv"
        run_batch_decisions(
            dataset_name="d3",
            input_csv_path=input_csv,
            decisions_csv_path=out_csv,
            repo_root=args.repo_root,
        )
    elif args.dataset == "d2":
        input_csv = Path(exp_cfg["d2"]["mapped_path"])
        out_csv = out_dir / "d2_decisions.csv"
        split_csv = Path("data/splits/d2_split.csv")
        allowed_splits = exp_cfg["decisions"]["d2_splits"]
        run_batch_decisions(
            dataset_name="d2",
            input_csv_path=input_csv,
            decisions_csv_path=out_csv,
            split_csv_path=split_csv,
            allowed_splits=allowed_splits,
            repo_root=args.repo_root,
        )


if __name__ == "__main__":
    main()
