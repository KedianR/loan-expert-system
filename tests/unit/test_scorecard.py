"""Unit tests for comparison scorecard (WP-18, FR-22, CR-05).

Verifies per docs/comparison-methodology.md:
  - scorecard.json and scorecard.md exist in reports/comparison/.
  - Exactly three systems scored: rule_system, logistic_regression, gradient_boosting.
  - Exactly four criteria scored: transparency, auditability, edge_cases, regulatory_defensibility.
  - Scores strictly in range [0, 3].
  - Every cell contains: score, met anchor, artifact path(s) that exist on disk, and one sentence.
  - No operational agility or financial performance scored criteria.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_SYSTEMS = ["rule_system", "logistic_regression", "gradient_boosting"]
EXPECTED_CRITERIA = ["transparency", "auditability", "edge_cases", "regulatory_defensibility"]


def test_scorecard_files_exist() -> None:
    """FR-22, CR-05: Verify scorecard.json and scorecard.md exist in reports/comparison/."""
    json_path = REPO_ROOT / "reports" / "comparison" / "scorecard.json"
    md_path = REPO_ROOT / "reports" / "comparison" / "scorecard.md"
    assert json_path.exists(), f"Missing {json_path}"
    assert md_path.exists(), f"Missing {md_path}"


def test_scorecard_systems_criteria_and_scale() -> None:
    """FR-22: Three systems, exactly four criteria, scores strictly in range 0 to 3."""
    json_path = REPO_ROOT / "reports" / "comparison" / "scorecard.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # Exactly the expected criteria
    criteria_keys = list(data.get("criteria", {}).keys())
    assert sorted(criteria_keys) == sorted(EXPECTED_CRITERIA), (
        f"Criteria mismatch. Expected {EXPECTED_CRITERIA}, got {criteria_keys}"
    )

    scores = data["scores"]
    assert sorted(scores.keys()) == sorted(EXPECTED_SYSTEMS), (
        f"Systems mismatch. Expected {EXPECTED_SYSTEMS}, got {list(scores.keys())}"
    )

    for sys_key in EXPECTED_SYSTEMS:
        for crit_key in EXPECTED_CRITERIA:
            assert crit_key in scores[sys_key], f"Missing {crit_key} in {sys_key}"
            cell = scores[sys_key][crit_key]
            score = cell["score"]
            assert isinstance(score, int) and 0 <= score <= 3, (
                f"Score for {sys_key}.{crit_key} must be int in [0, 3], got {score}"
            )


def test_every_cell_has_anchor_artifact_and_sentence() -> None:
    """FR-22, CR-05: Every cell has anchor, existing artifact path, and one sentence."""
    json_path = REPO_ROOT / "reports" / "comparison" / "scorecard.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    scores = data["scores"]
    for sys_key in EXPECTED_SYSTEMS:
        for crit_key in EXPECTED_CRITERIA:
            cell = scores[sys_key][crit_key]

            # Anchor must be present
            anchor = cell.get("anchor", "")
            assert anchor and isinstance(anchor, str), f"Missing anchor for {sys_key}.{crit_key}"

            # Justification must be non-empty string
            just = cell.get("justification", "")
            assert just and isinstance(just, str), f"Missing justification for {sys_key}.{crit_key}"

            # Artifacts list must not be empty, and every cited file must exist
            artifacts = cell.get("artifacts", [])
            assert artifacts and len(artifacts) > 0, f"No artifacts for {sys_key}.{crit_key}"
            for art in artifacts:
                art_path = REPO_ROOT / art
                assert art_path.exists(), (
                    f"Artifact path does not exist on disk: {art} (cited by {sys_key}.{crit_key})"
                )
