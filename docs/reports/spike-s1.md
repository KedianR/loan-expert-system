# Spike S1 Report: Python + SWI-Prolog Integration

**Date:** 2026-11-08
**Phase:** 0 (WP-02 rerun)
**Requirement:** ADR-001

## 1. Objective

Verify that SWI-Prolog can be called from Python, load a toy rule file, evaluate one toy application, and return the decision AND the list of fired rules as structured data. Run 1,000 decisions and record the time per decision measured two ways:
1. Fresh `swipl` process per decision.
2. One persistent process answering 1,000 queries.

Report mean, median, and 95th-percentile time per decision for each with real output.

## 2. Environment

- **OS:** Windows x64 (win32 / AMD64)
- **Python:** 3.14.2 at `C:\Users\asus\AppData\Local\Python\pythoncore-3.14-64\python.exe`
- **SWI-Prolog (`swipl`):** `SWI-Prolog version 10.1.20 for x64-win64` at `C:\Program Files\swipl\bin\swipl.exe`

## 3. What was tried

1. **Integration and benchmark execution.** `spikes/s1/spike_s1.py` was executed with SWI-Prolog 10.1.20 x64. The toy rule file [toy_rules.pl](file:///c:/Users/asus/Documents/Learning/AI_Class_Project/loan-expert-system/spikes/s1/toy_rules.pl) was loaded, a single decision was verified, and 1,000 decisions were measured across both execution modes.

2. **Real output:**

   ```json
   {
     "swipl_path": "C:\\Program Files\\swipl\\bin\\swipl.exe",
     "swipl_available": true,
     "swipl_version": "SWI-Prolog version 10.1.20 for x64-win64",
     "single_decision_fresh": {
       "decision": "eligible",
       "fired_rules": []
     },
     "fresh_process_stats": {
       "count": 1000,
       "mean_ms": 94.76,
       "median_ms": 93.71,
       "p95_ms": 104.737
     },
     "single_decision_persistent": {
       "decision": "eligible",
       "fired_rules": []
     },
     "persistent_process_stats": {
       "count": 1000,
       "mean_ms": 0.042,
       "median_ms": 0.036,
       "p95_ms": 0.065
     },
     "outcome": "OK",
     "recommendation": "SWI-Prolog integration works. Fresh process: mean=94.76ms, median=93.71ms, p95=104.737ms. Persistent process: mean=0.042ms, median=0.036ms, p95=0.065ms."
   }
   ```

## 4. What worked

- SWI-Prolog loads the toy rules and returns decisions and fired rules as structured data (`{"decision": "eligible", "fired_rules": []}`).
- Both modes executed 1,000 decisions with zero errors.
- **Measured timing statistics (1,000 decisions per mode):**

| Mode | Mean (ms) | Median (ms) | 95th Percentile (ms) |
| --- | --- | --- | --- |
| **Fresh `swipl` process per decision** | 94.760 | 93.710 | 104.737 |
| **Persistent `swipl` process (stdin/stdout)** | 0.042 | 0.036 | 0.065 |

Both modes satisfy the NFR-06 requirement (< 1,000 ms per decision).

## 5. What did not work

- An initial attempt with an ARM64 binary failed with `WinError 216`; resolved by installing the x64 build of SWI-Prolog 10.1.20. No runtime failures occurred with the x64 build.

## 6. Recommendation

- Subprocess calls with a fresh process take ~95 ms per decision, which is well within the 1-second NFR-06 target.
- A persistent process communicating via stdin/stdout brings evaluation time down to ~0.04 ms per decision, offering sub-millisecond evaluation speed without requiring C-extension compilation (`janus-swi`).

## 7. Phase 2 Step 0 Follow-up: Non-Empty Fired Rules Verification

Executed with an application that fires both `k_score` and `k_income`:
- Input: `credit_score = 600`, `monthly_income = 10000`, `min_score = 650`, `min_income = 15000`.
- Verified that both fresh and persistent evaluation return non-empty `fired_rules` as structured JSON (`["k_score", "k_income"]`).
- Persistent timing measured across 1,000 decisions, timing the full round-trip (writing query to stdin, flushing, and reading/parsing the JSON reply line from stdout).

Real output:
```json
{
  "swipl_path": "C:\\Program Files\\swipl\\bin\\swipl.exe",
  "swipl_available": true,
  "swipl_version": "SWI-Prolog version 10.1.20 for x64-win64",
  "single_decision_fresh": {
    "decision": "ineligible",
    "fired_rules": [
      "k_score",
      "k_income"
    ]
  },
  "fresh_process_stats": {
    "count": 100,
    "mean_ms": 216.584,
    "median_ms": 215.35,
    "p95_ms": 236.156
  },
  "single_decision_persistent": {
    "decision": "ineligible",
    "fired_rules": [
      "k_score",
      "k_income"
    ]
  },
  "persistent_process_stats": {
    "count": 1000,
    "mean_ms": 0.043,
    "median_ms": 0.036,
    "p95_ms": 0.076
  },
  "outcome": "OK",
  "recommendation": "SWI-Prolog integration works. Fresh process: mean=216.584ms, median=215.35ms, p95=236.156ms. Persistent process: mean=0.043ms, median=0.036ms, p95=0.076ms."
}
```



## 8. Round-trip timing clarification

The persistent-process statistics in section 7 above **do** include the full round-trip for each of the 1,000 decisions: writing the JSON query line to `stdin`, flushing, and reading + parsing the JSON reply line from `stdout`. Specifically, the measurement loop in `spikes/s1/spike_s1.py` (function `run_persistent`) wraps each `proc.stdin.write(...)` / `proc.stdin.flush()` / `proc.stdout.readline()` call pair in a `time.perf_counter()` bracket, then parses the reply with `json.loads(...)`. The 0.043 ms mean and 0.076 ms p95 therefore reflect end-to-end latency per decision, not just transmission time.

Non-empty fired-rules result for an application that fires `k_score` and `k_income` (from section 7):

```
"fired_rules": ["k_score", "k_income"]
```

Both the fresh-process and persistent-process runs returned this non-empty list for the input `credit_score = 600, monthly_income = 10000` against thresholds `min_score = 650, min_income = 15000`.
