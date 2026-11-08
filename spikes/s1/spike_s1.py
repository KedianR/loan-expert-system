"""
Spike S1: Python + SWI-Prolog integration test.

This file is a throwaway toy. It is NEVER used by the product.
It stays under spikes/s1/ and is not imported by the engine.

Purpose: verify that SWI-Prolog can be called from Python, that a toy
Prolog file can be loaded, and that decisions + fired-rule lists can be
returned as structured data, within the 1-second performance target.

Implements: WP-02, ADR-001 risk spike
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TOY_PROLOG_FILE = Path(__file__).parent / "toy_rules.pl"


def check_swipl() -> tuple[bool, str]:
    """
    Check whether SWI-Prolog is installed.
    Returns (available, version_string_or_error_message).
    """
    swipl = shutil.which("swipl")
    if swipl is None:
        return False, "swipl not found in PATH"
    try:
        result = subprocess.run(
            [swipl, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version_line = (result.stdout + result.stderr).strip().splitlines()[0]
        return True, version_line
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return False, str(exc)


def evaluate_toy_application(applicant_data: dict) -> dict | None:
    """
    Call swipl with the toy rule file and evaluate one toy application.

    Returns a dict with 'decision' and 'fired_rules', or None on failure.
    This uses subprocess + JSON over stdin/stdout as the Python–Prolog bridge.
    """
    swipl = shutil.which("swipl")
    if swipl is None:
        return None

    # Build a Prolog goal that:
    # 1. Loads the toy file.
    # 2. Asserts the applicant facts.
    # 3. Finds all fired rules.
    # 4. Determines the decision.
    # 5. Prints JSON to stdout.
    score = applicant_data.get("credit_score", 700)
    income = applicant_data.get("monthly_income", 25000)
    min_score = applicant_data.get("min_score", 650)
    min_income = applicant_data.get("min_income", 15000)

    # Inline Prolog script so we do not need file I/O for the goal
    prolog_goal = f"""
:- use_module(library(lists)).
:- ['spikes/s1/toy_rules.pl'].

:- 
    Score = {score},
    Income = {income},
    MinScore = {min_score},
    MinIncome = {min_income},
    findall(Rule, fired_rule(Score, Income, MinScore, MinIncome, Rule), Fired),
    (   Fired = [] 
    ->  Decision = eligible 
    ;   Decision = ineligible
    ),
    format('{{\"decision\": \"~w\", \"fired_rules\": ~w}}~n', [Decision, Fired]),
    halt.
"""
    # Write goal to a temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".pl", delete=False, encoding="utf-8"
    ) as f:
        f.write(prolog_goal)
        goal_path = f.name

    try:
        proc = subprocess.run(
            [swipl, "--quiet", goal_path],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = proc.stdout.strip()
        if not output:
            return None
        # Parse the first JSON line
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("{"):
                data = json.loads(line)
                return data
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None
    finally:
        Path(goal_path).unlink(missing_ok=True)


def run_spike() -> dict:
    """
    Run the full S1 spike. Returns a results dict for the report.
    """
    results: dict = {}

    # 1. Check SWI-Prolog availability
    available, version_info = check_swipl()
    results["swipl_available"] = available
    results["swipl_version"] = version_info

    if not available:
        results["outcome"] = "FAILED: SWI-Prolog not installed"
        results["recommendation"] = (
            "SWI-Prolog is not installed. Per ADR-001, the owner must decide "
            "whether to install it or fall back to the pure-Python evaluator. "
            "See docs/open-questions.md OQ-001."
        )
        return results

    # 2. Verify toy Prolog file exists
    if not TOY_PROLOG_FILE.exists():
        results["outcome"] = f"FAILED: toy_rules.pl not found at {TOY_PROLOG_FILE}"
        return results

    # 3. Evaluate one toy application
    test_app = {"credit_score": 700, "monthly_income": 25000, "min_score": 650, "min_income": 15000}
    decision_result = evaluate_toy_application(test_app)
    results["single_decision"] = decision_result

    if decision_result is None:
        results["outcome"] = "FAILED: could not get a decision from SWI-Prolog"
        return results

    # 4. Timing: 1,000 decisions
    n = 1000
    start = time.perf_counter()
    for _ in range(n):
        evaluate_toy_application(test_app)
    elapsed = time.perf_counter() - start

    results["timing_runs"] = n
    results["timing_total_s"] = round(elapsed, 3)
    results["timing_per_decision_ms"] = round(elapsed / n * 1000, 3)
    results["outcome"] = "OK"
    results["recommendation"] = (
        f"SWI-Prolog integration works. Each decision takes ~{results['timing_per_decision_ms']:.1f} ms "
        f"(subprocess overhead; a persistent process or Janus bridge would be faster)."
    )

    return results


if __name__ == "__main__":
    r = run_spike()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r.get("outcome") == "OK" else 1)

