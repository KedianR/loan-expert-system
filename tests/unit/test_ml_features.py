"""Unit tests for ML feature list and transformations (WP-17, FR-21, DR-02).

Spec: docs/ml-baseline-spec.md §3, 10.
Rules:
- No protected attribute in feature list.
- No identifier in feature list.
- No label-derived column in feature list.
- Every feature is defined in config/ml.toml.
- Pipeline accepts row with unknown/missing values.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.ml.features import (
    assert_no_protected_features,
    build_pipeline,
    get_feature_groups,
    load_ml_config,
    prepare_dataframe,
)


def test_DR02_no_protected_or_excluded_features() -> None:
    """Verify that no protected attribute, identifier or label column is a feature."""
    ml_cfg = load_ml_config("config/ml.toml")
    groups = get_feature_groups(ml_cfg)

    all_features = (
        groups["numeric"] + groups["categorical"] + groups["tri_state"] + groups["derived"]
    )

    # Must pass assert_no_protected_features
    assert_no_protected_features(all_features)

    # Specific hard checks
    hard_forbidden = {
        "age",
        "kyc_verified",
        "consent_given",
        "region_tier",
        "applicant_id",
        "TARGET",
        "policy_decision",
        "policy_eligible",
        "sim_default",
        "CODE_GENDER",
        "NAME_EDUCATION_TYPE",
        "NAME_FAMILY_STATUS",
        "REGION_RATING_CLIENT",
        "EXT_SOURCE_1",
        "EXT_SOURCE_2",
        "EXT_SOURCE_3",
        "SK_ID_CURR",
    }
    overlap = set(all_features).intersection(hard_forbidden)
    assert not overlap, f"Forbidden features found in model feature set: {overlap}"


def test_DR02_every_feature_in_config() -> None:
    """Verify that every feature used exists in config/ml.toml."""
    ml_cfg = load_ml_config("config/ml.toml")
    groups = get_feature_groups(ml_cfg)

    cfg_features = ml_cfg["features"]
    assert set(groups["numeric"]) == set(cfg_features["numeric"])
    assert set(groups["categorical"]) == set(cfg_features["categorical"])
    assert set(groups["tri_state"]) == set(cfg_features["tri_state"])
    assert set(groups["derived"]) == set(cfg_features["derived"])


def test_pipeline_accepts_row_with_unknown_values() -> None:
    """Verify that the preprocessing pipeline handles NaNs/unknowns cleanly."""
    ml_cfg = load_ml_config("config/ml.toml")
    groups = get_feature_groups(ml_cfg)

    # Train DataFrame
    train_data = {
        "applicant_id": ["app-1", "app-2", "app-3"],
        "employment_months": [12, 24, 36],
        "monthly_net_income": [50000, 60000, 70000],
        "monthly_obligations": [5000, 10000, 15000],
        "credit_score": [700, 750, 680],
        "enquiries_6m": [1, 2, 0],
        "requested_amount": [200000, 300000, 400000],
        "requested_tenure_months": [24, 36, 48],
        "employment_type": ["salaried", "self_employed", "other"],
        "obligations_source": ["bureau", "bureau_zero", "synthetic"],
        "severe_delinquency_36m": [False, True, False],
        "written_off": [False, False, False],
    }
    train_df = pd.DataFrame(train_data)
    train_df = prepare_dataframe(train_df, ml_cfg)

    pipeline = build_pipeline(
        groups["numeric"],
        groups["categorical"],
        groups["tri_state"],
        groups["derived"],
        scale_numeric=True,
    )
    pipeline.fit(train_df)

    # Test row where multiple values are NaN/unknown/None
    test_data = {
        "applicant_id": ["app-test"],
        "employment_months": [np.nan],
        "monthly_net_income": [40000],
        "monthly_obligations": [0],
        "credit_score": [np.nan],
        "enquiries_6m": [np.nan],
        "requested_amount": [100000],
        "requested_tenure_months": [np.nan],
        "employment_type": ["salaried"],
        "obligations_source": ["fallback_no_bureau"],
        "severe_delinquency_36m": ["unknown"],
        "written_off": ["unknown"],
    }
    test_df = pd.DataFrame(test_data)
    test_df = prepare_dataframe(test_df, ml_cfg)

    transformed = pipeline.transform(test_df)
    assert transformed.shape[0] == 1
    assert not np.isnan(transformed).any(), "Transformed output contains NaNs"
