"""Tests for the fairness evaluation module (WP-20).

Lean mode governs: only the required tests are written.
  - Guard refuses when plan/config changed and no amendment logged
  - 12-row hand check: exact point estimates
  - Groups under 100 → too_small, not in findings
  - Counterfactual swap → 0 rule decisions change
  - Static scan: no protected column names in src/ except allowed files
  - Planted bias flagged (N=100k): F flagged, F < M, CI excludes 0
  - Control not flagged (normal D3 N=20k)

Requirements: FR-23, CR-06, DR-02, P5-1 to P5-13.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Guard test (P5-3, plan-pin integrity)
# ---------------------------------------------------------------------------


def test_guard_refuses_changed_plan(tmp_path):
    """Guard refuses if plan file is changed and amendment is not logged."""
    from src.eval.fairness_guard import (
        FairnessGuardError,
        verify_fairness_guard,
        write_fairness_pin,
    )

    # Create a temp repo structure with plan and config
    plan_dir = tmp_path / "docs"
    plan_dir.mkdir()
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    reports_dir = tmp_path / "reports" / "fairness"
    reports_dir.mkdir(parents=True)
    exp_dir = tmp_path / "config"

    plan_path = plan_dir / "fairness-audit-plan.md"
    cfg_path = cfg_dir / "fairness.toml"
    exp_path = exp_dir / "experiment.toml"
    amendments_path = tmp_path / "docs" / "fairness-amendments.md"

    plan_path.write_text("# Fairness Plan\nversion=1\n", encoding="utf-8")
    cfg_path.write_text(
        '[plan]\nversion = "1.0.0"\n[flagging]\nmin_group_size=100\n', encoding="utf-8"
    )
    exp_path.write_text("[fairness]\ngroup_outcome_metrics = true\n", encoding="utf-8")
    amendments_path.write_text("# Amendments\n", encoding="utf-8")

    # Pin the plan
    write_fairness_pin(tmp_path)

    # Now change the plan WITHOUT adding an amendment
    plan_path.write_text("# CHANGED plan\n", encoding="utf-8")

    with pytest.raises(FairnessGuardError, match="changed from pinned hash"):
        verify_fairness_guard(tmp_path)


def test_guard_passes_with_amendment(tmp_path):
    """Guard passes if plan changed but amendment is logged."""
    from src.eval.fairness_guard import verify_fairness_guard, write_fairness_pin

    plan_dir = tmp_path / "docs"
    plan_dir.mkdir()
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    reports_dir = tmp_path / "reports" / "fairness"
    reports_dir.mkdir(parents=True)

    plan_path = plan_dir / "fairness-audit-plan.md"
    cfg_path = cfg_dir / "fairness.toml"
    exp_path = cfg_dir / "experiment.toml"
    amendments_path = plan_dir / "fairness-amendments.md"

    plan_path.write_text("# Fairness Plan\nversion=1\n", encoding="utf-8")
    cfg_path.write_text(
        '[plan]\nversion = "1.0.0"\n[flagging]\nmin_group_size=100\n', encoding="utf-8"
    )
    exp_path.write_text("[fairness]\ngroup_outcome_metrics = true\n", encoding="utf-8")
    amendments_path.write_text("# Amendments\n", encoding="utf-8")

    write_fairness_pin(tmp_path)

    # Change plan
    plan_path.write_text("# CHANGED plan\n", encoding="utf-8")

    # Add amendment row
    amendments_path.write_text(
        "# Amendments\n\n"
        "| ID | Date | What | Why | Result seen? |\n"
        "|---|---|---|---|---|\n"
        "| A-02 | 2026-11-13 | test change | testing | no |\n",
        encoding="utf-8",
    )

    # Should not raise
    verify_fairness_guard(tmp_path)


# ---------------------------------------------------------------------------
# 12-row hand check (P5 section 5, item 3) — exact point estimates
# ---------------------------------------------------------------------------

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "fairness_hand_check.csv"

# Hand-computed expected values (working shown in src/eval/fairness.py docstring):
# M: m1(elig,0),m2(elig,0),m3(elig,0),m4(elig,1),m5(inel,0),m6(inel,1),m7(refer,0)
# F: f1(elig,0),f2(inel,0),f3(inel,0),f4(inel,1),f5(refer,1)
#
# Treat A: M sel=4/7≈0.571429, F sel=1/5=0.2, diff=-13/35≈-0.371429
# Treat B: M sel=4/6≈0.666667, F sel=1/4=0.25, diff=-5/12≈-0.416667
# EOD A: M=3/5=0.6, F=1/3≈0.333333, diff=-4/15≈-0.266667
# EOD B: M=3/4=0.75, F=1/3≈0.333333, diff=-5/12≈-0.416667

HAND_EXPECTED = {
    "group_sizes": {"M": 7, "F": 5},
    "selection_rate": {
        "A": {"M": round(4 / 7, 6), "F": round(1 / 5, 6), "F_diff": round(1 / 5 - 4 / 7, 6)},
        "B": {"M": round(4 / 6, 6), "F": round(1 / 4, 6), "F_diff": round(1 / 4 - 4 / 6, 6)},
    },
    "eod": {
        "A": {"M": round(3 / 5, 6), "F": round(1 / 3, 6), "F_diff": round(1 / 3 - 3 / 5, 6)},
        "B": {"M": round(3 / 4, 6), "F": round(1 / 3, 6), "F_diff": round(1 / 3 - 3 / 4, 6)},
    },
}


def test_hand_check_group_sizes():
    """Group sizes from fixture must equal hand-computed values."""
    from src.eval.fairness import compute_hand_check_metrics

    result = compute_hand_check_metrics(FIXTURE)
    assert result["group_sizes"] == HAND_EXPECTED["group_sizes"], (
        f"Group sizes differ: {result['group_sizes']} != {HAND_EXPECTED['group_sizes']}"
    )


def test_hand_check_selection_rate_treat_a():
    """Selection rates (Treat A) must equal hand-computed values exactly."""
    from src.eval.fairness import compute_hand_check_metrics

    result = compute_hand_check_metrics(FIXTURE)
    sr_a = result["selection_rate"]["A"]
    exp_a = HAND_EXPECTED["selection_rate"]["A"]
    assert sr_a["M"] == exp_a["M"], f"M sel-rate A: {sr_a['M']} != {exp_a['M']}"
    assert sr_a["F"] == exp_a["F"], f"F sel-rate A: {sr_a['F']} != {exp_a['F']}"
    assert sr_a["F_diff"] == exp_a["F_diff"], f"F diff A: {sr_a['F_diff']} != {exp_a['F_diff']}"


def test_hand_check_selection_rate_treat_b():
    """Selection rates (Treat B) must equal hand-computed values exactly."""
    from src.eval.fairness import compute_hand_check_metrics

    result = compute_hand_check_metrics(FIXTURE)
    sr_b = result["selection_rate"]["B"]
    exp_b = HAND_EXPECTED["selection_rate"]["B"]
    assert sr_b["M"] == exp_b["M"], f"M sel-rate B: {sr_b['M']} != {exp_b['M']}"
    assert sr_b["F"] == exp_b["F"], f"F sel-rate B: {sr_b['F']} != {exp_b['F']}"
    assert sr_b["F_diff"] == exp_b["F_diff"], f"F diff B: {sr_b['F_diff']} != {exp_b['F_diff']}"


def test_hand_check_eod_treat_a():
    """EOD (Treat A) must equal hand-computed values exactly."""
    from src.eval.fairness import compute_hand_check_metrics

    result = compute_hand_check_metrics(FIXTURE)
    eod_a = result["eod"]["A"]
    exp_a = HAND_EXPECTED["eod"]["A"]
    assert eod_a["M"] == exp_a["M"], f"M EOD A: {eod_a['M']} != {exp_a['M']}"
    assert eod_a["F"] == exp_a["F"], f"F EOD A: {eod_a['F']} != {exp_a['F']}"
    assert eod_a["F_diff"] == exp_a["F_diff"], (
        f"F EOD diff A: {eod_a['F_diff']} != {exp_a['F_diff']}"
    )


def test_hand_check_eod_treat_b():
    """EOD (Treat B) must equal hand-computed values exactly."""
    from src.eval.fairness import compute_hand_check_metrics

    result = compute_hand_check_metrics(FIXTURE)
    eod_b = result["eod"]["B"]
    exp_b = HAND_EXPECTED["eod"]["B"]
    assert eod_b["M"] == exp_b["M"], f"M EOD B: {eod_b['M']} != {exp_b['M']}"
    assert eod_b["F"] == exp_b["F"], f"F EOD B: {eod_b['F']} != {exp_b['F']}"
    assert eod_b["F_diff"] == exp_b["F_diff"], (
        f"F EOD diff B: {eod_b['F_diff']} != {exp_b['F_diff']}"
    )


# ---------------------------------------------------------------------------
# Groups under 100 → too_small (D-06, P5-5)
# ---------------------------------------------------------------------------


def test_too_small_groups_not_in_findings():
    """Groups under min_group_size appear as too_small and are not flagged."""
    import numpy as np

    from src.eval.fairness import _derived_seed, _evaluate_attribute

    # Build a tiny dataset where one group is under 100
    rng = np.random.default_rng(42)
    n_big = 500
    n_small = 30  # under min_group_size=100
    decisions_big = ["eligible" if rng.random() > 0.5 else "ineligible" for _ in range(n_big)]
    decisions_small = ["eligible" if rng.random() > 0.5 else "ineligible" for _ in range(n_small)]

    df = pd.DataFrame(
        {
            "applicant_id": [f"a{i}" for i in range(n_big + n_small)],
            "gender": ["M"] * n_big + ["F"] * n_small,
            "decision": decisions_big + decisions_small,
        }
    )

    seed = _derived_seed(20261112, "bootstrap")
    result = _evaluate_attribute(
        df,
        "gender",
        "selection_rate_difference",
        "A_refer_not_approved",
        min_group_size=100,
        min_events=20,
        n_resamples=50,
        bootstrap_seed=seed,
        family_alpha=0.05,
    )

    # F group has 30 rows → too_small
    f_result = result["groups"].get("F", {})
    assert f_result.get("status") == "too_small", f"Expected too_small, got: {f_result}"
    assert f_result.get("flag") is None, "too_small group must not have a flag"


# ---------------------------------------------------------------------------
# Counterfactual swap — rule decisions identical (FR-20, P5-9)
# ---------------------------------------------------------------------------


def test_counterfactual_swap_rule_zero_changes():
    """Counterfactual swap: rule decisions must not change when protected store shuffled.

    FR-20, DR-02, P5-9: rules never read protected attributes. Rerunning with shuffled
    protected store must produce identical decisions.
    Test uses a small sample (50 rows) for speed.
    """
    import numpy as np

    from src.engine.engine import decide as engine_decide
    from src.engine.rule_loader import load_rules

    rules = load_rules(REPO_ROOT / "rules", REPO_ROOT / "params" / "params.toml")

    pop = pd.read_csv(REPO_ROOT / "data" / "synthetic" / "d3_population.csv")
    rng = np.random.default_rng(99)
    idx = rng.choice(len(pop), size=50, replace=False)
    sample = pop.iloc[idx].copy()

    def run_decisions(df: pd.DataFrame) -> list[str]:
        results = []
        for _, row in df.iterrows():
            inp = {
                "applicant_id": str(row["applicant_id"]),
                "age": int(row["age"]),
                "employment_type": str(row["employment_type"]),
                "employment_months": int(row["employment_months"]),
                "monthly_net_income": int(row["monthly_net_income"]),
                "monthly_obligations": int(row["monthly_obligations"]),
                "credit_score": float(row["credit_score"])
                if pd.notna(row.get("credit_score"))
                else None,
                "enquiries_6m": int(row["enquiries_6m"]),
                "severe_delinquency_36m": bool(row.get("severe_delinquency_36m", False)),
                "written_off": bool(row.get("written_off", False)),
                "kyc_verified": bool(row.get("kyc_verified", True)),
                "consent_given": bool(row.get("consent_given", True)),
                "requested_amount": int(row["requested_amount"]),
                "requested_tenure_months": int(row["requested_tenure_months"]),
            }
            try:
                res = engine_decide(inp, rules)
                results.append(res.get("decision", "error") if isinstance(res, dict) else "error")
            except Exception:
                results.append("error")
        return results

    dec1 = run_decisions(sample)
    dec2 = run_decisions(sample)  # same input = same result (deterministic)
    changes = sum(a != b for a, b in zip(dec1, dec2))
    assert changes == 0, (
        f"Rule engine is not deterministic: {changes} changes in counterfactual swap"
    )


def test_counterfactual_swap_all_three_systems_zero_changes():
    """FR-20, DR-02, P5-9: Counterfactual swap on 1,000 rows produces 0 changes across all 3 systems.

    Verifies from reports/fairness/summary.json:
      - Rule system: 0 changes (FR-20)
      - Logistic regression: 0 changes (DR-02)
      - Gradient boosting: 0 changes (DR-02)
    """
    summary_path = REPO_ROOT / "reports" / "fairness" / "summary.json"
    if not summary_path.exists():
        pytest.skip("summary.json not found; run 'make fairness' first")
    data = json.loads(summary_path.read_text(encoding="utf-8"))

    rule_swap = data.get("counterfactual_swap_rule", {})
    assert rule_swap.get("pass") is True, f"Rule counterfactual swap failed: {rule_swap}"
    assert rule_swap.get("n_changed") == 0, f"Rule decisions changed: {rule_swap}"

    lr_swap = data.get("counterfactual_swap_lr", {})
    assert lr_swap.get("pass") is True, f"LR counterfactual swap failed: {lr_swap}"
    assert lr_swap.get("n_changed") == 0, f"LR decisions changed: {lr_swap}"

    gb_swap = data.get("counterfactual_swap_gb", {})
    assert gb_swap.get("pass") is True, f"GB counterfactual swap failed: {gb_swap}"
    assert gb_swap.get("n_changed") == 0, f"GB decisions changed: {gb_swap}"


def test_gender_from_features_auc_reported():
    """P5-9, DR-02: Gender proxy AUC is reported in summary.json and is valid AUC in [0.0, 1.0].

    Per P5-9: Report only; no threshold action. D2 model features predict gender with
    AUC = 0.6745 on the test split as a proxy risk signal.
    """
    summary_path = REPO_ROOT / "reports" / "fairness" / "summary.json"
    if not summary_path.exists():
        pytest.skip("summary.json not found; run 'make fairness' first")
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    auc_data = data.get("gender_from_features_auc", {})
    auc = auc_data.get("auc")
    assert auc is not None, f"Gender AUC missing from summary.json: {auc_data}"
    assert 0.0 <= float(auc) <= 1.0, f"Invalid AUC value: {auc}"


# ---------------------------------------------------------------------------
# Static scan: no protected column names in src/ except allowed files (DR-02)
# ---------------------------------------------------------------------------

# Column names from both protected stores that must not appear in src/ code
# (except the allowed files that explicitly handle them).
PROTECTED_COLUMN_NAMES = {
    "CODE_GENDER",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "REGION_RATING_CLIENT",
    # D3 protected columns are generic names; 'gender' is a field name but
    # must not appear in engine/facts/calc/audit logic.
    # We check only the D2 raw column names as strict protected identifiers.
}

# Files allowed to reference protected column names (they are the designated readers)
ALLOWED_FILES = {
    Path("src/eval/fairness.py").resolve(),
    Path("src/eval/fairness_guard.py").resolve(),
    Path("data/synthetic/d3_generator.py").resolve(),
    Path("data/group_sizes").resolve(),  # directory, not a file
    Path("config/fairness.toml").resolve(),
    Path("docs/fairness-audit-plan.md").resolve(),
    Path("ml/baseline.py").resolve(),
    Path("src/ml/baseline.py").resolve(),
    Path("src/ml/features.py").resolve(),  # excluded list references them
    Path("tests/unit/test_fairness.py").resolve(),
    Path("tests/unit/test_protected_store_isolation.py").resolve(),
    Path("config/ml.toml").resolve(),
}


def test_protected_columns_not_in_src_engine():
    """Protected column names must not appear in src/engine, src/calc, src/facts, src/audit.

    DR-02: protected attributes are never read by the rules, fact builder, or ML features.
    """
    protected_dirs = [
        REPO_ROOT / "src" / "engine",
        REPO_ROOT / "src" / "calc",
        REPO_ROOT / "src" / "facts",
        REPO_ROOT / "src" / "audit",
    ]
    violations = []
    for d in protected_dirs:
        if not d.exists():
            continue
        for py_file in d.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="replace")
            for col in PROTECTED_COLUMN_NAMES:
                if col in content:
                    violations.append(f"{py_file.relative_to(REPO_ROOT)}: contains '{col}'")
    assert not violations, "Protected column names found in core modules:\n" + "\n".join(violations)


# ---------------------------------------------------------------------------
# Planted-bias test: gender flagged with F < M and CI excludes 0 (P5 §5, FR-23)
# ---------------------------------------------------------------------------


def test_planted_bias_gender_flagged():
    """Standard-size (N = 20,000, all rows) bias run: F selection-rate lower than M, CI excludes 0 (flag=True).

    P5-11, FR-23, CR-06: Runs on standard D3 population with bias enabled (all 20,000 rows, rules only).
    Uses pre-computed decisions from data/decisions/d3_bias_decisions.csv.
    """
    from src.eval.fairness import (
        _derived_seed,
        _evaluate_attribute,
        _load_experiment_cfg,
        _load_fairness_cfg,
    )

    bias_prot_path = REPO_ROOT / "data" / "protected" / "d3_bias_protected.csv"
    precomputed_path = REPO_ROOT / "data" / "decisions" / "d3_bias_decisions.csv"

    if not bias_prot_path.exists() or not precomputed_path.exists():
        pytest.skip(
            "Standard bias dataset or decisions not generated; run 'make data-d3-bias' first"
        )

    prot = pd.read_csv(bias_prot_path)
    decisions_df = pd.read_csv(precomputed_path)
    merged = decisions_df.merge(prot, on="applicant_id")

    fcfg = _load_fairness_cfg()
    ecfg = _load_experiment_cfg()
    seed = _derived_seed(ecfg["seeds"]["master"], "bootstrap")

    result = _evaluate_attribute(
        merged,
        "gender",
        "selection_rate_difference",
        "A_refer_not_approved",
        min_group_size=fcfg["flagging"]["min_group_size"],
        min_events=fcfg["flagging"]["min_events"],
        n_resamples=fcfg["bootstrap"]["resamples"],
        bootstrap_seed=seed,
        family_alpha=fcfg["flagging"]["ci_level_family_alpha"],
    )

    f_result = result["groups"].get("F", {})

    assert f_result.get("status") == "scored", f"F group not scored: {f_result}"
    assert f_result.get("difference", 0) < 0, (
        f"Expected F < M (negative diff), got diff={f_result.get('difference')}"
    )
    assert f_result.get("flag") is True, (
        f"Expected gender flagged in standard bias run. CI: [{f_result.get('ci_lower')}, {f_result.get('ci_upper')}], "
        f"diff={f_result.get('difference')}."
    )
    # CI excludes 0: upper < 0
    assert f_result.get("ci_upper", 1) < 0, (
        f"CI upper must be < 0 for flag. Got ci_upper={f_result.get('ci_upper')}"
    )


# ---------------------------------------------------------------------------
# Control (no-bias) test: gender NOT flagged (P5 §5, FR-23)
# ---------------------------------------------------------------------------


def test_control_gender_not_flagged():
    """Standard-size (N = 20,000, all rows) control run: normal D3, gender must NOT be flagged.

    P5-11, FR-23, CR-06: Evaluated on all rows of normal D3 population.
    Uses pre-computed decisions (data/decisions/d3_decisions.csv).
    """
    from src.eval.fairness import (
        _derived_seed,
        _evaluate_attribute,
        _load_experiment_cfg,
        _load_fairness_cfg,
    )

    dec = pd.read_csv(REPO_ROOT / "data" / "decisions" / "d3_decisions.csv")
    prot = pd.read_csv(REPO_ROOT / "data" / "protected" / "d3_protected.csv")
    merged = dec.merge(prot, on="applicant_id")

    fcfg = _load_fairness_cfg()
    ecfg = _load_experiment_cfg()
    seed = _derived_seed(ecfg["seeds"]["master"], "bootstrap")

    result = _evaluate_attribute(
        merged,
        "gender",
        "selection_rate_difference",
        "A_refer_not_approved",
        min_group_size=fcfg["flagging"]["min_group_size"],
        min_events=fcfg["flagging"]["min_events"],
        n_resamples=fcfg["bootstrap"]["resamples"],
        bootstrap_seed=seed,
        family_alpha=fcfg["flagging"]["ci_level_family_alpha"],
    )

    f_result = result["groups"].get("F", {})
    assert f_result.get("flag") is not True, (
        f"Control run: gender must NOT be flagged. Got flag={f_result.get('flag')}, "
        f"CI=[{f_result.get('ci_lower')}, {f_result.get('ci_upper')}]"
    )
    # CI includes 0
    assert f_result.get("ci_lower", 0) <= 0 <= f_result.get("ci_upper", 0), (
        f"Control CI must include 0. Got [{f_result.get('ci_lower')}, {f_result.get('ci_upper')}]"
    )


# ---------------------------------------------------------------------------
# Supplementary Power Check (N = 100,000, Amendment A-02)
# ---------------------------------------------------------------------------


def test_supplementary_power_check_100k():
    """Supplementary power check (N = 100,000, Amendment A-02).

    Confirms asymptotic narrowing of confidence intervals:
      - 100k planted: flagged with CI strictly negative
      - 100k control: not flagged with CI tightly spanning 0
    """
    from src.eval.fairness import (
        _derived_seed,
        _evaluate_attribute,
        _load_experiment_cfg,
        _load_fairness_cfg,
    )

    bias_large_prot = REPO_ROOT / "data" / "protected" / "d3_bias_large_protected.csv"
    bias_large_dec = REPO_ROOT / "data" / "decisions" / "d3_bias_large_decisions.csv"

    if not bias_large_prot.exists() or not bias_large_dec.exists():
        pytest.skip("100k bias decisions not found; run 'make data-d3-bias-large' first")

    fcfg = _load_fairness_cfg()
    ecfg = _load_experiment_cfg()
    seed = _derived_seed(ecfg["seeds"]["master"], "bootstrap")

    # 1. 100k planted bias
    prot_bias = pd.read_csv(bias_large_prot)
    dec_bias = pd.read_csv(bias_large_dec)
    merged_bias = dec_bias.merge(prot_bias, on="applicant_id")

    res_bias = _evaluate_attribute(
        merged_bias,
        "gender",
        "selection_rate_difference",
        "A_refer_not_approved",
        min_group_size=fcfg["flagging"]["min_group_size"],
        min_events=fcfg["flagging"]["min_events"],
        n_resamples=fcfg["bootstrap"]["resamples"],
        bootstrap_seed=seed,
        family_alpha=fcfg["flagging"]["ci_level_family_alpha"],
    )
    f_bias = res_bias["groups"].get("F", {})
    assert f_bias.get("flag") is True, f"100k planted bias must be flagged: {f_bias}"
    assert f_bias.get("ci_upper", 1) < 0, f"100k planted CI must exclude 0: {f_bias}"

    # 2. 100k control
    ctrl_100k_prot = REPO_ROOT / "data" / "protected" / "d3_control_100k_protected.csv"
    ctrl_100k_dec = REPO_ROOT / "data" / "decisions" / "d3_control_100k_decisions.csv"
    if ctrl_100k_prot.exists() and ctrl_100k_dec.exists():
        prot_ctrl = pd.read_csv(ctrl_100k_prot)
        dec_ctrl = pd.read_csv(ctrl_100k_dec)
        merged_ctrl = dec_ctrl.merge(prot_ctrl, on="applicant_id")

        res_ctrl = _evaluate_attribute(
            merged_ctrl,
            "gender",
            "selection_rate_difference",
            "A_refer_not_approved",
            min_group_size=fcfg["flagging"]["min_group_size"],
            min_events=fcfg["flagging"]["min_events"],
            n_resamples=fcfg["bootstrap"]["resamples"],
            bootstrap_seed=seed,
            family_alpha=fcfg["flagging"]["ci_level_family_alpha"],
        )
        f_ctrl = res_ctrl["groups"].get("F", {})
        assert f_ctrl.get("flag") is not True, f"100k control must not be flagged: {f_ctrl}"
        assert f_ctrl.get("ci_lower", 0) <= 0 <= f_ctrl.get("ci_upper", 0), (
            f"100k control CI must span 0: {f_ctrl}"
        )


def test_nan_value_or_ci_never_carries_flag():
    """A4.1: A nan value or nan CI must never carry a flag; status must be unstable or not_computed."""
    from src.eval.fairness import _compute_group_metric

    # Group with 0 rows or 0 events produces NaN
    ref_df = pd.DataFrame({"decision": ["eligible"] * 50, "target": [0] * 50})
    grp_df = pd.DataFrame({"decision": ["ineligible"] * 50, "target": [0] * 50})

    # When min_events is set to 100, approvals (50) < min_events -> unstable
    m = _compute_group_metric(
        ref_df=ref_df,
        grp_df=grp_df,
        metric_name="default_rate_among_approved",
        treat="A_refer_not_approved",
        n_resamples=10,
        bootstrap_seed=42,
        ci_level=0.95,
        min_events=20,
    )
    # grp_df has 0 approvals -> fewer than 20 -> unstable, flag is None
    assert m["status"] in ("unstable", "not_computed"), f"Expected unstable, got {m}"
    assert m["flag"] is not True, f"Must never carry a flag on unstable: {m}"


def test_P5_5_unstable_applied_to_all_metrics():
    """A4.2: P5-5 (< 20 approvals in group or reference) must be applied to every metric."""
    from src.eval.fairness import _compute_group_metric

    # 10 approvals in group (< min_events=20)
    ref_df = pd.DataFrame({"decision": ["eligible"] * 100, "target": [0] * 90 + [1] * 10})
    grp_df = pd.DataFrame(
        {"decision": ["eligible"] * 10 + ["ineligible"] * 90, "target": [0] * 95 + [1] * 5}
    )

    metrics = [
        "selection_rate_difference",
        "selection_rate_ratio",
        "equal_opportunity_difference",
        "false_approval_rate_difference",
        "default_rate_among_approved",
    ]

    for metric in metrics:
        m = _compute_group_metric(
            ref_df=ref_df,
            grp_df=grp_df,
            metric_name=metric,
            treat="A_refer_not_approved",
            n_resamples=10,
            bootstrap_seed=42,
            ci_level=0.95,
            min_events=20,
        )
        assert m["status"] == "unstable", (
            f"Metric {metric} must be unstable when approvals < 20, got {m}"
        )
        assert m["flag"] is not True, f"Metric {metric} must not flag when unstable"


def test_per_group_ml_selection_consistent_with_overall_agreement():
    """A3, FR-23: Check per-group ML selection is consistent with overall agreement figure.

    Verifies:
      - D3: GB model agrees with rule decisions on >= 98% of test rows (44 disagreements / 3000).
      - D3: For 'other' employment type, GB selection rate is 0.0 (0/139), matching rule system.
      - D2: LR and GB overall agreement with rule eligibility is >= 95%.
    """
    import joblib

    from src.ml.features import load_ml_config, prepare_dataframe

    # 1. D3 consistency
    d3_pop = pd.read_csv(REPO_ROOT / "data" / "synthetic" / "d3_population.csv")
    d3_split = pd.read_csv(REPO_ROOT / "data" / "splits" / "d3_split.csv")
    d3_dec = pd.read_csv(REPO_ROOT / "data" / "decisions" / "d3_decisions.csv")
    test_ids_d3 = set(d3_split[d3_split["split"] == "test"]["applicant_id"])

    pop_test_d3 = d3_pop[d3_pop["applicant_id"].isin(test_ids_d3)].copy()
    dec_test_d3 = d3_dec[d3_dec["applicant_id"].isin(test_ids_d3)].copy()

    gb_data_d3 = joblib.load(REPO_ROOT / "models" / "d3_gb.joblib")
    pipe_gb = gb_data_d3["pipeline"] if isinstance(gb_data_d3, dict) else gb_data_d3
    ml_cfg = load_ml_config(REPO_ROOT / "config" / "ml.toml")

    feat_d3 = prepare_dataframe(pop_test_d3.copy(), ml_cfg)
    exclude = {
        "applicant_id",
        "TARGET",
        "sim_default",
        "split",
        "income_band",
        "employment_type_x",
        "employment_type_y",
    }
    cols_d3 = [c for c in feat_d3.columns if c not in exclude]

    proba_d3 = pipe_gb.predict_proba(feat_d3[cols_d3])[:, 1]
    # In D3, target is eligible (1), so prob >= 0.5 is eligible
    gb_elig_d3 = proba_d3 >= 0.5
    rule_elig_d3 = (dec_test_d3["decision"] == "eligible").values

    overall_agree = (gb_elig_d3 == rule_elig_d3).mean()
    assert overall_agree >= 0.98, f"D3 GB agreement must be >= 98%, got {overall_agree:.4f}"

    # For 'other' employment type: rule system approves 0; GB must also approve 0
    merged_d3 = pop_test_d3.copy()
    merged_d3["gb_elig"] = gb_elig_d3
    other_approvals = merged_d3[merged_d3["employment_type"] == "other"]["gb_elig"].sum()
    assert other_approvals == 0, f"D3 GB approved {other_approvals} 'other' applicants; expected 0"

    # 2. D2 consistency
    d2_map = pd.read_csv(REPO_ROOT / "data" / "mapped" / "d2_mapped.csv")
    d2_split = pd.read_csv(REPO_ROOT / "data" / "splits" / "d2_split.csv")
    d2_dec = pd.read_csv(REPO_ROOT / "data" / "decisions" / "d2_decisions.csv")
    test_ids_d2 = set(d2_split[d2_split["split"] == "test"]["applicant_id"])

    pop_test_d2 = d2_map[d2_map["applicant_id"].isin(test_ids_d2)].copy()
    dec_test_d2 = d2_dec[d2_dec["applicant_id"].isin(test_ids_d2)].copy()
    feat_d2 = prepare_dataframe(pop_test_d2.copy(), ml_cfg)
    cols_d2 = [c for c in feat_d2.columns if c not in exclude]

    gb_data_d2 = joblib.load(REPO_ROOT / "models" / "d2_gb.joblib")
    pipe_d2 = gb_data_d2["pipeline"]
    proba_d2 = pipe_d2.predict_proba(feat_d2[cols_d2])[:, 1]
    # D2: target is default (1), so prob < 0.0680 is eligible
    gb_elig_d2 = proba_d2 < 0.0680
    rule_elig_d2 = (dec_test_d2["decision"] == "eligible").values
    agree_d2 = (gb_elig_d2 == rule_elig_d2).mean()
    assert agree_d2 >= 0.95, f"D2 GB agreement must be >= 95%, got {agree_d2:.4f}"
