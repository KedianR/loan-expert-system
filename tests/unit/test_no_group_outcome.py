"""Unit test ensuring no group-level outcome metrics in Phase 4 (WP-17, D-06).

Spec: docs/ml-baseline-spec.md §7, docs/experiment-protocol.md §5.
Guard:
- Group sizes module only computes counts per group.
- Never reads decisions or outcome columns.
- No outcome metrics by group are written in Phase 4.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd


def test_group_sizes_never_reads_decisions_or_outcomes() -> None:
    """Verify that src/data/group_sizes.py never references decisions, TARGET, or outcome."""
    code_path = Path("src/data/group_sizes.py")
    assert code_path.exists(), "src/data/group_sizes.py missing"
    content = code_path.read_text(encoding="utf-8")

    tree = ast.parse(content, filename=str(code_path))

    # Check string constants in AST
    forbidden_strings = {
        "decisions",
        "d2_decisions.csv",
        "d3_decisions.csv",
        "TARGET",
        "sim_default",
        "policy_decision",
        "eligible",
        "ineligible",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value.strip()
            assert val not in forbidden_strings, (
                f"group_sizes.py contains forbidden outcome string: {val!r}"
            )


def test_group_size_tables_have_no_outcome_columns() -> None:
    """Verify that generated group size tables contain ONLY counts and flags."""
    for dataset in ("d2", "d3"):
        gs_path = Path(f"data/group_sizes/{dataset}_group_sizes.csv")
        assert gs_path.exists(), f"Group size table missing: {gs_path}"
        df = pd.read_csv(gs_path)

        expected_columns = {
            "dataset",
            "attribute",
            "group_value",
            "count_full",
            "too_small_full",
            "count_test",
            "too_small_test",
        }
        assert set(df.columns) == expected_columns, (
            f"Unexpected columns in group sizes table: {df.columns}"
        )

        # No outcome rates
        for col in df.columns:
            assert "rate" not in col.lower()
            assert "approval" not in col.lower()
            assert "score" not in col.lower()
            assert "default" not in col.lower()
