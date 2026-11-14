"""D3 synthetic population generator.

Implements: WP-16b, DR-05, docs/08-datasets.md section 4.
Spec: config/generator.toml, config/experiment.toml, params/params.toml.
Deterministic per derived seed:
  seed_pop = derive_seed(master, "d3_population")
  seed_sim = derive_seed(master, "d3_sim_outcome")
  seed_bias = derive_seed(master, "d3_bias")

Outputs:
  data/synthetic/d3_population.csv
  data/protected/d3_protected.csv
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import tomllib
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import numpy as np
import pandas as pd


def derive_seed(master: int, name: str) -> int:
    """FR-21: deterministic per-name seed from master seed."""
    return int(hashlib.sha256(f"{master}:{name}".encode()).hexdigest(), 16) % (2**32)


def _age_band(age: int, edges: list[int]) -> str:
    """Return age band for given age."""
    if age < edges[0]:
        return "under-21"
    for i in range(len(edges) - 1):
        if edges[i] <= age < edges[i + 1]:
            lo = edges[i]
            hi = edges[i + 1] - 1
            return f"{lo}-{hi}"
    return f"{edges[-1]}+"


def generate_d3(
    size: int | None = None,
    master_seed: int | None = None,
    bias_enabled: bool | None = None,
    out_population_path: Path | str | None = None,
    out_protected_path: Path | str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate D3 synthetic population and protected store."""
    gen_cfg_path = Path("config/generator.toml")
    with open(gen_cfg_path, "rb") as fh:
        gen_cfg = tomllib.load(fh)

    exp_cfg_path = Path("config/experiment.toml")
    with open(exp_cfg_path, "rb") as fh:
        exp_cfg = tomllib.load(fh)

    param_cfg_path = Path("params/params.toml")
    with open(param_cfg_path, "rb") as fh:
        params = tomllib.load(fh)

    # Master seed and derived seeds
    m_seed = master_seed if master_seed is not None else int(exp_cfg["seeds"]["master"])
    seed_pop = derive_seed(m_seed, "d3_population")
    seed_sim = derive_seed(m_seed, "d3_sim_outcome")
    seed_bias = derive_seed(m_seed, "d3_bias")

    n_pop = size if size is not None else int(exp_cfg["d3"]["size"])
    is_bias_on = bias_enabled if bias_enabled is not None else bool(gen_cfg["bias"]["enabled"])

    pop_out = (
        Path(out_population_path)
        if out_population_path is not None
        else Path(exp_cfg["d3"]["mapped_path"])
    )
    prot_out = (
        Path(out_protected_path)
        if out_protected_path is not None
        else Path(exp_cfg["d3"]["protected_path"])
    )

    # Product parameters
    min_amount = int(params["product"]["min_amount"])
    max_amount = int(params["product"]["max_amount"])
    amount_step = int(params["product"]["amount_step"])

    # Generator settings
    age_min = int(gen_cfg["age"]["min"])
    age_max = int(gen_cfg["age"]["max"])
    emp_types = ["salaried", "self_employed", "other"]
    emp_probs = [
        float(gen_cfg["employment_type"]["salaried"]),
        float(gen_cfg["employment_type"]["self_employed"]),
        float(gen_cfg["employment_type"]["other"]),
    ]
    emp_mean = float(gen_cfg["employment_months"]["mean"])

    med_income_40 = float(gen_cfg["income"]["median_at_age_40"])
    income_sigma = float(gen_cfg["income"]["sigma"])
    age_coef = float(gen_cfg["income"]["age_coef_per_year"])
    tenure_coef = float(gen_cfg["income"]["tenure_coef_per_month"])
    income_floor = float(gen_cfg["income"]["floor"])

    ob_zero_fraction = float(gen_cfg["obligations"]["zero_fraction"])
    ob_alpha = float(gen_cfg["obligations"]["beta_alpha"])
    ob_beta = float(gen_cfg["obligations"]["beta_beta"])

    cs_mean = float(gen_cfg["credit_score"]["mean"])
    cs_std = float(gen_cfg["credit_score"]["std"])
    cs_min = int(gen_cfg["credit_score"]["min"])
    cs_max = int(gen_cfg["credit_score"]["max"])
    cs_null_frac = float(gen_cfg["credit_score"]["null_fraction"])

    enq_mean = float(gen_cfg["enquiries_6m"]["poisson_mean"])

    delinq_base = float(gen_cfg["delinquency"]["base"])
    delinq_slope = float(gen_cfg["delinquency"]["slope"])
    delinq_cap = float(gen_cfg["delinquency"]["cap"])

    wo_p = float(gen_cfg["written_off"]["p"])
    kyc_p = float(gen_cfg["kyc_consent"]["kyc_verified_p"])
    consent_p = float(gen_cfg["kyc_consent"]["consent_given_p"])

    req_mul_min = float(gen_cfg["request"]["multiple_min"])
    req_mul_max = float(gen_cfg["request"]["multiple_max"])
    tenure_choices = [int(t) for t in gen_cfg["request"]["tenure_choices"]]

    # Protected distributions
    genders = list(gen_cfg["protected"]["gender"].keys())
    gender_probs = [float(p) for p in gen_cfg["protected"]["gender"].values()]
    region_tiers = [int(k) for k in gen_cfg["protected"]["region_tier"].keys()]
    region_probs = [float(p) for p in gen_cfg["protected"]["region_tier"].values()]
    age_band_edges = [21, 30, 40, 50, 60]

    # Bias settings
    bias_group_attr = str(gen_cfg["bias"]["group_attribute"])
    bias_group_val = str(gen_cfg["bias"]["group_value"])
    bias_shift_pct = float(gen_cfg["bias"]["income_shift_pct"])

    # Sim outcome settings
    sim_enabled = bool(gen_cfg["sim_outcome"]["enabled"])
    sim_intercept = float(gen_cfg["sim_outcome"]["intercept"])
    sim_score_coef = float(gen_cfg["sim_outcome"]["score_coef"])
    sim_foir_coef = float(gen_cfg["sim_outcome"]["foir_coef"])
    sim_delinq_coef = float(gen_cfg["sim_outcome"]["delinquency_coef"])

    # RNGs
    rng_pop = np.random.default_rng(seed_pop)
    rng_sim = np.random.default_rng(seed_sim)
    rng_bias = np.random.default_rng(seed_bias)

    population_rows: list[dict[str, Any]] = []
    protected_rows: list[dict[str, Any]] = []

    for i in range(n_pop):
        applicant_id = f"syn-{i+1:05d}"

        # Protected attributes drawn first
        gender = str(rng_pop.choice(genders, p=gender_probs))
        region_tier = int(rng_pop.choice(region_tiers, p=region_probs))

        # age
        age = int(rng_pop.integers(age_min, age_max + 1))
        age_band = _age_band(age, age_band_edges)

        # employment_type
        employment_type = str(rng_pop.choice(emp_types, p=emp_probs))

        # employment_months
        exp_emp = rng_pop.exponential(scale=emp_mean)
        max_emp = 12 * (age - 18)
        employment_months = int(round(min(max(exp_emp, 0.0), max_emp)))

        # monthly_net_income
        log_med = np.log(med_income_40) + age_coef * (age - 40) + tenure_coef * (employment_months - 60)
        inc_raw = rng_pop.lognormal(mean=log_med, sigma=income_sigma)
        inc_val = max(inc_raw, income_floor)

        # Planted-bias shift
        if is_bias_on:
            match = False
            if bias_group_attr == "gender" and gender == bias_group_val:
                match = True
            elif bias_group_attr == "region_tier" and str(region_tier) == bias_group_val:
                match = True
            if match:
                inc_val = inc_val * (1.0 + bias_shift_pct / 100.0)
                inc_val = max(inc_val, income_floor)

        monthly_net_income = int(Decimal(str(inc_val)).to_integral_value(rounding=ROUND_HALF_UP))

        # monthly_obligations
        if rng_pop.random() < ob_zero_fraction:
            monthly_obligations = 0
        else:
            ob_share = rng_pop.beta(ob_alpha, ob_beta)
            ob_amount = Decimal(str(ob_share)) * Decimal(str(monthly_net_income))
            monthly_obligations = int(ob_amount.to_integral_value(rounding=ROUND_HALF_UP))
        obligations_source = "synthetic"

        # credit_score
        if rng_pop.random() < cs_null_frac:
            credit_score = None
        else:
            raw_cs = rng_pop.normal(cs_mean, cs_std)
            cs_clipped = min(max(raw_cs, cs_min), cs_max)
            credit_score = int(round(cs_clipped))

        # enquiries_6m
        enquiries_6m = int(rng_pop.poisson(lam=enq_mean))

        # severe_delinquency_36m
        if credit_score is None:
            delinq_p = delinq_base
        else:
            delinq_p = min(delinq_cap, delinq_base * np.exp(-delinq_slope * (credit_score - 700)))
        severe_delinquency_36m = bool(rng_pop.random() < delinq_p)

        # written_off
        written_off = bool(rng_pop.random() < wo_p)

        # kyc_verified, consent_given
        kyc_verified = bool(rng_pop.random() < kyc_p)
        consent_given = bool(rng_pop.random() < consent_p)

        # requested_amount
        mult = rng_pop.uniform(req_mul_min, req_mul_max)
        raw_req = monthly_net_income * mult
        # Round to amount_step half-up
        stepped = int(Decimal(str(raw_req / amount_step)).to_integral_value(rounding=ROUND_HALF_UP)) * amount_step
        requested_amount = min(max(stepped, min_amount), max_amount)

        # requested_tenure_months
        requested_tenure_months = int(rng_pop.choice(tenure_choices))

        # Simulated outcome
        if sim_enabled:
            score_eff = (credit_score if credit_score is not None else 700) - 700
            foir_eff = (
                float(monthly_obligations) / float(monthly_net_income)
                if monthly_net_income > 0
                else 0.0
            )
            delinq_eff = 1.0 if severe_delinquency_36m else 0.0
            logit = (
                sim_intercept
                + sim_score_coef * score_eff
                + sim_foir_coef * foir_eff
                + sim_delinq_coef * delinq_eff
            )
            prob_def = 1.0 / (1.0 + np.exp(-logit))
            sim_default = int(rng_sim.random() < prob_def)
        else:
            sim_default = 0

        population_rows.append(
            {
                "applicant_id": applicant_id,
                "age": age,
                "employment_type": employment_type,
                "employment_months": employment_months,
                "monthly_net_income": monthly_net_income,
                "monthly_obligations": monthly_obligations,
                "credit_score": credit_score,
                "enquiries_6m": enquiries_6m,
                "severe_delinquency_36m": severe_delinquency_36m,
                "written_off": written_off,
                "kyc_verified": kyc_verified,
                "consent_given": consent_given,
                "requested_amount": requested_amount,
                "requested_tenure_months": requested_tenure_months,
                "region_tier": region_tier,
                "obligations_source": obligations_source,
                "sim_default": sim_default,
            }
        )

        protected_rows.append(
            {
                "applicant_id": applicant_id,
                "gender": gender,
                "region_tier": region_tier,
                "age_band": age_band,
            }
        )

    POP_COLUMNS = [
        "applicant_id",
        "age",
        "employment_type",
        "employment_months",
        "monthly_net_income",
        "monthly_obligations",
        "credit_score",
        "enquiries_6m",
        "severe_delinquency_36m",
        "written_off",
        "kyc_verified",
        "consent_given",
        "requested_amount",
        "requested_tenure_months",
        "region_tier",
        "obligations_source",
        "sim_default",
    ]
    pop_df = pd.DataFrame(population_rows, columns=POP_COLUMNS)
    pop_df["credit_score"] = pop_df["credit_score"].astype("Int64")
    prot_df = pd.DataFrame(protected_rows)

    # Validate against Phase 1 validator
    from src.facts.fact_builder import validate_input  # noqa: PLC0415

    for _, row in pop_df.iterrows():
        input_dict = {
            col: (None if pd.isna(row[col]) else row[col])
            for col in POP_COLUMNS
            if col not in ("obligations_source", "sim_default")
        }
        errs = validate_input(input_dict)
        if errs:
            raise ValueError(f"D3 row validation failed for {row['applicant_id']}: {errs}")

    pop_out.parent.mkdir(parents=True, exist_ok=True)
    prot_out.parent.mkdir(parents=True, exist_ok=True)

    pop_df.to_csv(pop_out, index=False, lineterminator="\n")
    prot_df.to_csv(prot_out, index=False, lineterminator="\n")

    for p in (pop_out, prot_out):
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        print(f"SHA-256 {p}: {digest}")

    return pop_df, prot_df


def main() -> None:
    """CLI for generating D3 population."""
    parser = argparse.ArgumentParser(description="Generate D3 synthetic population.")
    parser.add_argument("--size", type=int, default=None, help="Population size.")
    parser.add_argument("--seed", type=int, default=None, help="Master seed override.")
    parser.add_argument("--bias", action="store_true", help="Enable bias mode.")
    parser.add_argument("--out-population", type=str, default=None, help="Population output path.")
    parser.add_argument("--out-protected", type=str, default=None, help="Protected output path.")
    args = parser.parse_args()

    bias = True if args.bias else None
    generate_d3(
        size=args.size,
        master_seed=args.seed,
        bias_enabled=bias,
        out_population_path=args.out_population,
        out_protected_path=args.out_protected,
    )


if __name__ == "__main__":
    main()
