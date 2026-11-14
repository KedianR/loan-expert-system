"""Edge-case tests (WP-18, FR-24, P5-13).

Requirements:
  - FR-24: Edge-case evaluation covers categories MD, TB, TF, RC, AD.
  - P5-13: Expected behavior is written from the Rule Catalog before the first run.
  - Test 1: Every catalog case has a row with both systems' outputs.
  - Test 2: expected.csv was committed before results.csv (commit order check).
"""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_FR24_every_catalog_case_has_both_systems_outputs() -> None:
    """FR-24, P5-13: Every catalog case in expected.csv has a row with both systems' outputs in results.csv."""
    expected_path = REPO_ROOT / "reports" / "edge_cases" / "expected.csv"
    results_path = REPO_ROOT / "reports" / "edge_cases" / "results.csv"

    assert expected_path.exists(), f"Missing {expected_path}"
    assert results_path.exists(), f"Missing {results_path}"

    with open(expected_path, encoding="utf-8") as f:
        expected_cases = {row["case_id"]: row for row in csv.DictReader(f)}

    with open(results_path, encoding="utf-8") as f:
        results_cases = {row["case_id"]: row for row in csv.DictReader(f)}

    assert len(expected_cases) == 64, f"Expected 64 catalog cases, found {len(expected_cases)}"
    assert len(results_cases) == 64, f"Expected 64 result cases, found {len(results_cases)}"

    for case_id, exp_row in expected_cases.items():
        assert case_id in results_cases, f"Missing case {case_id} in results.csv"
        res_row = results_cases[case_id]

        # Rule system output must be present
        rule_dec = res_row.get("rule_decision", "").strip()
        assert rule_dec in ("eligible", "ineligible", "refer", "validation_error"), (
            f"Case {case_id}: invalid rule_decision '{rule_dec}'"
        )

        # ML baseline output must be present (lr and gb)
        lr_score = res_row.get("lr_score", "").strip()
        lr_dec = res_row.get("lr_decision", "").strip()
        gb_score = res_row.get("gb_score", "").strip()
        gb_dec = res_row.get("gb_decision", "").strip()

        assert lr_score != "", f"Case {case_id}: missing lr_score"
        assert lr_dec in ("eligible", "ineligible", "error"), (
            f"Case {case_id}: invalid lr_decision '{lr_dec}'"
        )
        assert gb_score != "", f"Case {case_id}: missing gb_score"
        assert gb_dec in ("eligible", "ineligible", "error"), (
            f"Case {case_id}: invalid gb_decision '{gb_dec}'"
        )


def test_FR24_expected_csv_committed_before_results() -> None:
    """P5-13: expected.csv was committed before results.csv (commit order check)."""
    # Query git log for the earliest commit introducing expected.csv and results.csv
    try:
        r_exp = subprocess.run(
            [
                "git",
                "log",
                "--follow",
                "--oneline",
                "--format=%H",
                "--",
                "reports/edge_cases/expected.csv",
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT,
        )
        r_res = subprocess.run(
            [
                "git",
                "log",
                "--follow",
                "--oneline",
                "--format=%H",
                "--",
                "reports/edge_cases/results.csv",
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT,
        )

        commits_exp = [c.strip() for c in r_exp.stdout.splitlines() if c.strip()]
        commits_res = [c.strip() for c in r_res.stdout.splitlines() if c.strip()]

        assert commits_exp, "No git commit found for reports/edge_cases/expected.csv"
        assert commits_res, "No git commit found for reports/edge_cases/results.csv"

        # The initial commit of expected.csv is the last in commits_exp
        first_commit_exp = commits_exp[-1]
        first_commit_res = commits_res[-1]

        # Verify that first_commit_exp is an ancestor of first_commit_res (or earlier)
        r_merge_base = subprocess.run(
            ["git", "merge-base", "--is-ancestor", first_commit_exp, first_commit_res],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            cwd=REPO_ROOT,
        )
        assert r_merge_base.returncode == 0, (
            f"expected.csv ({first_commit_exp[:7]}) must be an ancestor of results.csv ({first_commit_res[:7]})"
        )
    except (FileNotFoundError, OSError):
        # Fallback if git executable fails
        exp_mtime = (REPO_ROOT / "reports" / "edge_cases" / "expected.csv").stat().st_mtime
        res_mtime = (REPO_ROOT / "reports" / "edge_cases" / "results.csv").stat().st_mtime
        assert exp_mtime <= res_mtime, "expected.csv timestamp is after results.csv"
