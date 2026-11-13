# Makefile for the loan expert system
#
# Usage on Windows (with MinGW make):
#   mingw32-make setup
#   mingw32-make test
#   mingw32-make check
#   mingw32-make check-params
#
# On Linux/macOS:
#   make setup / make test / make check / make check-params
#
# AGENTS.md: "A phase adds only the commands it needs; add the rest as their phase arrives."
# Phase 0 provides: setup, test, check, check-params
# Later phases will add: check-rules, decide, demo, replay, oracle-diff,
#                        baseline, compare, fairness, reproduce

PYTHON = python
PIP    = $(PYTHON) -m pip
PYTEST = $(PYTHON) -m pytest
RUFF   = $(PYTHON) -m ruff
PARAMS = params/params.toml

FIELDS = rules/fields.toml

.PHONY: setup test check check-params check-fields check-floats lint format \
        check-rules decide demo replay replay-all audit-verify review-report serve \
        oracle-diff data-d2 data-d3 data-d3-bias data-d3-bias-large decide-d3 decide-d2 split baseline baseline-filtered phase4 \
        fairness-pin edge-cases compare fairness fairness-bias-decide \
        demo-ui traceability check-docs monitor-sample phase5 reproduce

# ---------------------------------------------------------------------------
# WP-02: setup — install pinned dependencies
# ---------------------------------------------------------------------------
setup:
	$(PIP) install -r requirements.txt

# ---------------------------------------------------------------------------
# WP-02: test — run all tests including golden vectors
# ---------------------------------------------------------------------------
test:
	$(PYTEST) tests/ -v

# ---------------------------------------------------------------------------
# WP-01: check — tests + float ban + lint + format + check-params + check-fields + check-rules
# ---------------------------------------------------------------------------
check: check-floats lint format test check-params check-fields check-rules
	@echo ""
	@echo "=== make check complete ==="

# ---------------------------------------------------------------------------
# WP-03: check-params — load and validate params/params.toml
# ---------------------------------------------------------------------------
check-params:
	$(PYTHON) -m src.engine.param_loader $(PARAMS)

# ---------------------------------------------------------------------------
# WP-05: check-fields — load and validate rules/fields.toml
# ---------------------------------------------------------------------------
check-fields:
	$(PYTHON) -m src.engine.field_loader $(FIELDS)

# ---------------------------------------------------------------------------
# WP-06: check-rules — load and validate rule files, hygiene checks, protected-attribute scan
# ---------------------------------------------------------------------------
check-rules:
	$(PYTHON) -m src.engine.param_loader $(PARAMS)
	$(PYTHON) -m src.engine.field_loader $(FIELDS)
	$(PYTHON) -m src.engine.rule_loader rules $(PARAMS)
	$(PYTHON) -m src.engine.hygiene

# ---------------------------------------------------------------------------
# WP-01/WP-04: check-floats — fail the build if any float is used in src/calc or src/facts
# ---------------------------------------------------------------------------
# WP-01/WP-04/WP-12: check-floats — fail the build if any float is used in src/calc, src/facts, src/explain
# ---------------------------------------------------------------------------
check-floats:
	$(PYTHON) tools/check_floats.py src/calc src/facts src/explain src/data/d2_map.py

# ---------------------------------------------------------------------------
# Lint: ruff check
# ---------------------------------------------------------------------------
lint:
	$(RUFF) check src/ tests/ tools/

# ---------------------------------------------------------------------------
# Format check: ruff format --check
# ---------------------------------------------------------------------------
format:
	$(RUFF) format --check src/ tests/ tools/

# ---------------------------------------------------------------------------
# WP-16a: oracle-diff — compare engine output on D1 with oracle expected output
# ---------------------------------------------------------------------------
oracle-diff:
	$(PYTHON) tools/oracle_diff.py

# ---------------------------------------------------------------------------
# Phase 3 targets (WP-11 to WP-14)
# ---------------------------------------------------------------------------

decide:
	$(PYTHON) -m src.api.decide $(INPUT)

demo:
	$(PYTHON) tools/demo.py

audit-verify:
	$(PYTHON) -m src.audit.verify

replay-all:
	$(PYTHON) -m src.audit.replay_all

replay:
	$(PYTHON) -m src.audit.replay_all

review-report:
	$(PYTHON) -m src.api.review_report

serve:
	$(PYTHON) -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000

# ---------------------------------------------------------------------------
# Phase 4 targets (WP-15, WP-16b, WP-17)
# ---------------------------------------------------------------------------

data-d2:
	$(PYTHON) -m src.data.d2_map

data-d3:
	$(PYTHON) data/synthetic/d3_generator.py

data-d3-bias:
	$(PYTHON) data/synthetic/d3_generator.py --bias --out-population data/synthetic/d3_bias_population.csv --out-protected data/protected/d3_bias_protected.csv

decide-d3:
	$(PYTHON) -m src.data.batch_decide --dataset d3

decide-d2:
	$(PYTHON) -m src.data.batch_decide --dataset d2

split:
	$(PYTHON) -m src.data.split

baseline:
	$(PYTHON) -m src.ml.baseline

# ---------------------------------------------------------------------------
# Phase 4 close-out: filtered-subset comparison (owner answered B)
# ---------------------------------------------------------------------------
baseline-filtered:
	$(PYTHON) -m src.ml.baseline_filtered

phase4: data-d2 data-d3 decide-d3 split decide-d2 baseline baseline-filtered
	$(PYTHON) tools/check_floats.py src/calc src/facts src/explain src/data/d2_map.py
	$(PYTHON) -m src.engine.param_loader $(PARAMS)
	$(PYTHON) -m src.engine.field_loader $(FIELDS)
	$(PYTHON) -m src.engine.rule_loader rules $(PARAMS)
	$(PYTHON) -m src.engine.hygiene
	$(PYTHON) tools/oracle_diff.py
	$(PYTHON) -m src.data.manifest
	$(PYTHON) -m src.data.group_sizes
	@echo "=== Phase 4 complete ==="

# ---------------------------------------------------------------------------
# Stubs for later phases (added when each phase arrives)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Phase 5 targets (WP-18 to WP-22)
# ---------------------------------------------------------------------------

fairness-pin:
	$(PYTHON) -m src.eval.fairness_guard

edge-cases:
	$(PYTHON) -m src.eval.edge_cases

compare:
	$(PYTHON) -m src.eval.compare

fairness:
	$(PYTHON) -m src.eval.fairness

# WP-20: generate large bias dataset (N=100k) for planted-bias pipeline test
data-d3-bias-large:
	$(PYTHON) data/synthetic/d3_generator.py --bias --size 100000 --out-population data/synthetic/d3_bias_large.csv --out-protected data/protected/d3_bias_large_protected.csv

# WP-20: pre-compute engine decisions on bias dataset for fast test reuse
fairness-bias-decide:
	$(PYTHON) tools/fairness_bias_decide.py

# WP-22: demo UI
demo-ui:
	@echo "Starting demo UI on http://127.0.0.1:8080"
	$(PYTHON) -m uvicorn src.ui.app:app --host 127.0.0.1 --port 8080

# WP-21: traceability — requirement-to-test table
traceability:
	$(PYTHON) tools/traceability.py

# WP-21: check-docs — rule IDs, reason codes, param names in docs vs files
check-docs:
	$(PYTHON) tools/check_docs.py

# WP-21: monitor-sample — decision mix and reason-code table from d3 decisions
monitor-sample:
	$(PYTHON) tools/monitor_sample.py

# WP-21: phase5 manifest — runs Parts B-E in order and writes reports/phase5_manifest.json
phase5: edge-cases compare fairness
	$(PYTHON) tools/phase5_manifest.py
	@echo "=== Phase 5 complete ==="

# WP-21: reproduce — phase4 then phase5, compare with committed expected values
reproduce: phase4 phase5
	$(PYTHON) tools/reproduce_comparison.py
	@echo "=== Reproduce complete ==="

