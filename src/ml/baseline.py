"""ML Baseline module for Phase 4.

Implements: WP-17, FR-21, DR-02, DR-04, CR-05, CR-06.
Spec: docs/ml-baseline-spec.md, config/ml.toml, config/experiment.toml.

Trains Logistic Regression and HistGradientBoosting on D2 and D3,
plus Logistic Regression on D3 simulated outcome.
Selects operating points on validation; evaluates on test once.
Computes exact linear contributions for Logistic Regression.
Writes 5 metrics files to reports/ml/, reports/ml/feature_list.json,
and fitted models to models/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline

from src.ml.features import (
    assert_no_protected_features,
    build_pipeline,
    get_feature_groups,
    load_ml_config,
    prepare_dataframe,
)


def derive_seed(master: int, name: str) -> int:
    """FR-21: deterministic per-name seed from master seed."""
    return int(hashlib.sha256(f"{master}:{name}".encode()).hexdigest(), 16) % (2**32)


def file_sha256(path: Path | str) -> str:
    p = Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compute_reliability_table(
    y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = 10
) -> list[dict[str, Any]]:
    """Compute 10-bin calibration reliability table."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.digitize(y_proba, bins) - 1
    table: list[dict[str, Any]] = []

    for i in range(n_bins):
        mask = bin_indices == i
        count = int(mask.sum())
        if count > 0:
            mean_pred = float(np.mean(y_proba[mask]))
            mean_true = float(np.mean(y_true[mask]))
        else:
            mean_pred = float((bins[i] + bins[i + 1]) / 2.0)
            mean_true = 0.0

        table.append(
            {
                "bin": i + 1,
                "range": [round(float(bins[i]), 2), round(float(bins[i + 1]), 2)],
                "count": count,
                "mean_pred": round(mean_pred, 4),
                "mean_true": round(mean_true, 4),
            }
        )
    return table


def explain_logistic_regression(
    pipeline: Pipeline,
    row_df: pd.DataFrame,
    feature_groups: dict[str, list[str]],
    train_preprocessed_mean: np.ndarray,
) -> tuple[float, list[dict[str, Any]]]:
    """Compute exact linear contributions (SHAP-equivalent) for an applicant.

    Score is predicted probability of class 1.
    Top contributions are the top 3 features by absolute contribution to the logit.
    """
    preprocessor = pipeline.named_steps["preprocessor"]
    clf = pipeline.named_steps["classifier"]

    z = preprocessor.transform(row_df)[0]
    coef = clf.coef_[0]

    col_contribs = coef * (z - train_preprocessed_mean)

    num_and_derived = feature_groups["numeric"] + feature_groups["derived"]
    cat_all = feature_groups["categorical"] + feature_groups["tri_state"]

    cat_ohe = preprocessor.named_transformers_["cat_ohe"].named_steps["ohe"]
    cat_ohe_names = cat_ohe.get_feature_names_out(cat_all)

    col_to_feature: list[str] = []
    # 1. num_imputed
    for feat in num_and_derived:
        col_to_feature.append(feat)
    # 2. num_indicators
    for feat in num_and_derived:
        col_to_feature.append(feat)
    # 3. cat_ohe
    for col_name in cat_ohe_names:
        matched_feat = next((f for f in cat_all if col_name.startswith(f + "_")), col_name)
        col_to_feature.append(matched_feat)

    feature_contribs: dict[str, float] = {}
    for feat, c in zip(col_to_feature, col_contribs):
        feature_contribs[feat] = feature_contribs.get(feat, 0.0) + float(c)

    sorted_features = sorted(feature_contribs.items(), key=lambda x: abs(x[1]), reverse=True)
    top_3 = [{"feature": f, "contribution": round(c, 4)} for f, c in sorted_features[:3]]

    prob = float(clf.predict_proba([z])[0, 1])
    return prob, top_3


def evaluate_d2_model(
    model_name: str,
    pipeline: Pipeline,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    val_decisions: pd.DataFrame,
    test_decisions: pd.DataFrame,
    feature_groups: dict[str, list[str]],
    exp_cfg: dict[str, Any],
    ml_cfg: dict[str, Any],
    seed: int,
    split_file_hash: str,
    dataset_hash: str,
    models_dir: Path,
    metrics_dir: Path,
) -> dict[str, Any]:
    """Train and evaluate one model on D2."""
    cost_ratios = exp_cfg["cost"]["ratios"]  # [3, 5, 10]
    primary_ratio = exp_cfg["cost"]["primary"]  # 5

    y_train = train_df["TARGET"].astype(int).values
    y_val = val_df["TARGET"].astype(int).values
    y_test = test_df["TARGET"].astype(int).values

    print(f"Fitting D2 {model_name} on {len(train_df)} training rows...", file=sys.stderr)
    pipeline.fit(train_df, y_train)

    # Save model pipeline
    model_save_path = models_dir / f"d2_{model_name}.joblib"
    models_dir.mkdir(parents=True, exist_ok=True)

    train_mean = None
    if model_name == "lr":
        preproc = pipeline.named_steps["preprocessor"]
        X_train_trans = preproc.transform(train_df)
        train_mean = np.mean(X_train_trans, axis=0)
        joblib.dump({"pipeline": pipeline, "train_mean": train_mean}, model_save_path)
    else:
        joblib.dump({"pipeline": pipeline}, model_save_path)

    # Probabilities of default (TARGET = 1)
    val_proba = pipeline.predict_proba(val_df)[:, 1]
    test_proba = pipeline.predict_proba(test_df)[:, 1]

    val_auc = float(roc_auc_score(y_val, val_proba))
    test_auc = float(roc_auc_score(y_test, test_proba))
    test_brier = float(brier_score_loss(y_test, test_proba))

    # --- Rule system operating point on validation ---
    merged_val = pd.merge(
        val_df[["applicant_id"]], val_decisions[["applicant_id", "decision"]], on="applicant_id"
    )
    rule_val_approved_A = merged_val["decision"] == "eligible"
    target_approval_rate_A = float(rule_val_approved_A.mean())

    # 1. Matched approval rate threshold on validation
    # Lower default prob means approved; pick threshold quantile
    tau_matched = float(np.quantile(val_proba, target_approval_rate_A))

    # 2. Cost-based threshold on validation
    threshold_grid = np.linspace(float(np.min(val_proba)), float(np.max(val_proba)), 200)
    best_tau_cost = float(threshold_grid[0])
    min_cost = float("inf")
    for t in threshold_grid:
        approved = val_proba <= t
        fa = ((approved) & (y_val == 1)).sum()
        fd = ((~approved) & (y_val == 0)).sum()
        c = primary_ratio * fa + fd
        if c < min_cost:
            min_cost = c
            best_tau_cost = float(t)

    # Helper for evaluation at threshold
    def _eval_at_thresh(threshold: float) -> dict[str, Any]:
        approved = test_proba <= threshold
        app_rate = float(approved.mean())
        n_app = int(approved.sum())
        def_rate_among_app = float(y_test[approved].mean()) if n_app > 0 else 0.0

        # Positive class for default is TARGET=1; model predicts positive (default) if denied
        pred_pos = ~approved
        tn, fp, fn, tp = [int(v) for v in confusion_matrix(y_test, pred_pos, labels=[0, 1]).ravel()]
        prec = float(precision_score(y_test, pred_pos, zero_division=0))
        rec = float(recall_score(y_test, pred_pos, zero_division=0))
        f1 = float(f1_score(y_test, pred_pos, zero_division=0))

        cost_dict: dict[str, float] = {}
        for r in cost_ratios:
            fa = ((approved) & (y_test == 1)).sum()
            fd = ((~approved) & (y_test == 0)).sum()
            cost_dict[f"cost_{r}"] = round(float((r * fa + fd) / len(y_test)), 4)

        return {
            "threshold": round(threshold, 4),
            "approval_rate": round(app_rate, 4),
            "default_rate_among_approved": round(def_rate_among_app, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "confusion": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
            "cost_per_applicant": cost_dict,
        }

    matched_op = _eval_at_thresh(tau_matched)
    matched_op["target_approval_rate"] = round(target_approval_rate_A, 4)

    cost_op = _eval_at_thresh(best_tau_cost)
    cost_op["primary_cost_ratio"] = primary_ratio

    # Rule system metrics on test split
    merged_test = pd.merge(
        test_df[["applicant_id"]], test_decisions[["applicant_id", "decision"]], on="applicant_id"
    )

    # Treatment A: refer counts as not approved
    rule_app_A = (merged_test["decision"] == "eligible").values

    def _eval_rule_mask(approved_mask: np.ndarray, y_arr: np.ndarray) -> dict[str, Any]:
        app_rate = float(approved_mask.mean())
        n_app = int(approved_mask.sum())
        def_rate = float(y_arr[approved_mask].mean()) if n_app > 0 else 0.0
        pred_pos = ~approved_mask
        tn, fp, fn, tp = [int(v) for v in confusion_matrix(y_arr, pred_pos, labels=[0, 1]).ravel()]
        prec = float(precision_score(y_arr, pred_pos, zero_division=0))
        rec = float(recall_score(y_arr, pred_pos, zero_division=0))
        f1 = float(f1_score(y_arr, pred_pos, zero_division=0))
        cost_dict: dict[str, float] = {}
        for r in cost_ratios:
            fa = ((approved_mask) & (y_arr == 1)).sum()
            fd = ((~approved_mask) & (y_arr == 0)).sum()
            cost_dict[f"cost_{r}"] = round(float((r * fa + fd) / len(y_arr)), 4)
        return {
            "approval_rate": round(app_rate, 4),
            "default_rate_among_approved": round(def_rate, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "confusion": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
            "cost_per_applicant": cost_dict,
        }

    rule_metrics_A = _eval_rule_mask(rule_app_A, y_test)
    rule_metrics_A["description"] = "refer counts as not approved"

    # Treatment B: refer rows excluded
    non_refer_mask = (merged_test["decision"] != "refer").values
    rule_app_B = (merged_test.loc[non_refer_mask, "decision"] == "eligible").values
    y_test_B = y_test[non_refer_mask]
    rule_metrics_B = _eval_rule_mask(rule_app_B, y_test_B)
    rule_metrics_B["description"] = "refer rows excluded"
    rule_metrics_B["n_excluded_refer"] = int((~non_refer_mask).sum())

    # Top explanations for LR
    explanations_summary = None
    if model_name == "lr" and train_mean is not None:
        sample_probs = []
        for i in range(min(5, len(test_df))):
            row_sample = test_df.iloc[[i]]
            prob, top3 = explain_logistic_regression(
                pipeline, row_sample, feature_groups, train_mean
            )
            sample_probs.append(
                {
                    "applicant_id": str(row_sample["applicant_id"].values[0]),
                    "score": round(prob, 4),
                    "top_3_contributions": top3,
                }
            )
        explanations_summary = sample_probs

    metrics_out = {
        "dataset": "d2",
        "model": model_name,
        "seed": seed,
        "split_file_hash": split_file_hash,
        "dataset_hash": dataset_hash,
        "library_versions": {
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": "1.9.1",
            "joblib": joblib.__version__,
        },
        "class_balance": {
            "train": {
                "count": len(train_df),
                "positive": int(y_train.sum()),
                "positive_share": round(float(y_train.mean()), 4),
            },
            "validation": {
                "count": len(val_df),
                "positive": int(y_val.sum()),
                "positive_share": round(float(y_val.mean()), 4),
            },
            "test": {
                "count": len(test_df),
                "positive": int(y_test.sum()),
                "positive_share": round(float(y_test.mean()), 4),
            },
        },
        "validation_metrics": {
            "auc": round(val_auc, 4),
        },
        "test_metrics": {
            "auc": round(test_auc, 4),
            "brier_score": round(test_brier, 4),
            "reliability_table": compute_reliability_table(y_test, test_proba, n_bins=10),
        },
        "operating_points": {
            "matched_approval_rate": matched_op,
            "cost_based_primary": cost_op,
            "rule_system": {
                "treatment_A": rule_metrics_A,
                "treatment_B": rule_metrics_B,
            },
        },
        "explanations_sample": explanations_summary,
    }

    metrics_path = metrics_dir / f"metrics_d2_{model_name}.json"
    metrics_path.write_text(json.dumps(metrics_out, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {metrics_path}")
    return metrics_out


def evaluate_d3_model(
    model_name: str,
    pipeline: Pipeline,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    decisions_df: pd.DataFrame,
    feature_groups: dict[str, list[str]],
    exp_cfg: dict[str, Any],
    ml_cfg: dict[str, Any],
    seed: int,
    split_file_hash: str,
    dataset_hash: str,
    models_dir: Path,
    metrics_dir: Path,
    is_sim_outcome: bool = False,
) -> dict[str, Any]:
    """Train and evaluate model on D3 policy decision or simulated default."""
    dec_merged = pd.merge(
        train_df[["applicant_id"]], decisions_df[["applicant_id", "decision"]], on="applicant_id"
    )
    val_merged = pd.merge(
        val_df[["applicant_id"]], decisions_df[["applicant_id", "decision"]], on="applicant_id"
    )
    test_merged = pd.merge(
        test_df[["applicant_id"]], decisions_df[["applicant_id", "decision"]], on="applicant_id"
    )

    if is_sim_outcome:
        target_col = "sim_default"
        y_train = train_df[target_col].astype(int).values
        y_val = val_df[target_col].astype(int).values
        y_test = test_df[target_col].astype(int).values
        dataset_label = "d3_sim"
    else:
        # Decision P4-2: positive class is eligible (1), ineligible/refer is not eligible (0)
        y_train = (dec_merged["decision"] == "eligible").astype(int).values
        y_val = (val_merged["decision"] == "eligible").astype(int).values
        y_test = (test_merged["decision"] == "eligible").astype(int).values
        dataset_label = "d3"

    print(f"Fitting D3 ({dataset_label}) {model_name} on {len(train_df)} rows...", file=sys.stderr)
    pipeline.fit(train_df, y_train)

    model_save_path = models_dir / f"{dataset_label}_{model_name}.joblib"
    models_dir.mkdir(parents=True, exist_ok=True)

    train_mean = None
    if model_name == "lr":
        preproc = pipeline.named_steps["preprocessor"]
        X_train_trans = preproc.transform(train_df)
        train_mean = np.mean(X_train_trans, axis=0)
        joblib.dump({"pipeline": pipeline, "train_mean": train_mean}, model_save_path)
    else:
        joblib.dump({"pipeline": pipeline}, model_save_path)

    val_proba = pipeline.predict_proba(val_df)[:, 1]
    test_proba = pipeline.predict_proba(test_df)[:, 1]

    val_auc = float(roc_auc_score(y_val, val_proba))
    test_auc = float(roc_auc_score(y_test, test_proba))
    test_brier = float(brier_score_loss(y_test, test_proba))

    # Standard threshold 0.5 for policy decision prediction
    pred_pos = (test_proba >= 0.5).astype(int)
    tn, fp, fn, tp = [int(v) for v in confusion_matrix(y_test, pred_pos, labels=[0, 1]).ravel()]
    prec = float(precision_score(y_test, pred_pos, zero_division=0))
    rec = float(recall_score(y_test, pred_pos, zero_division=0))
    f1 = float(f1_score(y_test, pred_pos, zero_division=0))
    agreement = float((pred_pos == y_test).mean())

    # Breakdown by 3-way decision
    disagreements = {}
    if not is_sim_outcome:
        true_3way = test_merged["decision"].values
        disagreements = {
            "eligible_predicted_denied": int(((true_3way == "eligible") & (pred_pos == 0)).sum()),
            "ineligible_predicted_approved": int(
                ((true_3way == "ineligible") & (pred_pos == 1)).sum()
            ),
            "refer_predicted_approved": int(((true_3way == "refer") & (pred_pos == 1)).sum()),
            "refer_predicted_denied": int(((true_3way == "refer") & (pred_pos == 0)).sum()),
        }

    explanations_summary = None
    if model_name == "lr" and train_mean is not None:
        sample_probs = []
        for i in range(min(5, len(test_df))):
            row_sample = test_df.iloc[[i]]
            prob, top3 = explain_logistic_regression(
                pipeline, row_sample, feature_groups, train_mean
            )
            sample_probs.append(
                {
                    "applicant_id": str(row_sample["applicant_id"].values[0]),
                    "score": round(prob, 4),
                    "top_3_contributions": top3,
                }
            )
        explanations_summary = sample_probs

    metrics_out = {
        "dataset": dataset_label,
        "model": model_name,
        "seed": seed,
        "split_file_hash": split_file_hash,
        "dataset_hash": dataset_hash,
        "library_versions": {
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": "1.9.1",
            "joblib": joblib.__version__,
        },
        "class_balance": {
            "train": {
                "count": len(train_df),
                "positive": int(y_train.sum()),
                "positive_share": round(float(y_train.mean()), 4),
            },
            "validation": {
                "count": len(val_df),
                "positive": int(y_val.sum()),
                "positive_share": round(float(y_val.mean()), 4),
            },
            "test": {
                "count": len(test_df),
                "positive": int(y_test.sum()),
                "positive_share": round(float(y_test.mean()), 4),
            },
        },
        "validation_metrics": {
            "auc": round(val_auc, 4),
        },
        "test_metrics": {
            "auc": round(test_auc, 4),
            "brier_score": round(test_brier, 4),
            "reliability_table": compute_reliability_table(y_test, test_proba, n_bins=10),
        },
        "operating_point_0_5": {
            "threshold": 0.5,
            "agreement_rate": round(agreement, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "confusion": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
            "disagreements_by_true_class": disagreements,
        },
        "explanations_sample": explanations_summary,
    }

    metrics_path = metrics_dir / f"metrics_{dataset_label}_{model_name}.json"
    metrics_path.write_text(json.dumps(metrics_out, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {metrics_path}")
    return metrics_out


def run_baseline() -> None:
    """Run full Phase 4 baseline training and metrics generation."""
    ml_cfg = load_ml_config("config/ml.toml")
    with open("config/experiment.toml", "rb") as fh:
        exp_cfg = tomllib.load(fh)

    master_seed = int(exp_cfg["seeds"]["master"])
    seed_lr = derive_seed(master_seed, "model_lr")
    seed_gb = derive_seed(master_seed, "model_gb")

    feature_groups = get_feature_groups(ml_cfg)
    models_dir = Path(exp_cfg["outputs"]["models_dir"])
    metrics_dir = Path(exp_cfg["outputs"]["metrics_dir"])
    models_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    # Save feature_list.json
    num_and_derived = feature_groups["numeric"] + feature_groups["derived"]
    feature_list_content = {
        "numeric": feature_groups["numeric"],
        "categorical": feature_groups["categorical"],
        "tri_state": feature_groups["tri_state"],
        "derived": feature_groups["derived"],
        "missing_indicators": [f"{f}_missing" for f in num_and_derived],
    }
    all_features = (
        feature_groups["numeric"]
        + feature_groups["categorical"]
        + feature_groups["tri_state"]
        + feature_groups["derived"]
    )
    assert_no_protected_features(all_features)

    feat_list_path = metrics_dir / "feature_list.json"
    feat_list_path.write_text(json.dumps(feature_list_content, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {feat_list_path}")

    # --- Load D2 Data ---
    d2_path = Path(exp_cfg["d2"]["mapped_path"])
    d2_split_path = Path("data/splits/d2_split.csv")
    d2_decisions_path = Path("data/decisions/d2_decisions.csv")

    d2_df = pd.read_csv(d2_path, dtype=str)
    d2_df = prepare_dataframe(d2_df, ml_cfg)
    d2_split = pd.read_csv(d2_split_path, dtype=str)
    d2_decisions = pd.read_csv(d2_decisions_path, dtype=str)

    d2_df = pd.merge(d2_df, d2_split[["applicant_id", "split"]], on="applicant_id")
    d2_train = d2_df[d2_df["split"] == "train"].copy()
    d2_val = d2_df[d2_df["split"] == "validation"].copy()
    d2_test = d2_df[d2_df["split"] == "test"].copy()

    d2_hash = file_sha256(d2_path)
    d2_split_hash = file_sha256(d2_split_path)

    # Fit & evaluate D2 Logistic Regression
    pipe_d2_lr = build_pipeline(
        feature_groups["numeric"],
        feature_groups["categorical"],
        feature_groups["tri_state"],
        feature_groups["derived"],
        scale_numeric=True,
    )
    pipe_d2_lr.steps.append(
        (
            "classifier",
            LogisticRegression(
                C=1.0,
                solver="lbfgs",
                max_iter=1000,
                class_weight="balanced",
                random_state=seed_lr,
            ),
        )
    )
    evaluate_d2_model(
        "lr",
        pipe_d2_lr,
        d2_train,
        d2_val,
        d2_test,
        d2_decisions,
        d2_decisions,
        feature_groups,
        exp_cfg,
        ml_cfg,
        seed_lr,
        d2_split_hash,
        d2_hash,
        models_dir,
        metrics_dir,
    )

    # Fit & evaluate D2 HistGradientBoosting
    pipe_d2_gb = build_pipeline(
        feature_groups["numeric"],
        feature_groups["categorical"],
        feature_groups["tri_state"],
        feature_groups["derived"],
        scale_numeric=False,
    )
    pipe_d2_gb.steps.append(
        (
            "classifier",
            HistGradientBoostingClassifier(
                max_iter=200,
                learning_rate=0.1,
                max_leaf_nodes=31,
                min_samples_leaf=20,
                l2_regularization=0.0,
                early_stopping=False,
                class_weight="balanced",
                random_state=seed_gb,
            ),
        )
    )
    evaluate_d2_model(
        "gb",
        pipe_d2_gb,
        d2_train,
        d2_val,
        d2_test,
        d2_decisions,
        d2_decisions,
        feature_groups,
        exp_cfg,
        ml_cfg,
        seed_gb,
        d2_split_hash,
        d2_hash,
        models_dir,
        metrics_dir,
    )

    # --- Load D3 Data ---
    d3_path = Path(exp_cfg["d3"]["mapped_path"])
    d3_split_path = Path("data/splits/d3_split.csv")
    d3_decisions_path = Path("data/decisions/d3_decisions.csv")

    d3_df = pd.read_csv(d3_path, dtype=str)
    d3_df = prepare_dataframe(d3_df, ml_cfg)
    d3_split = pd.read_csv(d3_split_path, dtype=str)
    d3_decisions = pd.read_csv(d3_decisions_path, dtype=str)

    d3_df = pd.merge(d3_df, d3_split[["applicant_id", "split"]], on="applicant_id")
    d3_train = d3_df[d3_df["split"] == "train"].copy()
    d3_val = d3_df[d3_df["split"] == "validation"].copy()
    d3_test = d3_df[d3_df["split"] == "test"].copy()

    d3_hash = file_sha256(d3_path)
    d3_split_hash = file_sha256(d3_split_path)

    # Fit & evaluate D3 Logistic Regression
    pipe_d3_lr = build_pipeline(
        feature_groups["numeric"],
        feature_groups["categorical"],
        feature_groups["tri_state"],
        feature_groups["derived"],
        scale_numeric=True,
    )
    pipe_d3_lr.steps.append(
        (
            "classifier",
            LogisticRegression(
                C=1.0,
                solver="lbfgs",
                max_iter=1000,
                class_weight="balanced",
                random_state=seed_lr,
            ),
        )
    )
    evaluate_d3_model(
        "lr",
        pipe_d3_lr,
        d3_train,
        d3_val,
        d3_test,
        d3_decisions,
        feature_groups,
        exp_cfg,
        ml_cfg,
        seed_lr,
        d3_split_hash,
        d3_hash,
        models_dir,
        metrics_dir,
    )

    # Fit & evaluate D3 HistGradientBoosting
    pipe_d3_gb = build_pipeline(
        feature_groups["numeric"],
        feature_groups["categorical"],
        feature_groups["tri_state"],
        feature_groups["derived"],
        scale_numeric=False,
    )
    pipe_d3_gb.steps.append(
        (
            "classifier",
            HistGradientBoostingClassifier(
                max_iter=200,
                learning_rate=0.1,
                max_leaf_nodes=31,
                min_samples_leaf=20,
                l2_regularization=0.0,
                early_stopping=False,
                class_weight="balanced",
                random_state=seed_gb,
            ),
        )
    )
    evaluate_d3_model(
        "gb",
        pipe_d3_gb,
        d3_train,
        d3_val,
        d3_test,
        d3_decisions,
        feature_groups,
        exp_cfg,
        ml_cfg,
        seed_gb,
        d3_split_hash,
        d3_hash,
        models_dir,
        metrics_dir,
    )

    # Fit & evaluate D3 sim_default Logistic Regression
    pipe_d3_sim = build_pipeline(
        feature_groups["numeric"],
        feature_groups["categorical"],
        feature_groups["tri_state"],
        feature_groups["derived"],
        scale_numeric=True,
    )
    pipe_d3_sim.steps.append(
        (
            "classifier",
            LogisticRegression(
                C=1.0,
                solver="lbfgs",
                max_iter=1000,
                class_weight="balanced",
                random_state=seed_lr,
            ),
        )
    )
    evaluate_d3_model(
        "lr",
        pipe_d3_sim,
        d3_train,
        d3_val,
        d3_test,
        d3_decisions,
        feature_groups,
        exp_cfg,
        ml_cfg,
        seed_lr,
        d3_split_hash,
        d3_hash,
        models_dir,
        metrics_dir,
        is_sim_outcome=True,
    )

    print("All ML baseline models and metrics successfully computed!", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ML baseline pipelines.")
    parser.parse_args()
    run_baseline()


if __name__ == "__main__":
    main()
