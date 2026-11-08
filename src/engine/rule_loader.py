"""
Rule, reason-code, and manifest loaders with error checking.

Implements: FR-17, FR-18, WP-06
Spec: docs/09-file-formats.md sections 4, 5, 6
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.calc.registry import CALCULATION_REGISTRY
from src.engine.condition_parser import ASTNode, ConditionParseError, ConditionParser
from src.engine.field_loader import load_fields
from src.engine.param_loader import load_params

LAYER_ORDER = [
    "validation",
    "knockout",
    "referral",
    "eligibility",
    "amount",
    "pricing",
    "experimental",
]


@dataclass
class RuleError:
    code: str
    file: str
    place: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} {self.file} [{self.place}]: {self.message}"


@dataclass
class RuleWarning:
    code: str
    file: str
    place: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} {self.file} [{self.place}]: {self.message}"


@dataclass
class RuleDefinition:
    id: str
    layer: str
    description: str
    clause: str
    when: str
    outcome: str
    owner: str
    effective_date: str
    version: str
    status: str
    reason_code: str | dict[str, str] | None = None
    calc: list[str] = field(default_factory=list)
    computes: list[str] = field(default_factory=list)
    after: str | None = None
    parsed_condition: ASTNode | None = None


@dataclass
class ReasonCodeDefinition:
    code: str
    rule: str
    text: str
    allow_literals: list[str] = field(default_factory=list)


@dataclass
class ManifestDefinition:
    rules_version: str
    layers: list[str]
    fields: str
    reason_codes: str


@dataclass
class RuleSet:
    manifest: ManifestDefinition
    params: dict[str, Any]
    bands: list[dict[str, Any]]
    fields: dict[str, dict[str, Any]]  # name -> field dict
    reason_codes: dict[str, ReasonCodeDefinition]
    rules: dict[str, RuleDefinition]  # id -> RuleDefinition in evaluation order
    rules_by_layer: dict[str, list[RuleDefinition]]


# ---------------------------------------------------------------------------
# Loader Implementation
# ---------------------------------------------------------------------------


class RuleLoader:
    def __init__(self, rules_dir: Path, params_path: Path):
        self.rules_dir = rules_dir
        self.params_path = params_path
        self.errors: list[RuleError] = []
        self.warnings: list[RuleWarning] = []

    def load(self) -> RuleSet | None:
        self.errors.clear()
        self.warnings.clear()

        # 1. Load parameters
        p_res = load_params(self.params_path)
        for err in p_res.errors:
            self.errors.append(RuleError(err.code, err.file, err.place, err.message))
        for warn in p_res.warnings:
            self.warnings.append(RuleWarning(warn.code, warn.file, warn.place, warn.message))
        if not p_res.ok:
            return None

        # 2. Load manifest
        manifest_path = self.rules_dir / "manifest.toml"
        manifest = self._load_manifest(manifest_path)
        if manifest is None:
            return None

        # 3. Load fields
        fields_path = self.rules_dir / manifest.fields
        f_res = load_fields(fields_path)
        for err in f_res.errors:
            self.errors.append(RuleError(err.code, err.file, err.place, err.message))
        for warn in f_res.warnings:
            self.warnings.append(RuleWarning(warn.code, warn.file, warn.place, warn.message))
        if not f_res.ok:
            return None

        fields_dict: dict[str, dict[str, Any]] = {f["name"]: f for f in f_res.fields}

        # 4. Load reason codes
        reason_codes_path = self.rules_dir / manifest.reason_codes
        reason_codes = self._load_reason_codes(reason_codes_path, p_res.params, fields_dict)

        # 5. Load rule layers
        rules, rules_by_layer = self._load_rules(manifest, p_res.params, fields_dict, reason_codes)

        # 6. Cross-validation: orphan codes, cycles, placeholder checks
        if reason_codes is not None and rules is not None:
            self._check_orphans_and_reasons(reason_codes, rules)
            self._check_cycles(fields_dict, rules)
            self._check_placeholders(reason_codes, rules, p_res.params, fields_dict)

        if self.errors:
            return None

        return RuleSet(
            manifest=manifest,
            params=p_res.params,
            bands=p_res.bands,
            fields=fields_dict,
            reason_codes=reason_codes or {},
            rules=rules or {},
            rules_by_layer=rules_by_layer or {},
        )

    def _load_manifest(self, path: Path) -> ManifestDefinition | None:
        if not path.exists():
            self.errors.append(RuleError("MANIFEST_ERROR", str(path), "manifest", "File not found"))
            return None

        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.errors.append(RuleError("PARSE_ERROR", str(path), "manifest", str(exc)))
            return None

        rules_version = data.get("rules_version")
        layers = data.get("layers")
        fields_file = data.get("fields")
        rc_file = data.get("reason_codes")

        if not rules_version or not isinstance(rules_version, str):
            self.errors.append(
                RuleError(
                    "MANIFEST_ERROR", str(path), "rules_version", "Missing or invalid rules_version"
                )
            )
        if not layers or not isinstance(layers, list) or layers != LAYER_ORDER:
            self.errors.append(
                RuleError(
                    "MANIFEST_ERROR",
                    str(path),
                    "layers",
                    f"Layers must exactly match {LAYER_ORDER}, got {layers}",
                )
            )
        if not fields_file or not isinstance(fields_file, str):
            self.errors.append(
                RuleError(
                    "MANIFEST_ERROR", str(path), "fields", "Missing or invalid fields filename"
                )
            )
        if not rc_file or not isinstance(rc_file, str):
            self.errors.append(
                RuleError(
                    "MANIFEST_ERROR",
                    str(path),
                    "reason_codes",
                    "Missing or invalid reason_codes filename",
                )
            )

        if self.errors:
            return None

        return ManifestDefinition(
            rules_version=rules_version,
            layers=layers,
            fields=fields_file,
            reason_codes=rc_file,
        )

    def _load_reason_codes(
        self, path: Path, params: dict[str, Any], fields: dict[str, dict[str, Any]]
    ) -> dict[str, ReasonCodeDefinition] | None:
        if not path.exists():
            self.errors.append(
                RuleError("MANIFEST_ERROR", str(path), "reason_codes", "File not found")
            )
            return None

        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.errors.append(RuleError("PARSE_ERROR", str(path), "reason_codes", str(exc)))
            return None

        codes_raw = data.get("code")
        if not isinstance(codes_raw, list):
            self.errors.append(
                RuleError(
                    "MISSING_KEY", str(path), "code", "Expected [[code]] array in reason_codes.toml"
                )
            )
            return None

        # Build set of all scalar param values for literal warning check
        scalar_param_values = {str(v) for k, v in params.items() if isinstance(v, (int, str))}

        reason_codes: dict[str, ReasonCodeDefinition] = {}
        for entry in codes_raw:
            code = entry.get("code")
            rule_id = entry.get("rule")
            text = entry.get("text")
            allow_literals = entry.get("allow_literals", [])

            if not code or not isinstance(code, str):
                self.errors.append(
                    RuleError("MISSING_KEY", str(path), "code", "Missing code string")
                )
                continue
            if code in reason_codes:
                self.errors.append(
                    RuleError("DUPLICATE_NAME", str(path), code, f"Duplicate reason code '{code}'")
                )
                continue
            if not rule_id or not isinstance(rule_id, str):
                self.errors.append(
                    RuleError("MISSING_KEY", str(path), f"{code}.rule", "Missing rule string")
                )
                continue
            if not text or not isinstance(text, str):
                self.errors.append(
                    RuleError("MISSING_KEY", str(path), f"{code}.text", "Missing text string")
                )
                continue

            # Check literal warning
            numbers_in_text = re.findall(r"\b\d+\b", text)
            for num in numbers_in_text:
                if num in scalar_param_values and num not in allow_literals:
                    self.warnings.append(
                        RuleWarning(
                            "WARN_LITERAL_IN_TEXT",
                            str(path),
                            code,
                            f"Text contains literal '{num}' matching a parameter value. Add to allow_literals if intended.",
                        )
                    )

            reason_codes[code] = ReasonCodeDefinition(
                code=code,
                rule=rule_id,
                text=text,
                allow_literals=allow_literals if isinstance(allow_literals, list) else [],
            )

        return reason_codes

    def _load_rules(
        self,
        manifest: ManifestDefinition,
        params: dict[str, Any],
        fields: dict[str, dict[str, Any]],
        reason_codes: dict[str, ReasonCodeDefinition] | None,
    ) -> tuple[dict[str, RuleDefinition] | None, dict[str, list[RuleDefinition]] | None]:
        # Prepare condition parser environment
        field_types: dict[str, tuple[str, str | None]] = {
            f["name"]: (f["type"], f["name"] if f["type"] == "enum" else None)
            for f in fields.values()
        }
        param_types: dict[str, str] = {
            k: (
                "int"
                if isinstance(v, int)
                else "decimal"
                if hasattr(v, "as_tuple")
                else "bool"
                if isinstance(v, bool)
                else "str"
            )
            for k, v in params.items()
        }
        enum_values: dict[str, str] = {}
        for f in fields.values():
            if f["type"] == "enum":
                for val in f.get("values", []):
                    enum_values[val] = f["name"]
        required_fields = {f["name"] for f in fields.values() if f.get("required")}

        parser = ConditionParser(field_types, param_types, enum_values, required_fields)

        rules: dict[str, RuleDefinition] = {}
        rules_by_layer: dict[str, list[RuleDefinition]] = {layer: [] for layer in manifest.layers}

        layer_rule_prefixes = {
            "validation": "V",
            "knockout": "K",
            "referral": "R",
            "eligibility": "E",
            "amount": "A",
            "pricing": "P",
            "experimental": "X",
        }

        layer_order_idx = {name: i for i, name in enumerate(manifest.layers)}

        for layer_name in manifest.layers:
            layer_path = self.rules_dir / f"{layer_name}.toml"
            if not layer_path.exists():
                self.errors.append(
                    RuleError(
                        "MANIFEST_ERROR",
                        str(layer_path),
                        layer_name,
                        f"Missing layer file '{layer_path.name}'",
                    )
                )
                continue

            try:
                data = tomllib.loads(layer_path.read_text(encoding="utf-8"))
            except Exception as exc:
                self.errors.append(RuleError("PARSE_ERROR", str(layer_path), layer_name, str(exc)))
                continue

            file_layer = data.get("layer")
            if file_layer != layer_name:
                self.errors.append(
                    RuleError(
                        "LAYER_MISMATCH",
                        str(layer_path),
                        "layer",
                        f"Expected layer = '{layer_name}', got '{file_layer}'",
                    )
                )

            raw_rules = data.get("rule", [])
            if not isinstance(raw_rules, list):
                self.errors.append(
                    RuleError("PARSE_ERROR", str(layer_path), "rule", "Expected [[rule]] list")
                )
                continue

            for r_data in raw_rules:
                r_id = r_data.get("id")
                r_layer = r_data.get("layer")
                r_desc = r_data.get("description")
                r_clause = r_data.get("clause")
                r_when = r_data.get("when")
                r_outcome = r_data.get("outcome")
                r_owner = r_data.get("owner")
                r_date = r_data.get("effective_date")
                r_version = r_data.get("version")
                r_status = r_data.get("status")

                if not r_id or not isinstance(r_id, str):
                    self.errors.append(
                        RuleError("BAD_RULE_ID", str(layer_path), "unknown", "Missing rule id")
                    )
                    continue

                # Check ID format: prefix + 2 digits
                expected_prefix = layer_rule_prefixes.get(layer_name, "")
                if not re.match(rf"^{expected_prefix}\d{{2}}$", r_id):
                    self.errors.append(
                        RuleError(
                            "BAD_RULE_ID",
                            str(layer_path),
                            r_id,
                            f"Rule ID '{r_id}' does not match expected prefix '{expected_prefix}' followed by 2 digits",
                        )
                    )

                if r_id in rules:
                    self.errors.append(
                        RuleError(
                            "DUPLICATE_RULE_ID",
                            str(layer_path),
                            r_id,
                            f"Duplicate rule ID '{r_id}'",
                        )
                    )

                if r_layer != layer_name:
                    self.errors.append(
                        RuleError(
                            "LAYER_MISMATCH",
                            str(layer_path),
                            r_id,
                            f"Rule layer '{r_layer}' does not match file layer '{layer_name}'",
                        )
                    )

                if layer_name == "experimental" and r_status == "active":
                    self.errors.append(
                        RuleError(
                            "EXPERIMENTAL_STATUS",
                            str(layer_path),
                            r_id,
                            f"Experimental rule '{r_id}' cannot be 'active'",
                        )
                    )

                r_rc = r_data.get("reason_code")
                r_calc = r_data.get("calc", [])
                r_computes = r_data.get("computes", [])
                r_after = r_data.get("after")

                # Parse condition
                parsed_node: ASTNode | None = None
                if r_when and isinstance(r_when, str):
                    try:
                        parsed_node = parser.parse(r_when)
                    except ConditionParseError as err:
                        self.errors.append(RuleError(err.code, str(layer_path), r_id, err.message))
                else:
                    self.errors.append(
                        RuleError(
                            "MISSING_KEY", str(layer_path), r_id, "Missing 'when' condition string"
                        )
                    )

                # Check outcome and reason_code / calc
                if r_outcome == "derive":
                    if r_rc is not None:
                        self.errors.append(
                            RuleError(
                                "REASON_CODE_NOT_ALLOWED",
                                str(layer_path),
                                r_id,
                                "derive rule must not have reason_code",
                            )
                        )
                    if not r_calc:
                        self.errors.append(
                            RuleError(
                                "UNKNOWN_CALC", str(layer_path), r_id, "derive rule missing 'calc'"
                            )
                        )
                    else:
                        for cid in r_calc:
                            if cid not in CALCULATION_REGISTRY:
                                self.errors.append(
                                    RuleError(
                                        "UNKNOWN_CALC",
                                        str(layer_path),
                                        r_id,
                                        f"Unknown calculation ID '{cid}'",
                                    )
                                )
                    # Check computes matches registry and calc returns
                    expected_produced = [
                        f["name"]
                        for f in fields.values()
                        if f.get("produced_by")
                        and f.get("produced_by").split(",")[0].strip() == r_id
                    ]
                    if set(r_computes) != set(expected_produced):
                        self.errors.append(
                            RuleError(
                                "COMPUTES_MISMATCH",
                                str(layer_path),
                                r_id,
                                f"Rule computes {r_computes} does not match fields produced_by {expected_produced}",
                            )
                        )
                elif r_outcome in ("ineligible", "refer", "reduced_offer"):
                    if r_rc is None:
                        self.errors.append(
                            RuleError(
                                "REASON_CODE_MISSING",
                                str(layer_path),
                                r_id,
                                f"Rule with outcome '{r_outcome}' requires reason_code",
                            )
                        )
                    elif isinstance(r_rc, dict):
                        by_field = r_rc.get("by")
                        if not by_field or by_field not in fields:
                            self.errors.append(
                                RuleError(
                                    "REASON_MAP_INCOMPLETE",
                                    str(layer_path),
                                    r_id,
                                    f"reason_code table 'by' must be a valid field, got '{by_field}'",
                                )
                            )
                        else:
                            f_info = fields[by_field]
                            if f_info.get("type") != "enum":
                                self.errors.append(
                                    RuleError(
                                        "REASON_MAP_INCOMPLETE",
                                        str(layer_path),
                                        r_id,
                                        f"reason_code table 'by' field '{by_field}' must be enum",
                                    )
                                )
                            else:
                                applicable_values = (
                                    [ev for ev in f_info.get("values", []) if ev != "requested"]
                                    if by_field == "binding_limit"
                                    else f_info.get("values", [])
                                )
                                for ev in applicable_values:
                                    if ev not in r_rc:
                                        self.errors.append(
                                            RuleError(
                                                "REASON_MAP_INCOMPLETE",
                                                str(layer_path),
                                                r_id,
                                                f"reason_code table missing code for enum value '{ev}'",
                                            )
                                        )
                    elif isinstance(r_rc, str):
                        pass
                    else:
                        self.errors.append(
                            RuleError(
                                "TYPE_ERROR",
                                str(layer_path),
                                r_id,
                                "reason_code must be string or table",
                            )
                        )

                # Check FUTURE_READ for active rules
                if parsed_node and r_status == "active":
                    fields_read = parsed_node.get_fields_read()
                    for f_name in fields_read:
                        f_info = fields.get(f_name)
                        if f_info and f_info.get("kind") == "derived":
                            r_from = f_info.get("readable_from")
                            if r_from == "never":
                                self.errors.append(
                                    RuleError(
                                        "FUTURE_READ",
                                        str(layer_path),
                                        r_id,
                                        f"Rule reads field '{f_name}' which is marked readable_from='never'",
                                    )
                                )
                            elif r_from in layer_order_idx:
                                allowed_idx = layer_order_idx[r_from]
                                current_idx = layer_order_idx[layer_name]
                                if current_idx < allowed_idx:
                                    self.errors.append(
                                        RuleError(
                                            "FUTURE_READ",
                                            str(layer_path),
                                            r_id,
                                            f"Rule reads derived field '{f_name}' before its readable_from layer '{r_from}'",
                                        )
                                    )
                                elif current_idx == allowed_idx:
                                    raw_prod = f_info.get("produced_by", "")
                                    prod_rule = raw_prod.split(",")[0].strip() if raw_prod else ""
                                    earlier_rules_in_layer = [
                                        r.id for r in rules_by_layer[layer_name]
                                    ]
                                    if prod_rule and prod_rule in earlier_rules_in_layer:
                                        pass
                                    elif prod_rule and prod_rule == r_id:
                                        pass
                                    elif prod_rule:
                                        self.errors.append(
                                            RuleError(
                                                "FUTURE_READ",
                                                str(layer_path),
                                                r_id,
                                                f"Rule reads derived field '{f_name}' before producer rule '{prod_rule}'",
                                            )
                                        )

                rule_def = RuleDefinition(
                    id=r_id,
                    layer=layer_name,
                    description=r_desc or "",
                    clause=r_clause or "",
                    when=r_when or "",
                    outcome=r_outcome or "",
                    reason_code=r_rc,
                    calc=r_calc if isinstance(r_calc, list) else [],
                    computes=r_computes if isinstance(r_computes, list) else [],
                    after=r_after,
                    owner=r_owner or "",
                    effective_date=r_date or "",
                    version=r_version or "",
                    status=r_status or "active",
                    parsed_condition=parsed_node,
                )
                rules[r_id] = rule_def
                rules_by_layer[layer_name].append(rule_def)

        return rules, rules_by_layer

    def _check_orphans_and_reasons(
        self,
        reason_codes: dict[str, ReasonCodeDefinition],
        rules: dict[str, RuleDefinition],
    ) -> None:
        codes_raised_by_rules: set[str] = set()
        for r in rules.values():
            if isinstance(r.reason_code, str):
                codes_raised_by_rules.add(r.reason_code)
                if r.reason_code not in reason_codes:
                    self.errors.append(
                        RuleError(
                            "UNKNOWN_REASON_CODE",
                            f"rules/{r.layer}.toml",
                            r.id,
                            f"Rule names reason code '{r.reason_code}' not found in reason_codes.toml",
                        )
                    )
            elif isinstance(r.reason_code, dict):
                for k, code in r.reason_code.items():
                    if k == "by":
                        continue
                    codes_raised_by_rules.add(code)
                    if code not in reason_codes:
                        self.errors.append(
                            RuleError(
                                "UNKNOWN_REASON_CODE",
                                f"rules/{r.layer}.toml",
                                r.id,
                                f"Rule table names reason code '{code}' not found in reason_codes.toml",
                            )
                        )

        for code, rc_def in reason_codes.items():
            if rc_def.rule == "default":
                continue
            if rc_def.rule not in rules:
                self.errors.append(
                    RuleError(
                        "ORPHAN_CODE",
                        "rules/reason_codes.toml",
                        code,
                        f"Code '{code}' references non-existent rule '{rc_def.rule}'",
                    )
                )
                continue
            rule_obj = rules[rc_def.rule]
            raises = False
            if isinstance(rule_obj.reason_code, str) and rule_obj.reason_code == code:
                raises = True
            elif isinstance(rule_obj.reason_code, dict):
                if any(v == code for k, v in rule_obj.reason_code.items() if k != "by"):
                    raises = True

            if not raises:
                self.errors.append(
                    RuleError(
                        "ORPHAN_CODE",
                        "rules/reason_codes.toml",
                        code,
                        f"Code '{code}' specifies rule '{rc_def.rule}' which does not raise it",
                    )
                )

        for code, rc_def in reason_codes.items():
            if rc_def.rule != "default" and code not in codes_raised_by_rules:
                self.errors.append(
                    RuleError(
                        "ORPHAN_CODE",
                        "rules/reason_codes.toml",
                        code,
                        f"Reason code '{code}' is not raised by any rule",
                    )
                )

    def _check_cycles(
        self, fields: dict[str, dict[str, Any]], rules: dict[str, RuleDefinition]
    ) -> None:
        dep_graph: dict[str, set[str]] = {
            f_name: set() for f_name, f in fields.items() if f.get("kind") == "derived"
        }

        for f_name in dep_graph:
            f_info = fields[f_name]
            raw_prod = f_info.get("produced_by", "")
            producer_rule_id = raw_prod.split(",")[0].strip() if raw_prod else ""
            if not producer_rule_id or producer_rule_id not in rules:
                continue
            p_rule = rules[producer_rule_id]
            if p_rule.parsed_condition:
                for read_f in p_rule.parsed_condition.get_fields_read():
                    if read_f in dep_graph and read_f != f_name:
                        dep_graph[f_name].add(read_f)

        visited: dict[str, int] = {}

        def dfs(node: str, path: list[str]) -> None:
            visited[node] = 1
            for neighbor in dep_graph.get(node, []):
                if visited.get(neighbor, 0) == 1:
                    cycle_path = " -> ".join(path + [neighbor])
                    self.errors.append(
                        RuleError(
                            "CYCLE",
                            "rules/fields.toml",
                            node,
                            f"Cycle detected in derived fields: {cycle_path}",
                        )
                    )
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor, path + [neighbor])
            visited[node] = 2

        for d_field in dep_graph:
            if visited.get(d_field, 0) == 0:
                dfs(d_field, [d_field])

    def _check_placeholders(
        self,
        reason_codes: dict[str, ReasonCodeDefinition],
        rules: dict[str, RuleDefinition],
        params: dict[str, Any],
        fields: dict[str, dict[str, Any]],
    ) -> None:
        placeholder_pattern = re.compile(r"\{([^}]+)\}")

        for code, rc_def in reason_codes.items():
            text = rc_def.text
            matches = placeholder_pattern.findall(text)
            r_id = rc_def.rule
            r_def = rules.get(r_id)

            rule_read_fields: set[str] = set()
            if r_def and r_def.parsed_condition:
                rule_read_fields = r_def.parsed_condition.get_fields_read()
            if r_id == "A04":
                rule_read_fields |= {"recommended_amount", "requested_amount", "binding_limit"}
            elif r_id == "A03":
                rule_read_fields |= {"recommended_amount"}
            elif r_id == "E01":
                rule_read_fields |= {"existing_foir"}

            for ph in matches:
                if ph.startswith("param."):
                    param_name = ph[len("param.") :]
                    if param_name.endswith("_pct"):
                        param_name = param_name[:-4]
                    if param_name not in params:
                        self.errors.append(
                            RuleError(
                                "TEMPLATE_PLACEHOLDER",
                                "rules/reason_codes.toml",
                                code,
                                f"Placeholder '{ph}' references unknown parameter '{param_name}'",
                            )
                        )
                    continue

                if ph == "missing_fields":
                    if r_id != "V01":
                        self.errors.append(
                            RuleError(
                                "TEMPLATE_PLACEHOLDER",
                                "rules/reason_codes.toml",
                                code,
                                f"Placeholder '{{missing_fields}}' allowed only on V01, got on {r_id}",
                            )
                        )
                    continue

                if ph == "min_months":
                    if r_id != "K06":
                        self.errors.append(
                            RuleError(
                                "TEMPLATE_PLACEHOLDER",
                                "rules/reason_codes.toml",
                                code,
                                f"Placeholder '{{min_months}}' allowed only on K06, got on {r_id}",
                            )
                        )
                    continue

                field_name = ph
                if field_name.endswith("_pct"):
                    field_name = field_name[:-4]

                if field_name not in fields:
                    self.errors.append(
                        RuleError(
                            "TEMPLATE_PLACEHOLDER",
                            "rules/reason_codes.toml",
                            code,
                            f"Placeholder '{{{ph}}}' references unknown field '{field_name}'",
                        )
                    )
                    continue

                if r_def and field_name not in rule_read_fields:
                    self.errors.append(
                        RuleError(
                            "TEMPLATE_PLACEHOLDER",
                            "rules/reason_codes.toml",
                            code,
                            f"Rule '{r_id}' does not read field '{field_name}' used in placeholder '{{{ph}}}'",
                        )
                    )


def load_rules(rules_dir: Path, params_path: Path) -> RuleSet | None:
    loader = RuleLoader(rules_dir, params_path)
    res = loader.load()
    return res


if __name__ == "__main__":
    import sys

    r_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("rules")
    p_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("params/params.toml")

    loader = RuleLoader(r_dir, p_path)
    ruleset = loader.load()

    if loader.errors:
        print(f"\nFailed with {len(loader.errors)} error(s):")
        for err in loader.errors:
            print(f"  {err}")
        sys.exit(1)

    if loader.warnings:
        print(f"\nLoaded with {len(loader.warnings)} warning(s):")
        for w in loader.warnings:
            print(f"  {w}")

    print(
        f"OK: rules loaded successfully ({len(ruleset.rules)} rules across {len(ruleset.manifest.layers)} layers, "
        f"{len(ruleset.reason_codes)} reason codes)."
    )
    sys.exit(0)
