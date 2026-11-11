"""Unit test for protected store isolation (WP-15, WP-17, DR-02, CR-06).

Spec: docs/08-datasets.md §3, docs/ml-baseline-spec.md §10.
Static scan: no module under src/ engine, calc, explain, audit, api or ml
mentions protected column names or protected file paths.
"""

from __future__ import annotations

from pathlib import Path

FORBIDDEN_PROTECTED_TOKENS = [
    "CODE_GENDER",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "d2_protected",
    "d3_protected",
]

ALLOWED_FILES = {
    Path("src/data/d2_map.py").resolve(),
    Path("src/data/fallback.py").resolve(),
    Path("src/data/group_sizes.py").resolve(),
    Path("src/data/manifest.py").resolve(),
    Path("data/synthetic/d3_generator.py").resolve(),
}


def test_protected_store_isolation_static_scan() -> None:
    """Verify that protected store columns are never referenced in decision/ML code."""
    src_dir = Path("src")
    violations: list[str] = []

    for py_file in src_dir.rglob("*.py"):
        if py_file.resolve() in ALLOWED_FILES:
            continue

        content = py_file.read_text(encoding="utf-8")
        for token in FORBIDDEN_PROTECTED_TOKENS:
            if token in content:
                violations.append(f"{py_file}: contains forbidden token '{token}'")

    assert not violations, "Protected store tokens leaked into forbidden modules:\n" + "\n".join(
        violations
    )
