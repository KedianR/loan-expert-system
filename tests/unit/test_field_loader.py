"""
Field loader unit tests.

Implements: WP-05, docs/09-file-formats.md §3
Tests rules/fields.toml loading, schema validation, float rejection, and error collection.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.engine.field_loader import load_fields

REPO_ROOT = Path(__file__).resolve().parents[2]
FIELDS_PATH = REPO_ROOT / "rules" / "fields.toml"


class TestFieldLoader:
    """Tests for loading and validating field registry."""

    def test_baseline_fields_toml_loads_cleanly(self):
        """Baseline rules/fields.toml has 27 fields with 0 errors and 0 warnings."""
        res = load_fields(FIELDS_PATH)
        assert res.ok, f"Expected clean load, got errors: {res.errors}"
        assert len(res.warnings) == 0
        assert len(res.fields) == 27
        input_fields = [f for f in res.fields if f["kind"] == "input"]
        derived_fields = [f for f in res.fields if f["kind"] == "derived"]
        assert len(input_fields) == 15
        assert len(derived_fields) == 12

    def test_float_forbidden_in_fields_toml(self):
        """A TOML float in a field table is caught with FLOAT_FORBIDDEN."""
        content = """\
[[field]]
name = "bad_field"
kind = "input"
type = "decimal"
min = 0.5
predicate = "bad"
readable_from = "validation"
required = true
nullable = false
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp = Path(f.name)
        try:
            res = load_fields(tmp)
            assert not res.ok
            codes = [e.code for e in res.errors]
            assert "FLOAT_FORBIDDEN" in codes
        finally:
            tmp.unlink(missing_ok=True)

    def test_missing_required_keys_caught(self):
        """Missing name, kind, type, or predicate are reported."""
        content = """\
[[field]]
unit = "years"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp = Path(f.name)
        try:
            res = load_fields(tmp)
            assert not res.ok
            codes = [e.code for e in res.errors]
            assert "MISSING_KEY" in codes
        finally:
            tmp.unlink(missing_ok=True)

    def test_unknown_key_caught(self):
        """Unknown key on field is reported."""
        content = """\
[[field]]
name = "foo"
kind = "input"
type = "int"
predicate = "foo"
readable_from = "validation"
required = true
nullable = false
unknown_attr = "bar"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp = Path(f.name)
        try:
            res = load_fields(tmp)
            assert not res.ok
            codes = [e.code for e in res.errors]
            assert "UNKNOWN_KEY" in codes
        finally:
            tmp.unlink(missing_ok=True)

    def test_range_error_caught(self):
        """min > max is reported."""
        content = """\
[[field]]
name = "bad_range"
kind = "input"
type = "int"
min = 100
max = 10
predicate = "bad_range"
readable_from = "validation"
required = true
nullable = false
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp = Path(f.name)
        try:
            res = load_fields(tmp)
            assert not res.ok
            codes = [e.code for e in res.errors]
            assert "RANGE_ERROR" in codes
        finally:
            tmp.unlink(missing_ok=True)
