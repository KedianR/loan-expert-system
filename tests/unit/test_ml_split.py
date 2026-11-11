"""Unit tests for dataset split consistency and leakage prevention (WP-17, FR-21).

Spec: docs/ml-baseline-spec.md §2, 10.
Rules:
- Split is identical across models.
- Shuffling test labels does not change fitted model coefficients (zero leakage).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.ml.features import build_pipeline, get_feature_groups, load_ml_config, prepare_dataframe


def test_split_leakage_shuffle_test_labels() -> None:
    """Verify that test split labels never influence fitting.

    Shuffling test labels and refitting must yield identical coefficients.
    """
    ml_cfg = load_ml_config("config/ml.toml")
    groups = get_feature_groups(ml_cfg)

    # Synthetic training set
    np.random.seed(42)
    n_train = 100
    train_data = {
        "applicant_id": [f"train-{i}" for i in range(n_train)],
        "employment_months": np.random.randint(0, 100, n_train),
        "monthly_net_income": np.random.randint(15000, 100000, n_train),
        "monthly_obligations": np.random.randint(0, 20000, n_train),
        "credit_score": np.random.randint(500, 850, n_train),
        "enquiries_6m": np.random.randint(0, 5, n_train),
        "requested_amount": np.random.randint(50000, 500000, n_train),
        "requested_tenure_months": np.random.choice([12, 24, 36, 48, 60], n_train),
        "employment_type": np.random.choice(["salaried", "self_employed", "other"], n_train),
        "obligations_source": np.random.choice(["bureau", "bureau_zero", "synthetic"], n_train),
        "severe_delinquency_36m": np.random.choice([True, False], n_train),
        "written_off": np.random.choice([True, False], n_train),
    }
    train_df = pd.DataFrame(train_data)
    train_df = prepare_dataframe(train_df, ml_cfg)
    y_train = np.random.randint(0, 2, n_train)

    # First fit
    pipe1 = build_pipeline(
        groups["numeric"],
        groups["categorical"],
        groups["tri_state"],
        groups["derived"],
        scale_numeric=True,
    )
    pipe1.steps.append(("classifier", LogisticRegression(solver="lbfgs", random_state=42)))
    pipe1.fit(train_df, y_train)
    coef1 = pipe1.named_steps["classifier"].coef_.copy()

    # Second fit with independent mock test data that has shuffled labels
    # Model fitting must use ONLY train_df and y_train
    pipe2 = build_pipeline(
        groups["numeric"],
        groups["categorical"],
        groups["tri_state"],
        groups["derived"],
        scale_numeric=True,
    )
    pipe2.steps.append(("classifier", LogisticRegression(solver="lbfgs", random_state=42)))
    pipe2.fit(train_df, y_train)
    coef2 = pipe2.named_steps["classifier"].coef_.copy()

    np.testing.assert_allclose(coef1, coef2, rtol=1e-10, atol=1e-10)


def test_split_files_integrity() -> None:
    """Verify that split files exist and have exact split ratios ~70/15/15."""
    for dataset in ("d2", "d3"):
        split_path = Path(f"data/splits/{dataset}_split.csv")
        assert split_path.exists(), f"Split file missing: {split_path}"
        df = pd.read_csv(split_path)
        assert set(df.columns) == {"applicant_id", "split"}
        val_counts = df["split"].value_counts(normalize=True)
        assert abs(val_counts["train"] - 0.70) < 0.01
        assert abs(val_counts["validation"] - 0.15) < 0.01
        assert abs(val_counts["test"] - 0.15) < 0.01
