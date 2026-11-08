# Open Questions

Log of ambiguities, conflicts, and decisions needed. Never choose silently – log here and stop.

| ID | Date | Phase | Source | Question | Status |
| --- | --- | --- | --- | --- | --- |
| OQ-001 | 2026-11-08 | 0 | Environment | SWI-Prolog (`swipl`) is not installed on this machine. `where swipl` returns nothing; `Get-ChildItem "C:\Program Files"` shows no Prolog directory. Spike S1 (WP-02) cannot call SWI-Prolog. ADR-001 says to fall back to the pure-Python evaluator if the spike fails, but the spec says the owner decides. The spike report (docs/reports/spike-s1.md) records this and waits for a decision. | **Waiting for owner decision** |
| OQ-002 | 2026-11-08 | 0 | docs/08-datasets.md §2 | Home Credit Default Risk is listed at `https://kaggle.com/c/home-credit-default-risk`. The sandbox has no network access. Spike S2 cannot verify column names, licence terms, or file availability without network or local files. No files are present in `data/raw/`. Spike S2 reports the mapping as documented and flags every field that needs WP-15 verification. | **Waiting for WP-15; no raw data present** |
| OQ-003 | 2026-11-08 | 0 | docs/09-file-formats.md §7 PT-15 | PT-15 says "Hash the baseline files with LF line ends, then with CRLF – same hash. Changing one character gives a different hash." Only `params/params.toml` exists in Phase 0; the rule files do not. The test runs PT-15 on `params/params.toml` alone, as instructed. When the remaining files are added in Phases 1 and 2, PT-15 must be re-run on the full set. | Deferred to Phase 2 per phase instructions |

