"""Unit tests for ML metrics files and reproducibility (WP-17, FR-21).

Spec: docs/ml-baseline-spec.md §5, 7, 9, 10.
"""

from __future__ import annotations

import json
from pathlib import Path


def test_five_metrics_files_exist_and_validate() -> None:
    """Verify that all five required metrics files exist with valid schema."""
    metrics_dir = Path("reports/ml")
    expected_files = [
        "metrics_d2_lr.json",
        "metrics_d2_gb.json",
        "metrics_d3_lr.json",
        "metrics_d3_gb.json",
        "metrics_d3_sim_lr.json",
    ]

    for fname in expected_files:
        path = metrics_dir / fname
        assert path.exists(), f"Missing metrics file: {path}"
        data = json.loads(path.read_text(encoding="utf-8"))

        # Check required top-level keys
        assert "dataset" in data
        assert "model" in data
        assert "seed" in data
        assert "split_file_hash" in data
        assert "dataset_hash" in data
        assert "library_versions" in data
        assert "class_balance" in data
        assert "validation_metrics" in data
        assert "test_metrics" in data

        # Check class balance splits
        for split in ("train", "validation", "test"):
            assert split in data["class_balance"]
            assert data["class_balance"][split]["count"] > 0

        # AUC checks
        assert 0.5 <= data["validation_metrics"]["auc"] <= 1.0
        assert 0.5 <= data["test_metrics"]["auc"] <= 1.0
        assert "reliability_table" in data["test_metrics"]
        assert len(data["test_metrics"]["reliability_table"]) == 10


def test_feature_list_file_exists() -> None:
    """Verify that reports/ml/feature_list.json exists and contains correct groups."""
    feat_path = Path("reports/ml/feature_list.json")
    assert feat_path.exists(), "reports/ml/feature_list.json is missing"
    data = json.loads(feat_path.read_text(encoding="utf-8"))
    assert "numeric" in data
    assert "categorical" in data
    assert "tri_state" in data
    assert "derived" in data
    assert "missing_indicators" in data
