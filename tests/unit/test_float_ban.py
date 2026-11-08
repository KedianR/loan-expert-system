"""
Float-ban checker tests.

Verifies that the checker detects floats in src/calc and that the current
src/calc directory (empty in Phase 0) passes cleanly.

Implements: AGENTS.md Hard Rule 2, NFR-03, WP-01
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.check_floats import check_file, check_tree  # noqa: E402


class TestFloatBanChecker:
    """Tests for the float-ban static checker."""

    def test_clean_file_has_no_violations(self):
        """A file with only Decimal and int has no violations."""
        source = """\
from decimal import Decimal
def add(a: Decimal, b: Decimal) -> Decimal:
    return a + b

x: int = 42
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            tmp = Path(f.name)
        try:
            violations = check_file(tmp)
            assert violations == [], f"Unexpected violations: {violations}"
        finally:
            tmp.unlink(missing_ok=True)

    def test_float_literal_detected(self):
        """A float literal in the file is reported as a violation."""
        source = """\
# This is a comment
x = 0.5  # float literal - should be caught
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            tmp = Path(f.name)
        try:
            violations = check_file(tmp)
            assert len(violations) >= 1, "Expected at least one violation"
            assert any("float literal" in desc for _, _, desc in violations), (
                f"Expected 'float literal' in violation desc, got: {violations}"
            )
        finally:
            tmp.unlink(missing_ok=True)

    def test_float_call_detected(self):
        """A call to float() is reported as a violation."""
        source = """\
def bad(x):
    return float(x)  # forbidden in src/calc
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            tmp = Path(f.name)
        try:
            violations = check_file(tmp)
            assert len(violations) >= 1
            assert any("float()" in desc for _, _, desc in violations)
        finally:
            tmp.unlink(missing_ok=True)

    def test_src_calc_is_clean(self):
        """The current src/calc directory must have no float violations."""
        calc_dir = REPO_ROOT / "src" / "calc"
        assert calc_dir.exists(), f"src/calc not found at {calc_dir}"
        violations = check_tree(calc_dir)
        assert violations == [], "Float violations found in src/calc:\n" + "\n".join(
            f"  {fp}:{lineno}: {desc}" for fp, lineno, desc in violations
        )

    def test_src_facts_is_clean(self):
        """The current src/facts directory must have no float violations."""
        facts_dir = REPO_ROOT / "src" / "facts"
        assert facts_dir.exists(), f"src/facts not found at {facts_dir}"
        violations = check_tree(facts_dir)
        assert violations == [], "Float violations found in src/facts:\n" + "\n".join(
            f"  {fp}:{lineno}: {desc}" for fp, lineno, desc in violations
        )

    def test_injected_float_in_calc_or_facts_fails_check(self):
        """
        Proves the checker fails when a float is introduced in src/calc or src/facts.
        Tested by writing a temporary file into both directories and verifying
        check_file detects the violation.
        """
        bad_source = """\
# Injected float for test
def bad_calc():
    return 0.42
"""
        for target_dir in [REPO_ROOT / "src" / "calc", REPO_ROOT / "src" / "facts"]:
            assert target_dir.exists()
            tmp_file = target_dir / "_temp_injected_float.py"
            try:
                tmp_file.write_text(bad_source, encoding="utf-8")
                violations = check_tree(target_dir)
                assert len(violations) >= 1, (
                    f"Checker failed to detect injected float in {target_dir}"
                )
                assert any("_temp_injected_float.py" in fp for fp, _, _ in violations)
            finally:
                tmp_file.unlink(missing_ok=True)

    def test_injected_float_fails_check(self):
        """
        Proves the check fails when a float is added to a calc-like file.
        This is the 'build must fail' test from WP-01.
        """
        bad_source = """\
# Intentional float – this file should fail the float-ban check
RATE = 0.12  # float literal, forbidden
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(bad_source)
            tmp = Path(f.name)
        try:
            violations = check_file(tmp)
            assert len(violations) >= 1, (
                "Float-ban check failed to detect a float literal – the check is broken"
            )
        finally:
            tmp.unlink(missing_ok=True)
