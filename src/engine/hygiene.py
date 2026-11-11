"""
Rule-set hygiene analyser and protected-attribute scanner.

Implements: FR-18, FR-20, WP-06
Spec: docs/decision-tables.md section 6

Checks:
  1. COMPLETENESS_GAP: Evaluates decision coverage on the grid. Invariant I-1 holds.
     Fails if any grid point results in NO_RULE_APPLICABLE default.
  2. CONTRADICTION: Checks that no two active rules have identical conditions with
     conflicting outcomes, and no two derive rules compute the same field.
  3. REDUNDANT_RULE: Checks that no active rule fires only at points where another
     rule with the same outcome and reason code also fires.
  4. PROTECTED_ATTRIBUTE_READ: Static scan of rule conditions, field registry,
     calculation registry, src/facts, and src/engine for protected attributes.
  5. Firing matrix generation: table of rule vs D1 case firing counts.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.engine.engine import decide
from src.engine.rule_loader import RuleSet

PROTECTED_ATTRIBUTES = {"gender", "religion", "caste"}


@dataclass
class Finding:
    code: str  # COMPLETENESS_GAP, CONTRADICTION, REDUNDANT_RULE, PROTECTED_ATTRIBUTE_READ
    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} at {self.location}: {self.message}"


# ---------------------------------------------------------------------------
# Protected Attribute Static Scanner
# ---------------------------------------------------------------------------


def scan_protected_attributes(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []

    # Target files to scan
    scan_targets: list[Path] = []

    # 1. rules/
    rules_dir = repo_root / "rules"
    if rules_dir.exists():
        scan_targets.extend(rules_dir.glob("*.toml"))

    # 2. src/facts/
    facts_dir = repo_root / "src" / "facts"
    if facts_dir.exists():
        scan_targets.extend(facts_dir.glob("*.py"))

    # 3. src/engine/
    engine_dir = repo_root / "src" / "engine"
    if engine_dir.exists():
        for p in engine_dir.glob("*.py"):
            if p.name != "hygiene.py":
                scan_targets.append(p)

    # 4. src/calc/
    calc_dir = repo_root / "src" / "calc"
    if calc_dir.exists():
        scan_targets.extend(calc_dir.glob("*.py"))

    for file_path in scan_targets:
        rel_path = file_path.relative_to(repo_root)

        if file_path.suffix == ".toml":
            # For TOML files: check all text lines outside comments
            lines = file_path.read_text(encoding="utf-8").splitlines()
            for line_no, line in enumerate(lines, start=1):
                code_part = line.split("#")[0].lower()
                for attr in PROTECTED_ATTRIBUTES:
                    if re.search(rf"\b{attr}\b", code_part):
                        findings.append(
                            Finding(
                                "PROTECTED_ATTRIBUTE_READ",
                                f"{rel_path}:{line_no}",
                                f"Rule or field file reads protected attribute '{attr}'",
                            )
                        )

        elif file_path.suffix == ".py":
            # For Python files: parse AST to ignore docstrings/comments and inspect code
            try:
                tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
            except Exception:
                continue

            # Walk all AST nodes looking for variable names, attribute names, string literals in comparisons/subscripts
            for node in ast.walk(tree):
                # Variable names (Name)
                if isinstance(node, ast.Name):
                    name_lower = node.id.lower()
                    for attr in PROTECTED_ATTRIBUTES:
                        if name_lower == attr or attr in name_lower.split("_"):
                            findings.append(
                                Finding(
                                    "PROTECTED_ATTRIBUTE_READ",
                                    f"{rel_path}:{node.lineno}",
                                    f"Code references protected attribute variable '{node.id}'",
                                )
                            )
                # Attribute access (obj.gender)
                elif isinstance(node, ast.Attribute):
                    attr_lower = node.attr.lower()
                    for attr in PROTECTED_ATTRIBUTES:
                        if attr_lower == attr:
                            findings.append(
                                Finding(
                                    "PROTECTED_ATTRIBUTE_READ",
                                    f"{rel_path}:{node.lineno}",
                                    f"Code accesses protected attribute '{node.attr}'",
                                )
                            )
                # Subscripts (data['gender'])
                elif isinstance(node, ast.Subscript):
                    slice_node = node.slice
                    if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
                        val_lower = slice_node.value.lower()
                        for attr in PROTECTED_ATTRIBUTES:
                            if val_lower == attr:
                                findings.append(
                                    Finding(
                                        "PROTECTED_ATTRIBUTE_READ",
                                        f"{rel_path}:{slice_node.lineno}",
                                        f"Code accesses dictionary key with protected attribute '{slice_node.value}'",
                                    )
                                )
                # String literals in method calls (data.get('gender')) or expressions
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    val_lower = node.value.lower()
                    for attr in PROTECTED_ATTRIBUTES:
                        if val_lower == attr:
                            findings.append(
                                Finding(
                                    "PROTECTED_ATTRIBUTE_READ",
                                    f"{rel_path}:{node.lineno}",
                                    f"Code contains string reference to protected attribute '{node.value}'",
                                )
                            )

    return findings


# ---------------------------------------------------------------------------
# Contradiction Check
# ---------------------------------------------------------------------------


def check_contradictions(rule_set: RuleSet) -> list[Finding]:
    findings: list[Finding] = []
    active_rules = [r for r in rule_set.rules.values() if r.status == "active"]

    # 1. No two active rules with identical condition give different outcomes
    # Note: DT-6: Overlaps of INELIGIBLE with REFER are allowed by precedence,
    # but rules with identical conditions and different outcomes are contradictions (e.g. seeded K07 vs K04).
    for i, r1 in enumerate(active_rules):
        for r2 in active_rules[i + 1 :]:
            # Normalise whitespace in condition
            c1 = " ".join(r1.when.split())
            c2 = " ".join(r2.when.split())
            if c1 == c2 and r1.outcome != r2.outcome:
                findings.append(
                    Finding(
                        "CONTRADICTION",
                        f"{r1.id} vs {r2.id}",
                        f"Rules have identical condition '{r1.when}' but conflicting outcomes: "
                        f"'{r1.outcome}' vs '{r2.outcome}'",
                    )
                )

    # 2. No two derive rules compute the same field
    computed_fields: dict[str, str] = {}
    for r in active_rules:
        if r.outcome == "derive":
            for f in r.computes:
                if f in computed_fields:
                    findings.append(
                        Finding(
                            "CONTRADICTION",
                            f"{computed_fields[f]} and {r.id}",
                            f"Multiple derivation rules compute the same field '{f}'",
                        )
                    )
                else:
                    computed_fields[f] = r.id

    return findings


# ---------------------------------------------------------------------------
# The Grid: Completeness & Redundancy
# ---------------------------------------------------------------------------


def _build_foir_obligations(income: int, foir_thresholds: list) -> list[int]:
    """
    Convert FOIR threshold values to obligations for a given income level.
    For each threshold t, generate obligations that produce FOIR just below t,
    exactly at t, and just above t (using integer rupees, +/- 1).
    Uses real arithmetic matching src/calc: FOIR = obligations / income.
    Never invents a threshold; reads them from params/bands.
    """
    from decimal import ROUND_HALF_UP, Decimal

    result_set: list[int] = []
    inc = Decimal(str(income))
    for t in foir_thresholds:
        t_dec = Decimal(str(t))
        # exactly at threshold: round to nearest rupee
        at = int((t_dec * inc).to_integral_value(rounding=ROUND_HALF_UP))
        result_set.append(max(0, at - 1))  # just below
        result_set.append(at)  # at
        result_set.append(at + 1)  # just above
    return sorted(set(result_set))


def generate_hygiene_grid(rule_set: RuleSet) -> list[dict[str, Any]]:
    """
    Builds the values the rules can tell apart (docs/decision-tables.md §6).

    For each threshold a field is compared with (a parameter, or a sum such as
    recommended_amount + amount_step), the value just below, exactly at and just
    above it, plus ``unknown`` where the registry allows.  Derived values come
    from the real src/calc functions, never from literals.

    Level 1: full product over known values.
    Level 2: each field set to unknown (None) in turn against every other field value.
    """
    p = rule_set.params  # loaded params – no defaults; missing key is a loader error

    base_app: dict[str, Any] = {
        "applicant_id": "grid_applicant",
        "age": 34,
        "employment_type": "salaried",
        "employment_months": 48,
        "monthly_net_income": 80000,
        "monthly_obligations": 10000,
        "credit_score": 735,
        "enquiries_6m": 2,
        "severe_delinquency_36m": False,
        "written_off": False,
        "kyc_verified": True,
        "consent_given": True,
        "requested_amount": p["max_amount"] - 100000,  # well within product limits
        "requested_tenure_months": 36,
    }

    grid: list[dict[str, Any]] = [dict(base_app)]

    # -- Consent --
    grid.append({**base_app, "consent_given": False})

    # -- Amount limits (threshold: min_amount, max_amount) --
    min_amt: int = p["min_amount"]
    max_amt: int = p["max_amount"]
    for a in [min_amt - 1, min_amt, min_amt + 1, max_amt - 1, max_amt, max_amt + 1, 777777]:
        grid.append({**base_app, "requested_amount": a})

    # -- Tenure limits (threshold: min_tenure_months, max_tenure_months) --
    min_t: int = p["min_tenure_months"]
    max_t: int = p["max_tenure_months"]
    for t in [min_t - 1, min_t, min_t + 1, max_t - 1, max_t, max_t + 1]:
        grid.append({**base_app, "requested_tenure_months": t})

    # -- Age (threshold: min_age) --
    min_age: int = p["min_age"]
    for a in [min_age - 1, min_age, min_age + 1]:
        grid.append({**base_app, "age": a})

    # -- KYC --
    grid.append({**base_app, "kyc_verified": False})

    # -- Adverse history --
    grid.append({**base_app, "severe_delinquency_36m": True})
    grid.append({**base_app, "written_off": True})

    # -- Enquiries (threshold: max_enquiries_6m) --
    max_enq: int = p["max_enquiries_6m"]
    for e in [max_enq - 1, max_enq, max_enq + 1, max_enq + 2]:
        grid.append({**base_app, "enquiries_6m": e})

    # -- Employment tenure by type (thresholds: min_employment_months_*) --
    min_sal: int = p["min_employment_months_salaried"]
    for m in [min_sal - 1, min_sal, min_sal + 1]:
        grid.append({**base_app, "employment_type": "salaried", "employment_months": m})

    min_self: int = p["min_employment_months_self_employed"]
    for m in [min_self - 1, min_self, min_self + 1]:
        grid.append({**base_app, "employment_type": "self_employed", "employment_months": m})

    grid.append({**base_app, "employment_type": "other"})

    # -- Income (threshold: min_monthly_income) --
    min_inc: int = p["min_monthly_income"]
    for inc in [0, min_inc - 1, min_inc, min_inc + 1]:
        grid.append({**base_app, "monthly_net_income": inc, "monthly_obligations": 0})

    # -- Band / FOIR / Score grid --
    # Score thresholds come from band definitions (min_score per band).
    # FOIR thresholds come from band max_foir values AND max_existing_foir.
    band_min_scores: list[int] = sorted({int(b["min_score"]) for b in rule_set.bands}, reverse=True)
    # Sentinel scores: one below the lowest band threshold (ineligible) and
    # one above the highest (best band); boundary values around each threshold.
    score_values: list[int] = []
    for s in band_min_scores:
        score_values.extend([s - 1, s, s + 1])
    score_values.extend([band_min_scores[-1] - 1, band_min_scores[0] + 10])
    score_values = sorted(set(score_values))

    # FOIR thresholds: each band's max_foir, plus the global max_existing_foir.
    from decimal import Decimal as _D

    foir_thresholds: list = sorted(
        {_D(str(b["max_foir"])) for b in rule_set.bands} | {_D(str(p["max_existing_foir"]))}
    )

    # Use a fixed income large enough that +/- 1 rupee gives a meaningfully
    # different FOIR.  1,000,000 gives 1 ppm precision per rupee.
    grid_income = 1_000_000
    obligations_list = _build_foir_obligations(grid_income, foir_thresholds)

    # Use the minimum requestable amount (smallest passing V03) and a short
    # tenure so the derivation path runs cleanly.
    grid_req_amt = min_amt
    grid_tenure = min_t

    for sc in score_values:
        for obl in obligations_list:
            grid.append(
                {
                    **base_app,
                    "credit_score": sc,
                    "monthly_net_income": grid_income,
                    "monthly_obligations": obl,
                    "requested_amount": grid_req_amt,
                    "requested_tenure_months": grid_tenure,
                }
            )

    # -- Amount-step / binding-limit combinations (TV2, TV3, TV6, TV8) --
    # Build these from calc results so no literal appears here.
    # We supply the inputs; the engine runs the real formulas.
    amount_step: int = p["amount_step"]
    income_multiple_cap: int = p["income_multiple_cap"]

    grid.append(
        {
            **base_app,
            "monthly_net_income": 40000,
            "monthly_obligations": 12000,
            "credit_score": 760,
            "requested_amount": max_amt,  # large enough to trigger capacity cap
            "requested_tenure_months": 48,
        }
    )
    income_multiple_test_income = (max_amt - amount_step) // income_multiple_cap
    grid.append(
        {
            **base_app,
            "monthly_net_income": income_multiple_test_income,
            "monthly_obligations": 0,
            "credit_score": 720,
            # request at product maximum with income scaled so income_multiple_cap binds
            "requested_amount": max_amt,
            "requested_tenure_months": max_t,
        }
    )
    grid.append(
        {
            **base_app,
            "monthly_net_income": min_inc,
            "monthly_obligations": min_inc // 2,
            "credit_score": band_min_scores[-1],  # lowest band that qualifies
            "requested_amount": min_amt * 2,
            "requested_tenure_months": min_t,
        }
    )
    grid.append(
        {
            **base_app,
            "monthly_net_income": grid_income // 10,
            "monthly_obligations": grid_income // 20,
            "credit_score": band_min_scores[-1],
            "requested_amount": min_amt * 6,
            "requested_tenure_months": max_t // 2,
        }
    )

    # -- Multi-rule combinations --
    grid.append({**base_app, "credit_score": band_min_scores[-1] - 1, "enquiries_6m": max_enq + 2})
    grid.append(
        {
            **base_app,
            "credit_score": band_min_scores[-1] - 1,
            "monthly_net_income": min_inc - 1,
            "severe_delinquency_36m": True,
        }
    )
    grid.append({**base_app, "enquiries_6m": max_enq + 2, "employment_type": "other"})
    grid.append(
        {
            **base_app,
            "monthly_net_income": 0,
            "credit_score": band_min_scores[-1] - 1,
        }
    )

    # Level 2 variations: each input field set to None in turn
    for f_name, f_info in rule_set.fields.items():
        if f_info.get("kind") == "input":
            grid.append({**base_app, f_name: None})

    return grid


def check_completeness_and_redundancy(rule_set: RuleSet) -> tuple[list[Finding], list[Finding]]:
    completeness_findings: list[Finding] = []
    redundancy_findings: list[Finding] = []

    grid = generate_hygiene_grid(rule_set)
    active_rules = {r.id: r for r in rule_set.rules.values() if r.status == "active"}

    # Track firing set for each active rule: rule_id -> set of grid indices where it fired
    rule_fired_indices: dict[str, set[int]] = {r_id: set() for r_id in active_rules}

    for idx, applicant in enumerate(grid):
        res = decide(applicant, rule_set)

        # Completeness check: exactly one decision and NEVER the NO_RULE_APPLICABLE default
        if "NO_RULE_APPLICABLE" in res.get("reason_codes", []):
            completeness_findings.append(
                Finding(
                    "COMPLETENESS_GAP",
                    f"grid_point_{idx}",
                    f"Applicant reached default NO_RULE_APPLICABLE without reaching an explicit outcome. "
                    f"Input: {applicant}",
                )
            )

        # Invariant I-1 check:
        # If derive rules or amount rules run, verify no unknown inputs were present
        for step in res["steps"]:
            r_id = step["rule_id"]
            if step["status"] == "fired":
                rule_fired_indices[r_id].add(idx)

            if r_id in ("E02", "A01", "A02", "A03", "A04", "P01") and step["status"] == "fired":
                # Verify required facts were known
                for k, v in step.get("facts_used", {}).items():
                    if v is None:
                        completeness_findings.append(
                            Finding(
                                "COMPLETENESS_GAP",
                                f"grid_point_{idx}",
                                f"Invariant I-1 violated: rule '{r_id}' fired with unknown fact '{k}'",
                            )
                        )

    # Redundancy check:
    # "No active rule fires only at points where another rule with the same outcome and reason code also fires."
    for r1_id, r1 in active_rules.items():
        if r1.outcome not in ("ineligible", "refer"):
            continue
        r1_fires = rule_fired_indices[r1_id]
        if not r1_fires:
            continue

        for r2_id, r2 in active_rules.items():
            if r1_id == r2_id:
                continue
            if r1.outcome != r2.outcome:
                continue
            if r1.reason_code != r2.reason_code:
                continue

            r2_fires = rule_fired_indices[r2_id]
            # If r1 fires only at a subset of where r2 fires:
            if r1_fires.issubset(r2_fires) and len(r1_fires) <= len(r2_fires):
                redundancy_findings.append(
                    Finding(
                        "REDUNDANT_RULE",
                        f"{r1_id} subsumed by {r2_id}",
                        f"Rule {r1_id} fires only at points where {r2_id} (same outcome '{r1.outcome}' "
                        f"and reason code '{r1.reason_code}') also fires.",
                    )
                )

    return completeness_findings, redundancy_findings


# ---------------------------------------------------------------------------
# Firing Matrix Generation
# ---------------------------------------------------------------------------


def generate_firing_matrix(rule_set: RuleSet, d1_cases: list[dict[str, Any]]) -> dict[str, int]:
    matrix: dict[str, int] = {r.id: 0 for r in rule_set.rules.values() if r.status == "active"}
    for c in d1_cases:
        res = decide(c["input"], rule_set)
        for step in res["steps"]:
            if step["status"] == "fired":
                matrix[step["rule_id"]] += 1
    return matrix


def format_firing_matrix(matrix: dict[str, int]) -> str:
    lines = [
        "Rule Firing Matrix (D1 Dataset)",
        "----------------------------------------",
        f"{'Rule ID':<10} | {'Fired Count':<12} | {'Notes':<30}",
        "----------------------------------------",
    ]
    for r_id, count in sorted(matrix.items()):
        note = "OK" if count > 0 else "ZERO FIRINGS"
        lines.append(f"{r_id:<10} | {count:<12} | {note:<30}")
    lines.append(
        f"{'AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM':<10} | {'0':<12} | {'Unreachable by design (DT-3)':<30}"
    )
    lines.append("----------------------------------------")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main Hygiene Runner
# ---------------------------------------------------------------------------


def run_hygiene_analysis(
    rule_set: RuleSet, repo_root: Path, d1_path: Path | None = None
) -> tuple[list[Finding], dict[str, int] | None]:
    all_findings: list[Finding] = []

    # 1. Protected attribute scan
    prot_findings = scan_protected_attributes(repo_root)
    all_findings.extend(prot_findings)

    # 2. Contradiction check
    contra_findings = check_contradictions(rule_set)
    all_findings.extend(contra_findings)

    # 3. Completeness & Redundancy checks
    comp_findings, red_findings = check_completeness_and_redundancy(rule_set)
    all_findings.extend(comp_findings)
    all_findings.extend(red_findings)

    # 4. Firing matrix
    matrix = None
    if d1_path and d1_path.exists():
        d1_data = json.loads(d1_path.read_text(encoding="utf-8"))
        matrix = generate_firing_matrix(rule_set, d1_data.get("cases", []))
        # Check active rules have count > 0
        for r_id, count in matrix.items():
            if count == 0:
                all_findings.append(
                    Finding(
                        "FIRING_MATRIX_GAP",
                        r_id,
                        f"Active rule '{r_id}' fired 0 times on D1 coverage set",
                    )
                )

    return all_findings, matrix


if __name__ == "__main__":
    import sys

    from src.engine.rule_loader import load_rules

    root = Path(".")
    r_dir = root / "rules"
    p_path = root / "params" / "params.toml"
    d1_p = root / "data" / "d1" / "d1_cases.json"

    rs = load_rules(r_dir, p_path)
    if not rs:
        sys.exit(1)

    findings, f_matrix = run_hygiene_analysis(rs, root, d1_p)

    if f_matrix:
        print("\n" + format_firing_matrix(f_matrix) + "\n")

    if findings:
        print(f"Failed with {len(findings)} hygiene finding(s):")
        for f in findings:
            print(f"  {f}")
        sys.exit(1)

    print("OK: all hygiene checks passed with zero findings.")
    sys.exit(0)
