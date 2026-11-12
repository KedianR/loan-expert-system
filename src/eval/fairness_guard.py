"""Fairness plan pinning and execution guard.

Implements: WP-20, FR-23, DR-02, CR-06, P5-1 to P5-13.
Spec: docs/fairness-audit-plan.md, config/fairness.toml.

Guards:
- Writes reports/fairness/plan_pin.json (make fairness-pin).
- Refuses execution of fairness evaluations if:
  1. Pin file is missing.
  2. Plan or config hash differs from pin without an entry in docs/fairness-amendments.md.
  3. config/experiment.toml has [fairness] group_outcome_metrics = false.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path


class FairnessGuardError(Exception):
    """Raised when fairness guard conditions are violated."""

    pass


def file_sha256(path: Path | str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_fairness_pin(repo_root: Path | str = ".") -> Path:
    """Generate reports/fairness/plan_pin.json with SHA-256 of plan and config."""
    root = Path(repo_root)
    plan_path = root / "docs" / "fairness-audit-plan.md"
    config_path = root / "config" / "fairness.toml"
    out_dir = root / "reports" / "fairness"
    out_dir.mkdir(parents=True, exist_ok=True)
    pin_path = out_dir / "plan_pin.json"

    plan_hash = file_sha256(plan_path)
    cfg_hash = file_sha256(config_path)

    pin_data = {
        "plan_file": str(plan_path.as_posix()),
        "plan_sha256": plan_hash,
        "config_file": str(config_path.as_posix()),
        "config_sha256": cfg_hash,
    }

    pin_path.write_text(json.dumps(pin_data, indent=2) + "\n", encoding="utf-8")
    print(f"Fairness plan pin written to {pin_path}")
    print(f"  Plan:   {plan_hash}")
    print(f"  Config: {cfg_hash}")
    return pin_path


def has_amendments_logged(amendments_path: Path | str) -> bool:
    """Check if docs/fairness-amendments.md contains logged amendment rows."""
    p = Path(amendments_path)
    if not p.exists():
        return False
    lines = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()]
    # Look for table data rows after header (start with | FA- or non-empty ID)
    for ln in lines:
        if ln.startswith("|") and not ln.startswith("| ID") and not ln.startswith("|---"):
            parts = [col.strip() for col in ln.split("|")[1:-1]]
            if len(parts) >= 3 and parts[0]:
                return True
    return False


def verify_fairness_guard(
    repo_root: Path | str = ".",
    check_outcome_metrics_flag: bool = True,
) -> None:
    """Verify that fairness plan pin is valid before allowing fairness runs.

    Raises FairnessGuardError if guard fails.
    """
    root = Path(repo_root)
    pin_path = root / "reports" / "fairness" / "plan_pin.json"
    plan_path = root / "docs" / "fairness-audit-plan.md"
    config_path = root / "config" / "fairness.toml"
    amendments_path = root / "docs" / "fairness-amendments.md"
    exp_config_path = root / "config" / "experiment.toml"

    # 1. Pin file must exist
    if not pin_path.exists():
        raise FairnessGuardError(
            f"Fairness plan pin missing at {pin_path}. Run 'make fairness-pin' first."
        )

    # 2. Pin file structure and hashes
    try:
        pin_data = json.loads(pin_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise FairnessGuardError(f"Corrupt fairness pin file {pin_path}: {e}") from e

    expected_plan_hash = pin_data.get("plan_sha256")
    expected_cfg_hash = pin_data.get("config_sha256")

    current_plan_hash = file_sha256(plan_path)
    current_cfg_hash = file_sha256(config_path)

    plan_diff = current_plan_hash != expected_plan_hash
    cfg_diff = current_cfg_hash != expected_cfg_hash

    if plan_diff or cfg_diff:
        if not has_amendments_logged(amendments_path):
            raise FairnessGuardError(
                "Fairness plan or configuration has changed from pinned hash, "
                f"but no amendment is logged in {amendments_path}.\n"
                f"  Plan: current {current_plan_hash} vs pinned {expected_plan_hash}\n"
                f"  Config: current {current_cfg_hash} vs pinned {expected_cfg_hash}"
            )

    # 3. Check group_outcome_metrics flag if requested
    if check_outcome_metrics_flag:
        if exp_config_path.exists():
            with open(exp_config_path, "rb") as fh:
                exp_cfg = tomllib.load(fh)
            allowed = exp_cfg.get("fairness", {}).get("group_outcome_metrics", False)
            if not allowed:
                raise FairnessGuardError(
                    "group_outcome_metrics is false in config/experiment.toml. "
                    "Group outcome metrics are prohibited until guard is released after plan pinning."
                )


def main():
    write_fairness_pin()


if __name__ == "__main__":
    main()
