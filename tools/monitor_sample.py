"""Monitor sample: decision mix and reason-code table from d3 decisions (WP-21).

Per docs/monitoring-plan.md §2: brief summary of the decision mix and
top reason codes from data/decisions/d3_decisions.csv.

Usage: make monitor-sample
       python tools/monitor_sample.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
D3_DECISIONS = REPO_ROOT / "data" / "decisions" / "d3_decisions.csv"
OUTPUT = REPO_ROOT / "reports" / "monitor_sample.md"


def main() -> None:
    if not D3_DECISIONS.exists():
        print(f"D3 decisions not found at {D3_DECISIONS}. Run 'make decide-d3' first.")
        return

    df = pd.read_csv(D3_DECISIONS)
    total = len(df)

    # Decision mix
    dec_counts = df["decision"].value_counts()
    dec_pct = (dec_counts / total * 100).round(1)

    # Reason codes (split semicolon-separated)
    all_codes = []
    for codes_str in df["reason_codes"].dropna():
        all_codes.extend(str(codes_str).split(";"))
    all_codes = [c.strip() for c in all_codes if c.strip()]

    code_counts = pd.Series(all_codes).value_counts().head(15)

    lines = [
        "# Monitor Sample — D3 Decision Mix",
        "",
        f"**Source:** `data/decisions/d3_decisions.csv`  |  **Total rows:** {total}",
        "",
        "## Decision Mix",
        "",
        "| Decision | Count | % |",
        "|---|---|---|",
    ]
    for dec, count in dec_counts.items():
        lines.append(f"| {dec} | {count} | {dec_pct[dec]}% |")

    lines += [
        "",
        "## Top 15 Reason Codes",
        "",
        "| Reason Code | Count |",
        "|---|---|",
    ]
    for code, count in code_counts.items():
        lines.append(f"| {code} | {count} |")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Monitor sample written to {OUTPUT}")
    print(f"Total rows: {total}")
    print(dec_counts.to_string())


if __name__ == "__main__":
    main()
