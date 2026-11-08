"""
Prolog code generator for the loan expert system.

Implements: FR-17, FR-18, WP-06, ADR-001
Spec: docs/04-predicates-and-facts.md §4, docs/09-file-formats.md §4

Generates deterministic SWI-Prolog clauses from the rule set into build/rules.pl.
Output is build output (never edited by hand, not included in rule-set hash).
"""

from __future__ import annotations

from pathlib import Path

from src.engine.rule_loader import RuleDefinition, RuleSet


class PrologGenerator:
    """Generates deterministic Prolog code from a loaded RuleSet."""

    def __init__(self, rule_set: RuleSet):
        self.rule_set = rule_set

    def generate(self) -> str:
        lines: list[str] = [
            "% Auto-generated rules for loan expert system. DO NOT EDIT BY HAND.",
            ":- use_module(library(lists)).",
            ":- use_module(library(http/json)).",
            "",
            ":- discontiguous fired/4.",
            ":- discontiguous band/2.",
            "",
            "% --- Required fields for V01 ---",
        ]

        # 1. required_field/1
        req_fields = [
            f["name"]
            for f in self.rule_set.fields.values()
            if f.get("required") and f.get("kind") == "input"
        ]
        # Map requested_tenure_months to requested_tenure if needed, but in facts it's field name
        # In fact schema: required_field(F) :- member(F, [age, employment_type, employment_months, ...])
        lines.append(f"required_field(F) :- member(F, [{', '.join(sorted(req_fields))}]).")
        lines.append("")

        # 2. Parameters: param(Name, Value)
        lines.append("% --- Policy parameters ---")
        for k in sorted(self.rule_set.params.keys()):
            val = self.rule_set.params[k]
            if isinstance(val, bool):
                val_str = "true" if val else "false"
            elif isinstance(val, int):
                val_str = str(val)
            else:
                val_str = f"'{val}'"
            lines.append(f"param({k}, {val_str}).")
        lines.append("")

        # 3. Bands: band_param(Band, MinScore, MaxFoir, IndicativeRate, PostLoanFoirCap)
        lines.append("% --- Pricing bands ---")
        for b in sorted(self.rule_set.bands, key=lambda x: x["id"]):
            b_id = b["id"].lower()
            min_score = b["min_score"]
            max_foir = f"'{b['max_foir']}'"
            ind_rate = f"'{b['indicative_rate']}'"
            cap = f"'{b['post_loan_foir_cap']}'"
            lines.append(f"band_param({b_id}, {min_score}, {max_foir}, {ind_rate}, {cap}).")
        lines.append("")

        # 4. A04 reason code mapping: a04_reason_code(BindingLimit, ReasonCode)
        lines.append("% --- A04 Reason code mappings ---")
        a04_rule = self.rule_set.rules.get("A04")
        if a04_rule and isinstance(a04_rule.reason_code, dict):
            for k, code in sorted(a04_rule.reason_code.items()):
                if k == "by":
                    continue
                lines.append(f"a04_reason_code({k}, {code.lower()}).")
        lines.append("")

        # 5. Rule metadata
        lines.append("% --- Rule metadata ---")
        for order, (r_id, r_def) in enumerate(self.rule_set.rules.items(), start=1):
            lines.append(f"rule_layer({r_def.id.lower()}, {r_def.layer}).")
        lines.append("")
        for order, (r_id, r_def) in enumerate(self.rule_set.rules.items(), start=1):
            lines.append(f"rule_order({r_def.id.lower()}, {order}).")
        lines.append("")
        for order, (r_id, r_def) in enumerate(self.rule_set.rules.items(), start=1):
            lines.append(f"rule_status({r_def.id.lower()}, {r_def.status}).")
        lines.append("")

        # 6. Blocking definition
        lines.append("% --- Blocking outcome check ---")
        lines.append("blocked_before_amount(A) :-")
        lines.append("    fired(A, Id, Out, _),")
        lines.append("    memberchk(Out, [ineligible, refer]),")
        lines.append("    rule_layer(Id, L),")
        lines.append("    memberchk(L, [validation, knockout, referral, eligibility]).")
        lines.append("")

        # 7. Rules clauses
        lines.append("% --- Active rule clauses ---")
        for r_id, r_def in self.rule_set.rules.items():
            if r_def.status != "active":
                continue
            clause = self._generate_rule_clause(r_def)
            if clause:
                lines.append(clause)
                lines.append("")

        # 8. Decision precedence
        lines.append("% --- Final decision precedence ---")
        lines.append("decision(A, ineligible) :- fired(A, _, ineligible, _), !.")
        lines.append("decision(A, refer)      :- fired(A, _, refer, _), !.")
        lines.append("decision(A, eligible)   :- band(A, _), recommended_amount(A, _), !.")
        lines.append("decision(_, refer).     % CP-8.1 default: no rule applied")
        lines.append("")

        return "\n".join(lines)

    def _generate_rule_clause(self, r: RuleDefinition) -> str:
        if r.id == "V01":
            return (
                "fired(A, v01, refer, incomplete_application) :-\n"
                "    findall(F, (required_field(F), unknown(A, F)), [_|_])."
            )
        elif r.id == "V02":
            return (
                "fired(A, v02, ineligible, consent_not_given) :-\n"
                "    \\+ unknown(A, consent_given),\n"
                "    consent_given(A, false)."
            )
        elif r.id == "V03":
            return (
                "fired(A, v03, ineligible, amount_outside_product_limits) :-\n"
                "    \\+ unknown(A, requested_amount),\n"
                "    requested_amount(A, Rs), param(min_amount, Min), param(max_amount, Max),\n"
                "    (Rs < Min ; Rs > Max)."
            )
        elif r.id == "V04":
            return (
                "fired(A, v04, ineligible, tenure_outside_product_limits) :-\n"
                "    \\+ unknown(A, requested_tenure_months),\n"
                "    requested_tenure(A, N), param(min_tenure_months, Min), param(max_tenure_months, Max),\n"
                "    (N < Min ; N > Max)."
            )
        elif r.id == "K01":
            return (
                "fired(A, k01, ineligible, legal_capacity_not_met) :-\n"
                "    \\+ unknown(A, age),\n"
                "    age(A, Y), param(min_age, Min), Y < Min."
            )
        elif r.id == "K02":
            return (
                "fired(A, k02, ineligible, kyc_not_verified) :-\n"
                "    \\+ unknown(A, kyc_verified),\n"
                "    kyc_verified(A, false)."
            )
        elif r.id == "K03":
            return (
                "fired(A, k03, ineligible, adverse_repayment_history) :-\n"
                "    \\+ unknown(A, severe_delinquency_36m),\n"
                "    \\+ unknown(A, written_off),\n"
                "    (severe_delinquency_36m(A, true) ; written_off(A, true))."
            )
        elif r.id == "K04":
            # Must match exact example in docs/04 §4 and docs/09 §4
            return (
                "fired(A, k04, ineligible, credit_score_below_minimum) :-\n"
                "    \\+ unknown(A, credit_score),\n"
                "    credit_score(A, S), param(min_credit_score, Min), S < Min."
            )
        elif r.id == "K05":
            return (
                "fired(A, k05, ineligible, income_below_minimum) :-\n"
                "    \\+ unknown(A, monthly_net_income),\n"
                "    monthly_net_income(A, I), param(min_monthly_income, Min), I < Min."
            )
        elif r.id == "K06":
            return (
                "fired(A, k06, ineligible, employment_tenure_too_short) :-\n"
                "    \\+ unknown(A, employment_type),\n"
                "    \\+ unknown(A, employment_months),\n"
                "    employment_type(A, Type), employment_months(A, M),\n"
                "    (   Type == salaried,\n"
                "        param(min_employment_months_salaried, MinS),\n"
                "        M < MinS\n"
                "    ;   Type == self_employed,\n"
                "        param(min_employment_months_self_employed, MinSE),\n"
                "        M < MinSE\n"
                "    )."
            )
        elif r.id == "R01":
            return "fired(A, r01, refer, no_credit_history) :-\n    unknown(A, credit_score)."
        elif r.id == "R02":
            return (
                "fired(A, r02, refer, high_recent_enquiries) :-\n"
                "    \\+ unknown(A, enquiries_6m),\n"
                "    enquiries_6m(A, N), param(max_enquiries_6m, Max), N > Max."
            )
        elif r.id == "R03":
            return (
                "fired(A, r03, refer, employment_type_requires_review) :-\n"
                "    \\+ unknown(A, employment_type),\n"
                "    employment_type(A, other)."
            )
        elif r.id == "E01":
            return (
                "fired(A, e01, ineligible, high_existing_obligations) :-\n"
                "    \\+ unknown(A, existing_foir),\n"
                "    existing_foir(A, F), param(max_existing_foir, Max), F > Max."
            )
        elif r.id == "E02":
            return (
                "band(A, B) :-\n"
                "    \\+ blocked_before_amount(A),\n"
                "    \\+ unknown(A, credit_score),\n"
                "    \\+ unknown(A, existing_foir),\n"
                "    member(B, [a, b, c]),\n"
                "    band_param(B, MinScore, MaxFoir, _Rate, _Cap),\n"
                "    credit_score(A, S), existing_foir(A, F),\n"
                "    S >= MinScore, F =< MaxFoir, !."
            )
        elif r.id == "A03":
            return (
                "fired(A, a03, ineligible, insufficient_repayment_capacity) :-\n"
                "    \\+ blocked_before_amount(A),\n"
                "    \\+ unknown(A, recommended_amount),\n"
                "    recommended_amount(A, P), param(min_amount, Min), P < Min."
            )
        elif r.id == "A04":
            return (
                "fired(A, a04, reduced_offer, Reason) :-\n"
                "    \\+ blocked_before_amount(A),\n"
                "    \\+ unknown(A, recommended_amount),\n"
                "    \\+ unknown(A, requested_amount),\n"
                "    recommended_amount(A, P), param(amount_step, Step), requested_amount(A, Q),\n"
                "    P + Step =< Q,\n"
                "    binding_limit(A, Limit),\n"
                "    a04_reason_code(Limit, Reason)."
            )
        elif r.outcome == "derive":
            return f"% {r.id} ({r.description}) derived via calc module."
        return ""


def generate_prolog(rule_set: RuleSet, output_path: Path) -> str:
    generator = PrologGenerator(rule_set)
    content = generator.generate()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return content


if __name__ == "__main__":
    import sys

    from src.engine.rule_loader import load_rules

    r_dir = Path("rules")
    p_path = Path("params/params.toml")
    rs = load_rules(r_dir, p_path)
    if not rs:
        sys.exit(1)
    out_file = Path("build/rules.pl")
    generate_prolog(rs, out_file)
    print(f"Prolog generated successfully: {out_file}")
