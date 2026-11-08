"""
Field registry loader and validator for rules/fields.toml.

Implements: WP-05, FR-17, docs/09-file-formats.md §3
Follows Phase 0 loader pattern:
- Collects all errors in one pass; never stops on first error.
- No TOML floats permitted.
- Exits non-zero on error.
"""

from __future__ import annotations

import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.engine.param_loader import LoadError, LoadWarning, _find_floats

IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")

ALLOWED_KINDS = frozenset({"input", "derived"})
ALLOWED_TYPES = frozenset({"int", "decimal", "bool", "enum", "string"})
ALLOWED_UNITS = frozenset({"INR", "fraction", "percent", "years", "months", "count", "points", ""})
ALLOWED_LAYERS = frozenset(
    {
        "validation",
        "knockout",
        "referral",
        "eligibility",
        "amount",
        "pricing",
        "experimental",
        "never",
    }
)

INPUT_ALLOWED_KEYS = frozenset(
    {
        "name",
        "kind",
        "type",
        "unit",
        "min",
        "max",
        "values",
        "required",
        "nullable",
        "predicate",
        "readable_from",
    }
)

DERIVED_ALLOWED_KEYS = frozenset(
    {
        "name",
        "kind",
        "type",
        "unit",
        "min",
        "max",
        "values",
        "required",
        "nullable",
        "predicate",
        "produced_by",
        "readable_from",
    }
)


@dataclass
class FieldLoadResult:
    """Result of loading rules/fields.toml."""

    fields: list[dict[str, Any]] = field(default_factory=list)
    errors: list[LoadError] = field(default_factory=list)
    warnings: list[LoadWarning] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def load_fields(path: Path | str) -> FieldLoadResult:
    """
    Load and validate rules/fields.toml.
    Collects all errors in one pass.
    """
    path = Path(path)
    result = FieldLoadResult()
    errors = result.errors
    file_str = str(path)

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(LoadError("MISSING_FILE", file_str, "(file)", f"File not found: {path}"))
        return result
    except tomllib.TOMLDecodeError as exc:
        errors.append(LoadError("PARSE_ERROR", file_str, "(file)", str(exc)))
        return result

    # 1. Float check
    for fpath, fval in _find_floats(raw, ""):
        errors.append(
            LoadError(
                "FLOAT_FORBIDDEN",
                file_str,
                fpath,
                f"value {fval!r} is a float; floats are forbidden in rule files",
            )
        )

    # 2. Top-level keys: only 'field' allowed
    for key in raw:
        if key != "field":
            errors.append(LoadError("UNKNOWN_KEY", file_str, key, f"Unknown top-level key '{key}'"))

    field_list = raw.get("field")
    if field_list is None:
        errors.append(LoadError("MISSING_KEY", file_str, "field", "No [[field]] entries found"))
        return result

    if not isinstance(field_list, list):
        errors.append(LoadError("TYPE_ERROR", file_str, "field", "field must be a list of tables"))
        return result

    seen_names: set[str] = set()

    for idx, fld in enumerate(field_list):
        place = f"field[{idx}]"
        if not isinstance(fld, dict):
            errors.append(LoadError("TYPE_ERROR", file_str, place, "Entry must be a table"))
            continue

        name = fld.get("name")
        if not name:
            errors.append(LoadError("MISSING_KEY", file_str, f"{place}.name", "Field has no name"))
            continue

        place = f"field '{name}'"

        if not isinstance(name, str) or not IDENTIFIER_RE.match(name):
            errors.append(
                LoadError(
                    "INVALID_NAME",
                    file_str,
                    place,
                    f"Name '{name}' is not a valid snake_case identifier",
                )
            )

        if name in seen_names:
            errors.append(
                LoadError("DUPLICATE_NAME", file_str, place, f"Duplicate field name '{name}'")
            )
        seen_names.add(name)

        kind = fld.get("kind")
        if not kind:
            errors.append(LoadError("MISSING_KEY", file_str, place, "Missing 'kind'"))
        elif kind not in ALLOWED_KINDS:
            errors.append(
                LoadError(
                    "INVALID_KIND",
                    file_str,
                    place,
                    f"kind '{kind}' must be one of {sorted(ALLOWED_KINDS)}",
                )
            )

        ftype = fld.get("type")
        if not ftype:
            errors.append(LoadError("MISSING_KEY", file_str, place, "Missing 'type'"))
        elif ftype not in ALLOWED_TYPES:
            errors.append(
                LoadError(
                    "INVALID_TYPE",
                    file_str,
                    place,
                    f"type '{ftype}' must be one of {sorted(ALLOWED_TYPES)}",
                )
            )

        # Unit check
        unit = fld.get("unit")
        if unit is not None:
            if not isinstance(unit, str) or unit not in ALLOWED_UNITS:
                errors.append(
                    LoadError(
                        "INVALID_UNIT",
                        file_str,
                        place,
                        f"unit '{unit}' must be one of {sorted(ALLOWED_UNITS)}",
                    )
                )

        # Predicate check
        predicate = fld.get("predicate")
        if not predicate:
            errors.append(LoadError("MISSING_KEY", file_str, place, "Missing 'predicate'"))
        elif not isinstance(predicate, str) or not IDENTIFIER_RE.match(predicate):
            errors.append(
                LoadError(
                    "INVALID_PREDICATE",
                    file_str,
                    place,
                    f"predicate '{predicate}' is not a valid identifier",
                )
            )

        # readable_from check
        readable_from = fld.get("readable_from")
        if not readable_from:
            errors.append(LoadError("MISSING_KEY", file_str, place, "Missing 'readable_from'"))
        elif readable_from not in ALLOWED_LAYERS:
            errors.append(
                LoadError(
                    "INVALID_LAYER",
                    file_str,
                    place,
                    f"readable_from '{readable_from}' must be one of {sorted(ALLOWED_LAYERS)}",
                )
            )

        # Kind-specific checks
        if kind == "input":
            for k in fld:
                if k not in INPUT_ALLOWED_KEYS:
                    errors.append(
                        LoadError(
                            "UNKNOWN_KEY",
                            file_str,
                            f"{place}.{k}",
                            f"Unknown key '{k}' for input field",
                        )
                    )

            if "required" not in fld:
                errors.append(LoadError("MISSING_KEY", file_str, place, "Missing 'required'"))
            elif not isinstance(fld["required"], bool):
                errors.append(
                    LoadError(
                        "TYPE_ERROR", file_str, f"{place}.required", "'required' must be a boolean"
                    )
                )

            if "nullable" not in fld:
                errors.append(LoadError("MISSING_KEY", file_str, place, "Missing 'nullable'"))
            elif not isinstance(fld["nullable"], bool):
                errors.append(
                    LoadError(
                        "TYPE_ERROR", file_str, f"{place}.nullable", "'nullable' must be a boolean"
                    )
                )

        elif kind == "derived":
            for k in fld:
                if k not in DERIVED_ALLOWED_KEYS:
                    errors.append(
                        LoadError(
                            "UNKNOWN_KEY",
                            file_str,
                            f"{place}.{k}",
                            f"Unknown key '{k}' for derived field",
                        )
                    )

            if "produced_by" not in fld:
                errors.append(LoadError("MISSING_KEY", file_str, place, "Missing 'produced_by'"))
            elif not isinstance(fld["produced_by"], str) or not fld["produced_by"].strip():
                errors.append(
                    LoadError(
                        "TYPE_ERROR",
                        file_str,
                        f"{place}.produced_by",
                        "'produced_by' must be a non-empty string",
                    )
                )

        # Range checks for int
        if ftype == "int":
            min_val = fld.get("min")
            max_val = fld.get("max")
            if min_val is not None and not isinstance(min_val, int):
                errors.append(
                    LoadError("TYPE_ERROR", file_str, f"{place}.min", "'min' must be an integer")
                )
            if max_val is not None and not isinstance(max_val, int):
                errors.append(
                    LoadError("TYPE_ERROR", file_str, f"{place}.max", "'max' must be an integer")
                )
            if (
                isinstance(min_val, int)
                and isinstance(max_val, int)
                and not isinstance(min_val, bool)
                and not isinstance(max_val, bool)
            ):
                if min_val > max_val:
                    errors.append(
                        LoadError(
                            "RANGE_ERROR",
                            file_str,
                            place,
                            f"min ({min_val}) cannot be greater than max ({max_val})",
                        )
                    )

        # Enum checks
        if ftype == "enum":
            values = fld.get("values")
            if not values:
                errors.append(
                    LoadError("MISSING_KEY", file_str, place, "Missing 'values' for enum type")
                )
            elif not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
                errors.append(
                    LoadError(
                        "TYPE_ERROR",
                        file_str,
                        f"{place}.values",
                        "'values' must be a list of non-empty strings",
                    )
                )

    result.fields = field_list
    return result


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    path = Path(args[0]) if args else Path("rules/fields.toml")

    result = load_fields(path)

    for warning in result.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if not result.ok:
        print(
            f"ERROR: {len(result.errors)} error(s) found in {path}:",
            file=sys.stderr,
        )
        for error in result.errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    input_count = sum(1 for f in result.fields if f.get("kind") == "input")
    derived_count = sum(1 for f in result.fields if f.get("kind") == "derived")
    print(
        f"OK: {path} loaded with 0 warning(s) and no errors.\n"
        f"    {len(result.fields)} fields ({input_count} input, {derived_count} derived)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
