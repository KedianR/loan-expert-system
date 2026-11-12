"""Comparison scorecard generator (WP-18, FR-22, CR-05).

Implements: docs/comparison-methodology.md.
Evaluates Rule System, Logistic Regression, and Gradient Boosting across:
  1. Transparency (0 to 3)
  2. Auditability (0 to 3)
  3. Edge Cases (0 to 3)
  4. Regulatory Defensibility (0 to 3)

Outputs:
  - reports/comparison/scorecard.json
  - reports/comparison/scorecard.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports" / "comparison"


def build_scorecard_data() -> dict[str, Any]:
    """Build the comparison scorecard dictionary with anchors and artifact citations."""
    scorecard = {
        "metadata": {
            "title": "Loan Eligibility System Comparison Scorecard",
            "spec": "docs/comparison-methodology.md",
            "requirement_ids": ["FR-22", "CR-05"],
            "caveat": "Illustrative policy values (D-02). Not a performance ranking; reflects architectural design properties.",
        },
        "criteria": {
            "transparency": {
                "name": "Transparency",
                "question": "Can a person see why this decision was made?",
                "scale": "0 to 3",
            },
            "auditability": {
                "name": "Auditability",
                "question": "Can a decision be reconstructed and checked later?",
                "scale": "0 to 3",
            },
            "edge_cases": {
                "name": "Edge Cases",
                "question": "Does it behave sensibly where inputs are odd?",
                "scale": "0 to 3",
            },
            "regulatory_defensibility": {
                "name": "Regulatory Defensibility",
                "question": "Could this be defended against the framework in docs/regulatory-mapping.md?",
                "scale": "0 to 3",
            },
        },
        "scores": {
            "rule_system": {
                "transparency": {
                    "score": 3,
                    "anchor": "Every decision lists the rules that fired and the facts they used, and the applicant-facing reasons are exactly the reason codes of those rules (tested on all of D1).",
                    "artifacts": [
                        "tests/integration/test_phase3_api_and_audit.py",
                        "src/explain/notice.py",
                    ],
                    "justification": "Every decision generates an exact trace containing only fired rules, with adverse notices rendered verbatim from reason code definitions in rules/reason_codes.toml.",
                },
                "auditability": {
                    "score": 3,
                    "anchor": "A stored record per decision, a version for the logic used, and a replay that reproduces the decision and trace, with a mismatch reported when a parameter changes.",
                    "artifacts": [
                        "tests/integration/test_phase3_api_and_audit.py",
                        "tests/golden/rule_set_pin.json",
                        "data/manifest.json",
                    ],
                    "justification": "Every decision is committed to an append-only SQLite audit log with input SHA-256 and ruleset hash, verifiable via byte-identical replay.",
                },
                "edge_cases": {
                    "score": 3,
                    "anchor": "No unexplained difference in any category; every missing-data and boundary case ends in a stated outcome.",
                    "artifacts": [
                        "reports/edge_cases/summary.md",
                        "reports/edge_cases/results.csv",
                    ],
                    "justification": "Evaluated on 64 edge cases across 5 categories with 61 exact catalog matches, 3 explained FOIR-capacity interactions (OQ-012), and zero unexplained differences.",
                },
                "regulatory_defensibility": {
                    "score": 3,
                    "anchor": "All six rows met with evidence.",
                    "artifacts": [
                        "docs/regulatory-mapping.md",
                    ],
                    "justification": "Fully satisfies requirements CR-01 to CR-06 with verifiable tests for specific reason notices, KFS summaries, consent enforcement, and human referral.",
                },
            },
            "logistic_regression": {
                "transparency": {
                    "score": 2,
                    "anchor": "Each decision has an exact, per-decision explanation from the model's own arithmetic (the logistic regression's feature contributions), but the explanation is a score contribution, not a policy reason the applicant can act on.",
                    "artifacts": [
                        "src/ml/baseline.py",
                        "reports/ml/metrics_d3_lr.json",
                    ],
                    "justification": "Linear feature contributions provide exact additive logit shifts per applicant, but output numerical score weights rather than actionable policy clauses.",
                },
                "auditability": {
                    "score": 2,
                    "anchor": "Versioned artifact and seed, and the numbers reproduce, but no per-decision record or replay.",
                    "artifacts": [
                        "models/d3_lr.joblib",
                        "reports/ml/metrics_d3_lr.json",
                    ],
                    "justification": "Model training reproduces deterministically from derived seed with recorded dataset and split hashes, but lacks an append-only decision audit store and replay capability.",
                },
                "edge_cases": {
                    "score": 1,
                    "anchor": "An unexplained difference in the missing-data or boundary categories.",
                    "artifacts": [
                        "reports/edge_cases/summary.md",
                        "reports/edge_cases/results.csv",
                    ],
                    "justification": "Silently imputes missing mandatory data with median training values without schema validation, and smoothly crosses policy thresholds without discrete bounds.",
                },
                "regulatory_defensibility": {
                    "score": 1,
                    "anchor": "Two or three rows partly met or gaps.",
                    "artifacts": [
                        "docs/regulatory-mapping.md",
                    ],
                    "justification": "Meets CR-05 (model card) and CR-06 (bias testing), but leaves gaps on CR-01 (actionable specific adverse reasons), CR-02 (KFS offer terms), and CR-04 (human referral).",
                },
            },
            "gradient_boosting": {
                "transparency": {
                    "score": 1,
                    "anchor": "Only a global explanation exists (permutation importance), not one per decision.",
                    "artifacts": [
                        "reports/ml/metrics_d3_gb.json",
                    ],
                    "justification": "Provides global tree feature importances only; non-linear ensemble interactions lack exact closed-form per-decision explanations without complex local approximations.",
                },
                "auditability": {
                    "score": 2,
                    "anchor": "Versioned artifact and seed, and the numbers reproduce, but no per-decision record or replay.",
                    "artifacts": [
                        "models/d3_gb.joblib",
                        "reports/ml/metrics_d3_gb.json",
                    ],
                    "justification": "Reproducible training pipeline from fixed seed and versioned split hashes, without individual decision tracing or replay store.",
                },
                "edge_cases": {
                    "score": 1,
                    "anchor": "An unexplained difference in the missing-data or boundary categories.",
                    "artifacts": [
                        "reports/edge_cases/summary.md",
                        "reports/edge_cases/results.csv",
                    ],
                    "justification": "Imputes missing values without error flagging and produces continuous prediction manifolds across hard policy thresholds.",
                },
                "regulatory_defensibility": {
                    "score": 1,
                    "anchor": "Two or three rows partly met or gaps.",
                    "artifacts": [
                        "docs/regulatory-mapping.md",
                    ],
                    "justification": "Meets CR-05 and CR-06, but cannot provide per-decision adverse reasons (CR-01), loan terms (CR-02), or human review routing (CR-04).",
                },
            },
        },
        "accuracy_context": {
            "d2_test": {
                "population_note": "Test split (N = 46,127). The rule system approves 1.68% (776 applicants) due to severe mapping constraints (K04, K05, unknown delinquency).",
                "metrics": {
                    "rule_system_treatment_A": {
                        "auc": "N/A (discrete rules)",
                        "approval_rate": "1.68% (776 / 46,127)",
                        "default_rate_among_approved": "3.35% [95% CI: 2.14% - 4.70%]",
                        "cost_per_applicant_primary_5": "0.9058",
                    },
                    "rule_system_treatment_B": {
                        "auc": "N/A (discrete rules)",
                        "approval_rate": "1.84% (776 / 42,072)",
                        "default_rate_among_approved": "3.35% [95% CI: 2.12% - 4.67%]",
                        "cost_per_applicant_primary_5": "0.8993",
                    },
                    "logistic_regression_matched": {
                        "auc": "0.7248",
                        "approval_rate": "1.56% (720 / 46,127)",
                        "default_rate_among_approved": "1.39% [95% CI: 0.56% - 2.42%]",
                        "cost_per_applicant_primary_5": "0.9050",
                    },
                    "gradient_boosting_matched": {
                        "auc": "0.7378",
                        "approval_rate": "1.71% (787 / 46,127)",
                        "default_rate_among_approved": "1.27% [95% CI: 0.58% - 2.12%]",
                        "cost_per_applicant_primary_5": "0.9035",
                    },
                },
            },
            "d3_test": {
                "population_note": "Synthetic test split (N = 3,000). Agreement with policy is partly circular because D3 labels derive from simulated credit policy rules.",
                "metrics": {
                    "logistic_regression": {
                        "auc": "0.8852",
                        "policy_agreement": "80.97% (threshold 0.5)",
                    },
                    "gradient_boosting": {
                        "auc": "0.9902",
                        "policy_agreement": "98.53% (threshold 0.5)",
                    },
                },
            },
        },
    }
    return scorecard


def write_scorecard_files(
    out_json: Path | str = REPORTS_DIR / "scorecard.json",
    out_md: Path | str = REPORTS_DIR / "scorecard.md",
) -> None:
    """Generate both scorecard.json and scorecard.md."""
    json_path = Path(out_json)
    md_path = Path(out_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    data = build_scorecard_data()

    # 1. Write scorecard.json
    json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote comparison scorecard JSON to {json_path}")

    # 2. Write scorecard.md
    lines = [
        "# Comparison Scorecard: Rule System vs ML Baselines (WP-18, FR-22, CR-05)",
        "",
        "> [!NOTE]",
        "> **Illustrative Policy Values (D-02)**: The policy values and thresholds are illustrative coursework artifacts.",
        "> This comparison demonstrates architectural and design trade-offs (explainability, auditability, defensibility),",
        "> not a contest of commercial underwriting efficacy. D2 results rest on 776 rule approvals driven by mapping constraints.",
        "",
        "## 1. Multi-Criterion Comparison Scorecard",
        "",
        "Scoring scale: **0 to 3** per criterion (anchors defined in `docs/comparison-methodology.md`).",
        "",
        "| System | Transparency | Auditability | Edge Cases | Regulatory Defensibility |",
        "|---|---|---|---|---|",
    ]

    scores = data["scores"]
    for sys_key, sys_name in [
        ("rule_system", "Rule-Based Expert System"),
        ("logistic_regression", "Logistic Regression (Transparent Baseline)"),
        ("gradient_boosting", "Gradient Boosting (Non-linear Baseline)"),
    ]:
        s = scores[sys_key]
        t_cell = f"**{s['transparency']['score']}**<br>Anchor: {s['transparency']['anchor'][:50]}...<br>Artifact: `{s['transparency']['artifacts'][0]}`"
        a_cell = f"**{s['auditability']['score']}**<br>Anchor: {s['auditability']['anchor'][:50]}...<br>Artifact: `{s['auditability']['artifacts'][0]}`"
        e_cell = f"**{s['edge_cases']['score']}**<br>Anchor: {s['edge_cases']['anchor'][:50]}...<br>Artifact: `{s['edge_cases']['artifacts'][0]}`"
        r_cell = f"**{s['regulatory_defensibility']['score']}**<br>Anchor: {s['regulatory_defensibility']['anchor'][:50]}...<br>Artifact: `{s['regulatory_defensibility']['artifacts'][0]}`"
        lines.append(f"| **{sys_name}** | {t_cell} | {a_cell} | {e_cell} | {r_cell} |")

    lines.extend([
        "",
        "## 2. Detailed Scores, Anchors, and Evidence",
        "",
    ])

    for sys_key, sys_name in [
        ("rule_system", "Rule-Based Expert System"),
        ("logistic_regression", "Logistic Regression"),
        ("gradient_boosting", "Gradient Boosting"),
    ]:
        lines.extend([
            f"### {sys_name}",
            "",
            "| Criterion | Score | Met Anchor | Artifacts | Rationale |",
            "|---|---|---|---|---|",
        ])
        s = scores[sys_key]
        for crit_key, crit_name in [
            ("transparency", "Transparency"),
            ("auditability", "Auditability"),
            ("edge_cases", "Edge Cases"),
            ("regulatory_defensibility", "Regulatory Defensibility"),
        ]:
            c = s[crit_key]
            art_str = "<br>".join(f"`{a}`" for a in c["artifacts"])
            lines.append(
                f"| **{crit_name}** | **{c['score']}** | {c['anchor']} | {art_str} | {c['justification']} |"
            )
        lines.append("")

    # Accuracy context table
    lines.extend([
        "## 3. Accuracy Context Table (Not a Score)",
        "",
        "The following context metrics are drawn from Phase 4 artifacts (`reports/ml/`). They do not constitute an evaluation score,",
        "as D2 evaluation rests on only 776 rule approvals (1.68% approval rate) and D3 policy agreement is partly circular by construction.",
        "",
        "### D2 Dataset (Home Credit Mapped, Test Split N = 46,127)",
        "",
        "| System / Operating Point | Test AUC | Approval Rate | Default Rate among Approved (95% CI) | Cost / Applicant (Ratio 5) |",
        "|---|---|---|---|---|",
        "| **Rule System (Treatment A)** | N/A (rules) | 1.68% (776) | 3.35% [2.14% - 4.70%] | 0.9058 |",
        "| **Rule System (Treatment B)** | N/A (rules) | 1.84% (776) | 3.35% [2.12% - 4.67%] | 0.8993 |",
        "| **Logistic Regression (Matched)** | 0.7248 | 1.56% (720) | 1.39% [0.56% - 2.42%] | 0.9050 |",
        "| **Gradient Boosting (Matched)** | 0.7378 | 1.71% (787) | 1.27% [0.58% - 2.12%] | 0.9035 |",
        "",
        "### D3 Dataset (Synthetic Population, Test Split N = 3,000)",
        "",
        "| Model | Test AUC | Policy Agreement Rate (Threshold 0.5) | Note |",
        "|---|---|---|---|",
        "| **Logistic Regression** | 0.8852 | 80.97% | Linear approximation of non-linear rule boundaries |",
        "| **Gradient Boosting** | 0.9902 | 98.53% | Captures non-linear thresholds with high fidelity |",
        "",
        "## 4. Key Architectural Trade-Offs and Edge-Case Disagreements",
        "",
        "- **Auditability & Traceability**: The rule system guarantees bit-level replayability via SHA-256 rule set pinning and append-only SQLite tracing. ML baselines lack decision-level replayability and explanation integrity.",
        "- **Silent Imputation Vulnerability**: On missing mandatory fields (`EC-MD-01` to `EC-MD-06`), ML baselines silently impute values with sample medians, producing plausible scores without error notifications, violating CR-01 and CR-03.",
        "- **Non-compensatory Enforcement**: Rule knockouts (`EC-RC-01`) enforce legal boundaries strictly regardless of applicant wealth; linear models allow extreme income to compensate for disqualifying credit history.",
        "",
    ])

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote comparison scorecard Markdown to {md_path}")


def main() -> None:
    write_scorecard_files()


if __name__ == "__main__":
    main()
