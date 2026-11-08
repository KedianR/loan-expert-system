"""
Spike S1: Python + SWI-Prolog integration test.

This file is a throwaway toy. It is NEVER used by the product.
It stays under spikes/s1/ and is not imported by the engine.

Purpose: verify that SWI-Prolog can be called from Python, that a toy
Prolog file can be loaded, and that decisions + fired-rule lists can be
returned as structured data, within the 1-second performance target.
Measures two ways for 1,000 decisions:
1. Fresh swipl process per decision
2. One persistent swipl process answering queries over stdin/stdout

Implements: WP-02, ADR-001 risk spike
"""

from __future__ import annotations

import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TOY_PROLOG_FILE = Path(__file__).parent / "toy_rules.pl"

DEFAULT_SWIPL_PATHS = [
    Path(r"C:\Program Files\swipl\bin\swipl.exe"),
    Path(r"C:\Program Files (x86)\swipl\bin\swipl.exe"),
]


def resolve_swipl() -> str | None:
    """Find swipl executable in PATH or standard install locations."""
    which_path = shutil.which("swipl")
    if which_path:
        return which_path
    for p in DEFAULT_SWIPL_PATHS:
        if p.exists():
            return str(p)
    return None


def check_swipl() -> tuple[bool, str, str | None]:
    """
    Check whether SWI-Prolog is installed and executable.
    Returns (available, version_or_error_message, swipl_path).
    """
    swipl = resolve_swipl()
    if swipl is None:
        return False, "swipl not found in PATH or standard install paths", None
    try:
        result = subprocess.run(
            [swipl, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False, f"swipl --version exited with {result.returncode}: {result.stderr.strip()}", swipl
        version_line = (result.stdout + result.stderr).strip().splitlines()[0]
        return True, version_line, swipl
    except OSError as exc:
        return False, f"OSError executing {swipl}: {exc}", swipl
    except subprocess.TimeoutExpired as exc:
        return False, f"Timeout checking swipl version: {exc}", swipl


def evaluate_toy_application_fresh(swipl: str, applicant_data: dict) -> dict | None:
    """
    Evaluate one toy application using a fresh swipl process.
    Returns a dict with 'decision' and 'fired_rules', or None on failure.
    """
    score = applicant_data.get("credit_score", 700)
    income = applicant_data.get("monthly_income", 25000)
    min_score = applicant_data.get("min_score", 650)
    min_income = applicant_data.get("min_income", 15000)

    toy_rules_prolog_path = str(TOY_PROLOG_FILE.resolve()).replace("\\", "/")

    goal = (
        f"use_module(library(http/json)), ['{toy_rules_prolog_path}'], "
        f"findall(Rule, fired_rule({score}, {income}, {min_score}, {min_income}, Rule), Fired), "
        f"(Fired = [] -> Decision = eligible ; Decision = ineligible), "
        f"json_write(current_output, json([decision=Decision, fired_rules=Fired])), nl, halt."
    )

    try:
        proc = subprocess.run(
            [swipl, "-q", "-g", goal, "-t", "halt"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = proc.stdout.strip()
        if not output:
            return None
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None


class PersistentPrologSession:
    """Manages a single persistent swipl process answering queries via stdin/stdout."""

    def __init__(self, swipl: str, rule_file: Path):
        self.swipl = swipl
        self.rule_file = rule_file
        self.proc: subprocess.Popen | None = None
        self.server_path: str | None = None

    def start(self) -> None:
        toy_rules_path = str(self.rule_file.resolve()).replace("\\", "/")
        server_script = f"""
:- use_module(library(lists)).
:- use_module(library(http/json)).
:- ['{toy_rules_path}'].

server :-
    read_line_to_string(current_input, Line),
    (   Line == end_of_file
    ->  halt
    ;   (   term_string(eval(Score, Income, MinScore, MinIncome), Line)
        ->  findall(Rule, fired_rule(Score, Income, MinScore, MinIncome, Rule), Fired),
            (   Fired = [] -> Decision = eligible ; Decision = ineligible ),
            json_write(current_output, json([decision=Decision, fired_rules=Fired])),
            nl,
            flush_output
        ;   format('{{\"error\": \"invalid_input\"}}~n', []),
            flush_output
        ),
        server
    ).
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pl", delete=False, encoding="utf-8"
        ) as f:
            f.write(server_script)
            self.server_path = f.name

        self.proc = subprocess.Popen(
            [self.swipl, "-q", "-s", self.server_path, "-g", "server", "-t", "halt"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

    def evaluate(self, applicant_data: dict) -> dict | None:
        if self.proc is None or self.proc.poll() is not None:
            return None
        score = applicant_data.get("credit_score", 700)
        income = applicant_data.get("monthly_income", 25000)
        min_score = applicant_data.get("min_score", 650)
        min_income = applicant_data.get("min_income", 15000)

        query = f"eval({score}, {income}, {min_score}, {min_income}).\n"
        self.proc.stdin.write(query)
        self.proc.stdin.flush()

        resp_line = self.proc.stdout.readline().strip()
        if not resp_line:
            return None
        return json.loads(resp_line)

    def close(self) -> None:
        if self.proc is not None:
            try:
                self.proc.stdin.close()
                self.proc.terminate()
                self.proc.wait(timeout=2)
            except Exception:
                pass
            self.proc = None
        if self.server_path is not None:
            Path(self.server_path).unlink(missing_ok=True)
            self.server_path = None


def compute_stats_ms(latencies_ms: list[float]) -> dict:
    """Compute mean, median, and 95th percentile latency in milliseconds."""
    latencies_sorted = sorted(latencies_ms)
    n = len(latencies_sorted)
    # 95th percentile using nearest rank
    idx_p95 = min(int(round(0.95 * n)), n - 1)
    return {
        "count": n,
        "mean_ms": round(statistics.mean(latencies_ms), 3),
        "median_ms": round(statistics.median(latencies_ms), 3),
        "p95_ms": round(latencies_sorted[idx_p95], 3),
    }


def run_spike() -> dict:
    """
    Run the full S1 spike. Returns a results dict for the report.
    """
    results: dict = {}

    # 1. Check SWI-Prolog availability and executable status
    available, version_info, swipl_path = check_swipl()
    results["swipl_path"] = swipl_path
    results["swipl_available"] = available
    results["swipl_version"] = version_info

    if not available:
        results["outcome"] = f"FAILED: {version_info}"
        results["recommendation"] = (
            "SWI-Prolog is installed but failed to execute (or is not found). "
            "Ensure the 64-bit x64 build of SWI-Prolog is installed on this x64 machine. "
            "See docs/reports/spike-s1.md."
        )
        return results

    # 2. Verify toy Prolog file exists
    if not TOY_PROLOG_FILE.exists():
        results["outcome"] = f"FAILED: toy_rules.pl not found at {TOY_PROLOG_FILE}"
        return results

    # 3. Evaluate one toy application (firing k_score and k_income)
    test_app = {"credit_score": 600, "monthly_income": 10000, "min_score": 650, "min_income": 15000}
    decision_result = evaluate_toy_application_fresh(swipl_path, test_app)
    results["single_decision_fresh"] = decision_result

    if decision_result is None or "decision" not in decision_result or "fired_rules" not in decision_result:
        results["outcome"] = "FAILED: could not get valid decision and fired_rules from SWI-Prolog"
        return results

    # 4. Measure Way 1: Fresh swipl process per decision (100 runs)
    n_fresh = 100
    fresh_latencies_ms: list[float] = []
    for _ in range(n_fresh):
        t0 = time.perf_counter()
        res = evaluate_toy_application_fresh(swipl_path, test_app)
        t1 = time.perf_counter()
        if res is None:
            results["outcome"] = "FAILED: fresh process evaluation failed mid-run"
            return results
        fresh_latencies_ms.append((t1 - t0) * 1000.0)

    results["fresh_process_stats"] = compute_stats_ms(fresh_latencies_ms)

    # 5. Measure Way 2: Persistent swipl process answering queries (1,000 runs)
    n_persistent = 1000
    persistent_session = PersistentPrologSession(swipl_path, TOY_PROLOG_FILE)
    persistent_latencies_ms: list[float] = []
    try:
        persistent_session.start()
        # Verify single decision from persistent process
        res_p = persistent_session.evaluate(test_app)
        results["single_decision_persistent"] = res_p
        if res_p is None or "decision" not in res_p or "fired_rules" not in res_p:
            results["outcome"] = "FAILED: persistent process failed to evaluate"
            return results

        for _ in range(n_persistent):
            t0 = time.perf_counter()
            res = persistent_session.evaluate(test_app)
            t1 = time.perf_counter()
            if res is None:
                results["outcome"] = "FAILED: persistent process query failed mid-run"
                return results
            persistent_latencies_ms.append((t1 - t0) * 1000.0)
    finally:
        persistent_session.close()

    results["persistent_process_stats"] = compute_stats_ms(persistent_latencies_ms)

    results["outcome"] = "OK"
    results["recommendation"] = (
        f"SWI-Prolog integration works. Fresh process: "
        f"mean={results['fresh_process_stats']['mean_ms']}ms, "
        f"median={results['fresh_process_stats']['median_ms']}ms, "
        f"p95={results['fresh_process_stats']['p95_ms']}ms. "
        f"Persistent process: "
        f"mean={results['persistent_process_stats']['mean_ms']}ms, "
        f"median={results['persistent_process_stats']['median_ms']}ms, "
        f"p95={results['persistent_process_stats']['p95_ms']}ms."
    )

    return results


if __name__ == "__main__":
    r = run_spike()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r.get("outcome") == "OK" else 1)


