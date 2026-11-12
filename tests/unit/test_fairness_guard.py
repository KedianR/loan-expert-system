"""Unit tests for the fairness plan pin and execution guard.

Implements: WP-20, FR-23, DR-02, CR-06.
Spec: docs/fairness-audit-plan.md, config/fairness.toml.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.eval.fairness_guard import (
    FairnessGuardError,
    verify_fairness_guard,
    write_fairness_pin,
)


def test_fairness_guard_refuses_when_pin_missing(tmp_path: Path):
    """Guard must raise FairnessGuardError if reports/fairness/plan_pin.json is absent."""
    # Create fake directory structure without pin
    fake_plan = tmp_path / "docs" / "fairness-audit-plan.md"
    fake_cfg = tmp_path / "config" / "fairness.toml"
    fake_plan.parent.mkdir(parents=True, exist_ok=True)
    fake_cfg.parent.mkdir(parents=True, exist_ok=True)
    fake_plan.write_text("fake plan", encoding="utf-8")
    fake_cfg.write_text("fake config", encoding="utf-8")

    with pytest.raises(FairnessGuardError, match="missing"):
        verify_fairness_guard(repo_root=tmp_path, check_outcome_metrics_flag=False)


def test_fairness_guard_refuses_on_changed_file_without_amendment(tmp_path: Path):
    """Guard must refuse to run if plan or config hash changes after pinning without amendment."""
    docs_dir = tmp_path / "docs"
    cfg_dir = tmp_path / "config"
    docs_dir.mkdir(parents=True, exist_ok=True)
    cfg_dir.mkdir(parents=True, exist_ok=True)

    plan_file = docs_dir / "fairness-audit-plan.md"
    cfg_file = cfg_dir / "fairness.toml"
    amend_file = docs_dir / "fairness-amendments.md"

    plan_file.write_text("Original plan content v1.0", encoding="utf-8")
    cfg_file.write_text("key = 'original'", encoding="utf-8")
    amend_file.write_text(
        "# Amendments\n\n| ID | Date | What | Reason | Results |\n|---|---|---|---|---|\n",
        encoding="utf-8",
    )

    # Generate pin
    write_fairness_pin(repo_root=tmp_path)

    # Verification should pass initially
    verify_fairness_guard(repo_root=tmp_path, check_outcome_metrics_flag=False)

    # Change plan content
    plan_file.write_text("Modified plan content without logging!", encoding="utf-8")

    # Must raise FairnessGuardError
    with pytest.raises(FairnessGuardError, match="changed from pinned hash"):
        verify_fairness_guard(repo_root=tmp_path, check_outcome_metrics_flag=False)


def test_fairness_guard_permits_changed_file_when_amendment_is_logged(tmp_path: Path):
    """Guard permits changed plan or config if logged in docs/fairness-amendments.md."""
    docs_dir = tmp_path / "docs"
    cfg_dir = tmp_path / "config"
    docs_dir.mkdir(parents=True, exist_ok=True)
    cfg_dir.mkdir(parents=True, exist_ok=True)

    plan_file = docs_dir / "fairness-audit-plan.md"
    cfg_file = cfg_dir / "fairness.toml"
    amend_file = docs_dir / "fairness-amendments.md"

    plan_file.write_text("Original plan content v1.0", encoding="utf-8")
    cfg_file.write_text("key = 'original'", encoding="utf-8")
    amend_file.write_text(
        "# Amendments\n\n| ID | Date | What | Reason | Results |\n|---|---|---|---|---|\n",
        encoding="utf-8",
    )

    write_fairness_pin(repo_root=tmp_path)

    # Change config and log amendment
    cfg_file.write_text("key = 'modified_legitimately'", encoding="utf-8")
    amend_file.write_text(
        "# Amendments\n\n"
        "| ID | Date | What | Reason | Results |\n"
        "|---|---|---|---|---|\n"
        "| FA-001 | 2026-11-13 | Updated threshold | Pre-registered justification | No |\n",
        encoding="utf-8",
    )

    # Should pass because amendment is logged
    verify_fairness_guard(repo_root=tmp_path, check_outcome_metrics_flag=False)


def test_fairness_guard_refuses_when_group_outcome_metrics_is_false(tmp_path: Path):
    """Guard refuses if group_outcome_metrics = false in config/experiment.toml."""
    docs_dir = tmp_path / "docs"
    cfg_dir = tmp_path / "config"
    docs_dir.mkdir(parents=True, exist_ok=True)
    cfg_dir.mkdir(parents=True, exist_ok=True)

    plan_file = docs_dir / "fairness-audit-plan.md"
    cfg_file = cfg_dir / "fairness.toml"
    exp_cfg_file = cfg_dir / "experiment.toml"
    amend_file = docs_dir / "fairness-amendments.md"

    plan_file.write_text("Plan v1.0", encoding="utf-8")
    cfg_file.write_text("key = 'val'", encoding="utf-8")
    amend_file.write_text("# Amendments\n", encoding="utf-8")
    exp_cfg_file.write_text("[fairness]\ngroup_outcome_metrics = false\n", encoding="utf-8")

    write_fairness_pin(repo_root=tmp_path)

    with pytest.raises(FairnessGuardError, match="group_outcome_metrics is false"):
        verify_fairness_guard(repo_root=tmp_path, check_outcome_metrics_flag=True)
