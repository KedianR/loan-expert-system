"""Filtered-subset comparison for Phase 4 close-out (item 9, owner answered B).

Applies to the D2 validation and test rows that already have decisions.
No retraining — uses the fitted models from make baseline.

Subsets:
  F1 = rows where none of V03 (AMOUNT_OUTSIDE_PRODUCT_LIMITS),
       V04 (TENURE_OUTSIDE_PRODUCT_LIMITS), K05 (INCOME_BELOW_MINIMUM) fired.
  F2 = F1 AND K04 (CREDIT_SCORE_BELOW_MINIMUM) did not fire.

For each subset:
  - Operating points chosen on the filtered validation rows
    (matched approval rate to rule system Treatment A on those rows,
     and cost-based at primary ratio = 5).
  - Metrics on filtered test rows for:
      rule system Treatment A (refer = not approved)
      rule system Treatment B (refer rows excluded from denominator)
      Logistic Regression (matched and cost-based)
      HistGradientBoosting (matched and cost-based)
  - Bootstrap 95% CI for default rate among approved (1,000 resamples,
    seed derived from "bootstrap", resample test applicants).

Outputs (all labelled "filtered subset"):
  reports/ml/comparison_main.json
  reports/ml/comparison_f1.json
  reports/ml/comparison_f2.json

These are identical across two runs (fixed seeds, no randomness beyond bootstrap).

NOTE: filtering on rule outcomes mechanically raises the rule system's approval
rate — rows that the rule system ineligible/referred for V03, V04, K05 are
removed, leaving a higher share of eligible decisions.  This is stated plainly
in every output.

Implements: docs/experiment-protocol.md section 8, decisions P4-11, P4-12.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.ml.features import load_ml_config, prepare_dataframe

# Reason codes for each filter dimension
_CODES_V03 = "AMOUNT_OUTSIDE_PRODUCT_LIMITS"
_CODES_V04 = "TENURE_OUTSIDE_PRODUCT_LIMITS"
_CODES_K05 = "INCOME_BELOW_MINIMUM"
_CODES_K04 = "CREDIT_SCORE_BELOW_MINIMUM"

_F1_EXCLUDE = frozenset([_CODES_V03, _CODES_V04, _CODES_K05])
_F2_EXCLUDE = frozenset([_CODES_V03, _CODES_V04, _CODES_K05, _CODES_K04])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def derive_seed(master: int, name: str) -> int:
    """Deterministic per-name seed from master seed (FR-21)."""
    return int(hashlib.sha256(f"{master}:{name}".encode()).hexdigest(), 16) % (2**32)


def file_sha256(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _has_code(codes_str: str, code: str) -> bool:
    if not codes_str or codes_str != codes_str:  # nan check
        return False
    return code in codes_str.split(";")


def _filter_mask(decisions: pd.DataFrame, exclude_codes: frozenset[str]) -> pd.Series:
    """Return boolean mask of rows where NONE of exclude_codes fired."""
    codes_series = decisions["reason_codes"].fillna("")
    fired = pd.Series(False, index=decisions.index)
    for code in exclude_codes:
        fired = fired | codes_series.str.contains(code, regex=False)
    return ~fired


def _bootstrap_ci(
    approved_mask: np.ndarray,
    y: np.ndarray,
    rng: np.random.Generator,
    n_resamples: int,
    ci: float,
) -> dict[str, float]:
    """Bootstrap CI for default rate among approved.

    Resamples test applicants (rows) with replacement.
    Returns point estimate and [lower, upper] bounds.
    """
    n = len(y)
    n_app = int(approved_mask.sum())
    point = float(y[approved_mask].mean()) if n_app > 0 else float("nan")

    boot_rates = []
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        b_approved = approved_mask[idx]
        b_y = y[idx]
        b_n = int(b_approved.sum())
        boot_rates.append(float(b_y[b_approved].mean()) if b_n > 0 else float("nan"))

    boot_arr = np.array([r for r in boot_rates if not np.isnan(r)])
    alpha = 1.0 - ci
    lower = float(np.percentile(boot_arr, 100 * alpha / 2)) if len(boot_arr) else float("nan")
    upper = float(np.percentile(boot_arr, 100 * (1 - alpha / 2))) if len(boot_arr) else float("nan")
    return {
        "point": round(point, 4),
        "ci_lower": round(lower, 4),
        "ci_upper": round(upper, 4),
        "ci_level": ci,
        "n_resamples": n_resamples,
        "n_approved": n_app,
    }


def _eval_ml_on_subset(
    model_name: str,
    pipeline: Any,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    val_decisions: pd.DataFrame,
    test_decisions: pd.DataFrame,
    y_val: np.ndarray,
    y_test: np.ndarray,
    cost_ratios: list[int],
    primary_ratio: int,
    bootstrap_rng: np.random.Generator,
    n_resamples: int,
    ci_level: float,
) -> dict[str, Any]:
    """Evaluate one ML model on a filtered subset (no retraining)."""
    val_proba = pipeline.predict_proba(val_df)[:, 1]
    test_proba = pipeline.predict_proba(test_df)[:, 1]

    # --- Operating point 1: matched approval rate ---
    # Approval rate of rule system Treatment A on the filtered VALIDATION rows
    rule_val_approved_A = (val_decisions["decision"] == "eligible").values
    target_rate_A = float(rule_val_approved_A.mean())
    tau_matched = float(np.quantile(val_proba, target_rate_A))

    # --- Operating point 2: cost-based on filtered VALIDATION rows ---
    grid = np.linspace(float(np.min(val_proba)), float(np.max(val_proba)), 200)
    best_tau_cost = float(grid[0])
    min_cost = float("inf")
    for t in grid:
        approved = val_proba <= t
        fa = int(((approved) & (y_val == 1)).sum())
        fd = int(((~approved) & (y_val == 0)).sum())
        c = primary_ratio * fa + fd
        if c < min_cost:
            min_cost = c
            best_tau_cost = float(t)

    def _eval(threshold: float) -> dict[str, Any]:
        approved = test_proba <= threshold
        n_app = int(approved.sum())
        def_rate = float(y_test[approved].mean()) if n_app > 0 else 0.0
        pred_pos = ~approved
        tn, fp, fn, tp = [int(v) for v in confusion_matrix(y_test, pred_pos, labels=[0, 1]).ravel()]
        prec = float(precision_score(y_test, pred_pos, zero_division=0))
        rec = float(recall_score(y_test, pred_pos, zero_division=0))
        f1 = float(f1_score(y_test, pred_pos, zero_division=0))
        cost_dict: dict[str, float] = {}
        for r in cost_ratios:
            fa = int(((approved) & (y_test == 1)).sum())
            fd = int(((~approved) & (y_test == 0)).sum())
            cost_dict[f"cost_{r}"] = round(float((r * fa + fd) / len(y_test)), 4)
        ci_dict = _bootstrap_ci(approved, y_test, bootstrap_rng, n_resamples, ci_level)
        return {
            "threshold": round(threshold, 4),
            "approval_rate": round(float(approved.mean()), 4),
            "n_approved": n_app,
            "default_rate_among_approved": round(def_rate, 4),
            "default_rate_among_approved_ci": ci_dict,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "confusion": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
            "cost_per_applicant": cost_dict,
        }

    matched_op = _eval(tau_matched)
    matched_op["target_approval_rate"] = round(target_rate_A, 4)
    cost_op = _eval(best_tau_cost)
    cost_op["primary_cost_ratio"] = primary_ratio

    test_auc = (
        float(roc_auc_score(y_test, test_proba)) if len(np.unique(y_test)) > 1 else float("nan")
    )
    test_brier = float(brier_score_loss(y_test, test_proba))

    return {
        "model": model_name,
        "note": "No retraining. Fitted on full D2 training set. Applied to filtered subset.",
        "test_auc": round(test_auc, 4),
        "test_brier": round(test_brier, 4),
        "operating_points": {
            "matched_approval_rate": matched_op,
            "cost_based_primary": cost_op,
        },
    }


def _eval_rule_on_subset(
    test_decisions: pd.DataFrame,
    y_test: np.ndarray,
    cost_ratios: list[int],
    bootstrap_rng: np.random.Generator,
    n_resamples: int,
    ci_level: float,
) -> dict[str, Any]:
    """Evaluate rule system (Treatments A and B) on a filtered subset."""

    def _rule_metrics(approved_mask: np.ndarray, y: np.ndarray, description: str) -> dict[str, Any]:
        n_app = int(approved_mask.sum())
        def_rate = float(y[approved_mask].mean()) if n_app > 0 else 0.0
        pred_pos = ~approved_mask
        tn, fp, fn, tp = [int(v) for v in confusion_matrix(y, pred_pos, labels=[0, 1]).ravel()]
        prec = float(precision_score(y, pred_pos, zero_division=0))
        rec = float(recall_score(y, pred_pos, zero_division=0))
        f1 = float(f1_score(y, pred_pos, zero_division=0))
        cost_dict: dict[str, float] = {}
        for r in cost_ratios:
            fa = int(((approved_mask) & (y == 1)).sum())
            fd = int(((~approved_mask) & (y == 0)).sum())
            cost_dict[f"cost_{r}"] = round(float((r * fa + fd) / len(y)), 4)
        ci_dict = _bootstrap_ci(approved_mask, y, bootstrap_rng, n_resamples, ci_level)
        return {
            "description": description,
            "approval_rate": round(float(approved_mask.mean()), 4),
            "n_approved": n_app,
            "default_rate_among_approved": round(def_rate, 4),
            "default_rate_among_approved_ci": ci_dict,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "confusion": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
            "cost_per_applicant": cost_dict,
        }

    # Treatment A: refer = not approved
    rule_A = (test_decisions["decision"] == "eligible").values
    metrics_A = _rule_metrics(rule_A, y_test, "refer counts as not approved (Treatment A)")

    # Treatment B: refer rows excluded from denominator
    non_refer = (test_decisions["decision"] != "refer").values
    rule_B = (test_decisions.loc[non_refer, "decision"] == "eligible").values
    y_B = y_test[non_refer]
    metrics_B = _rule_metrics(rule_B, y_B, "refer rows excluded (Treatment B)")
    metrics_B["n_excluded_refer"] = int((~non_refer).sum())

    return {
        "treatment_A": metrics_A,
        "treatment_B": metrics_B,
        "note_filtering": (
            "Filtering on rule outcomes mechanically raises the rule system's approval rate: "
            "rows the rule system rejected or referred for V03, V04, K05 (and K04 for F2) are "
            "removed, so the remaining rows have a higher share of eligible decisions. "
            "This is not a performance improvement."
        ),
    }


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------


def run_baseline_filtered() -> None:
    """Run filtered-subset comparison. No retraining."""
    ml_cfg = load_ml_config("config/ml.toml")
    with open("config/experiment.toml", "rb") as fh:
        exp_cfg = tomllib.load(fh)

    master_seed = int(exp_cfg["seeds"]["master"])
    bootstrap_seed = derive_seed(master_seed, "bootstrap")
    bs_cfg = exp_cfg.get("bootstrap", {})
    n_resamples = int(bs_cfg.get("resamples", 1000))
    ci_level = float(bs_cfg.get("ci", 0.95))

    cost_ratios = exp_cfg["cost"]["ratios"]
    primary_ratio = exp_cfg["cost"]["primary"]

    models_dir = Path(exp_cfg["outputs"]["models_dir"])
    metrics_dir = Path(exp_cfg["outputs"]["metrics_dir"])
    metrics_dir.mkdir(parents=True, exist_ok=True)

    # --- Load fitted models (no retraining) ---
    d2_lr_data = joblib.load(models_dir / "d2_lr.joblib")
    d2_gb_data = joblib.load(models_dir / "d2_gb.joblib")
    pipe_lr = d2_lr_data["pipeline"]
    pipe_gb = d2_gb_data["pipeline"]

    # --- Load D2 data ---
    d2_path = Path(exp_cfg["d2"]["mapped_path"])
    d2_split_path = Path("data/splits/d2_split.csv")
    d2_decisions_path = Path("data/decisions/d2_decisions.csv")

    d2_df = pd.read_csv(d2_path, dtype=str)
    d2_df = prepare_dataframe(d2_df, ml_cfg)
    d2_split = pd.read_csv(d2_split_path, dtype=str)
    d2_decisions = pd.read_csv(d2_decisions_path, dtype=str)

    d2_df = pd.merge(d2_df, d2_split[["applicant_id", "split"]], on="applicant_id")
    d2_decisions_merged = pd.merge(
        d2_decisions, d2_split[["applicant_id", "split"]], on="applicant_id"
    )

    d2_val = d2_df[d2_df["split"] == "validation"].copy()
    d2_test = d2_df[d2_df["split"] == "test"].copy()
    d2_val_dec = d2_decisions_merged[d2_decisions_merged["split"] == "validation"].copy()
    d2_test_dec = d2_decisions_merged[d2_decisions_merged["split"] == "test"].copy()

    # Align decisions to same order as features
    d2_val_dec = (
        d2_val_dec.set_index("applicant_id").reindex(d2_val["applicant_id"].values).reset_index()
    )
    d2_test_dec = (
        d2_test_dec.set_index("applicant_id").reindex(d2_test["applicant_id"].values).reset_index()
    )

    y_val_full = d2_val["TARGET"].astype(int).values
    y_test_full = d2_test["TARGET"].astype(int).values

    d2_hash = file_sha256(d2_path)
    d2_split_hash = file_sha256(d2_split_path)

    subsets: dict[str, frozenset[str]] = {
        "main": frozenset(),
        "f1": _F1_EXCLUDE,
        "f2": _F2_EXCLUDE,
    }

    outputs: dict[str, dict[str, Any]] = {}

    for subset_name, exclude_codes in subsets.items():
        print(f"\n--- Subset: {subset_name.upper()} ---", file=sys.stderr)

        if exclude_codes:
            val_mask = _filter_mask(d2_val_dec, exclude_codes)
            test_mask = _filter_mask(d2_test_dec, exclude_codes)
        else:
            val_mask = pd.Series(True, index=d2_val_dec.index)
            test_mask = pd.Series(True, index=d2_test_dec.index)

        val_df_sub = d2_val[val_mask.values].copy()
        test_df_sub = d2_test[test_mask.values].copy()
        val_dec_sub = d2_val_dec[val_mask.values].copy()
        test_dec_sub = d2_test_dec[test_mask.values].copy()

        y_val_sub = y_val_full[val_mask.values]
        y_test_sub = y_test_full[test_mask.values]

        n_val = len(val_df_sub)
        n_test = len(test_df_sub)
        print(f"  val rows: {n_val}, test rows: {n_test}", file=sys.stderr)

        if exclude_codes:
            subset_label = f"filtered subset {subset_name.upper()}"
            filter_description = (
                f"Rows where none of {sorted(exclude_codes)} fired. "
                "No retraining. Operating points chosen on filtered validation rows. "
                "Filtering on rule outcomes mechanically raises the rule system's approval rate."
            )
        else:
            subset_label = "main (all evaluated rows)"
            filter_description = (
                "All D2 validation and test rows. "
                "Operating points from full baseline (reports/ml/metrics_d2_*.json)."
            )

        # Fresh bootstrap RNG for each subset — same seed → same results
        bs_rng = np.random.default_rng(bootstrap_seed)

        # Rule system metrics
        rule_metrics = _eval_rule_on_subset(
            test_dec_sub, y_test_sub, cost_ratios, bs_rng, n_resamples, ci_level
        )

        # ML model metrics
        lr_metrics = _eval_ml_on_subset(
            "lr",
            pipe_lr,
            val_df_sub,
            test_df_sub,
            val_dec_sub,
            test_dec_sub,
            y_val_sub,
            y_test_sub,
            cost_ratios,
            primary_ratio,
            bs_rng,
            n_resamples,
            ci_level,
        )
        gb_metrics = _eval_ml_on_subset(
            "gb",
            pipe_gb,
            val_df_sub,
            test_df_sub,
            val_dec_sub,
            test_dec_sub,
            y_val_sub,
            y_test_sub,
            cost_ratios,
            primary_ratio,
            bs_rng,
            n_resamples,
            ci_level,
        )

        result = {
            "subset": subset_label,
            "filter_description": filter_description,
            "row_counts": {
                "validation": n_val,
                "test": n_test,
            },
            "bootstrap": {
                "seed": bootstrap_seed,
                "n_resamples": n_resamples,
                "ci_level": ci_level,
                "note": "Resamples test applicants with replacement.",
            },
            "group_outcome_metrics": False,
            "dataset_hash": d2_hash,
            "split_hash": d2_split_hash,
            "rule_system": rule_metrics,
            "logistic_regression": lr_metrics,
            "gradient_boosting": gb_metrics,
        }

        out_path = metrics_dir / f"comparison_{subset_name}.json"
        out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"  Wrote {out_path}", file=sys.stderr)
        outputs[subset_name] = result

    print("\nAll filtered comparison files written.", file=sys.stderr)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run filtered-subset ML comparison.")
    parser.parse_args()
    run_baseline_filtered()


if __name__ == "__main__":
    main()
