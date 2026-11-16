"""Traceability: requirement-to-test mapping (WP-21).

Dynamically parses all 47 requirements from docs/01-srs.md (FR-01..FR-26,
NFR-01..NFR-10, DR-01..DR-05, CR-01..CR-06), scans test functions in tests/
(excluding fixtures and setup helpers), and builds reports/traceability.md.

Usage: make traceability
       python tools/traceability.py

Output: reports/traceability.md and docs/reports/phase-5-6-evidence/traceability.md
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"
SRS_PATH = REPO_ROOT / "docs" / "01-srs.md"
OUTPUT_PATH = REPO_ROOT / "reports" / "traceability.md"
EVIDENCE_PATH = REPO_ROOT / "docs" / "reports" / "phase-5-6-evidence" / "traceability.md"

REQ_PATTERN = re.compile(r"\b(FR|NFR|DR|CR)[-_]?(\d+)\b", re.IGNORECASE)

# Supplementary mappings for requirements verified by dedicated test suites
# that may not carry explicit regex citations in their function names
EXPLICIT_TEST_MAPPINGS: dict[str, list[tuple[str, str]]] = {
    "FR-03": [
        ("tests/golden/test_calculations_tv.py", "test_tv1_clean_prime"),
        ("tests/golden/test_calculations_tv.py", "test_tv2_boundary_capacity_binding"),
        ("tests/unit/test_calc_unit.py", "test_f1_disposable_income"),
    ],
    "FR-04": [
        ("tests/golden/test_engine_tv.py", "test_golden_vectors_through_engine"),
        (
            "tests/unit/test_engine_behaviours.py",
            "test_fr06_decision_precedence_and_recommendation",
        ),
    ],
    "FR-07": [
        (
            "tests/property/test_calc_properties.py",
            "test_property_recommended_amount_caps_and_step",
        ),
        ("tests/golden/test_calculations_tv.py", "test_tv2_boundary_capacity_binding"),
    ],
    "FR-09": [
        ("tests/golden/test_calculations_tv.py", "test_tv8_repayment_capacity_below_minimum"),
        ("tests/unit/test_calc_unit.py", "test_f3_emi_invalid_tenure"),
    ],
    "FR-26": [
        (
            "tests/unit/test_rules_firing_and_boundaries.py",
            "test_A03_insufficient_repayment_capacity",
        ),
        ("tests/unit/test_engine_behaviours.py", "test_fr19_deterministic_engine_evaluation"),
    ],
    "NFR-03": [
        ("tests/unit/test_float_ban.py", "test_no_float_in_calc_or_facts"),
        ("tests/unit/test_param_loader.py", "test_no_floats_in_result"),
    ],
    "NFR-06": [
        (
            "tests/integration/test_phase3_api_and_audit.py",
            "test_fr10_fr11_d1_traces_notices_and_latency",
        ),
    ],
    "NFR-07": [
        ("tests/unit/test_d3_generator.py", "test_generator_generates_valid_json"),
        (
            "tests/unit/test_protected_store_isolation.py",
            "test_protected_store_isolation_static_scan",
        ),
    ],
    "NFR-08": [
        (
            "tests/integration/test_phase3_api_and_audit.py",
            "test_fr15_nfr02_audit_records_and_immutable_triggers",
        ),
    ],
    "NFR-09": [
        ("tests/unit/test_ui.py", "test_index_page_200_and_banner"),
        ("tests/unit/test_ui.py", "test_static_scan_no_innerhtml"),
    ],
    "NFR-10": [
        ("tests/unit/test_ui.py", "test_index_page_200_and_banner"),
    ],
    "DR-04": [
        ("tests/unit/test_d2_map.py", "test_d2_column_mapping_valid"),
        ("tests/unit/test_d2_map.py", "test_d2_datasheet_exists"),
    ],
}

# Special notes for specific requirements
REQUIREMENT_NOTES: dict[str, str] = {
    "NFR-06": "Met on engine-direct path only; single decision completes under 1s, batch of 10,000 under 5m.",
    "NFR-08": "Append-only audit log enforced by SQLite database triggers rejecting UPDATE and DELETE.",
}


def parse_srs_requirements() -> dict[str, str]:
    """Dynamically parse all requirement IDs and descriptions from docs/01-srs.md."""
    if not SRS_PATH.exists():
        raise FileNotFoundError(f"SRS file not found: {SRS_PATH}")

    content = SRS_PATH.read_text(encoding="utf-8")
    reqs: dict[str, str] = {}

    # 1. FR and CR table rows: | ID | Description | ...
    for m in re.finditer(r"\|\s*((?:FR|CR)-\d+)\s*\|\s*([^|]+?)\s*\|", content):
        req_id = m.group(1).strip()
        desc = m.group(2).strip()
        reqs[req_id] = desc

    # 2. NFR table rows: | NFR-xx Title | Description | ...
    for m in re.finditer(r"\|\s*(NFR-\d+)(?:\s+[^|]+?)?\s*\|\s*([^|]+?)\s*\|", content):
        req_id = m.group(1).strip()
        desc = m.group(2).strip()
        reqs[req_id] = desc

    # 3. DR bullets: - DR-xx: Description
    for m in re.finditer(r"-\s*(DR-\d+):\s*([^\n]+)", content):
        req_id = m.group(1).strip()
        desc = m.group(2).strip()
        reqs[req_id] = desc

    if len(reqs) != 47:
        raise ValueError(f"Expected 47 requirements in {SRS_PATH}, but parsed {len(reqs)}")

    return reqs


def scan_tests(all_requirements: dict[str, str]) -> dict[str, list[tuple[str, str]]]:
    """Scan test functions across tests/ and map them to requirement IDs.

    Excludes fixture/helper functions (e.g. test_db_path, @pytest.fixture).
    """
    mapping: dict[str, list[tuple[str, str]]] = {r: [] for r in all_requirements}

    # Apply supplementary explicit mappings first
    for req_id, tests in EXPLICIT_TEST_MAPPINGS.items():
        if req_id in mapping:
            for t in tests:
                if t not in mapping[req_id]:
                    mapping[req_id].append(t)

    # Scan test files
    for py_file in sorted(TESTS_DIR.rglob("*.py")):
        content = py_file.read_text(encoding="utf-8", errors="replace")
        rel_path = str(py_file.relative_to(REPO_ROOT)).replace("\\", "/")

        # Check module header (first 1500 chars)
        header_ids = set()
        for match in REQ_PATTERN.finditer(content[:1500]):
            prefix = match.group(1).upper()
            num = int(match.group(2))
            header_ids.add(f"{prefix}-{num:02d}")

        # Find test functions, excluding fixtures
        tests_in_file: list[tuple[str, set[str]]] = []
        for m in re.finditer(r"^\s*def (test_[^\s(]+)", content, re.MULTILINE):
            fn_name = m.group(1)
            start = m.start()

            # Exclude functions preceded by @pytest.fixture or known helper fixtures
            prefix_slice = content[max(0, start - 150) : start]
            if "@pytest.fixture" in prefix_slice or fn_name in ("test_db_path", "test_service"):
                continue

            snippet = content[max(0, start - 200) : start + 800]
            ids_found = set()
            for match in REQ_PATTERN.finditer(snippet):
                prefix = match.group(1).upper()
                num = int(match.group(2))
                ids_found.add(f"{prefix}-{num:02d}")
            tests_in_file.append((fn_name, ids_found))

        # Associate header IDs with the first real test function in the file
        if header_ids and tests_in_file:
            first_fn = tests_in_file[0][0]
            for req_id in header_ids:
                if req_id in mapping and not any(t[1] == first_fn for t in mapping[req_id]):
                    mapping[req_id].append((rel_path, first_fn))

        for fn_name, ids_found in tests_in_file:
            for req_id in ids_found:
                if req_id in mapping:
                    # Do not misattribute NFR-06 to audit triggers (NFR-06 is Performance; NFR-08 is Security)
                    if req_id == "NFR-06" and "audit_records_and_immutable_triggers" in fn_name:
                        continue
                    if not any(t[1] == fn_name for t in mapping[req_id]):
                        mapping[req_id].append((rel_path, fn_name))

    return mapping


def build_report(
    all_requirements: dict[str, str], mapping: dict[str, list[tuple[str, str]]]
) -> str:
    lines = [
        "# Requirement Traceability (auto-generated by tools/traceability.py)",
        "",
        "Every SRS requirement ID (dynamically parsed from `docs/01-srs.md`) and the test names verifying it.",
        "Generated by scanning test function names, docstrings, and explicit requirement mappings.",
        "",
        "| Requirement | Description | Tests | Status | Notes |",
        "|---|---|---|---|---|",
    ]

    unmet = []

    for req_id, description in sorted(all_requirements.items()):
        tests = mapping.get(req_id, [])
        note = REQUIREMENT_NOTES.get(req_id, "")
        if tests:
            test_names = "; ".join(f"`{t[1]}`" for t in tests[:3])
            if len(tests) > 3:
                test_names += f" (+{len(tests) - 3} more)"
            status = "✅ covered"
        else:
            test_names = "—"
            status = "⚠️ no test found"
            unmet.append((req_id, description))

        lines.append(
            f"| {req_id} | {description[:60]}{'…' if len(description) > 60 else ''} | {test_names} | {status} | {note} |"
        )

    if unmet:
        lines += [
            "",
            "## Unmet Requirements",
            "",
            "The following requirements have no test citing them by ID:",
            "",
        ]
        for req_id, description in unmet:
            lines.append(f"- **{req_id}**: {description}")

    return "\n".join(lines) + "\n"


def main() -> None:
    all_requirements = parse_srs_requirements()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    mapping = scan_tests(all_requirements)
    report = build_report(all_requirements, mapping)

    OUTPUT_PATH.write_text(report, encoding="utf-8")
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(report, encoding="utf-8")

    total = len(all_requirements)
    covered = sum(1 for tests in mapping.values() if tests)
    print(f"Traceability report written to {OUTPUT_PATH} and {EVIDENCE_PATH}")
    print(f"Requirements covered: {covered}/{total}")
    unmet = total - covered
    if unmet:
        print(f"Unmet: {unmet} — see report for details")


if __name__ == "__main__":
    main()
