"""
Hygiene analyser unit tests on seeded faults and grid parameter sensitivity.

Implements: docs/decision-tables.md §6
Findings:
  1. COMPLETENESS_GAP
  2. CONTRADICTION
  3. REDUNDANT_RULE
  4. PROTECTED_ATTRIBUTE_READ

Also tests that the hygiene grid is built from loaded parameters (no hard-coded
policy values), so a change to one parameter is reflected in the grid.
"""

from __future__ import annotations

import shutil
from decimal import Decimal
from pathlib import Path

from src.engine.hygiene import (
    _build_foir_obligations,
    check_completeness_and_redundancy,
    check_contradictions,
    generate_hygiene_grid,
    scan_protected_attributes,
)
from src.engine.rule_loader import RuleDefinition, RuleLoader, RuleSet, load_rules

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_RULES_DIR = REPO_ROOT / "rules"
REAL_PARAMS_PATH = REPO_ROOT / "params" / "params.toml"


class TestHygieneFaults:
    def test_completeness_gap_seeded_fault(self, tmp_path: Path):
        """Seeded fault: Remove band C from parameters: points with score >= 650 reach default NO_RULE_APPLICABLE."""
        rs = load_rules(REAL_RULES_DIR, REAL_PARAMS_PATH)
        assert rs is not None

        # Create a modified rule set with band C removed
        bands_without_c = [b for b in rs.bands if b["id"] != "C"]
        modified_rs = RuleSet(
            manifest=rs.manifest,
            params=rs.params,
            bands=bands_without_c,
            fields=rs.fields,
            reason_codes=rs.reason_codes,
            rules=rs.rules,
            rules_by_layer=rs.rules_by_layer,
        )

        comp_findings, _ = check_completeness_and_redundancy(modified_rs)
        assert len(comp_findings) > 0
        finding_codes = [f.code for f in comp_findings]
        assert "COMPLETENESS_GAP" in finding_codes

    def test_contradiction_seeded_fault(self):
        """Seeded fault: Add K07 with the same when as K04 and outcome refer."""
        rs = load_rules(REAL_RULES_DIR, REAL_PARAMS_PATH)
        assert rs is not None

        k04 = rs.rules["K04"]
        k07 = RuleDefinition(
            id="K07",
            layer="knockout",
            description="Contradictory K07 rule",
            clause="Fault",
            when=k04.when,
            outcome="refer",
            owner="test",
            effective_date="2026-11-05",
            version="0.1.0",
            status="active",
            reason_code="NO_CREDIT_HISTORY",
            parsed_condition=k04.parsed_condition,
        )

        modified_rules = dict(rs.rules)
        modified_rules["K07"] = k07

        modified_rs = RuleSet(
            manifest=rs.manifest,
            params=rs.params,
            bands=rs.bands,
            fields=rs.fields,
            reason_codes=rs.reason_codes,
            rules=modified_rules,
            rules_by_layer=rs.rules_by_layer,
        )

        contra_findings = check_contradictions(modified_rs)
        assert len(contra_findings) > 0
        finding_codes = [f.code for f in contra_findings]
        assert "CONTRADICTION" in finding_codes

    def test_redundant_rule_seeded_fault(self, tmp_path: Path):
        """Seeded fault: Add K07 with credit_score < min_credit_score and enquiries_6m > max_enquiries_6m, code CREDIT_SCORE_BELOW_MINIMUM."""
        # Create temp copy of rules
        temp_rules = tmp_path / "rules"
        shutil.copytree(REAL_RULES_DIR, temp_rules)

        ko_file = temp_rules / "knockout.toml"
        ko_text = ko_file.read_text(encoding="utf-8")
        k07_toml = """
[[rule]]
id = "K07"
layer = "knockout"
description = "Redundant K07 rule"
clause = "Fault"
when = "credit_score < min_credit_score and enquiries_6m > max_enquiries_6m"
outcome = "ineligible"
reason_code = "CREDIT_SCORE_BELOW_MINIMUM"
owner = "test"
effective_date = "2026-11-05"
version = "0.1.0"
status = "active"
"""
        ko_file.write_text(ko_text + k07_toml, encoding="utf-8")

        loader = RuleLoader(temp_rules, REAL_PARAMS_PATH)
        rs = loader.load()
        assert rs is not None

        _, red_findings = check_completeness_and_redundancy(rs)
        assert len(red_findings) > 0
        finding_codes = [f.code for f in red_findings]
        assert "REDUNDANT_RULE" in finding_codes

    def test_protected_attribute_scan_seeded_fault(self, tmp_path: Path):
        """Seeded fault: A line naming gender in a test copy of the fact builder."""
        temp_repo = tmp_path / "repo"
        shutil.copytree(REPO_ROOT / "src", temp_repo / "src")
        shutil.copytree(REPO_ROOT / "rules", temp_repo / "rules")

        # Seed gender read into fact builder
        fb_file = temp_repo / "src" / "facts" / "fact_builder.py"
        fb_text = fb_file.read_text(encoding="utf-8")
        # Add code that reads gender
        seeded_code = fb_text + "\n\ndef _seeded_check(data):\n    return data.get('gender')\n"
        fb_file.write_text(seeded_code, encoding="utf-8")

        findings = scan_protected_attributes(temp_repo)
        assert len(findings) > 0
        finding_codes = [f.code for f in findings]
        assert "PROTECTED_ATTRIBUTE_READ" in finding_codes

    # -------------------------------------------------------------------------
    # Item 1 (Phase 2 closing patch): grid built from loaded parameters only.
    # Implements: docs/decision-tables.md §6
    # -------------------------------------------------------------------------

    def test_grid_reflects_param_change(self, tmp_path: Path):
        """
        Changing max_existing_foir in a copy of params.toml from 0.50 to 0.45
        must produce grid points just below, exactly at and just above 0.45.
        No hard-coded FOIR threshold may appear in generate_hygiene_grid.
        """
        # --- copy params.toml and change max_existing_foir to 0.45 ---
        orig_text = REAL_PARAMS_PATH.read_text(encoding="utf-8")
        modified_text = orig_text.replace(
            'max_existing_foir = "0.50"',
            'max_existing_foir = "0.45"',
        )
        assert modified_text != orig_text, (
            "Replacement failed; original params.toml may have changed"
        )
        tmp_params = tmp_path / "params.toml"
        tmp_params.write_text(modified_text, encoding="utf-8")

        # Load the rule set with the modified params
        loader = RuleLoader(REAL_RULES_DIR, tmp_params)
        rs = loader.load()
        assert rs is not None, "Rule loader failed with modified params"

        # Verify the loaded value
        assert Decimal(str(rs.params["max_existing_foir"])) == Decimal("0.45"), (
            "max_existing_foir was not changed in the loaded rule set"
        )

        # Build the grid from the modified rule set
        grid = generate_hygiene_grid(rs)
        assert len(grid) > 0

        # The FOIR grid uses income = 1_000_000.
        # At 0.45: obligations = 450_000.
        # Just below: 449_999; just above: 450_001.
        grid_income = 1_000_000
        threshold = Decimal("0.45")
        expected_obligations = _build_foir_obligations(grid_income, [threshold])
        # Must contain at least the three boundary points
        assert len(expected_obligations) >= 3
        at_threshold = int((threshold * grid_income).to_integral_value())
        assert at_threshold - 1 in expected_obligations
        assert at_threshold in expected_obligations
        assert at_threshold + 1 in expected_obligations

        # Verify these obligation values appear in the hygiene grid
        grid_obligations = {
            pt["monthly_obligations"]
            for pt in grid
            if pt.get("monthly_net_income") == grid_income
            and pt.get("monthly_obligations") is not None
        }
        assert at_threshold - 1 in grid_obligations, (
            f"{at_threshold - 1} (just below 0.45 × {grid_income}) not in grid"
        )
        assert at_threshold in grid_obligations, (
            f"{at_threshold} (at 0.45 × {grid_income}) not in grid"
        )
        assert at_threshold + 1 in grid_obligations, (
            f"{at_threshold + 1} (just above 0.45 × {grid_income}) not in grid"
        )
