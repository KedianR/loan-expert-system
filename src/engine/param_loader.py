"""
Parameter file loader for params/params.toml.

Implements: FR-17, WP-03
Spec: docs/09-file-formats.md sections 2, 5, 6

Rules:
- Collects all errors in one pass; never stops at the first error.
- No default values; a missing key is MISSING_KEY.
- No type coercion; a decimal string is not an int, an int is not a bool.
- No TOML floats; FLOAT_FORBIDDEN is raised if any float appears.
- Unknown keys are UNKNOWN_KEY.
- Returns integers as int, decimals as Decimal, booleans as bool.
- Exits with non-zero status on any error; warnings do not change the exit status.
"""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Error and warning records
# ---------------------------------------------------------------------------

DECIMAL_PATTERN_HELP = "digits, optional point, digits; no sign, no exponent, digit before point"


@dataclass(frozen=True)
class LoadError:
    """An error that stops the load."""

    code: str
    file: str
    place: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} {self.file} [{self.place}]: {self.message}"


@dataclass(frozen=True)
class LoadWarning:
    """A warning that is printed but does not stop the load."""

    code: str
    file: str
    place: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} {self.file} [{self.place}]: {self.message}"


# ---------------------------------------------------------------------------
# Known parameter schema
# (name -> section, type_tag, valid_range_fn_or_None)
# type_tag: "int" | "decimal" | "bool"
# ---------------------------------------------------------------------------


# Valid range predicates receive the parsed value and return True if in range.
def _range_int(lo: int | None, hi: int | None):
    def check(v: int) -> bool:
        if lo is not None and v < lo:
            return False
        if hi is not None and v > hi:
            return False
        return True

    return check


def _range_decimal(lo_str: str | None, hi_str: str | None, lo_exclusive: bool = False):
    lo = Decimal(lo_str) if lo_str is not None else None
    hi = Decimal(hi_str) if hi_str is not None else None

    def check(v: Decimal) -> bool:
        if lo is not None:
            if lo_exclusive and v <= lo:
                return False
            if not lo_exclusive and v < lo:
                return False
        if hi is not None and v > hi:
            return False
        return True

    return check


# Schema: maps parameter name -> (section, type_tag, range_checker, range_description)
SCALAR_SCHEMA: dict[str, tuple[str, str, Any, str]] = {
    # product
    "min_amount": ("product", "int", _range_int(1, None), "1 or more"),
    "max_amount": ("product", "int", _range_int(1, None), "1 or more"),
    "amount_step": ("product", "int", _range_int(1, None), "1 or more"),
    "min_tenure_months": ("product", "int", _range_int(1, None), "1 or more"),
    "max_tenure_months": ("product", "int", _range_int(1, None), "1 or more"),
    "processing_fee_rate": (
        "product",
        "decimal",
        _range_decimal("0", "1", lo_exclusive=True),
        "above 0, at most 1",
    ),
    "income_multiple_cap": ("product", "int", _range_int(1, None), "1 or more"),
    # eligibility
    "min_age": ("eligibility", "int", _range_int(1, 120), "1 to 120"),
    "min_monthly_income": ("eligibility", "int", _range_int(0, None), "0 or more"),
    "min_credit_score": ("eligibility", "int", _range_int(300, 900), "300 to 900"),
    "min_employment_months_salaried": ("eligibility", "int", _range_int(0, 600), "0 to 600"),
    "min_employment_months_self_employed": ("eligibility", "int", _range_int(0, 600), "0 to 600"),
    "max_existing_foir": (
        "eligibility",
        "decimal",
        _range_decimal("0", "1", lo_exclusive=True),
        "above 0, at most 1",
    ),
    "max_enquiries_6m": ("eligibility", "int", _range_int(0, None), "0 or more"),
    # experimental
    "x01_enabled": ("experimental", "bool", None, "true or false"),
    "x02_enabled": ("experimental", "bool", None, "true or false"),
    "max_age_at_maturity": ("experimental", "int", _range_int(18, 120), "18 to 120"),
    "high_risk_region_tier": ("experimental", "int", _range_int(1, 3), "1 to 3"),
}

BAND_KEYS = {
    "id",
    "min_score",
    "max_foir",
    "rate_low",
    "rate_high",
    "indicative_rate",
    "post_loan_foir_cap",
}

# meta keys allowed
META_KEYS = {"schema_version", "params_version", "currency", "description"}

# Top-level section names allowed
ALLOWED_SECTIONS = {"meta", "product", "eligibility", "experimental", "band"}


# ---------------------------------------------------------------------------
# Decimal string validator
# ---------------------------------------------------------------------------


def _is_valid_decimal_string(s: str) -> bool:
    """
    A decimal string is digits, an optional point and more digits:
    no sign, no exponent, no spaces, a digit before the point.
    '0.5' yes; '.5', '5e-1', '0,5' and '+0.5' no.
    """
    if not isinstance(s, str):
        return False
    # Must start with a digit
    if not s or not s[0].isdigit():
        return False
    # May have exactly one dot, rest are digits
    parts = s.split(".")
    if len(parts) > 2:
        return False
    for part in parts:
        if not part.isdigit():
            return False
    return True


# ---------------------------------------------------------------------------
# Float detection
# ---------------------------------------------------------------------------


def _find_floats(obj: Any, path: str) -> list[tuple[str, Any]]:
    """Recursively find any float values in a nested structure."""
    results = []
    if isinstance(obj, float):
        results.append((path, obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            results.extend(_find_floats(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            results.extend(_find_floats(v, f"{path}[{i}]"))
    return results


# ---------------------------------------------------------------------------
# Main loader
# ---------------------------------------------------------------------------


@dataclass
class LoadResult:
    """Result of loading params/params.toml."""

    params: dict[str, Any] = field(default_factory=dict)
    bands: list[dict[str, Any]] = field(default_factory=list)
    errors: list[LoadError] = field(default_factory=list)
    warnings: list[LoadWarning] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def load_params(path: Path | str) -> LoadResult:
    """
    Load and validate params/params.toml.

    Returns a LoadResult. If result.ok is False, params and bands may be
    incomplete; callers must check result.ok before using them.

    Implements sections 2 and 5 of docs/09-file-formats.md.
    """
    path = Path(path)
    result = LoadResult()
    errors = result.errors
    warnings = result.warnings
    file_str = str(path)

    # --- Parse TOML ---
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(LoadError("MISSING_KEY", file_str, "(file)", f"File not found: {path}"))
        return result
    except tomllib.TOMLDecodeError as exc:
        errors.append(LoadError("PARSE_ERROR", file_str, "(file)", str(exc)))
        return result

    # --- Float check (must be first; a float anywhere is an error) ---
    for fpath, fval in _find_floats(raw, ""):
        errors.append(
            LoadError(
                "FLOAT_FORBIDDEN",
                file_str,
                fpath,
                f"value {fval!r} is a float; write it as a quoted decimal string",
            )
        )
    # Continue even if floats found; collect all errors.

    # --- Check top-level keys ---
    for key in raw:
        if key == "band":
            continue  # handled separately
        if key not in ALLOWED_SECTIONS:
            errors.append(
                LoadError("UNKNOWN_KEY", file_str, key, f"Unknown top-level section '{key}'")
            )

    # --- meta section (optional checks, not strict schema) ---
    meta = raw.get("meta", {})
    if not isinstance(meta, dict):
        errors.append(LoadError("TYPE_ERROR", file_str, "meta", "meta must be a table"))
    else:
        for k in meta:
            if k not in META_KEYS:
                errors.append(
                    LoadError("UNKNOWN_KEY", file_str, f"meta.{k}", f"Unknown meta key '{k}'")
                )

    # --- Collect all parameter names for duplicate detection ---
    # Scan all scalar sections for the known parameters
    seen_names: dict[str, str] = {}  # name -> first seen location

    parsed_scalars: dict[str, Any] = {}

    for param_name, (section, type_tag, range_check, range_desc) in SCALAR_SCHEMA.items():
        location = f"{section}.{param_name}"

        # Duplicate check: has this name appeared in any other section?
        if param_name in seen_names:
            errors.append(
                LoadError(
                    "DUPLICATE_NAME",
                    file_str,
                    location,
                    f"Parameter '{param_name}' also appears in [{seen_names[param_name]}]",
                )
            )
            continue
        seen_names[param_name] = section

        section_data = raw.get(section, {})
        if not isinstance(section_data, dict):
            # section itself is wrong type; will be caught by another check
            errors.append(
                LoadError("MISSING_KEY", file_str, location, f"Section [{section}] is not a table")
            )
            continue

        if param_name not in section_data:
            errors.append(
                LoadError(
                    "MISSING_KEY",
                    file_str,
                    location,
                    f"Required parameter '{param_name}' is missing",
                )
            )
            continue

        raw_val = section_data[param_name]

        # Float check for this specific value (already caught globally, but be explicit)
        if isinstance(raw_val, float):
            errors.append(
                LoadError(
                    "FLOAT_FORBIDDEN",
                    file_str,
                    location,
                    f"value {raw_val!r} is a float; write it as a quoted decimal string",
                )
            )
            continue

        # Type check and parse
        parsed_val = _parse_typed_value(raw_val, type_tag, file_str, location, errors, range_desc)
        if parsed_val is None:
            continue  # error already added

        # Range check
        if range_check is not None and not range_check(parsed_val):
            errors.append(
                LoadError(
                    "RANGE_ERROR",
                    file_str,
                    location,
                    f"value {raw_val!r} is outside valid range ({range_desc})",
                )
            )
            continue

        parsed_scalars[param_name] = parsed_val

    # --- Check for unknown keys in product/eligibility/experimental sections ---
    param_names_by_section: dict[str, set[str]] = {}
    for param_name, (section, _, _, _) in SCALAR_SCHEMA.items():
        param_names_by_section.setdefault(section, set()).add(param_name)

    for section in ("product", "eligibility", "experimental"):
        section_data = raw.get(section, {})
        if isinstance(section_data, dict):
            for k in section_data:
                allowed_in_section = param_names_by_section.get(section, set())
                if k not in allowed_in_section:
                    errors.append(
                        LoadError(
                            "UNKNOWN_KEY",
                            file_str,
                            f"{section}.{k}",
                            f"Unknown parameter '{k}' in section [{section}]",
                        )
                    )

    # --- Cross-parameter checks (ORDER_ERROR) ---
    if "min_amount" in parsed_scalars and "max_amount" in parsed_scalars:
        if parsed_scalars["min_amount"] > parsed_scalars["max_amount"]:
            errors.append(
                LoadError(
                    "ORDER_ERROR",
                    file_str,
                    "product",
                    f"min_amount ({parsed_scalars['min_amount']}) exceeds max_amount ({parsed_scalars['max_amount']})",
                )
            )
    if (
        "amount_step" in parsed_scalars
        and "min_amount" in parsed_scalars
        and "max_amount" in parsed_scalars
    ):
        step = parsed_scalars["amount_step"]
        for name in ("min_amount", "max_amount"):
            if name in parsed_scalars and parsed_scalars[name] % step != 0:
                errors.append(
                    LoadError(
                        "ORDER_ERROR",
                        file_str,
                        f"product.{name}",
                        f"{name} ({parsed_scalars[name]}) is not a multiple of amount_step ({step})",
                    )
                )

    if "min_tenure_months" in parsed_scalars and "max_tenure_months" in parsed_scalars:
        if parsed_scalars["min_tenure_months"] > parsed_scalars["max_tenure_months"]:
            errors.append(
                LoadError(
                    "ORDER_ERROR",
                    file_str,
                    "product",
                    f"min_tenure_months ({parsed_scalars['min_tenure_months']}) exceeds max_tenure_months ({parsed_scalars['max_tenure_months']})",
                )
            )

    # --- Band parsing and validation ---
    raw_bands = raw.get("band", [])
    if not isinstance(raw_bands, list):
        errors.append(
            LoadError("TYPE_ERROR", file_str, "band", "[[band]] must be an array of tables")
        )
        raw_bands = []

    parsed_bands: list[dict[str, Any]] = []
    seen_band_ids: set[str] = set()

    for i, raw_band in enumerate(raw_bands):
        band_loc = f"band[{i}]"
        if not isinstance(raw_band, dict):
            errors.append(
                LoadError("TYPE_ERROR", file_str, band_loc, "Each band entry must be a table")
            )
            continue

        # Unknown keys in band
        for k in raw_band:
            if k not in BAND_KEYS:
                errors.append(
                    LoadError("UNKNOWN_KEY", file_str, f"{band_loc}.{k}", f"Unknown band key '{k}'")
                )

        # Float check
        for k, v in raw_band.items():
            if isinstance(v, float):
                errors.append(
                    LoadError(
                        "FLOAT_FORBIDDEN",
                        file_str,
                        f"{band_loc}.{k}",
                        f"value {v!r} is a float; write it as a quoted decimal string",
                    )
                )

        band: dict[str, Any] = {}

        # id: string, one uppercase letter
        bid = raw_band.get("id")
        if bid is None:
            errors.append(
                LoadError("MISSING_KEY", file_str, f"{band_loc}.id", "Band 'id' is missing")
            )
        elif not isinstance(bid, str) or len(bid) != 1 or not bid.isupper() or not bid.isalpha():
            errors.append(
                LoadError(
                    "TYPE_ERROR",
                    file_str,
                    f"{band_loc}.id",
                    f"Band id must be one uppercase letter, got {bid!r}",
                )
            )
        elif bid in seen_band_ids:
            errors.append(
                LoadError(
                    "DUPLICATE_NAME",
                    file_str,
                    f"{band_loc}.id",
                    f"Band id '{bid}' appears more than once",
                )
            )
        else:
            seen_band_ids.add(bid)
            band["id"] = bid

        # min_score: int 300-900
        raw_ms = raw_band.get("min_score")
        if raw_ms is None:
            errors.append(
                LoadError(
                    "MISSING_KEY", file_str, f"{band_loc}.min_score", "Band 'min_score' is missing"
                )
            )
        else:
            ms = _parse_typed_value(
                raw_ms, "int", file_str, f"{band_loc}.min_score", errors, "300 to 900"
            )
            if ms is not None:
                if not _range_int(300, 900)(ms):
                    errors.append(
                        LoadError(
                            "RANGE_ERROR",
                            file_str,
                            f"{band_loc}.min_score",
                            f"min_score {ms} is outside 300 to 900",
                        )
                    )
                else:
                    band["min_score"] = ms

        # max_foir: decimal, above 0, at most 1
        for key in ("max_foir", "rate_low", "rate_high", "indicative_rate", "post_loan_foir_cap"):
            raw_v = raw_band.get(key)
            if raw_v is None:
                errors.append(
                    LoadError(
                        "MISSING_KEY", file_str, f"{band_loc}.{key}", f"Band '{key}' is missing"
                    )
                )
            else:
                v = _parse_typed_value(
                    raw_v,
                    "decimal",
                    file_str,
                    f"{band_loc}.{key}",
                    errors,
                    "above 0, at most 100 for rates",
                )
                if v is not None:
                    if key in ("max_foir", "post_loan_foir_cap"):
                        if not _range_decimal("0", "1", lo_exclusive=True)(v):
                            errors.append(
                                LoadError(
                                    "RANGE_ERROR",
                                    file_str,
                                    f"{band_loc}.{key}",
                                    f"{key} {v} is outside (0, 1]",
                                )
                            )
                        else:
                            band[key] = v
                    else:  # rate fields
                        if not _range_decimal("0", "100", lo_exclusive=True)(v):
                            errors.append(
                                LoadError(
                                    "RANGE_ERROR",
                                    file_str,
                                    f"{band_loc}.{key}",
                                    f"{key} {v} must be above 0 and at most 100",
                                )
                            )
                        else:
                            band[key] = v

        parsed_bands.append(band)

    # --- Band ordering and coverage checks ---
    if parsed_bands and all("min_score" in b and "max_foir" in b for b in parsed_bands):
        for i in range(1, len(parsed_bands)):
            prev = parsed_bands[i - 1]
            curr = parsed_bands[i]
            loc = f"band[{i}]"
            if curr["min_score"] > prev["min_score"]:
                errors.append(
                    LoadError(
                        "BAND_ORDER",
                        file_str,
                        loc,
                        f"min_score rises from band {parsed_bands[i - 1].get('id', '?')} ({prev['min_score']}) "
                        f"to band {curr.get('id', '?')} ({curr['min_score']}); bands must be ordered best first",
                    )
                )
            if curr["max_foir"] < prev["max_foir"]:
                errors.append(
                    LoadError(
                        "BAND_ORDER",
                        file_str,
                        loc,
                        f"max_foir falls from band {parsed_bands[i - 1].get('id', '?')} ({prev['max_foir']}) "
                        f"to band {curr.get('id', '?')} ({curr['max_foir']}); bands must be ordered best first",
                    )
                )

    # --- Band coverage check ---
    if (
        parsed_bands
        and "min_credit_score" in parsed_scalars
        and "max_existing_foir" in parsed_scalars
        and all("min_score" in b and "max_foir" in b for b in parsed_bands)
    ):
        last = parsed_bands[-1]
        min_score = parsed_scalars["min_credit_score"]
        max_foir = parsed_scalars["max_existing_foir"]
        if last["min_score"] > min_score:
            errors.append(
                LoadError(
                    "BAND_COVERAGE_GAP",
                    file_str,
                    f"band[{len(parsed_bands) - 1}]",
                    f"Last band min_score ({last['min_score']}) exceeds min_credit_score ({min_score}); "
                    "an applicant who clears K04 may get no band",
                )
            )
        if last["max_foir"] < max_foir:
            errors.append(
                LoadError(
                    "BAND_COVERAGE_GAP",
                    file_str,
                    f"band[{len(parsed_bands) - 1}]",
                    f"Last band max_foir ({last['max_foir']}) is below max_existing_foir ({max_foir}); "
                    "an applicant who clears E01 may get no band",
                )
            )

    # --- indicative_rate midpoint check and pricing order warning ---
    for i, band in enumerate(parsed_bands):
        band_loc = f"band[{i}]"
        if "rate_low" in band and "rate_high" in band and "indicative_rate" in band:
            midpoint = (band["rate_low"] + band["rate_high"]) / Decimal("2")
            if band["indicative_rate"] != midpoint:
                errors.append(
                    LoadError(
                        "RATE_NOT_MIDPOINT",
                        file_str,
                        band_loc,
                        f"indicative_rate ({band['indicative_rate']}) is not the midpoint of "
                        f"rate_low ({band['rate_low']}) and rate_high ({band['rate_high']}); "
                        f"expected {midpoint}",
                    )
                )

        if i > 0:
            prev_band = parsed_bands[i - 1]
            if "indicative_rate" in band and "indicative_rate" in prev_band:
                if band["indicative_rate"] < prev_band["indicative_rate"]:
                    warnings.append(
                        LoadWarning(
                            "WARN_PRICING_ORDER",
                            file_str,
                            band_loc,
                            f"indicative_rate falls from band {prev_band.get('id', '?')} "
                            f"({prev_band['indicative_rate']}) to band {band.get('id', '?')} "
                            f"({band['indicative_rate']})",
                        )
                    )
            if "post_loan_foir_cap" in band and "post_loan_foir_cap" in prev_band:
                if band["post_loan_foir_cap"] > prev_band["post_loan_foir_cap"]:
                    warnings.append(
                        LoadWarning(
                            "WARN_PRICING_ORDER",
                            file_str,
                            band_loc,
                            f"post_loan_foir_cap rises from band {prev_band.get('id', '?')} "
                            f"({prev_band['post_loan_foir_cap']}) to band {band.get('id', '?')} "
                            f"({band['post_loan_foir_cap']})",
                        )
                    )

    # --- Store results ---
    result.params = parsed_scalars
    result.bands = parsed_bands
    return result


def _parse_typed_value(
    raw_val: Any,
    type_tag: str,
    file_str: str,
    location: str,
    errors: list[LoadError],
    range_desc: str,
) -> Any:
    """
    Parse and type-check a single value. Returns the parsed value or None on error.
    Never coerces types.
    """
    if isinstance(raw_val, float):
        errors.append(
            LoadError(
                "FLOAT_FORBIDDEN",
                file_str,
                location,
                f"value {raw_val!r} is a float; write it as a quoted decimal string",
            )
        )
        return None

    if type_tag == "int":
        if not isinstance(raw_val, bool) and isinstance(raw_val, int):
            return raw_val
        errors.append(
            LoadError(
                "TYPE_ERROR",
                file_str,
                location,
                f"expected an integer, got {type(raw_val).__name__} {raw_val!r}",
            )
        )
        return None

    if type_tag == "bool":
        if isinstance(raw_val, bool):
            return raw_val
        errors.append(
            LoadError(
                "TYPE_ERROR",
                file_str,
                location,
                f"expected a boolean (true or false), got {type(raw_val).__name__} {raw_val!r}",
            )
        )
        return None

    if type_tag == "decimal":
        if not _is_valid_decimal_string(raw_val):
            errors.append(
                LoadError(
                    "TYPE_ERROR",
                    file_str,
                    location,
                    f"expected a decimal string ({DECIMAL_PATTERN_HELP}), got {raw_val!r}",
                )
            )
            return None
        try:
            return Decimal(raw_val)
        except InvalidOperation:
            errors.append(
                LoadError(
                    "TYPE_ERROR", file_str, location, f"could not parse decimal from {raw_val!r}"
                )
            )
            return None

    errors.append(LoadError("TYPE_ERROR", file_str, location, f"Unknown type_tag {type_tag!r}"))
    return None


# ---------------------------------------------------------------------------
# CLI entry point (used by make check-params)
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """
    Load and validate params/params.toml.

    Exit codes:
        0  No errors (warnings may be present).
        1  One or more errors found.
        2  Unexpected exception.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate params/params.toml")
    parser.add_argument(
        "path",
        nargs="?",
        default="params/params.toml",
        help="Path to the parameter file (default: params/params.toml)",
    )
    args = parser.parse_args(argv)

    result = load_params(args.path)

    for w in result.warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    for e in result.errors:
        print(f"ERROR:   {e}", file=sys.stderr)

    if result.ok:
        print(f"OK: {args.path} loaded with {len(result.warnings)} warning(s) and no errors.")
        print(f"    {len(result.params)} scalar parameters, {len(result.bands)} band(s).")
    else:
        print(f"FAILED: {args.path} has {len(result.errors)} error(s).", file=sys.stderr)

    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
