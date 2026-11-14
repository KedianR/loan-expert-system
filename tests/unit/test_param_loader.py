"""
Parameter loader tests: PT-01 to PT-15.

Implements: docs/09-file-formats.md §7 "Parameter loader (Phase 0)"
Requirements: FR-17, NFR-03, WP-03

Each test starts from the baseline params/params.toml and changes one thing,
then asserts the loader reports exactly the stated error code(s), or loads
cleanly for the valid cases.

PT-15 runs on params/params.toml only (rule files do not exist in Phase 0).
"""

from __future__ import annotations

import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]

# Insert src/ onto path so imports work without installation
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.engine.param_loader import load_params  # noqa: E402  (after path setup)
from src.engine.ruleset_hash import compute_hash, normalise_line_endings  # noqa: E402

# The baseline TOML as a single string.  Used in every test that modifies it.
BASELINE_TOML = """\
[meta]
schema_version = 1
params_version = "0.1.0"
currency = "INR"
description = "Illustrative personal loan policy, Credit Policy and Rule Catalog v0.1"

[product]
min_amount = 50000
max_amount = 2500000
amount_step = 5000
min_tenure_months = 12
max_tenure_months = 60
processing_fee_rate = "0.02"
income_multiple_cap = 10

[eligibility]
min_age = 18
min_monthly_income = 15000
min_credit_score = 650
min_employment_months_salaried = 6
min_employment_months_self_employed = 24
max_existing_foir = "0.50"
max_enquiries_6m = 5

[experimental]
x01_enabled = false
x02_enabled = false
max_age_at_maturity = 65
high_risk_region_tier = 3

[[band]]
id = "A"
min_score = 750
max_foir = "0.30"
rate_low = "11.0"
rate_high = "13.0"
indicative_rate = "12.0"
post_loan_foir_cap = "0.55"

[[band]]
id = "B"
min_score = 700
max_foir = "0.40"
rate_low = "13.0"
rate_high = "16.0"
indicative_rate = "14.5"
post_loan_foir_cap = "0.50"

[[band]]
id = "C"
min_score = 650
max_foir = "0.50"
rate_low = "16.0"
rate_high = "20.0"
indicative_rate = "18.0"
post_loan_foir_cap = "0.45"
"""


def _load_toml_string(toml_str: str):
    """Write toml_str to a temp file and load it."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False, encoding="utf-8") as f:
        f.write(toml_str)
        tmp_path = Path(f.name)
    try:
        result = load_params(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
    return result


def _error_codes(result) -> list[str]:
    return [e.code for e in result.errors]


def _warning_codes(result) -> list[str]:
    return [w.code for w in result.warnings]


def _has_error(result, code: str) -> bool:
    return code in _error_codes(result)


# ---------------------------------------------------------------------------
# PT-01: Baseline loads cleanly
# ---------------------------------------------------------------------------


class TestPT01:
    """PT-01: No change. Loads cleanly with correct types."""

    def test_loads_with_no_errors(self):
        """NFR-04: All policy thresholds in params/params.toml load cleanly without errors."""
        result = _load_toml_string(BASELINE_TOML)
        assert result.ok, f"Expected no errors, got: {result.errors}"

    def test_min_credit_score_is_int_650(self):
        """FR-17: min_credit_score must be int 650 (not a float, not a string)."""
        result = _load_toml_string(BASELINE_TOML)
        assert result.ok
        v = result.params["min_credit_score"]
        assert isinstance(v, int), f"Expected int, got {type(v)}"
        assert not isinstance(v, bool)
        assert v == 650

    def test_max_existing_foir_is_decimal_050(self):
        """FR-17: max_existing_foir must equal Decimal('0.50')."""
        result = _load_toml_string(BASELINE_TOML)
        assert result.ok
        v = result.params["max_existing_foir"]
        assert isinstance(v, Decimal), f"Expected Decimal, got {type(v)}"
        assert v == Decimal("0.50")

    def test_band_a_min_score_is_750(self):
        """Band A must have min_score 750."""
        result = _load_toml_string(BASELINE_TOML)
        assert result.ok
        band_a = next(b for b in result.bands if b.get("id") == "A")
        assert band_a["min_score"] == 750

    def test_no_floats_in_result(self):
        """A walk of the loaded object must find no float."""

        result = _load_toml_string(BASELINE_TOML)
        assert result.ok

        def _find_floats(obj, path=""):
            if isinstance(obj, float):
                return [path]
            if isinstance(obj, dict):
                found = []
                for k, v in obj.items():
                    found.extend(_find_floats(v, f"{path}.{k}"))
                return found
            if isinstance(obj, list):
                found = []
                for i, v in enumerate(obj):
                    found.extend(_find_floats(v, f"{path}[{i}]"))
                return found
            return []

        floats_in_params = _find_floats(result.params)
        floats_in_bands = _find_floats(result.bands)
        assert floats_in_params == [], f"Floats found in params: {floats_in_params}"
        assert floats_in_bands == [], f"Floats found in bands: {floats_in_bands}"


# ---------------------------------------------------------------------------
# PT-02: TOML float triggers FLOAT_FORBIDDEN
# ---------------------------------------------------------------------------


class TestPT02:
    """PT-02: max_existing_foir = 0.5 as a TOML float → FLOAT_FORBIDDEN."""

    def test_toml_float_gives_float_forbidden(self):
        toml = BASELINE_TOML.replace('max_existing_foir = "0.50"', "max_existing_foir = 0.5")
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "FLOAT_FORBIDDEN"), f"Errors: {result.errors}"


# ---------------------------------------------------------------------------
# PT-03: Malformed decimal strings → TYPE_ERROR
# ---------------------------------------------------------------------------


class TestPT03:
    """PT-03: Various malformed decimal strings each give TYPE_ERROR."""

    BAD_DECIMALS = ["0,5", "5e-1", ".5", "+0.5", " 0.5", "0.5 "]

    @pytest.mark.parametrize("bad", BAD_DECIMALS)
    def test_bad_decimal_gives_type_error(self, bad: str):
        toml = BASELINE_TOML.replace('max_existing_foir = "0.50"', f'max_existing_foir = "{bad}"')
        result = _load_toml_string(toml)
        assert not result.ok, f"Expected TYPE_ERROR for {bad!r} but loaded OK"
        assert _has_error(result, "TYPE_ERROR"), (
            f"Expected TYPE_ERROR for {bad!r}, got: {result.errors}"
        )


# ---------------------------------------------------------------------------
# PT-04: Missing required key → MISSING_KEY
# ---------------------------------------------------------------------------


class TestPT04:
    """PT-04: Remove min_credit_score → MISSING_KEY."""

    def test_missing_key(self):
        toml = BASELINE_TOML.replace("min_credit_score = 650\n", "")
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "MISSING_KEY"), f"Errors: {result.errors}"


# ---------------------------------------------------------------------------
# PT-05: Unknown key → UNKNOWN_KEY
# ---------------------------------------------------------------------------


class TestPT05:
    """PT-05: Add min_cibil = 650 → UNKNOWN_KEY."""

    def test_unknown_key(self):
        toml = BASELINE_TOML.replace("[eligibility]", "[eligibility]\nmin_cibil = 650")
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "UNKNOWN_KEY"), f"Errors: {result.errors}"


# ---------------------------------------------------------------------------
# PT-06: Duplicate parameter name → DUPLICATE_NAME
# ---------------------------------------------------------------------------


class TestPT06:
    """PT-06: Same parameter name in two sections → DUPLICATE_NAME."""

    def test_duplicate_name(self):
        # Put min_credit_score in both eligibility and product
        toml = BASELINE_TOML.replace("[product]\n", "[product]\nmin_credit_score = 650\n")
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "DUPLICATE_NAME") or _has_error(result, "UNKNOWN_KEY"), (
            f"Expected DUPLICATE_NAME or UNKNOWN_KEY, got: {result.errors}"
        )


# ---------------------------------------------------------------------------
# PT-07: Wrong type for integer field → TYPE_ERROR
# ---------------------------------------------------------------------------


class TestPT07:
    """PT-07: min_age = true and min_age = '18' each → TYPE_ERROR."""

    def test_bool_for_int(self):
        toml = BASELINE_TOML.replace("min_age = 18", "min_age = true")
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "TYPE_ERROR"), f"Errors: {result.errors}"

    def test_string_for_int(self):
        toml = BASELINE_TOML.replace("min_age = 18", 'min_age = "18"')
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "TYPE_ERROR"), f"Errors: {result.errors}"


# ---------------------------------------------------------------------------
# PT-08: Value out of range → RANGE_ERROR
# ---------------------------------------------------------------------------


class TestPT08:
    """PT-08: min_credit_score = 1000 → RANGE_ERROR."""

    def test_range_error(self):
        toml = BASELINE_TOML.replace("min_credit_score = 650", "min_credit_score = 1000")
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "RANGE_ERROR"), f"Errors: {result.errors}"


# ---------------------------------------------------------------------------
# PT-09: Amount ordering errors → ORDER_ERROR
# ---------------------------------------------------------------------------


class TestPT09:
    """PT-09: min_amount above max_amount, then max_amount not a multiple of step."""

    def test_min_above_max(self):
        toml = BASELINE_TOML.replace("min_amount = 50000", "min_amount = 3000000")
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "ORDER_ERROR"), f"Errors: {result.errors}"

    def test_max_not_multiple_of_step(self):
        toml = BASELINE_TOML.replace("max_amount = 2500000", "max_amount = 2500001")
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "ORDER_ERROR"), f"Errors: {result.errors}"


# ---------------------------------------------------------------------------
# PT-10: Swapped band order → BAND_ORDER
# ---------------------------------------------------------------------------


class TestPT10:
    """PT-10: Swap bands A and C → BAND_ORDER."""

    def test_band_order(self):
        # Replace band C (min_score 650) to come before band A (min_score 750)
        # We rebuild the band section with C first, then B, then A
        band_a = """\
[[band]]
id = "A"
min_score = 750
max_foir = "0.30"
rate_low = "11.0"
rate_high = "13.0"
indicative_rate = "12.0"
post_loan_foir_cap = "0.55"
"""
        band_b = """\
[[band]]
id = "B"
min_score = 700
max_foir = "0.40"
rate_low = "13.0"
rate_high = "16.0"
indicative_rate = "14.5"
post_loan_foir_cap = "0.50"
"""
        band_c = """\
[[band]]
id = "C"
min_score = 650
max_foir = "0.50"
rate_low = "16.0"
rate_high = "20.0"
indicative_rate = "18.0"
post_loan_foir_cap = "0.45"
"""
        prefix = BASELINE_TOML.split("[[band]]")[0]
        toml = prefix + band_c + band_b + band_a  # C first = wrong order
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "BAND_ORDER"), f"Errors: {result.errors}"


# ---------------------------------------------------------------------------
# PT-11: Last band min_score too high → BAND_COVERAGE_GAP
# ---------------------------------------------------------------------------


class TestPT11:
    """PT-11: Last band min_score = 700 (> min_credit_score 650) → BAND_COVERAGE_GAP."""

    def test_coverage_gap(self):
        # Replace band C min_score with 700 instead of 650
        toml = BASELINE_TOML.replace(
            'id = "C"\nmin_score = 650',
            'id = "C"\nmin_score = 700',
        )
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "BAND_COVERAGE_GAP"), f"Errors: {result.errors}"


# ---------------------------------------------------------------------------
# PT-12: Wrong indicative_rate → RATE_NOT_MIDPOINT
# ---------------------------------------------------------------------------


class TestPT12:
    """PT-12: Band A indicative_rate = '12.5' → RATE_NOT_MIDPOINT."""

    def test_rate_not_midpoint(self):
        toml = BASELINE_TOML.replace(
            'id = "A"\nmin_score = 750\nmax_foir = "0.30"\nrate_low = "11.0"\nrate_high = "13.0"\nindicative_rate = "12.0"',
            'id = "A"\nmin_score = 750\nmax_foir = "0.30"\nrate_low = "11.0"\nrate_high = "13.0"\nindicative_rate = "12.5"',
        )
        result = _load_toml_string(toml)
        assert not result.ok
        assert _has_error(result, "RATE_NOT_MIDPOINT"), f"Errors: {result.errors}"


# ---------------------------------------------------------------------------
# PT-13: Three faults in one file → all three reported
# ---------------------------------------------------------------------------


class TestPT13:
    """PT-13: Three faults in one file → all three error codes reported."""

    def test_three_errors_reported(self):
        # Fault 1: FLOAT_FORBIDDEN — max_existing_foir = 0.5
        # Fault 2: MISSING_KEY — remove min_credit_score
        # Fault 3: BAND_ORDER — swap A and C
        band_a = """\
[[band]]
id = "A"
min_score = 750
max_foir = "0.30"
rate_low = "11.0"
rate_high = "13.0"
indicative_rate = "12.0"
post_loan_foir_cap = "0.55"
"""
        band_c = """\
[[band]]
id = "C"
min_score = 650
max_foir = "0.50"
rate_low = "16.0"
rate_high = "20.0"
indicative_rate = "18.0"
post_loan_foir_cap = "0.45"
"""
        band_b = """\
[[band]]
id = "B"
min_score = 700
max_foir = "0.40"
rate_low = "13.0"
rate_high = "16.0"
indicative_rate = "14.5"
post_loan_foir_cap = "0.50"
"""
        # Start from baseline, apply three changes
        toml = BASELINE_TOML
        # 1. FLOAT_FORBIDDEN
        toml = toml.replace('max_existing_foir = "0.50"', "max_existing_foir = 0.5")
        # 2. MISSING_KEY
        toml = toml.replace("min_credit_score = 650\n", "")
        # 3. BAND_ORDER: replace band section with C first
        prefix = toml.split("[[band]]")[0]
        toml = prefix + band_c + band_b + band_a

        result = _load_toml_string(toml)
        assert not result.ok
        codes = set(_error_codes(result))
        assert "FLOAT_FORBIDDEN" in codes, f"Missing FLOAT_FORBIDDEN in {codes}"
        assert "MISSING_KEY" in codes, f"Missing MISSING_KEY in {codes}"
        assert "BAND_ORDER" in codes, f"Missing BAND_ORDER in {codes}"


# ---------------------------------------------------------------------------
# PT-14: Lower rate in band C triggers WARN_PRICING_ORDER but loads OK
# ---------------------------------------------------------------------------


class TestPT14:
    """PT-14: Band C rate_low=10.0, rate_high=12.0, indicative_rate=11.0 → loads, WARN_PRICING_ORDER."""

    def test_pricing_order_warning(self):
        toml = BASELINE_TOML.replace(
            'id = "C"\nmin_score = 650\nmax_foir = "0.50"\nrate_low = "16.0"\nrate_high = "20.0"\nindicative_rate = "18.0"',
            'id = "C"\nmin_score = 650\nmax_foir = "0.50"\nrate_low = "10.0"\nrate_high = "12.0"\nindicative_rate = "11.0"',
        )
        result = _load_toml_string(toml)
        assert result.ok, f"Expected OK, got errors: {result.errors}"
        assert "WARN_PRICING_ORDER" in _warning_codes(result), (
            f"Expected WARN_PRICING_ORDER warning, got: {result.warnings}"
        )


# ---------------------------------------------------------------------------
# PT-15: Hash is line-ending-agnostic but content-sensitive
# ---------------------------------------------------------------------------


class TestPT15:
    """
    PT-15: Hash the baseline file with LF line ends, then with CRLF.
    Same hash. Changing one character gives a different hash.

    Per phase instructions, runs on params/params.toml alone (rule files
    do not yet exist). Logged in docs/open-questions.md as OQ-003.
    """

    def test_lf_and_crlf_give_same_hash(self):
        """LF and CRLF versions must hash identically."""
        content_lf = BASELINE_TOML.encode("utf-8")
        # Ensure we're using LF (replace any CRLF just in case)
        content_lf = content_lf.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        # Create CRLF version
        content_crlf = content_lf.replace(b"\n", b"\r\n")

        hash_lf = compute_hash([("params/params.toml", content_lf)])
        hash_crlf = compute_hash([("params/params.toml", content_crlf)])
        assert hash_lf == hash_crlf, f"LF hash {hash_lf} differs from CRLF hash {hash_crlf}"

    def test_changing_one_character_changes_hash(self):
        """A single-character change must produce a different hash."""
        content_original = BASELINE_TOML.encode("utf-8")
        # Change one character: bump schema_version from 1 to 2
        content_modified = BASELINE_TOML.replace("schema_version = 1", "schema_version = 2").encode(
            "utf-8"
        )

        hash_original = compute_hash([("params/params.toml", content_original)])
        hash_modified = compute_hash([("params/params.toml", content_modified)])
        assert hash_original != hash_modified, "Hash must change when content changes"

    def test_hash_format(self):
        """Hash must start with 'sha256:' and be 71 characters total."""
        content = BASELINE_TOML.encode("utf-8")
        h = compute_hash([("params/params.toml", content)])
        assert h.startswith("sha256:"), f"Hash must start with 'sha256:', got: {h}"
        assert len(h) == len("sha256:") + 64, f"Expected 71 chars, got {len(h)}: {h}"

    def test_hash_on_actual_params_file(self):
        """Running on the real params/params.toml produces a stable hash."""
        params_path = REPO_ROOT / "params" / "params.toml"
        assert params_path.exists(), f"params/params.toml not found at {params_path}"
        content = params_path.read_bytes()
        h = compute_hash([("params/params.toml", content)])
        assert h.startswith("sha256:")
        # Hash is deterministic: running twice gives the same result
        h2 = compute_hash([("params/params.toml", content)])
        assert h == h2

    def test_bom_stripped(self):
        """A UTF-8 BOM at the start of the file is stripped before hashing."""
        content_no_bom = BASELINE_TOML.encode("utf-8")
        content_with_bom = b"\xef\xbb\xbf" + content_no_bom
        normalised_no_bom = normalise_line_endings(content_no_bom)
        normalised_with_bom = normalise_line_endings(content_with_bom)
        assert normalised_no_bom == normalised_with_bom, (
            "BOM should be stripped so both versions normalise identically"
        )
