"""Tests for the filtered-subset comparison module (Phase 4 close-out).

Required tests (docs/ml-baseline-spec.md §10, Phase 4 close-out prompt item 9):
  - Filtered baseline never retrains (uses same model weights as baseline).
  - Comparison JSON files are identical across two runs (DR-05 reproducibility).
  - No group outcome metric in any comparison file.
  - F1 and F2 filter masks are correct.

Implements: DR-05, FR-21, experiment-protocol.md §8.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


METRICS_DIR = Path("reports/ml")
COMPARISON_FILES = ["comparison_main.json", "comparison_f1.json", "comparison_f2.json"]


@pytest.mark.skipif(
    not (METRICS_DIR / "comparison_main.json").exists(),
    reason="Run make baseline-filtered first",
)
def test_DR05_filtered_comparison_files_exist():
    """All three comparison files must exist after make baseline-filtered."""
    for fname in COMPARISON_FILES:
        p = METRICS_DIR / fname
        assert p.exists(), f"Missing: {p}"


@pytest.mark.skipif(
    not (METRICS_DIR / "comparison_main.json").exists(),
    reason="Run make baseline-filtered first",
)
def test_filtered_no_group_outcome_metrics():
    """No comparison file may contain outcome metrics by protected group (DR-06)."""
    for fname in COMPARISON_FILES:
        p = METRICS_DIR / fname
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data.get("group_outcome_metrics") is False, (
            f"{fname}: group_outcome_metrics must be False"
        )
        # Structural check: no 'group' key at top level
        assert "group_metrics" not in data, f"{fname}: must not contain group_metrics"


@pytest.mark.skipif(
    not (METRICS_DIR / "comparison_main.json").exists(),
    reason="Run make baseline-filtered first",
)
def test_filtered_lr_and_gb_note_no_retrain():
    """LR and GB sections must carry the no-retrain note (item 9 requirement)."""
    for fname in ["comparison_f1.json", "comparison_f2.json"]:
        p = METRICS_DIR / fname
        data = json.loads(p.read_text(encoding="utf-8"))
        for model_key in ("logistic_regression", "gradient_boosting"):
            note = data[model_key].get("note", "")
            assert "No retraining" in note, f"{fname}/{model_key}: must carry no-retrain note"


@pytest.mark.skipif(
    not (METRICS_DIR / "comparison_f1.json").exists(),
    reason="Run make baseline-filtered first",
)
def test_filtered_f1_f2_subsets_labelled():
    """F1 and F2 outputs must be labelled as 'filtered subset'."""
    for fname, expected in [
        ("comparison_f1.json", "filtered subset F1"),
        ("comparison_f2.json", "filtered subset F2"),
    ]:
        p = METRICS_DIR / fname
        data = json.loads(p.read_text(encoding="utf-8"))
        subset_label = data.get("subset", "")
        assert "filtered subset" in subset_label.lower(), (
            f"{fname}: subset label must contain 'filtered subset', got: {subset_label!r}"
        )


@pytest.mark.skipif(
    not (METRICS_DIR / "comparison_f1.json").exists(),
    reason="Run make baseline-filtered first",
)
def test_filtered_rule_note_mechanical_approval():
    """Rule system section must state that filtering mechanically raises approval rate."""
    for fname in ["comparison_f1.json", "comparison_f2.json"]:
        p = METRICS_DIR / fname
        data = json.loads(p.read_text(encoding="utf-8"))
        note = data["rule_system"].get("note_filtering", "")
        assert "mechanically" in note.lower(), (
            f"{fname}: rule_system must note mechanical approval-rate increase"
        )


@pytest.mark.skipif(
    not (METRICS_DIR / "comparison_f1.json").exists(),
    reason="Run make baseline-filtered first",
)
def test_filtered_bootstrap_ci_present():
    """Every approval operating point must include a bootstrap CI dict."""
    for fname in COMPARISON_FILES:
        p = METRICS_DIR / fname
        data = json.loads(p.read_text(encoding="utf-8"))
        for system in ("logistic_regression", "gradient_boosting"):
            for op in ("matched_approval_rate", "cost_based_primary"):
                ci = data[system]["operating_points"][op].get("default_rate_among_approved_ci", {})
                assert "ci_lower" in ci and "ci_upper" in ci, (
                    f"{fname}/{system}/{op}: missing bootstrap CI"
                )
        # Rule system Treatment A
        ci_A = data["rule_system"]["treatment_A"].get("default_rate_among_approved_ci", {})
        assert "ci_lower" in ci_A, f"{fname}/rule_system/treatment_A: missing CI"


@pytest.mark.skipif(
    not (METRICS_DIR / "comparison_main.json").exists(),
    reason="Run make baseline-filtered first",
)
def test_DR05_filtered_comparison_reproducible(tmp_path):
    """Hashes of comparison files must be stable (DR-05).

    We re-run baseline_filtered and verify the files do not change.
    This test reads the existing hashes and re-runs the module,
    then checks the hashes are equal.
    """
    hashes_before = {f: file_sha256(METRICS_DIR / f) for f in COMPARISON_FILES}

    # Re-run the module
    from src.ml.baseline_filtered import run_baseline_filtered

    run_baseline_filtered()

    hashes_after = {f: file_sha256(METRICS_DIR / f) for f in COMPARISON_FILES}
    for f in COMPARISON_FILES:
        assert hashes_before[f] == hashes_after[f], (
            f"{f}: hash changed between runs — not reproducible"
        )


def test_filter_mask_f1_excludes_correct_codes():
    """F1 mask removes rows with V03, V04, or K05 reason codes."""
    from src.ml.baseline_filtered import _F1_EXCLUDE, _filter_mask

    rows = pd.DataFrame(
        {
            "reason_codes": [
                "INCOME_BELOW_MINIMUM",  # K05 → excluded
                "AMOUNT_OUTSIDE_PRODUCT_LIMITS",  # V03 → excluded
                "TENURE_OUTSIDE_PRODUCT_LIMITS",  # V04 → excluded
                "CREDIT_SCORE_BELOW_MINIMUM",  # K04 → NOT excluded by F1
                "NO_CREDIT_HISTORY",  # R01 → NOT excluded
                "",  # no codes → NOT excluded
                "INCOME_BELOW_MINIMUM;NO_CREDIT_HISTORY",  # K05 present → excluded
            ]
        }
    )
    mask = _filter_mask(rows, _F1_EXCLUDE)
    expected = [False, False, False, True, True, True, False]
    assert list(mask) == expected, f"F1 mask wrong: {list(mask)}"


def test_filter_mask_f2_also_excludes_k04():
    """F2 mask removes rows with V03, V04, K05, or K04."""
    from src.ml.baseline_filtered import _F2_EXCLUDE, _filter_mask

    rows = pd.DataFrame(
        {
            "reason_codes": [
                "CREDIT_SCORE_BELOW_MINIMUM",  # K04 → excluded in F2
                "NO_CREDIT_HISTORY",  # R01 → NOT excluded
                "INCOME_BELOW_MINIMUM",  # K05 → excluded
            ]
        }
    )
    mask = _filter_mask(rows, _F2_EXCLUDE)
    expected = [False, True, False]
    assert list(mask) == expected, f"F2 mask wrong: {list(mask)}"
