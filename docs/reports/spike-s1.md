# Spike S1 Report: Python + SWI-Prolog Integration

**Date:** 2026-11-08
**Phase:** 0 (WP-02)
**Requirement:** ADR-001

## 1. Objective

Verify that SWI-Prolog can be called from Python, load a toy rule file, evaluate one toy application, and return the decision AND the list of fired rules as structured data. Run 1,000 decisions and record the time per decision.

## 2. Environment

- **OS:** Windows (win32)
- **Python:** 3.14.2 at `C:\Users\asus\AppData\Local\Python\pythoncore-3.14-64\python.exe`
- **SWI-Prolog (`swipl`):** **NOT INSTALLED**

Searches performed:
- `where.exe swipl` → not found
- `Get-ChildItem "C:\Program Files"` → no Prolog directory
- `Get-ChildItem "C:\Program Files (x86)"` → no Prolog directory
- `pip list | Select-String "janus|prolog"` → no packages found

## 3. What was tried

1. **Availability check.** `shutil.which("swipl")` returned `None`. The spike script (`spikes/s1/spike_s1.py`) exited with:

   ```json
   {
     "swipl_available": false,
     "swipl_version": "swipl not found in PATH",
     "outcome": "FAILED: SWI-Prolog not installed",
     "recommendation": "SWI-Prolog is not installed. Per ADR-001, the owner must decide whether to install it or fall back to the pure-Python evaluator. See docs/open-questions.md OQ-001."
   }
   ```

2. **Toy Prolog file.** Written to `spikes/s1/toy_rules.pl`. Defines two knockout rules (`k_score` and `k_income`) and a `fired_rule/5` predicate. This file is a throwaway toy and is never used by the product (AGENTS.md Hard Rule 3).

3. **Python bridge script.** Written to `spikes/s1/spike_s1.py`. Would call `swipl` via subprocess, pass a goal that loads the toy file, runs `findall/3` to collect fired rules, and prints JSON to stdout. Could not run because `swipl` is absent.

4. **Timing.** Not performed. Requires a working SWI-Prolog installation.

## 4. What worked

- The spike script itself runs cleanly and reports the failure in structured form.
- The toy Prolog file and the bridge approach are ready to test once SWI-Prolog is installed.

## 5. What did not work

- SWI-Prolog is not installed on this machine. No timing or integration test was possible.

## 6. Recommendation

**Owner decision needed (OQ-001):** Per ADR-001, the options are:

| Option | Action |
| --- | --- |
| **A. Install SWI-Prolog** | Install SWI-Prolog, add `swipl` to PATH, re-run this spike. The toy file and bridge script are ready. Estimated time: 15 minutes for install + 10 minutes to run the spike. |
| **B. Fall back to pure-Python evaluator** | Use a pure-Python rule engine that reads the same rule files and produces the same trace format, as described in ADR-001. No Prolog needed. The rest of the project (loader, hash, params, tests) is unaffected. |

Both options produce the same trace format and the same decisions, so the choice does not affect Phases 1–5.

If SWI-Prolog is installed and the spike succeeds, the expected approach is:
- **Phase 0–1:** subprocess with JSON (simple, no extra dependency).
- **Phase 2+:** evaluate `janus-swi` (the official Python–SWI bridge) for better performance (no subprocess overhead). If `janus-swi` works, expect sub-millisecond per decision. If not, subprocess calls at ~5–20 ms each are still well within the 1-second NFR-06 target.

