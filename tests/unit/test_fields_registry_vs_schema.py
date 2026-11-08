"""
Registry vs Schema consistency test.

Implements: WP-05, FR-01, FR-17, docs/09-file-formats.md §3
Spec: compare rules/fields.toml with schemas/input.schema.json on:
  - Field names
  - Types
  - Min and max ranges
  - Enum values
  - Required mapping: registry required == True <-> schema property x-v01-required == True
    (applicant_id is required at schema root; others have x-v01-required)
  - Nullability is NOT compared (owner decision; resolved in docs/open-questions.md).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.engine.field_loader import load_fields

REPO_ROOT = Path(__file__).resolve().parents[2]
FIELDS_PATH = REPO_ROOT / "rules" / "fields.toml"
SCHEMA_PATH = REPO_ROOT / "schemas" / "input.schema.json"


@pytest.fixture(scope="module")
def field_registry():
    res = load_fields(FIELDS_PATH)
    assert res.ok, f"Failed to load fields.toml: {res.errors}"
    return res.fields


@pytest.fixture(scope="module")
def input_schema():
    text = SCHEMA_PATH.read_text(encoding="utf-8")
    return json.loads(text)


class TestFieldsRegistryVsSchema:
    """Validate consistency between field registry and input JSON Schema."""

    def test_input_field_names_match(self, field_registry, input_schema):
        """Every input field in fields.toml matches schema properties exactly."""
        registry_inputs = {f["name"] for f in field_registry if f["kind"] == "input"}
        schema_props = set(input_schema["properties"].keys())

        assert registry_inputs == schema_props, (
            f"Field name mismatch:\n"
            f"  In registry but not schema: {registry_inputs - schema_props}\n"
            f"  In schema but not registry: {schema_props - registry_inputs}"
        )

    def test_field_types_match(self, field_registry, input_schema):
        """Registry types map to schema types."""
        props = input_schema["properties"]
        type_mapping = {
            "int": "integer",
            "string": "string",
            "bool": "boolean",
            "enum": "string",
        }

        for fld in field_registry:
            if fld["kind"] != "input":
                continue
            name = fld["name"]
            prop = props[name]
            expected_type = type_mapping[fld["type"]]

            prop_type = prop.get("type")
            if isinstance(prop_type, list):
                # Nullable fields have type list: [type, "null"]
                assert expected_type in prop_type, (
                    f"Field '{name}': expected {expected_type} in {prop_type}"
                )
            else:
                assert prop_type == expected_type, (
                    f"Field '{name}': expected {expected_type}, got {prop_type}"
                )

    def test_field_ranges_match(self, field_registry, input_schema):
        """Min and max constraints match between registry and schema."""
        props = input_schema["properties"]

        for fld in field_registry:
            if fld["kind"] != "input":
                continue
            name = fld["name"]
            prop = props[name]

            if "min" in fld:
                assert "minimum" in prop, (
                    f"Field '{name}' has min in registry but no minimum in schema"
                )
                assert fld["min"] == prop["minimum"], f"Field '{name}' minimum mismatch"
            else:
                assert "minimum" not in prop, (
                    f"Field '{name}' has minimum in schema but no min in registry"
                )

            if "max" in fld:
                assert "maximum" in prop, (
                    f"Field '{name}' has max in registry but no maximum in schema"
                )
                assert fld["max"] == prop["maximum"], f"Field '{name}' maximum mismatch"
            else:
                assert "maximum" not in prop, (
                    f"Field '{name}' has maximum in schema but no max in registry"
                )

    def test_enum_values_match(self, field_registry, input_schema):
        """Enum values in registry match schema enum list."""
        props = input_schema["properties"]

        for fld in field_registry:
            if fld["kind"] != "input" or fld["type"] != "enum":
                continue
            name = fld["name"]
            prop = props[name]

            registry_values = set(fld["values"])
            # Schema enum list may contain None (null)
            schema_values = {v for v in prop.get("enum", []) if v is not None}

            assert registry_values == schema_values, (
                f"Enum values mismatch for field '{name}': {registry_values} vs {schema_values}"
            )

    def test_required_mapping_matches(self, field_registry, input_schema):
        """
        Registry required == True corresponds to schema property marked x-v01-required.
        applicant_id is required at schema root.
        """
        props = input_schema["properties"]
        schema_root_required = set(input_schema.get("required", []))

        for fld in field_registry:
            if fld["kind"] != "input":
                continue
            name = fld["name"]
            prop = props[name]
            is_req = fld["required"]

            if name == "applicant_id":
                assert is_req is True
                assert name in schema_root_required
            else:
                schema_v01_req = prop.get("x-v01-required", False)
                assert is_req == schema_v01_req, (
                    f"Field '{name}': registry required={is_req} does not match schema x-v01-required={schema_v01_req}"
                )
