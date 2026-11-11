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
        oracle-diff baseline compare fairness reproduce

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
	$(PYTHON) tools/check_floats.py src/calc src/facts src/explain

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
# Stubs for later phases (added when each phase arrives)
# ---------------------------------------------------------------------------

baseline:
	@echo "baseline: not yet implemented (Phase 4)"
	@exit 1

compare:
	@echo "compare: not yet implemented (Phase 5)"
	@exit 1

fairness:
	@echo "fairness: not yet implemented (Phase 5)"
	@exit 1

reproduce:
	@echo "reproduce: not yet implemented (Phase 5)"
	@exit 1

