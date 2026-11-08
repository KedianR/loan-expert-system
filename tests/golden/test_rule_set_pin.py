"""
Rule-set hash pin test.

Implements: docs/09-file-formats.md §6 "The pin test"
Spec: make test must fail when the hash changes without the pin being updated.

Phase 0: only params/params.toml exists. The hash covers only that file.
Phase 2 will add rule files and update the pin.

Referenced in docs/open-questions.md OQ-003.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.engine.ruleset_hash import compute_hash_from_root  # noqa: E402


class TestRuleSetPin:
    """The hash of all present rule-set files must match the pin."""

    def test_hash_matches_pin(self):
        """
        Compute the hash from the repository and compare with the stored pin.

        A failure here means either:
          (a) a policy file changed without updating the pin, or
          (b) the pin was updated without the policy file changing.

        Either way: update the pin and the version together.
        """
        pin_path = REPO_ROOT / "tests" / "golden" / "rule_set_pin.json"
        assert pin_path.exists(), f"Pin file not found: {pin_path}"

        pin = json.loads(pin_path.read_text(encoding="utf-8"))
        stored_hash = pin["rule_set_hash"]
        stored_version = pin["rule_set_version"]

        current_hash = compute_hash_from_root(REPO_ROOT)

        assert current_hash == stored_hash, (
            f"\nRule-set hash mismatch!\n"
            f"  Stored  : {stored_hash}\n"
            f"  Computed: {current_hash}\n"
            f"  Version : {stored_version}\n"
            "If you changed a policy file, update tests/golden/rule_set_pin.json "
            "and bump the version together."
        )
