"""
Oracle comparison tool: compares engine output on D1 against data/d1/oracle_expected.json.

Implements: WP-16a, docs/08-datasets.md §4, docs/decision-tables.md
Writes diff report to data/d1/oracle_diff.md.
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.engine.engine import decide
from src.engine.rule_loader import load_rules

D1_CASES_PATH = Path("data/d1/d1_cases.json")
ORACLE_EXPECTED_PATH = Path("data/d1/oracle_expected.json")
DIFF_REPORT_PATH = Path("data/d1/oracle_diff.md")


def run_oracle_diff() -> int:
    if not ORACLE_EXPECTED_PATH.exists():
        msg = (
            f"Oracle expected file '{ORACLE_EXPECTED_PATH}' does not exist yet.\n"
            "The reference oracle must be built and run in a separate oracle session.\n"
        )
        print(msg)
        DIFF_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        DIFF_REPORT_PATH.write_text(
            f"# Oracle Comparison Diff\n\n{msg}\nStatus: WAITING_FOR_ORACLE_SESSION\n",
            encoding="utf-8",
        )
        return 0

    if not D1_CASES_PATH.exists():
        print(f"Error: D1 cases file '{D1_CASES_PATH}' not found.")
        return 1

    rule_set = load_rules(Path("rules"), Path("params/params.toml"))
    if not rule_set:
        print("Error: Could not load rule set.")
        return 1

    d1_cases = json.loads(D1_CASES_PATH.read_text(encoding="utf-8")).get("cases", [])
    oracle_expected = json.loads(ORACLE_EXPECTED_PATH.read_text(encoding="utf-8")).get(
        "expected", {}
    )

    diffs: list[dict[str, Any]] = []

    for case in d1_cases:
        cid = case["case_id"]
        if cid not in oracle_expected:
            diffs.append(
                {
                    "case_id": cid,
                    "field": "missing_oracle_case",
                    "engine": "present",
                    "oracle": "missing",
                }
            )
            continue

        exp = oracle_expected[cid]
        act = decide(case["input"], rule_set)

        # 1. Decision
        if act["decision"] != exp.get("decision"):
            diffs.append(
                {
                    "case_id": cid,
                    "field": "decision",
                    "engine": act["decision"],
                    "oracle": exp.get("decision"),
                }
            )

        # 2. Reason codes
        if sorted(act.get("reason_codes", [])) != sorted(exp.get("reason_codes", [])):
            diffs.append(
                {
                    "case_id": cid,
                    "field": "reason_codes",
                    "engine": act.get("reason_codes", []),
                    "oracle": exp.get("reason_codes", []),
                }
            )

        # 3. Fired rules
        act_fired = sorted([s["rule_id"] for s in act["steps"] if s["status"] == "fired"])
        exp_fired = sorted(exp.get("fired_rules", []))
        if exp_fired and act_fired != exp_fired:
            diffs.append(
                {
                    "case_id": cid,
                    "field": "fired_rules",
                    "engine": act_fired,
                    "oracle": exp_fired,
                }
            )

        # 4. For eligible cases: band, recommended amount, binding limit, indicative rate, EMI, fee, APR
        if act["decision"] == "eligible" and exp.get("decision") == "eligible":
            act_offer = act.get("offer", {})
            exp_offer = exp.get("offer", {})

            # Band
            if act_offer.get("band") != exp_offer.get("band"):
                diffs.append(
                    {
                        "case_id": cid,
                        "field": "band",
                        "engine": act_offer.get("band"),
                        "oracle": exp_offer.get("band"),
                    }
                )

            # Amount
            if act_offer.get("amount") != exp_offer.get("amount"):
                diffs.append(
                    {
                        "case_id": cid,
                        "field": "amount",
                        "engine": act_offer.get("amount"),
                        "oracle": exp_offer.get("amount"),
                    }
                )

            # Binding limit
            act_limit = act.get("derived", {}).get("binding_limit")
            exp_limit = exp.get("binding_limit")
            if exp_limit and act_limit != exp_limit:
                diffs.append(
                    {
                        "case_id": cid,
                        "field": "binding_limit",
                        "engine": act_limit,
                        "oracle": exp_limit,
                    }
                )

            # Indicative rate
            if act_offer.get("indicative_rate") != exp_offer.get("indicative_rate"):
                diffs.append(
                    {
                        "case_id": cid,
                        "field": "indicative_rate",
                        "engine": act_offer.get("indicative_rate"),
                        "oracle": exp_offer.get("indicative_rate"),
                    }
                )

            # EMI
            if act_offer.get("emi") != exp_offer.get("emi"):
                diffs.append(
                    {
                        "case_id": cid,
                        "field": "emi",
                        "engine": act_offer.get("emi"),
                        "oracle": exp_offer.get("emi"),
                    }
                )

            # Fee
            if act_offer.get("fee") != exp_offer.get("fee"):
                diffs.append(
                    {
                        "case_id": cid,
                        "field": "fee",
                        "engine": act_offer.get("fee"),
                        "oracle": exp_offer.get("fee"),
                    }
                )

            # APR (within 0.01 tolerance)
            act_apr = Decimal(act_offer.get("apr", "0"))
            exp_apr = Decimal(exp_offer.get("apr", "0"))
            if abs(act_apr - exp_apr) > Decimal("0.01"):
                diffs.append(
                    {
                        "case_id": cid,
                        "field": "apr",
                        "engine": str(act_apr),
                        "oracle": str(exp_apr),
                    }
                )

    # Write diff report
    report_lines = [
        "# Oracle Comparison Diff Report",
        "",
        f"Compared {len(d1_cases)} D1 cases against oracle expectations.",
        f"Total differences found: {len(diffs)}",
        "",
    ]
    if not diffs:
        report_lines.append("Status: MATCH (0 differences).")
    else:
        report_lines.append("## Differences")
        report_lines.append("| Case ID | Field | Engine Output | Oracle Expected |")
        report_lines.append("| --- | --- | --- | --- |")
        for d in diffs:
            report_lines.append(
                f"| {d['case_id']} | {d['field']} | `{d['engine']}` | `{d['oracle']}` |"
            )

    DIFF_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DIFF_REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Diff report written to {DIFF_REPORT_PATH} ({len(diffs)} differences).")
    return 0 if len(diffs) == 0 else 1


if __name__ == "__main__":
    sys.exit(run_oracle_diff())
