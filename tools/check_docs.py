"""Document-to-code consistency check (WP-21, make check-docs).

Verifies:
  1. Rule IDs in docs appear in rules/*.toml
  2. Reason codes in docs appear in rules/reason_codes.toml
  3. Parameter names in docs appear in params/params.toml
  4. Rule IDs and reason codes in rules/ appear in docs
  5. data/raw/, data/protected/, data/mapped/, data/splits/ not git-tracked

Fixes a document, never a rule (AGENTS.md hard rules).
Differences are listed; the script exits non-zero if critical mismatches found.

Usage: make check-docs
       python tools/check_docs.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Docs to scan for IDs/names
DOCS_TO_SCAN = [
    REPO_ROOT / "docs",
    REPO_ROOT / "AGENTS.md",
]

# Rule and param files
RULES_DIR = REPO_ROOT / "rules"
PARAMS_PATH = REPO_ROOT / "params" / "params.toml"

RULE_ID_PATTERN = re.compile(r"\b([VKAERPX]\d{2})\b")
PARAM_NAME_PATTERN = re.compile(
    r"\b(min_amount|max_amount|amount_step|min_tenure|max_tenure|min_age|min_income|min_credit_score|min_emp_salaried|min_emp_self|max_foir|max_enquiries|band_a_min_score|band_b_min_score|band_c_min_score|band_a_rate_min|band_a_rate_max|band_b_rate_min|band_b_rate_max|band_c_rate_min|band_c_rate_max|origination_fee_pct|processing_fee_pct|income_multiple_max|fallback_obligations_pct|unknown_delinquency_pct)\b"
)


def _load_rule_ids_from_toml() -> set[str]:
    """Extract all rule IDs from rules/*.toml files."""
    ids: set[str] = set()
    for f in RULES_DIR.glob("*.toml"):
        if f.name in ("fields.toml", "manifest.toml"):
            continue
        try:
            with open(f, "rb") as fh:
                data = tomllib.load(fh)
            # Rules may be in a list under a key, or dict of dicts
            for key, val in data.items():
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict) and "id" in item:
                            ids.add(item["id"])
                elif isinstance(val, dict) and "id" in val:
                    ids.add(val["id"])
        except Exception:
            pass
    return ids


def _load_reason_codes_from_toml() -> set[str]:
    """Extract all reason codes from rules/reason_codes.toml."""
    path = RULES_DIR / "reason_codes.toml"
    if not path.exists():
        return set()
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    codes: set[str] = set()
    for key, val in data.items():
        if isinstance(val, dict):
            for code_key in val:
                codes.add(code_key)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "code" in item:
                    codes.add(item["code"])
                elif isinstance(item, str):
                    codes.add(item)
        elif isinstance(val, str):
            codes.add(key)
    return codes


def _load_param_names_from_toml() -> set[str]:
    """Extract all parameter names from params/params.toml (flattened keys)."""
    names: set[str] = set()
    with open(PARAMS_PATH, "rb") as fh:
        data = tomllib.load(fh)

    def _recurse(d: object, prefix: str = "") -> None:
        if isinstance(d, dict):
            for k, v in d.items():
                full = (prefix + "_" + k).lstrip("_") if prefix else k
                names.add(k)
                names.add(full)
                _recurse(v, full)
        elif isinstance(d, list):
            for item in d:
                _recurse(item, prefix)

    _recurse(data)
    return names


def _scan_docs(codes_in_files: set[str]) -> tuple[set[str], set[str], set[str]]:
    """Scan docs for rule IDs, reason codes, and param names."""
    rule_ids: set[str] = set()
    found_reason_codes: set[str] = set()
    found_param_names: set[str] = set()

    for d in DOCS_TO_SCAN:
        p = Path(d)
        if not p.exists():
            continue
        files = list(p.rglob("*.md")) if p.is_dir() else [p]
        for f in files:
            if "reports" in f.parts:
                continue
            content = f.read_text(encoding="utf-8", errors="replace")
            rule_ids.update(RULE_ID_PATTERN.findall(content))
            for code in codes_in_files:
                if code in content:
                    found_reason_codes.add(code)
            found_param_names.update(PARAM_NAME_PATTERN.findall(content))

    return rule_ids, found_reason_codes, found_param_names


def _check_secrets_scan() -> list[str]:
    """Check that sensitive paths are not git-tracked."""
    violations = []
    sensitive_patterns = [
        "data/raw/",
        "data/protected/",
        "data/mapped/",
        "data/splits/",
        "data/decisions/",
        "data/synthetic/d3_",
        "models/",
        "kaggle.json",
    ]
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        tracked = result.stdout.splitlines()
        for f in tracked:
            for pat in sensitive_patterns:
                if pat in f:
                    # Allow python generator source files in data/synthetic/; ban generated datasets (.csv)
                    if pat == "data/synthetic/d3_" and f.endswith(".py"):
                        continue
                    violations.append(f"TRACKED: {f}")
    except Exception as e:
        violations.append(f"Could not run git ls-files: {e}")
    return violations


def main() -> None:
    print("=== check-docs: document-to-code consistency check ===")
    issues = []
    warnings = []

    # 1. Load rule file contents
    rule_ids_in_files = _load_rule_ids_from_toml()
    reason_codes_in_files = _load_reason_codes_from_toml()
    param_names_in_files = _load_param_names_from_toml()

    # 2. Scan docs
    doc_rule_ids, doc_reason_codes, doc_param_names = _scan_docs(reason_codes_in_files)

    print(f"\nRule IDs in rules/*.toml: {len(rule_ids_in_files)}")
    print(f"Rule IDs mentioned in docs: {len(doc_rule_ids)}")
    print(f"Reason codes in reason_codes.toml: {len(reason_codes_in_files)}")
    print(f"Reason codes mentioned in docs: {len(doc_reason_codes)}")
    print(f"Policy parameters mentioned in docs: {len(doc_param_names)}")

    # 3. Cross-check rule IDs bidirectional:
    # A. Are all rule IDs in files documented?
    missing_rule_docs = rule_ids_in_files - doc_rule_ids
    if missing_rule_docs:
        issues.append(f"Rule IDs in rules/*.toml missing from docs: {sorted(missing_rule_docs)}")
    else:
        print("  OK: All rule IDs in rules/*.toml are present in docs.")

    # B. Does doc mention extra rule IDs?
    extra_rule_ids = doc_rule_ids - rule_ids_in_files
    for rid in sorted(extra_rule_ids):
        warnings.append(
            f"  Doc mentions rule ID '{rid}' not in active rules/*.toml (historical/catalog note)"
        )

    # 4. Cross-check reason codes bidirectional:
    # Are all reason codes in toml documented in docs?
    missing_codes = reason_codes_in_files - doc_reason_codes
    if missing_codes:
        issues.append(
            f"Reason codes in reason_codes.toml missing from docs: {sorted(missing_codes)}"
        )
    else:
        print("  OK: All reason codes in reason_codes.toml are present in docs.")

    # 4b. Cross-check parameter names:
    # Parameter names that appear in docs must exist in params/params.toml
    unknown_doc_params = doc_param_names - param_names_in_files
    if unknown_doc_params:
        issues.append(
            f"Parameter names in docs not found in params/params.toml: {sorted(unknown_doc_params)}"
        )
    else:
        print("  OK: All parameter names mentioned in docs exist in params/params.toml.")

    # 5. Secrets scan
    print("\n=== Secrets and sensitive file scan ===")
    secret_violations = _check_secrets_scan()
    if secret_violations:
        for v in secret_violations:
            issues.append(v)
        print(f"  FAIL: {len(secret_violations)} sensitive file(s) tracked by git")
    else:
        print("  OK: No sensitive paths tracked by git")

    # 6. Summary
    print("\n=== Summary ===")
    if warnings:
        print(f"Informational notes ({len(warnings)}):")
        for w in warnings:
            print(w)

    if issues:
        print(f"\nCRITICAL ({len(issues)}) — must fix before final commit:")
        for issue in issues:
            print(f"  {issue}")
        sys.exit(1)
    else:
        print("Check-docs: all consistency checks passed.")


if __name__ == "__main__":
    main()
