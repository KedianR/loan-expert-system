"""
Rule loader unit tests.

Implements: RT-01, RT-02, RT-04, RT-05, RT-07, RT-09, RT-11
Spec: docs/09-file-formats.md §7
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from src.engine.rule_loader import RuleLoader, load_rules

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_RULES_DIR = REPO_ROOT / "rules"
REAL_PARAMS_PATH = REPO_ROOT / "params" / "params.toml"


@pytest.fixture
def temp_rules_dir(tmp_path: Path) -> Path:
    """Creates a temporary copy of rules/ directory for mutation testing."""
    shutil.copytree(REAL_RULES_DIR, tmp_path / "rules")
    return tmp_path / "rules"


class TestRuleLoader:
    def test_RT01_baseline_loads(self):
        """RT-01, NFR-05: Baseline rule set loads cleanly with 20 active rules, 2 disabled, 21 reason codes."""
        ruleset = load_rules(REAL_RULES_DIR, REAL_PARAMS_PATH)
        assert ruleset is not None
        active_rules = [r for r in ruleset.rules.values() if r.status == "active"]
        disabled_rules = [r for r in ruleset.rules.values() if r.status == "disabled"]
        assert len(active_rules) == 20
        assert len(disabled_rules) == 2
        assert len(ruleset.reason_codes) == 21

    def test_RT02_duplicate_rule_id(self, temp_rules_dir: Path):
        """RT-02: K04 appears twice -> DUPLICATE_RULE_ID."""
        ko_file = temp_rules_dir / "knockout.toml"
        content = ko_file.read_text(encoding="utf-8")
        # Duplicate K04 entry
        duplicate = """
[[rule]]
id = "K04"
layer = "knockout"
description = "Duplicate K04"
clause = "CP-2.3"
when = "credit_score < min_credit_score"
outcome = "ineligible"
reason_code = "CREDIT_SCORE_BELOW_MINIMUM"
owner = "credit-policy"
effective_date = "2026-11-05"
version = "0.1.0"
status = "active"
"""
        ko_file.write_text(content + duplicate, encoding="utf-8")
        loader = RuleLoader(temp_rules_dir, REAL_PARAMS_PATH)
        res = loader.load()
        assert res is None
        error_codes = [e.code for e in loader.errors]
        assert "DUPLICATE_RULE_ID" in error_codes

    def test_RT04_magic_number(self, temp_rules_dir: Path):
        """RT-04: Numeric literal in when -> MAGIC_NUMBER."""
        ko_file = temp_rules_dir / "knockout.toml"
        content = ko_file.read_text(encoding="utf-8")
        modified = content.replace("credit_score < min_credit_score", "credit_score < 650")
        ko_file.write_text(modified, encoding="utf-8")
        loader = RuleLoader(temp_rules_dir, REAL_PARAMS_PATH)
        res = loader.load()
        assert res is None
        error_codes = [e.code for e in loader.errors]
        assert "MAGIC_NUMBER" in error_codes

    def test_RT05_unknown_name(self, temp_rules_dir: Path):
        """RT-05: Misspelt field name in when -> UNKNOWN_NAME."""
        ko_file = temp_rules_dir / "knockout.toml"
        content = ko_file.read_text(encoding="utf-8")
        modified = content.replace(
            "credit_score < min_credit_score", "credit_scor < min_credit_score"
        )
        ko_file.write_text(modified, encoding="utf-8")
        loader = RuleLoader(temp_rules_dir, REAL_PARAMS_PATH)
        res = loader.load()
        assert res is None
        error_codes = [e.code for e in loader.errors]
        assert "UNKNOWN_NAME" in error_codes

    def test_RT07_future_read(self, temp_rules_dir: Path):
        """RT-07: A knockout rule that reads recommended_amount -> FUTURE_READ."""
        ko_file = temp_rules_dir / "knockout.toml"
        content = ko_file.read_text(encoding="utf-8")
        modified = content.replace(
            "credit_score < min_credit_score",
            "credit_score < min_credit_score and recommended_amount < min_amount",
        )
        ko_file.write_text(modified, encoding="utf-8")
        loader = RuleLoader(temp_rules_dir, REAL_PARAMS_PATH)
        res = loader.load()
        assert res is None
        error_codes = [e.code for e in loader.errors]
        assert "FUTURE_READ" in error_codes

    def test_RT09_reason_code_missing_and_not_allowed(self, temp_rules_dir: Path):
        """RT-09: Ineligible rule without reason_code -> REASON_CODE_MISSING; derive rule with one -> REASON_CODE_NOT_ALLOWED."""
        # 1. Ineligible rule without reason_code
        ko_file = temp_rules_dir / "knockout.toml"
        content = ko_file.read_text(encoding="utf-8")
        modified = content.replace('reason_code = "CREDIT_SCORE_BELOW_MINIMUM"', "")
        ko_file.write_text(modified, encoding="utf-8")
        loader = RuleLoader(temp_rules_dir, REAL_PARAMS_PATH)
        res = loader.load()
        assert res is None
        assert "REASON_CODE_MISSING" in [e.code for e in loader.errors]

        # 2. Derive rule with reason_code
        el_file = temp_rules_dir / "eligibility.toml"
        el_content = el_file.read_text(encoding="utf-8")
        modified_el = el_content.replace(
            'computes = ["band"]',
            'computes = ["band"]\nreason_code = "INCOMPLETE_APPLICATION"',
        )
        el_file.write_text(modified_el, encoding="utf-8")
        loader2 = RuleLoader(temp_rules_dir, REAL_PARAMS_PATH)
        res2 = loader2.load()
        assert res2 is None
        assert "REASON_CODE_NOT_ALLOWED" in [e.code for e in loader2.errors]

    def test_RT11_orphan_code(self, temp_rules_dir: Path):
        """RT-11: Delete rule R03 and leave its code -> ORPHAN_CODE."""
        ref_file = temp_rules_dir / "referral.toml"
        content = ref_file.read_text(encoding="utf-8")
        # Remove R03 rule block
        r03_pos = content.find('id = "R03"')
        block_start = content.rfind("[[rule]]", 0, r03_pos)
        modified = content[:block_start].strip()
        ref_file.write_text(modified + "\n", encoding="utf-8")

        loader = RuleLoader(temp_rules_dir, REAL_PARAMS_PATH)
        res = loader.load()
        assert res is None
        error_codes = [e.code for e in loader.errors]
        assert "ORPHAN_CODE" in error_codes
