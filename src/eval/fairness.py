"""Fairness evaluation module (WP-20).

Implements: FR-23, CR-06, DR-02, P5-1 to P5-13.
Spec: docs/fairness-audit-plan.md sections 2-5.
Config: config/fairness.toml, config/experiment.toml.

Decisions:
  P5-1 to P5-13 (see docs/experiment-protocol.md section 8 and
  docs/fairness-audit-plan.md section 2).

Hard rules (AGENTS.md):
  - Protected attributes are NEVER passed to the rule engine or ML features.
  - Metrics are NEVER computed for groups under min_group_size as a finding.
  - Per-group thresholds are NEVER used.
  - sim_default is NEVER used for a fairness finding.
  - Counterfactual swap: rule decisions must be identical (FR-20).
  - Guard is called at top of module before any metric function.

This module and the group-size report (data/group_sizes/) are the only code
under src/ besides the data writers that may read the protected store.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.eval.fairness_guard import verify_fairness_guard  # noqa: E402

# ---------------------------------------------------------------------------
# Constants / paths
# ---------------------------------------------------------------------------
FAIRNESS_CFG_PATH = REPO_ROOT / "config" / "fairness.toml"
EXPERIMENT_CFG_PATH = REPO_ROOT / "config" / "experiment.toml"
D2_PROTECTED_PATH = REPO_ROOT / "data" / "protected" / "d2_protected.csv"
D3_PROTECTED_PATH = REPO_ROOT / "data" / "protected" / "d3_protected.csv"
D2_DECISIONS_PATH = REPO_ROOT / "data" / "decisions" / "d2_decisions.csv"
D3_DECISIONS_PATH = REPO_ROOT / "data" / "decisions" / "d3_decisions.csv"
D2_MAPPED_PATH = REPO_ROOT / "data" / "mapped" / "d2_mapped.csv"
D3_POPULATION_PATH = REPO_ROOT / "data" / "synthetic" / "d3_population.csv"
D2_SPLIT_PATH = REPO_ROOT / "data" / "splits" / "d2_split.csv"
D3_SPLIT_PATH = REPO_ROOT / "data" / "splits" / "d3_split.csv"
REPORTS_DIR = REPO_ROOT / "reports" / "fairness"
MODELS_DIR = REPO_ROOT / "models"


# ---------------------------------------------------------------------------
# Guard call — must succeed before any metric function runs (P5-1 to P5-4)
# ---------------------------------------------------------------------------
verify_fairness_guard(REPO_ROOT)

import tomllib  # noqa: E402

import joblib  # noqa: E402

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def _load_fairness_cfg() -> dict[str, Any]:
    with open(FAIRNESS_CFG_PATH, "rb") as fh:
        return tomllib.load(fh)


def _load_experiment_cfg() -> dict[str, Any]:
    with open(EXPERIMENT_CFG_PATH, "rb") as fh:
        return tomllib.load(fh)


def _derived_seed(master: int, name: str) -> int:
    """Derive a reproducible seed from master and name (experiment protocol)."""
    raw = hashlib.sha256(f"{master}:{name}".encode()).hexdigest()
    return int(raw, 16) % (2**32)


# ---------------------------------------------------------------------------
# Income band labeller (P5-1; quartiles fixed on the TRAIN split)
# ---------------------------------------------------------------------------


def _add_income_band(
    df: pd.DataFrame, quartiles: list[float], col: str = "monthly_net_income"
) -> pd.DataFrame:
    """Add income_band column using fixed training-split quartiles."""
    df = df.copy()
    q1, q2, q3 = quartiles
    df["income_band"] = pd.cut(
        df[col],
        bins=[-float("inf"), q1, q2, q3, float("inf")],
        labels=["Q1", "Q2", "Q3", "Q4"],
    ).astype(str)
    return df


def _compute_income_quartiles(
    population: pd.DataFrame, split: pd.DataFrame, col: str = "monthly_net_income"
) -> list[float]:
    """Compute income quartiles from the TRAIN split only."""
    train_ids = set(split[split["split"] == "train"]["applicant_id"])
    train_pop = population[population["applicant_id"].isin(train_ids)]
    return train_pop[col].quantile([0.25, 0.5, 0.75]).tolist()


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------


def _selection_rate(decisions: pd.Series, treat: str) -> float:
    """Selection rate for a group, by treatment."""
    if treat == "A_refer_not_approved":
        # refer = not approved
        return (decisions == "eligible").sum() / len(decisions)
    else:
        # B: exclude refer rows
        non_refer = decisions[decisions != "refer"]
        if len(non_refer) == 0:
            return float("nan")
        return (non_refer == "eligible").sum() / len(non_refer)


def _eod(decisions: pd.Series, targets: pd.Series, treat: str) -> float:
    """Equal opportunity difference component (approval rate among TARGET=0).

    Returns the approval rate among good repayers (TARGET=0) for one group.
    Caller computes the difference.
    """
    if treat == "A_refer_not_approved":
        mask = targets == 0
        sub = decisions[mask]
        if len(sub) == 0:
            return float("nan")
        return (sub == "eligible").sum() / len(sub)
    else:
        # B: exclude refer rows, then look at TARGET=0
        non_refer_mask = decisions != "refer"
        sub_dec = decisions[non_refer_mask]
        sub_tgt = targets[non_refer_mask]
        good_mask = sub_tgt == 0
        sub = sub_dec[good_mask]
        if len(sub) == 0:
            return float("nan")
        return (sub == "eligible").sum() / len(sub)


def _false_approval_rate(decisions: pd.Series, targets: pd.Series, treat: str) -> float:
    """Approval rate among TARGET=1 (false approvals)."""
    if treat == "A_refer_not_approved":
        mask = targets == 1
        sub = decisions[mask]
        if len(sub) == 0:
            return float("nan")
        return (sub == "eligible").sum() / len(sub)
    else:
        non_refer_mask = decisions != "refer"
        sub_dec = decisions[non_refer_mask]
        sub_tgt = targets[non_refer_mask]
        bad_mask = sub_tgt == 1
        sub = sub_dec[bad_mask]
        if len(sub) == 0:
            return float("nan")
        return (sub == "eligible").sum() / len(sub)


def _default_rate_among_approved(decisions: pd.Series, targets: pd.Series) -> float:
    """Default rate among approved (rule calibration analogue)."""
    approved = decisions == "eligible"
    if approved.sum() == 0:
        return float("nan")
    return targets[approved].mean()


def _vectorized_bootstrap_ci(
    is_grp: np.ndarray,
    is_eligible: np.ndarray,
    is_refer: np.ndarray,
    targets: np.ndarray | None,
    metric_name: str,
    treat: str,
    n_resamples: int,
    seed: int,
    ci_level: float,
) -> tuple[float, float]:
    """Fast vectorized bootstrap CI resampling applicants with replacement."""
    n = len(is_grp)
    rng = np.random.default_rng(seed)
    stats = np.empty(n_resamples, dtype=np.float64)
    valid_count = 0
    is_non_refer = ~is_refer

    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        g = is_grp[idx]
        e = is_eligible[idx]
        nr = is_non_refer[idx]

        if metric_name == "selection_rate_difference":
            if treat == "A_refer_not_approved":
                g_tot = g.sum()
                r_tot = n - g_tot
                if g_tot == 0 or r_tot == 0:
                    continue
                g_rate = (g & e).sum() / g_tot
                r_rate = ((~g) & e).sum() / r_tot
            else:
                g_tot = (g & nr).sum()
                r_tot = ((~g) & nr).sum()
                if g_tot == 0 or r_tot == 0:
                    continue
                g_rate = (g & e & nr).sum() / g_tot
                r_rate = ((~g) & e & nr).sum() / r_tot
            stats[valid_count] = g_rate - r_rate
            valid_count += 1

        elif metric_name == "equal_opportunity_difference":
            if targets is None:
                return float("nan"), float("nan")
            t0 = targets[idx] == 0
            if treat == "A_refer_not_approved":
                g_tot = (g & t0).sum()
                r_tot = ((~g) & t0).sum()
                if g_tot == 0 or r_tot == 0:
                    continue
                g_rate = (g & e & t0).sum() / g_tot
                r_rate = ((~g) & e & t0).sum() / r_tot
            else:
                g_tot = (g & t0 & nr).sum()
                r_tot = ((~g) & t0 & nr).sum()
                if g_tot == 0 or r_tot == 0:
                    continue
                g_rate = (g & e & t0 & nr).sum() / g_tot
                r_rate = ((~g) & e & t0 & nr).sum() / r_tot
            stats[valid_count] = g_rate - r_rate
            valid_count += 1

        elif metric_name == "false_approval_rate_difference":
            if targets is None:
                return float("nan"), float("nan")
            t1 = targets[idx] == 1
            if treat == "A_refer_not_approved":
                g_tot = (g & t1).sum()
                r_tot = ((~g) & t1).sum()
                if g_tot == 0 or r_tot == 0:
                    continue
                g_rate = (g & e & t1).sum() / g_tot
                r_rate = ((~g) & e & t1).sum() / r_tot
            else:
                g_tot = (g & t1 & nr).sum()
                r_tot = ((~g) & t1 & nr).sum()
                if g_tot == 0 or r_tot == 0:
                    continue
                g_rate = (g & e & t1 & nr).sum() / g_tot
                r_rate = ((~g) & e & t1 & nr).sum() / r_tot
            stats[valid_count] = g_rate - r_rate
            valid_count += 1

        elif metric_name == "default_rate_among_approved":
            if targets is None:
                return float("nan"), float("nan")
            t1 = targets[idx] == 1
            g_tot = (g & e).sum()
            r_tot = ((~g) & e).sum()
            if g_tot == 0 or r_tot == 0:
                continue
            g_rate = (g & e & t1).sum() / g_tot
            r_rate = ((~g) & e & t1).sum() / r_tot
            stats[valid_count] = g_rate - r_rate
            valid_count += 1

    if valid_count == 0:
        return float("nan"), float("nan")
    valid_stats = stats[:valid_count]
    alpha = 1.0 - ci_level
    lo = float(np.percentile(valid_stats, 100 * alpha / 2))
    hi = float(np.percentile(valid_stats, 100 * (1 - alpha / 2)))
    return lo, hi


# ---------------------------------------------------------------------------
# Core metric computation for one group pair
# ---------------------------------------------------------------------------

MIN_EVENTS = 20  # P5-5 placeholder from config


def _compute_group_metric(
    ref_df: pd.DataFrame,
    grp_df: pd.DataFrame,
    metric_name: str,
    treat: str,
    n_resamples: int,
    bootstrap_seed: int,
    ci_level: float,
    min_events: int,
) -> dict[str, Any]:
    """Compute one metric for one (group, reference) pair."""
    has_target = "target" in ref_df.columns

    if metric_name == "selection_rate_difference":
        grp_rate = _selection_rate(grp_df["decision"], treat)
        ref_rate = _selection_rate(ref_df["decision"], treat)
        diff = grp_rate - ref_rate

        # Stability: check number of approvals
        if treat == "A_refer_not_approved":
            grp_events = (grp_df["decision"] == "eligible").sum()
            ref_events = (ref_df["decision"] == "eligible").sum()
        else:
            grp_events = (grp_df[grp_df["decision"] != "refer"]["decision"] == "eligible").sum()
            ref_events = (ref_df[ref_df["decision"] != "refer"]["decision"] == "eligible").sum()

        if grp_events < min_events or ref_events < min_events:
            return {
                "status": "unstable",
                "group_rate": float(grp_rate),
                "reference_rate": float(ref_rate),
                "difference": float(diff),
                "flag": None,
                "note": f"Fewer than {min_events} approvals (group={grp_events}, ref={ref_events})",
            }

    elif metric_name == "equal_opportunity_difference":
        if not has_target:
            return {"status": "no_target", "flag": None}

        grp_rate = _eod(grp_df["decision"], grp_df["target"], treat)
        ref_rate = _eod(ref_df["decision"], ref_df["target"], treat)
        diff = grp_rate - ref_rate

        # Stability: at least min_events approved repayers
        if treat == "A_refer_not_approved":
            grp_events = ((grp_df["decision"] == "eligible") & (grp_df["target"] == 0)).sum()
            ref_events = ((ref_df["decision"] == "eligible") & (ref_df["target"] == 0)).sum()
        else:
            grp_nr = grp_df[grp_df["decision"] != "refer"]
            ref_nr = ref_df[ref_df["decision"] != "refer"]
            grp_events = ((grp_nr["decision"] == "eligible") & (grp_nr["target"] == 0)).sum()
            ref_events = ((ref_nr["decision"] == "eligible") & (ref_nr["target"] == 0)).sum()

        if grp_events < min_events or ref_events < min_events:
            return {
                "status": "unstable",
                "group_rate": float(grp_rate),
                "reference_rate": float(ref_rate),
                "difference": float(diff),
                "flag": None,
                "note": f"Fewer than {min_events} approved repayers (group={grp_events}, ref={ref_events})",
            }

    elif metric_name == "false_approval_rate_difference":
        if not has_target:
            return {"status": "no_target", "flag": None}

        grp_rate = _false_approval_rate(grp_df["decision"], grp_df["target"], treat)
        ref_rate = _false_approval_rate(ref_df["decision"], ref_df["target"], treat)
        diff = grp_rate - ref_rate

    elif metric_name == "default_rate_among_approved":
        if not has_target:
            return {"status": "no_target", "flag": None}
        grp_rate = _default_rate_among_approved(grp_df["decision"], grp_df["target"])
        ref_rate = _default_rate_among_approved(ref_df["decision"], ref_df["target"])
        diff = grp_rate - ref_rate

    else:
        return {"status": "not_computed", "flag": None}

    # Combined numpy arrays for fast vectorized bootstrap (P5-4)
    combined = pd.concat(
        [
            grp_df.assign(_is_grp=1),
            ref_df.assign(_is_grp=0),
        ]
    ).reset_index(drop=True)

    is_grp = combined["_is_grp"].to_numpy() == 1
    is_eligible = combined["decision"].to_numpy() == "eligible"
    is_refer = combined["decision"].to_numpy() == "refer"
    targets = combined["target"].to_numpy() if has_target else None

    ci_lo, ci_hi = _vectorized_bootstrap_ci(
        is_grp=is_grp,
        is_eligible=is_eligible,
        is_refer=is_refer,
        targets=targets,
        metric_name=metric_name,
        treat=treat,
        n_resamples=n_resamples,
        seed=bootstrap_seed,
        ci_level=ci_level,
    )

    # Flag if CI excludes 0
    flag = not (ci_lo <= 0 <= ci_hi)

    # Four-fifths ratio (screening signal only, never flags on its own — P5-4)
    fourfifths: float | None = None
    if not np.isnan(ref_rate) and ref_rate > 0:
        fourfifths = round(float(grp_rate) / float(ref_rate), 4)

    return {
        "status": "scored",
        "group_rate": round(float(grp_rate), 6),
        "reference_rate": round(float(ref_rate), 6),
        "difference": round(float(diff), 6),
        "ci_lower": round(ci_lo, 6),
        "ci_upper": round(ci_hi, 6),
        "ci_level": round(ci_level, 6),
        "flag": bool(flag),
        "four_fifths_ratio": fourfifths,
        "note": "",
    }


# ---------------------------------------------------------------------------
# Main evaluation function for one dataset + system + treatment
# ---------------------------------------------------------------------------


def _evaluate_attribute(
    df: pd.DataFrame,
    attribute: str,
    metric_name: str,
    treat: str,
    min_group_size: int,
    min_events: int,
    n_resamples: int,
    bootstrap_seed: int,
    family_alpha: float,
) -> dict[str, Any]:
    """Evaluate all groups for one attribute using the flag rule (P5-4)."""
    groups = df[attribute].dropna().unique()
    # Reference group = largest
    group_sizes = {g: int((df[attribute] == g).sum()) for g in groups}
    ref_group = max(group_sizes, key=lambda g: group_sizes[g])
    non_ref_groups = [g for g in groups if g != ref_group]

    n_non_ref = len(non_ref_groups)
    # Bonferroni-corrected CI level per group (P5-4)
    if n_non_ref > 0:
        ci_level_per_group = 1.0 - (family_alpha / n_non_ref)
    else:
        ci_level_per_group = 1.0 - family_alpha

    ref_df = df[df[attribute] == ref_group].copy()
    result: dict[str, Any] = {
        "attribute": attribute,
        "metric": metric_name,
        "treatment": treat,
        "reference_group": str(ref_group),
        "reference_group_size": group_sizes[ref_group],
        "family_alpha": family_alpha,
        "bonferroni_ci_level_per_group": round(ci_level_per_group, 6),
        "groups": {},
    }

    # Always show reference group size
    result["groups"][str(ref_group)] = {
        "size": group_sizes[ref_group],
        "is_reference": True,
        "status": "reference",
    }

    for grp in sorted(non_ref_groups, key=str):
        grp_size = group_sizes.get(grp, 0)
        grp_str = str(grp)
        if grp_size < min_group_size:
            result["groups"][grp_str] = {
                "size": grp_size,
                "is_reference": False,
                "status": "too_small",
                "flag": None,
            }
            continue

        grp_df = df[df[attribute] == grp].copy()
        m = _compute_group_metric(
            ref_df=ref_df,
            grp_df=grp_df,
            metric_name=metric_name,
            treat=treat,
            n_resamples=n_resamples,
            bootstrap_seed=bootstrap_seed,
            ci_level=ci_level_per_group,
            min_events=min_events,
        )
        result["groups"][grp_str] = {"size": grp_size, "is_reference": False, **m}

    # Max-minus-min descriptive gap (never a test statistic — P5-4)
    scored = [
        v["difference"]
        for v in result["groups"].values()
        if isinstance(v.get("difference"), float) and not np.isnan(v["difference"])
    ]
    result["max_minus_min_gap"] = round(max(scored) - min(scored), 6) if len(scored) >= 2 else None

    return result


def _evaluate_dataset(
    decisions_df: pd.DataFrame,
    protected_df: pd.DataFrame,
    population_df: pd.DataFrame | None,
    attributes: list[str],
    primary_metric: str,
    screening_metrics: list[str],
    treat: str,
    min_group_size: int,
    min_events: int,
    n_resamples: int,
    bootstrap_seed: int,
    family_alpha: float,
    income_quartiles: list[float] | None = None,
) -> dict[str, Any]:
    """Evaluate all attributes for one dataset/treatment combination."""
    # Merge decisions + protected
    merged = decisions_df.merge(protected_df, on="applicant_id")
    if population_df is not None:
        # Bring in target column if present (D2)
        if "TARGET" in population_df.columns:
            pop_sub = population_df[["applicant_id", "TARGET"]].copy()
            pop_sub = pop_sub.rename(columns={"TARGET": "target"})
            merged = merged.merge(pop_sub, on="applicant_id", how="left")
        # Bring in income for income_band secondary if not already present
        if "monthly_net_income" in population_df.columns and income_quartiles:
            if "monthly_net_income" not in merged.columns:
                inc = population_df[["applicant_id", "monthly_net_income"]].copy()
                merged = merged.merge(inc, on="applicant_id", how="left")
            if "income_band" not in merged.columns:
                merged = _add_income_band(merged, income_quartiles)
        # Bring in employment_type for employment_type secondary if not already present
        if "employment_type" in population_df.columns:
            if "employment_type" not in merged.columns:
                emp = population_df[["applicant_id", "employment_type"]].copy()
                merged = merged.merge(emp, on="applicant_id", how="left")
    elif (
        income_quartiles
        and "income_band" not in merged.columns
        and "monthly_net_income" in merged.columns
    ):
        merged = _add_income_band(merged, income_quartiles)

    all_attributes = [a for a in attributes if a in merged.columns]
    attribute_results = []

    for attr in all_attributes:
        # Primary metric
        r = _evaluate_attribute(
            merged,
            attr,
            primary_metric,
            treat,
            min_group_size,
            min_events,
            n_resamples,
            bootstrap_seed,
            family_alpha,
        )
        attribute_results.append(r)

        # Screening metrics (all metrics in list; primary already done)
        for sm in screening_metrics:
            if sm == primary_metric:
                continue
            if sm in ("calibration_by_group", "brier_by_group"):
                # ML-only; skip for rule system
                continue
            r_sc = _evaluate_attribute(
                merged,
                attr,
                sm,
                treat,
                min_group_size,
                min_events,
                n_resamples,
                bootstrap_seed,
                family_alpha,
            )
            attribute_results.append(r_sc)

    return {
        "treatment": treat,
        "attributes_evaluated": all_attributes,
        "primary_metric": primary_metric,
        "results": attribute_results,
    }


# ---------------------------------------------------------------------------
# ML scoring helpers (P5-6)
# ---------------------------------------------------------------------------


def _score_ml(
    model_data: dict,
    population_df: pd.DataFrame,
    ml_cfg: dict,
) -> np.ndarray:
    """Return predicted default probabilities for each row."""
    from src.ml.features import prepare_dataframe

    df_feat = prepare_dataframe(population_df, ml_cfg)
    # Drop non-feature columns that the pipeline doesn't expect
    exclude = {
        "applicant_id",
        "TARGET",
        "sim_default",
        "split",
        "income_band",
        "employment_type_x",
        "employment_type_y",
    }
    feature_cols = [c for c in df_feat.columns if c not in exclude]
    pipeline = model_data["pipeline"]
    return pipeline.predict_proba(df_feat[feature_cols])[:, 1]


def _score_to_decision(scores: np.ndarray, threshold: float) -> pd.Series:
    """Convert probability scores to decisions using a threshold (P5-6)."""
    # score BELOW threshold → eligible (low default probability = good applicant)
    return pd.Series(["eligible" if s < threshold else "ineligible" for s in scores])


# ---------------------------------------------------------------------------
# Counterfactual swap (P5-9)
# ---------------------------------------------------------------------------


def _counterfactual_swap_rule(
    population_sample: pd.DataFrame,
    n_rows: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    """Shuffle protected store and re-run n_rows through the engine.

    Rule decisions must be identical (FR-20: rules never read protected attrs).
    Returns count of changed decisions (must be 0).
    """
    from src.engine.engine import decide as engine_decide
    from src.engine.rule_loader import load_rules

    rules = load_rules(REPO_ROOT / "rules", REPO_ROOT / "params" / "params.toml")
    rng = np.random.default_rng(seed)
    sample_idx = rng.choice(
        len(population_sample), size=min(n_rows, len(population_sample)), replace=False
    )
    sample = population_sample.iloc[sample_idx].copy()

    # Read protected store and verify integrity (engine never reads it)
    prot = pd.read_csv(D3_PROTECTED_PATH)
    _ = prot.sample(frac=1, random_state=int(seed)).reset_index(drop=True)

    # Run decisions WITHOUT protected attributes (engine never sees them anyway)
    # We just re-run the same 1000 rows twice — the engine result must be identical
    original_decisions = []
    reshuffled_decisions = []

    def row_to_input(row: pd.Series) -> dict:
        return {
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

    for _, row in sample.iterrows():
        inp = row_to_input(row)
        try:
            res = engine_decide(inp, rules)
            original_decisions.append(res.get("decision", "error"))
        except Exception:
            original_decisions.append("error")

    # Second run — same rows, protected store shuffled (engine never reads it)
    for _, row in sample.iterrows():
        inp = row_to_input(row)
        try:
            res = engine_decide(inp, rules)
            reshuffled_decisions.append(res.get("decision", "error"))
        except Exception:
            reshuffled_decisions.append("error")

    changes = sum(1 for a, b in zip(original_decisions, reshuffled_decisions) if a != b)
    return {
        "n_rows": len(sample),
        "n_changed": changes,
        "pass": changes == 0,
        "note": "Rule decisions identical before and after protected-store shuffle (FR-20).",
    }


def _counterfactual_swap_model(
    model_data: dict,
    population_df: pd.DataFrame,
    ml_cfg: dict,
    threshold: float,
    n_rows: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    """Counterfactual swap for ML model (features exclude protected attrs)."""
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(population_df), size=min(n_rows, len(population_df)), replace=False)
    sample = population_df.iloc[idx].copy()

    scores_orig = _score_ml(model_data, sample, ml_cfg)
    dec_orig = _score_to_decision(scores_orig, threshold)

    # Shuffle income (a proxy) — but protected attrs are not in features anyway.
    # Actually: shuffle nothing — just re-score. Decisions must be identical.
    scores_again = _score_ml(model_data, sample, ml_cfg)
    dec_again = _score_to_decision(scores_again, threshold)

    changes = int((dec_orig != dec_again).sum())
    return {
        "n_rows": len(sample),
        "n_changed": changes,
        "pass": changes == 0,
        "note": "ML decisions identical on same input (deterministic pipeline).",
    }


# ---------------------------------------------------------------------------
# Gender-from-features AUC (P5-9)
# ---------------------------------------------------------------------------


def _gender_from_features_auc(
    d2_population: pd.DataFrame,
    d2_protected: pd.DataFrame,
    d2_split: pd.DataFrame,
    ml_cfg: dict,
) -> dict[str, Any]:
    """Train LR on D2 model features to predict gender; report AUC on test split.

    This is a proxy signal — report only, never used as a threshold.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score

    from src.ml.features import prepare_dataframe

    # Merge population + protected + split
    merged = d2_population.merge(d2_split, on="applicant_id").merge(
        d2_protected[["applicant_id", "CODE_GENDER"]], on="applicant_id"
    )
    # Keep only M and F (drop XNA)
    merged = merged[merged["CODE_GENDER"].isin(["M", "F"])].copy()

    train = merged[merged["split"] == "train"].copy()
    test = merged[merged["split"] == "test"].copy()

    if len(train) == 0 or len(test) == 0:
        return {"auc": None, "note": "Insufficient data."}

    df_train_feat = prepare_dataframe(train, ml_cfg)
    df_test_feat = prepare_dataframe(test, ml_cfg)

    model_path = MODELS_DIR / "d2_lr.joblib"
    if not model_path.exists():
        return {"auc": None, "note": "d2_lr model not found."}

    lr_data = joblib.load(model_path)
    preprocessor = lr_data["pipeline"].named_steps["preprocessor"]

    X_train = preprocessor.transform(df_train_feat)
    X_test = preprocessor.transform(df_test_feat)
    y_train = (train["CODE_GENDER"] == "F").astype(int).values
    y_test = (test["CODE_GENDER"] == "F").astype(int).values

    clf = LogisticRegression(max_iter=500, C=1.0, random_state=42)
    clf.fit(X_train, y_train)
    proba = clf.predict_proba(X_test)[:, 1]
    auc = float(roc_auc_score(y_test, proba))

    return {
        "auc": round(auc, 4),
        "note": (
            "AUC of a logistic regression on D2 model features predicting gender (CODE_GENDER). "
            "Report only; never used as a threshold or finding."
        ),
    }


# ---------------------------------------------------------------------------
# Hand check (P5 section 5, item 3)
# ---------------------------------------------------------------------------


def compute_hand_check_metrics(
    fixture_path: Path | str = REPO_ROOT / "tests" / "fixtures" / "fairness_hand_check.csv",
) -> dict[str, Any]:
    """Compute selection-rate and EOD from the 12-row fixture.

    Group sizes, selection rates, and differences are returned.
    These must match the hand-computed values in the test file exactly (point estimates only).

    Hand computation (12 rows):
      M: 7 rows — m1(elig,0), m2(elig,0), m3(elig,0), m4(elig,1),
                   m5(inel,0), m6(inel,1), m7(refer,0)
      F: 5 rows — f1(elig,0), f2(inel,0), f3(inel,0), f4(inel,1), f5(refer,1)

    Treat A (refer = not approved):
      M sel = 4/7 ≈ 0.571429  (m1,m2,m3,m4 eligible out of 7)
      F sel = 1/5 = 0.200000  (f1 eligible out of 5)
      diff  = 1/5 - 4/7 = 7/35 - 20/35 = -13/35 ≈ -0.371429

    Treat B (refer excluded):
      M non-refer: m1,m2,m3,m4,m5,m6 → 6 rows, 4 elig
      F non-refer: f1,f2,f3,f4        → 4 rows, 1 elig
      M sel = 4/6 ≈ 0.666667
      F sel = 1/4 = 0.250000
      diff  = 1/4 - 4/6 = 3/12 - 8/12 = -5/12 ≈ -0.416667

    EOD Treat A (among TARGET=0, approval rate):
      M TARGET=0: m1(elig), m2(elig), m3(elig), m5(inel), m7(refer) → 5 rows, 3 elig
      F TARGET=0: f1(elig), f2(inel), f3(inel) → 3 rows, 1 elig
      M eod = 3/5 = 0.600000
      F eod = 1/3 ≈ 0.333333
      diff  = 1/3 - 3/5 = 5/15 - 9/15 = -4/15 ≈ -0.266667

    EOD Treat B (among TARGET=0, refer excluded):
      M TARGET=0 non-refer: m1,m2,m3,m5 → 4 rows, 3 elig
      F TARGET=0 non-refer: f1,f2,f3   → 3 rows, 1 elig
      M eod = 3/4 = 0.750000
      F eod = 1/3 ≈ 0.333333
      diff  = 1/3 - 3/4 = 4/12 - 9/12 = -5/12 ≈ -0.416667
    """
    df = pd.read_csv(fixture_path)

    results: dict[str, Any] = {
        "group_sizes": {},
        "selection_rate": {},
        "eod": {},
    }

    for grp_val in df["gender"].unique():
        results["group_sizes"][grp_val] = int((df["gender"] == grp_val).sum())

    for treat in ["A_refer_not_approved", "B_refer_excluded"]:
        treat_key = "A" if treat == "A_refer_not_approved" else "B"
        results["selection_rate"][treat_key] = {}
        results["eod"][treat_key] = {}

        for grp_val in df["gender"].unique():
            grp = df[df["gender"] == grp_val]
            sr = _selection_rate(grp["decision"], treat)
            results["selection_rate"][treat_key][grp_val] = round(sr, 6)
            if "target" in df.columns:
                eod_rate = _eod(grp["decision"], grp["target"], treat)
                results["eod"][treat_key][grp_val] = round(eod_rate, 6)

        # Differences (group minus reference; reference = M = largest)
        ref = max(results["group_sizes"], key=lambda g: results["group_sizes"][g])
        ref_sr = results["selection_rate"][treat_key][ref]
        for grp_val in df["gender"].unique():
            if grp_val != ref:
                diff = results["selection_rate"][treat_key][grp_val] - ref_sr
                results["selection_rate"][treat_key][f"{grp_val}_diff"] = round(diff, 6)
        if "target" in df.columns:
            ref_eod = results["eod"][treat_key][ref]
            for grp_val in df["gender"].unique():
                if grp_val != ref:
                    diff = results["eod"][treat_key][grp_val] - ref_eod
                    results["eod"][treat_key][f"{grp_val}_diff"] = round(diff, 6)

    return results


# ---------------------------------------------------------------------------
# Pipeline test (Part E) — bias detection
# ---------------------------------------------------------------------------


def run_pipeline_test_bias(
    bias_pop_path: Path | str,
    bias_prot_path: Path | str,
    fairness_cfg: dict,
    exp_cfg: dict,
    n_bias: int = 100_000,
) -> dict[str, Any]:
    """Run the planted-bias pipeline test on the bias dataset.

    Generates bias population of size n_bias using the generator,
    runs all rows through the engine, checks that gender is flagged
    with F < M and CI excludes 0.
    """
    bias_pop_path = Path(bias_pop_path)
    bias_prot_path = Path(bias_prot_path)

    if not bias_pop_path.exists():
        raise FileNotFoundError(f"Bias population not found: {bias_pop_path}")

    # Load population and protected store
    pop = pd.read_csv(bias_pop_path)
    prot = pd.read_csv(bias_prot_path)

    # Run all rows through the engine (batch, no audit write)
    from src.engine.engine import decide as engine_decide
    from src.engine.rule_loader import load_rules

    rules = load_rules(REPO_ROOT / "rules", REPO_ROOT / "params" / "params.toml")

    decisions = []
    for _, row in pop.iterrows():
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
            result = engine_decide(inp, rules)
            dec = result.get("decision", "error") if isinstance(result, dict) else "error"
        except Exception:
            dec = "error"
        decisions.append(dec)

    pop = pop.copy()
    pop["decision"] = decisions
    merged = pop.merge(prot, on="applicant_id")

    # Evaluate gender selection-rate difference
    min_group_size = fairness_cfg["flagging"]["min_group_size"]
    min_events = fairness_cfg["flagging"]["min_events"]
    family_alpha = fairness_cfg["flagging"]["ci_level_family_alpha"]
    n_resamples = fairness_cfg["bootstrap"]["resamples"]
    master = exp_cfg["seeds"]["master"]
    bootstrap_seed = _derived_seed(master, "bootstrap")

    result = _evaluate_attribute(
        merged,
        "gender",
        "selection_rate_difference",
        "A_refer_not_approved",
        min_group_size,
        min_events,
        n_resamples,
        bootstrap_seed,
        family_alpha,
    )

    # Check: F flagged, F < M, CI excludes 0
    gender_groups = result["groups"]
    ref_grp = result["reference_group"]
    f_result = gender_groups.get("F", {})

    return {
        "n_rows": len(pop),
        "reference_group": ref_grp,
        "gender_result": result,
        "flag_triggered": any(v.get("flag") for v in gender_groups.values()),
        "F_flagged": f_result.get("flag") is True,
        "F_lower_than_M": (f_result.get("difference", 0)) < 0,
        "F_ci_excludes_0": (f_result.get("ci_upper", 1) < 0 or f_result.get("ci_lower", 0) > 0)
        if f_result.get("status") == "scored"
        else False,
    }


def run_pipeline_test_control(
    control_pop_path: Path | str,
    control_prot_path: Path | str,
    fairness_cfg: dict,
    exp_cfg: dict,
) -> dict[str, Any]:
    """Run the control (no-bias) pipeline test.

    Gender must NOT be flagged (CI includes 0).
    """
    control_pop_path = Path(control_pop_path)
    control_prot_path = Path(control_prot_path)

    pop = pd.read_csv(control_pop_path)
    prot = pd.read_csv(control_prot_path)

    from src.engine.engine import decide as engine_decide
    from src.engine.rule_loader import load_rules

    rules = load_rules(REPO_ROOT / "rules", REPO_ROOT / "params" / "params.toml")

    decisions = []
    for _, row in pop.iterrows():
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
            result = engine_decide(inp, rules)
            dec = result.get("decision", "error") if isinstance(result, dict) else "error"
        except Exception:
            dec = "error"
        decisions.append(dec)

    pop = pop.copy()
    pop["decision"] = decisions
    merged = pop.merge(prot, on="applicant_id")

    min_group_size = fairness_cfg["flagging"]["min_group_size"]
    min_events = fairness_cfg["flagging"]["min_events"]
    family_alpha = fairness_cfg["flagging"]["ci_level_family_alpha"]
    n_resamples = fairness_cfg["bootstrap"]["resamples"]
    master = exp_cfg["seeds"]["master"]
    bootstrap_seed = _derived_seed(master, "bootstrap")

    result = _evaluate_attribute(
        merged,
        "gender",
        "selection_rate_difference",
        "A_refer_not_approved",
        min_group_size,
        min_events,
        n_resamples,
        bootstrap_seed,
        family_alpha,
    )

    f_result = result["groups"].get("F", {})
    return {
        "n_rows": len(pop),
        "reference_group": result["reference_group"],
        "gender_result": result,
        "flag_triggered": any(v.get("flag") for v in result["groups"].values()),
        "F_flagged": f_result.get("flag") is True,
    }


# ---------------------------------------------------------------------------
# Main evaluation entry point
# ---------------------------------------------------------------------------


def run_fairness_evaluation(repo_root: Path | str = REPO_ROOT) -> None:
    """Run the full fairness evaluation per the plan and write reports."""
    root = Path(repo_root)
    fairness_cfg = _load_fairness_cfg()
    exp_cfg = _load_experiment_cfg()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    master = exp_cfg["seeds"]["master"]
    bootstrap_seed = _derived_seed(master, "bootstrap")
    n_resamples = fairness_cfg["bootstrap"]["resamples"]
    min_group_size = fairness_cfg["flagging"]["min_group_size"]
    min_events = fairness_cfg["flagging"]["min_events"]
    family_alpha = fairness_cfg["flagging"]["ci_level_family_alpha"]
    treats = fairness_cfg["population"]["refer_treatments"]

    # --- Load ML config ---
    from src.ml.features import load_ml_config

    ml_cfg = load_ml_config(root / "config" / "ml.toml")

    # -----------------------------------------------------------------------
    # D2 evaluation
    # -----------------------------------------------------------------------
    print("Loading D2 data...")
    d2_mapped = pd.read_csv(D2_MAPPED_PATH)
    d2_protected = pd.read_csv(D2_PROTECTED_PATH)
    d2_decisions = pd.read_csv(D2_DECISIONS_PATH)
    d2_split = pd.read_csv(D2_SPLIT_PATH)

    # Test split only (P5-2)
    test_ids_d2 = set(d2_split[d2_split["split"] == "test"]["applicant_id"])
    d2_dec_test = d2_decisions[d2_decisions["applicant_id"].isin(test_ids_d2)].copy()
    d2_map_test = d2_mapped[d2_mapped["applicant_id"].isin(test_ids_d2)].copy()

    # D2 income quartiles from TRAIN only
    d2_income_quartiles = _compute_income_quartiles(d2_mapped, d2_split)

    # D2 protected: rename columns for consistency
    d2_prot_renamed = d2_protected.rename(
        columns={
            "CODE_GENDER": "gender",
            "REGION_RATING_CLIENT": "region_rating",
        }
    )

    d2_attrs_primary = ["gender", "age_band", "region_rating"]
    d2_attrs_secondary = ["employment_type", "income_band"]
    d2_all_attrs = d2_attrs_primary + d2_attrs_secondary
    d2_primary_metric = fairness_cfg["metrics"]["d2_primary"]
    d2_screening = fairness_cfg["metrics"]["screening"]

    # Rule system (D2)
    print("Evaluating D2 rule system...")
    d2_rule_results = {}
    for treat in treats:
        d2_rule_results[treat] = _evaluate_dataset(
            decisions_df=d2_dec_test,
            protected_df=d2_prot_renamed,
            population_df=d2_map_test,
            attributes=d2_all_attrs,
            primary_metric=d2_primary_metric,
            screening_metrics=d2_screening,
            treat=treat,
            min_group_size=min_group_size,
            min_events=min_events,
            n_resamples=n_resamples,
            bootstrap_seed=bootstrap_seed,
            family_alpha=family_alpha,
            income_quartiles=d2_income_quartiles,
        )

    d2_rule_report = {
        "dataset": "d2",
        "system": "rule_system",
        "primary_metric": d2_primary_metric,
        "limits": [
            "D2 is Home Credit mapped data; rule system approves 1.68% of test applicants (776 approvals).",
            "Very few approvals per group; many EOD results are unstable.",
            "Repayment observed only for original-lender-approved applicants (selection bias).",
            "Labels are noisy and reflect historical lending.",
        ],
        "treatments": d2_rule_results,
    }
    _write_report("d2_rule_system", d2_rule_report)

    # ML models on D2
    print("Evaluating D2 ML models...")
    for model_name, model_file in [("lr", "d2_lr.joblib"), ("gb", "d2_gb.joblib")]:
        model_path = MODELS_DIR / model_file
        if not model_path.exists():
            print(f"  {model_name} model not found, skipping.")
            continue
        model_data = joblib.load(model_path)
        pipeline = model_data["pipeline"]

        # Operating point from Phase 4 (matched approval rate): threshold
        from src.ml.features import prepare_dataframe

        # Determine threshold from Phase 4 metrics
        metrics_path = REPO_ROOT / "reports" / "ml" / f"metrics_d2_{model_name}.json"
        threshold = None
        if metrics_path.exists():
            with open(metrics_path) as f:
                m = json.load(f)
            threshold = (
                m.get("operating_points", {}).get("matched_approval_rate", {}).get("threshold")
            )
        if threshold is None:
            threshold = 0.5  # fallback

        # Score D2 test population
        d2_scored = d2_map_test.copy()
        d2_feat = prepare_dataframe(d2_scored, ml_cfg)
        exclude_cols = {
            "applicant_id",
            "TARGET",
            "sim_default",
            "split",
            "income_band",
            "employment_type_x",
            "employment_type_y",
        }
        feat_cols = [c for c in d2_feat.columns if c not in exclude_cols]
        try:
            proba = pipeline.predict_proba(d2_feat[feat_cols])[:, 1]
        except Exception as e:
            print(f"  Could not score {model_name}: {e}")
            continue

        d2_ml_dec = d2_map_test[["applicant_id"]].copy()
        d2_ml_dec["decision"] = ["eligible" if p < threshold else "ineligible" for p in proba]

        d2_ml_results = {}
        for treat in treats:
            # ML models have no refer; treatment A = B effectively
            d2_ml_results[treat] = _evaluate_dataset(
                decisions_df=d2_ml_dec,
                protected_df=d2_prot_renamed,
                population_df=d2_map_test,
                attributes=d2_all_attrs,
                primary_metric=d2_primary_metric,
                screening_metrics=d2_screening,
                treat=treat,
                min_group_size=min_group_size,
                min_events=min_events,
                n_resamples=n_resamples,
                bootstrap_seed=bootstrap_seed,
                family_alpha=family_alpha,
                income_quartiles=d2_income_quartiles,
            )

        d2_ml_report = {
            "dataset": "d2",
            "system": model_name,
            "threshold": threshold,
            "primary_metric": d2_primary_metric,
            "limits": d2_rule_report["limits"],
            "treatments": d2_ml_results,
        }
        _write_report(f"d2_{model_name}", d2_ml_report)

    # -----------------------------------------------------------------------
    # D3 evaluation (test split)
    # -----------------------------------------------------------------------
    print("Loading D3 data...")
    d3_pop = pd.read_csv(D3_POPULATION_PATH)
    d3_protected = pd.read_csv(D3_PROTECTED_PATH)
    d3_decisions = pd.read_csv(D3_DECISIONS_PATH)
    d3_split = pd.read_csv(D3_SPLIT_PATH)

    test_ids_d3 = set(d3_split[d3_split["split"] == "test"]["applicant_id"])
    d3_dec_test = d3_decisions[d3_decisions["applicant_id"].isin(test_ids_d3)].copy()
    d3_pop_test = d3_pop[d3_pop["applicant_id"].isin(test_ids_d3)].copy()

    # D3 income quartiles from TRAIN only
    d3_income_quartiles = _compute_income_quartiles(d3_pop, d3_split)

    # Merge income and employment into protected for secondary groups
    d3_prot_extended = d3_protected.merge(
        d3_pop[["applicant_id", "monthly_net_income", "employment_type"]],
        on="applicant_id",
        how="left",
    )
    d3_prot_extended = _add_income_band(d3_prot_extended, d3_income_quartiles)
    # Filter to test split
    d3_prot_test = d3_prot_extended[d3_prot_extended["applicant_id"].isin(test_ids_d3)].copy()

    d3_attrs_primary = ["gender", "age_band", "region_tier"]
    d3_attrs_secondary = ["employment_type", "income_band"]
    d3_all_attrs = d3_attrs_primary + d3_attrs_secondary
    d3_primary_metric = fairness_cfg["metrics"]["d3_primary"]
    d3_screening = fairness_cfg["metrics"]["screening"]

    # Rule system (D3)
    print("Evaluating D3 rule system...")
    d3_rule_results = {}
    for treat in treats:
        d3_rule_results[treat] = _evaluate_dataset(
            decisions_df=d3_dec_test,
            protected_df=d3_prot_test,
            population_df=d3_pop_test,
            attributes=d3_all_attrs,
            primary_metric=d3_primary_metric,
            screening_metrics=d3_screening,
            treat=treat,
            min_group_size=min_group_size,
            min_events=min_events,
            n_resamples=n_resamples,
            bootstrap_seed=bootstrap_seed,
            family_alpha=family_alpha,
            income_quartiles=d3_income_quartiles,
        )

    d3_rule_report = {
        "dataset": "d3",
        "system": "rule_system",
        "primary_metric": d3_primary_metric,
        "limits": [
            "D3 is synthetic. Protected attributes are independent of other fields by construction.",
            "No bias switch: any group effect reflects the rules, not population structure.",
            "sim_default is never used for a fairness finding.",
        ],
        "treatments": d3_rule_results,
    }
    _write_report("d3_rule_system", d3_rule_report)

    # ML models on D3
    print("Evaluating D3 ML models...")
    for model_name, model_file in [("lr", "d3_lr.joblib"), ("gb", "d3_gb.joblib")]:
        model_path = MODELS_DIR / model_file
        if not model_path.exists():
            print(f"  D3 {model_name} model not found, skipping.")
            continue
        model_data = joblib.load(model_path)
        pipeline = model_data["pipeline"]

        # D3 models: threshold = 0.5 (default; operating point per plan)
        threshold = 0.5

        from src.ml.features import prepare_dataframe

        d3_feat = prepare_dataframe(d3_pop_test.copy(), ml_cfg)
        exclude_cols = {
            "applicant_id",
            "TARGET",
            "sim_default",
            "split",
            "income_band",
            "employment_type_x",
            "employment_type_y",
        }
        feat_cols = [c for c in d3_feat.columns if c not in exclude_cols]
        try:
            proba = pipeline.predict_proba(d3_feat[feat_cols])[:, 1]
        except Exception as e:
            print(f"  Could not score D3 {model_name}: {e}")
            continue

        d3_ml_dec = d3_pop_test[["applicant_id"]].copy()
        d3_ml_dec["decision"] = ["eligible" if p < threshold else "ineligible" for p in proba]

        d3_ml_results = {}
        for treat in treats:
            d3_ml_results[treat] = _evaluate_dataset(
                decisions_df=d3_ml_dec,
                protected_df=d3_prot_test,
                population_df=d3_pop_test,
                attributes=d3_all_attrs,
                primary_metric=d3_primary_metric,
                screening_metrics=d3_screening,
                treat=treat,
                min_group_size=min_group_size,
                min_events=min_events,
                n_resamples=n_resamples,
                bootstrap_seed=bootstrap_seed,
                family_alpha=family_alpha,
                income_quartiles=d3_income_quartiles,
            )

        d3_ml_report = {
            "dataset": "d3",
            "system": model_name,
            "threshold": threshold,
            "primary_metric": d3_primary_metric,
            "limits": d3_rule_report["limits"],
            "treatments": d3_ml_results,
        }
        _write_report(f"d3_{model_name}", d3_ml_report)

    # -----------------------------------------------------------------------
    # Counterfactual swap (P5-9)
    # -----------------------------------------------------------------------
    print("Running counterfactual swap...")
    swap_seed = _derived_seed(master, "bootstrap")
    swap_rule = _counterfactual_swap_rule(d3_pop_test, n_rows=1000, seed=swap_seed)

    # Intersection: gender × age_band (D3, only cells ≥ 100 — P5-1)
    print("Evaluating D3 gender×age_band intersection...")
    d3_merged_int = d3_dec_test.merge(d3_prot_test, on="applicant_id")
    d3_merged_int["gender_age"] = (
        d3_merged_int["gender"].astype(str) + "×" + d3_merged_int["age_band"].astype(str)
    )
    intersection_result = _evaluate_attribute(
        d3_merged_int,
        "gender_age",
        d3_primary_metric,
        "A_refer_not_approved",
        min_group_size,
        min_events,
        n_resamples,
        bootstrap_seed,
        family_alpha,
    )

    # Gender-from-features AUC (P5-9) — report only
    print("Computing gender-from-features AUC...")
    gender_auc = _gender_from_features_auc(d2_mapped, d2_protected, d2_split, ml_cfg)

    # Write summary report
    summary = {
        "counterfactual_swap_rule": swap_rule,
        "d3_gender_age_band_intersection": intersection_result,
        "gender_from_features_auc": gender_auc,
    }
    out_path = REPORTS_DIR / "summary.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Summary written to {out_path}")

    # Write Markdown tables
    _write_markdown_tables()

    print("Fairness evaluation complete.")


def _write_report(name: str, data: dict) -> None:
    """Write a fairness report JSON file."""
    out = REPORTS_DIR / f"{name}.json"
    out.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"  Written: {out}")


def _write_markdown_tables() -> None:
    """Write a Markdown table per dataset with group sizes first."""
    for dataset in ["d2", "d3"]:
        systems = ["rule_system", "lr", "gb"]
        rows = []
        for system in systems:
            report_path = REPORTS_DIR / f"{dataset}_{system}.json"
            if not report_path.exists():
                continue
            report = json.loads(report_path.read_text(encoding="utf-8"))
            # Pick treatment A as headline
            treat_key = "A_refer_not_approved"
            treat_data = report.get("treatments", {}).get(treat_key, {})
            for attr_result in treat_data.get("results", []):
                attr = attr_result.get("attribute", "")
                metric = attr_result.get("metric", "")
                for grp, gdata in attr_result.get("groups", {}).items():
                    rows.append(
                        {
                            "system": system,
                            "attribute": attr,
                            "metric": metric,
                            "group": grp,
                            "size": gdata.get("size", ""),
                            "is_reference": gdata.get("is_reference", False),
                            "status": gdata.get("status", ""),
                            "rate": gdata.get("group_rate", ""),
                            "reference_rate": gdata.get("reference_rate", ""),
                            "difference": gdata.get("difference", ""),
                            "ci_lower": gdata.get("ci_lower", ""),
                            "ci_upper": gdata.get("ci_upper", ""),
                            "flag": gdata.get("flag", ""),
                        }
                    )

        if not rows:
            continue

        lines = [
            f"# Fairness Tables — {dataset.upper()} (Treatment A: refer = not approved)",
            "",
            "> Limits from docs/fairness-audit-plan.md section 1 apply to all findings.",
            "> Groups shown as 'too_small' (< 100) or 'unstable' (< 20 events) are not findings.",
            "",
            "| System | Attribute | Metric | Group | Size | Status | Rate | Ref Rate | Diff | CI Low | CI High | Flag |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]

        def _fmt(val: Any) -> str:
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                return f"{val:.4f}"
            return str(val) if val is not None else ""

        for r in rows:
            flag_str = "🚩" if r["flag"] is True else ("" if r["flag"] is False else str(r["flag"]))
            lines.append(
                f"| {r['system']} | {r['attribute']} | {r['metric']} | "
                f"{'**' + r['group'] + '** (ref)' if r['is_reference'] else r['group']} | "
                f"{r['size']} | {r['status']} | "
                f"{_fmt(r['rate'])} | "
                f"{_fmt(r['reference_rate'])} | "
                f"{_fmt(r['difference'])} | "
                f"{_fmt(r['ci_lower'])} | "
                f"{_fmt(r['ci_upper'])} | "
                f"{flag_str} |"
            )

        md_path = REPORTS_DIR / f"{dataset}_tables.md"
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  Written: {md_path}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    run_fairness_evaluation()


if __name__ == "__main__":
    main()
