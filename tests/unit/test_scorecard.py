"""Unit tests for comparison scorecard (WP-18, FR-22, CR-05).

Verifies:
  - scorecard.json and scorecard.md exist.
  - Every score cell in scorecard.json has an artifact path that exists on disk.
  - Every score is an integer between 0 and 3.
  - Every score has a non-empty anchor and justification.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_scorecard_files_exist() -> None:
    """Verify scorecard.json and scorecard.md exist in reports/comparison/."""
    json_path = REPO_ROOT / "reports" / "comparison" / "scorecard.json"
    md_path = REPO_ROOT / "reports" / "comparison" / "scorecard.md"
    assert json_path.exists(), f"Missing {json_path}"
    assert md_path.exists(), f"Missing {md_path}"


def test_every_score_has_valid_artifacts() -> None:
    """Verify that every score cell contains artifact paths that exist on disk."""
    json_path = REPO_ROOT / "reports" / "comparison" / "scorecard.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    scores = data["scores"]
    systems = ["rule_system", "logistic_regression", "gradient_boosting"]
    criteria = ["transparency", "auditability", "edge_cases", "regulatory_defensibility"]

    for sys_key in systems:
        assert sys_key in scores, f"Missing system: {sys_key}"
        for crit_key in criteria:
            assert crit_key in scores[sys_key], f"Missing criterion: {crit_key} in {sys_key}"
            cell = scores[sys_key][crit_key]

            # Score in [0, 3]
            score = cell["score"]
            assert isinstance(score, int) and 0 <= score <= 3, (
                f"Invalid score {score} for {sys_key}.{crit_key}"
            )

            # Anchor and justification
            assert cell.get("anchor"), f"Missing anchor for {sys_key}.{crit_key}"
            assert cell.get("justification"), f"Missing justification for {sys_key}.{crit_key}"

            # Artifacts must exist on disk
            artifacts = cell.get("artifacts", [])
            assert len(artifacts) > 0, f"No artifacts cited for {sys_key}.{crit_key}"
            for art in artifacts:
                art_path = REPO_ROOT / art
                assert art_path.exists(), (
                    f"Artifact path does not exist on disk: {art} (cited by {sys_key}.{crit_key})"
                )
