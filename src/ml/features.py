"""Feature engineering for the ML baseline.

Requirements: FR-21, DR-02, DR-04, CR-05, CR-06.
Spec: docs/ml-baseline-spec.md sections 3-4.
Config: config/ml.toml [features], [preprocessing].

NEVER includes protected attributes, identifiers or label-derived columns
(DR-02, R-08; ml-baseline-spec.md section 3).

Floats are permitted here (P4-8: ML code may use floats).
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ---------------------------------------------------------------------------
# Column name constants (all values come from config/ml.toml, never hard-coded
# policy values – these are structural/column-name strings, not thresholds).
# ---------------------------------------------------------------------------


def load_ml_config(ml_cfg_path: str | Path = "config/ml.toml") -> dict[str, Any]:
    """Return the parsed contents of config/ml.toml."""
    with open(ml_cfg_path, "rb") as fh:
        return tomllib.load(fh)


def get_excluded_columns(ml_cfg_path: str | Path = "config/ml.toml") -> frozenset[str]:
    """Read excluded column names from config/ml.toml [features.excluded]."""
    cfg = load_ml_config(ml_cfg_path)
    exc = cfg.get("features", {}).get("excluded", {})
    all_exc: set[str] = set()
    for k in ("facts", "raw_columns", "label_columns"):
        all_exc.update(exc.get(k, []))
    return frozenset(all_exc)


def get_feature_groups(ml_cfg: dict[str, Any]) -> dict[str, list[str]]:
    """Return feature groups as defined in ml.toml [features].

    Returns a dict with keys: numeric, categorical, tri_state, derived.
    """
    feat = ml_cfg["features"]
    return {
        "numeric": list(feat["numeric"]),
        "categorical": list(feat["categorical"]),
        "tri_state": list(feat["tri_state"]),
        "derived": list(feat["derived"]),
    }


def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    """Element-wise division; NaN where denominator is zero or NaN."""
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where((den.isna()) | (den == 0), np.nan, num / den)
    return pd.Series(result, index=num.index)


def compute_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived ratio columns to *df* (in-place copy).

    Columns added (spec section 3):
      existing_foir                = monthly_obligations / monthly_net_income
      amount_to_annual_income      = requested_amount / (12 * monthly_net_income)
      instalment_to_income         = (requested_amount / requested_tenure_months)
                                     / monthly_net_income

    Floats are allowed in ML code (P4-8).
    """
    df = df.copy()
    df["existing_foir"] = _safe_div(
        df["monthly_obligations"].astype(float),
        df["monthly_net_income"].astype(float),
    )
    df["amount_to_annual_income"] = _safe_div(
        df["requested_amount"].astype(float),
        (df["monthly_net_income"].astype(float) * 12),
    )
    df["instalment_to_income"] = _safe_div(
        _safe_div(
            df["requested_amount"].astype(float),
            df["requested_tenure_months"].astype(float),
        ),
        df["monthly_net_income"].astype(float),
    )
    return df


def normalise_tri_state(df: pd.DataFrame, tri_state_cols: list[str]) -> pd.DataFrame:
    """Convert True/False/None/NaN tri-state columns to string categories.

    Mapping:
      True  → "true"
      False → "false"
      None / NaN / anything else → "unknown"

    Returns a copy of *df* with the named columns replaced.
    """
    df = df.copy()
    for col in tri_state_cols:
        if col not in df.columns:
            df[col] = "unknown"
            continue
        raw = df[col]
        mapped = []
        for v in raw:
            if v is True or v == "True" or v == "true" or v == 1:
                mapped.append("true")
            elif v is False or v == "False" or v == "false" or v == 0:
                mapped.append("false")
            else:
                mapped.append("unknown")
        df[col] = mapped
    return df


class MissingIndicatorTransformer(BaseEstimator, TransformerMixin):
    """Adds ``{col}_missing`` boolean columns for the named numeric columns.

    Fit: records column names (no-op otherwise).
    Transform: appends 1/0 missing-indicator columns.

    The spec says one missing indicator per numeric feature and per derived
    ratio (ml-baseline-spec.md section 3).
    """

    def __init__(self, feature_names: list[str]) -> None:
        self.feature_names = feature_names

    def fit(self, X: np.ndarray, y: Any = None) -> MissingIndicatorTransformer:  # noqa: N803
        return self

    def transform(self, X: np.ndarray, y: Any = None) -> np.ndarray:  # noqa: N803
        # X is already a numpy array (output of SimpleImputer or similar).
        # We pass the original pre-imputed data via fit_transform; here we
        # reconstruct indicators from the already-imputed X – but indicators
        # must be built BEFORE imputation. This transformer is therefore
        # always placed in a Pipeline BEFORE the imputer via FeatureUnion or
        # used as a separate branch in ColumnTransformer.
        # See build_pipeline() for the actual wiring.
        return X

    def get_feature_names_out(self, input_features: list[str] | None = None) -> np.ndarray:
        return np.array(self.feature_names)


class PreImpMissingIndicator(BaseEstimator, TransformerMixin):
    """Returns a binary matrix: 1 where the input is NaN, 0 otherwise.

    Must be applied to the raw (un-imputed) data.
    Output column names: ``{col}_missing`` for each input column.
    """

    def __init__(self) -> None:
        self._n_features: int = 0
        self._feature_names_in: list[str] = []

    def fit(self, X: pd.DataFrame | np.ndarray, y: Any = None) -> PreImpMissingIndicator:  # noqa: N803
        if hasattr(X, "columns"):
            self._feature_names_in = list(X.columns)
        else:
            self._feature_names_in = [f"x{i}" for i in range(X.shape[1])]
        self._n_features = len(self._feature_names_in)
        self.n_features_in_ = self._n_features
        return self

    def __sklearn_is_fitted__(self) -> bool:
        return hasattr(self, "n_features_in_")

    def transform(self, X: pd.DataFrame | np.ndarray, y: Any = None) -> np.ndarray:  # noqa: N803
        if hasattr(X, "values"):
            arr = X.values.astype(float)
        else:
            arr = np.asarray(X, dtype=float)
        return np.isnan(arr).astype(np.float64)

    def get_feature_names_out(self, input_features: list[str] | None = None) -> np.ndarray:
        names = input_features if input_features is not None else self._feature_names_in
        return np.array([f"{n}_missing" for n in names])


def build_pipeline(
    numeric_cols: list[str],
    categorical_cols: list[str],
    tri_state_cols: list[str],
    derived_cols: list[str],
    scale_numeric: bool,
) -> Pipeline:
    """Build a scikit-learn Pipeline for one model.

    Preprocessing (spec section 4):
    - Numeric + derived: median imputation + missing indicators (before imputation).
      StandardScaler on numeric+derived if ``scale_numeric`` is True (LR only).
      Missing-indicator columns are NOT scaled.
    - Categorical + tri_state: OHE with handle_unknown="ignore", drop=None.
    - Fit ONLY on train split (enforced by the caller).

    Args:
        numeric_cols: Raw numeric feature names.
        categorical_cols: Categorical feature names (already strings).
        tri_state_cols: Three-state feature names (already converted to strings).
        derived_cols: Derived ratio feature names.
        scale_numeric: Whether to apply StandardScaler to numeric+derived.

    Returns:
        An unfitted sklearn Pipeline whose first step is 'preprocessor'
        (a ColumnTransformer) and whose caller must append the classifier.
    """
    num_and_derived = numeric_cols + derived_cols
    cat_all = categorical_cols + tri_state_cols

    # --- Branch 1: missing indicators (computed on raw data, before imputation) ---
    indicator_branch = Pipeline(
        steps=[
            ("indicator", PreImpMissingIndicator()),
        ]
    )

    # --- Branch 2: imputed (and optionally scaled) numeric+derived ---
    impute_steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="median")),
    ]
    if scale_numeric:
        impute_steps.append(("scaler", StandardScaler()))
    numeric_branch = Pipeline(steps=impute_steps)

    # --- Branch 3: categorical OHE ---
    cat_branch = Pipeline(
        steps=[
            (
                "ohe",
                OneHotEncoder(handle_unknown="ignore", drop=None, sparse_output=False),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num_imputed", numeric_branch, num_and_derived),
            ("num_indicators", indicator_branch, num_and_derived),
            ("cat_ohe", cat_branch, cat_all),
        ],
        remainder="drop",
    )

    pipeline = Pipeline(steps=[("preprocessor", preprocessor)])
    return pipeline


def prepare_dataframe(
    df: pd.DataFrame,
    ml_cfg: dict[str, Any],
) -> pd.DataFrame:
    """Return a copy of *df* with derived columns added and tri-state columns normalised.

    Does NOT drop excluded columns – the pipeline's ColumnTransformer selects
    only the needed columns by name.
    """
    groups = get_feature_groups(ml_cfg)
    df = compute_derived(df)
    df = normalise_tri_state(df, groups["tri_state"])
    return df


def assert_no_protected_features(
    feature_names: list[str], ml_cfg_path: str | Path = "config/ml.toml"
) -> None:
    """Raise ValueError if any protected/excluded column appears in feature_names.

    Used by tests (ml-baseline-spec.md section 10).
    """
    excluded = get_excluded_columns(ml_cfg_path)
    bad = [f for f in feature_names if f in excluded]
    if bad:
        raise ValueError(f"Protected/excluded columns found in feature list: {bad}")
