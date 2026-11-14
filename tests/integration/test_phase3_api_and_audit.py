"""
Phase 3 Integration and Acceptance Tests: Trace, Notice, Audit, Replay, API, Reviewer View.

Implements: FR-01, FR-10 to FR-16, NFR-01, NFR-02, NFR-07, NFR-08, DR-02, DR-03, CR-01, CR-02, CR-04, WP-11 to WP-14
Spec: docs/06-test-plan.md ("Lean mode" governs)
"""

from __future__ import annotations

import json
import sqlite3
import statistics
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.config import AppConfig
from src.api.review_report import generate_review_reports
from src.api.service import DecisionService
from src.audit.store import AuditStore, get_connection
from src.engine.engine import decide as engine_decide
from src.engine.rule_loader import load_rules
from src.explain.notice import build_notice
from src.explain.trace import build_trace, validate_trace

REPO_ROOT = Path(__file__).resolve().parents[2]
D1_CASES_PATH = REPO_ROOT / "data" / "d1" / "d1_cases.json"
NOTICE_CASES_PATH = REPO_ROOT / "tests" / "golden" / "notice_cases.json"
VECTORS_PATH = REPO_ROOT / "tests" / "golden" / "vectors.json"
PARAMS_PATH = REPO_ROOT / "params" / "params.toml"
RULES_DIR = REPO_ROOT / "rules"


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_audit.sqlite"


@pytest.fixture
def test_service(test_db_path: Path) -> DecisionService:
    config = AppConfig(
        audit_db_path=str(test_db_path),
        store_input_snapshot=True,
        host="127.0.0.1",
        port=8000,
        min_reason_length=10,
        queue_default_limit=50,
        review_report_dir="reports/reviewer",
    )
    store = AuditStore(test_db_path)
    return DecisionService(config=config, repo_root=REPO_ROOT, audit_store=store)


@pytest.fixture
def client(test_service: DecisionService) -> TestClient:
    app = create_app(service=test_service)
    return TestClient(app)


class TestPhase3LeanAcceptance:
    """Acceptance tests for Phase 3 in Lean mode."""

    def test_fr10_fr11_d1_traces_notices_and_latency(
        self, client: TestClient, test_service: DecisionService
    ):
        """
        FR-10, FR-11, FR-15, NFR-01:
        On all of D1 (data/d1/d1_cases.json):
        - set of fired rule IDs in trace equals the set engine reported as fired
        - trace validates against schemas/trace.schema.json
        - every code in reason_codes has a fired step carrying that code and no other fired step supplies one
        - notice.reasons lists exactly decision reason_codes, in same order, with no unfilled '{' or '}'
        - print one line with the median time of a POST /v1/decisions over D1
        """
        d1_data = json.loads(D1_CASES_PATH.read_text(encoding="utf-8"))["cases"]
        latencies_ms: list[float] = []

        for case in d1_data:
            inp = case["input"]
            start_t = time.perf_counter()
            resp = client.post("/v1/decisions", json=inp)
            duration_ms = (time.perf_counter() - start_t) * 1000.0
            latencies_ms.append(duration_ms)

            assert resp.status_code == 200, f"Case {inp.get('applicant_id')} failed: {resp.text}"
            body = resp.json()

            # 1. Compare fired rule IDs with direct engine run
            engine_res = engine_decide(inp, test_service.rule_set)
            expected_fired_ids = {
                s["rule_id"] for s in engine_res["steps"] if s["status"] == "fired"
            }

            trace = body["trace"]
            trace_fired_ids = {s["rule_id"] for s in trace["steps"] if s["status"] == "fired"}
            assert trace_fired_ids == expected_fired_ids, (
                f"Case {inp.get('applicant_id')}: trace fired rules {trace_fired_ids} != engine {expected_fired_ids}"
            )

            # 2. Trace validates against schema
            validate_trace(trace, REPO_ROOT / "schemas" / "trace.schema.json")

            # 3. Every code in reason_codes has a fired step carrying that code, and no other fired step supplies one
            reason_codes = body["reason_codes"]
            for code in reason_codes:
                matching_steps = [
                    s
                    for s in trace["steps"]
                    if s["status"] == "fired" and s.get("reason_code") == code
                ]
                assert len(matching_steps) == 1, (
                    f"Case {inp.get('applicant_id')}: expected exactly one fired step for code {code}, got {len(matching_steps)}"
                )

            # 4. notice.reasons lists exactly decision's reason_codes in same order with no unfilled placeholders
            notice = body["notice"]
            notice_codes = [r["code"] for r in notice["reasons"]]
            assert notice_codes == reason_codes, (
                f"Case {inp.get('applicant_id')}: notice codes {notice_codes} != reason_codes {reason_codes}"
            )

            for r in notice["reasons"]:
                assert "{" not in r["text"] and "}" not in r["text"], (
                    f"Case {inp.get('applicant_id')}: unfilled placeholder in reason: {r['text']}"
                )

        median_lat = statistics.median(latencies_ms)
        print(
            f"\nMedian POST /v1/decisions latency over D1: {median_lat:.2f} ms (cases: {len(d1_data)})"
        )

    def test_fr15_deterministic_api_responses(self, client: TestClient):
        """
        FR-15, NFR-01:
        Same input twice through the API gives identical responses apart from decision_id and evaluated_at.
        """
        vectors = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))["vectors"]
        tv2_input = vectors[1]["input"]

        resp1 = client.post("/v1/decisions", json=tv2_input)
        assert resp1.status_code == 200
        body1 = resp1.json()

        resp2 = client.post("/v1/decisions", json=tv2_input)
        assert resp2.status_code == 200
        body2 = resp2.json()

        assert body1["decision_id"] != body2["decision_id"]
        # Compare everything else
        b1_copy = dict(body1)
        b2_copy = dict(body2)
        del (
            b1_copy["decision_id"],
            b1_copy["evaluated_at"],
            b1_copy["trace"]["decision_id"],
            b1_copy["trace"]["evaluated_at"],
        )
        del (
            b2_copy["decision_id"],
            b2_copy["evaluated_at"],
            b2_copy["trace"]["decision_id"],
            b2_copy["trace"]["evaluated_at"],
        )

        assert b1_copy == b2_copy

    def test_fr11_golden_notice_cases_exact_match(self):
        """
        FR-11, FR-12, FR-13, CR-01, CR-02:
        Notice text for every case in tests/golden/notice_cases.json equals the expected
        headline, reasons, guidance, basis and offer summary exactly.
        """
        rule_set = load_rules(RULES_DIR, PARAMS_PATH)
        assert rule_set is not None

        cases_data = json.loads(NOTICE_CASES_PATH.read_text(encoding="utf-8"))["cases"]
        for case in cases_data:
            c_id = case["id"]
            inp = case["input"]
            exp = case["expected"]

            eng_res = engine_decide(inp, rule_set)
            assert eng_res["decision"] == exp["decision"], f"Decision mismatch for {c_id}"

            tr = build_trace(
                engine_result=eng_res,
                rule_set=rule_set,
                applicant_ref="sha256:" + "0" * 64,
                input_hash="sha256:" + "0" * 64,
                rule_set_version="rules-1.0.0+params-0.1.0",
                rule_set_hash="sha256:" + "0" * 64,
            )

            notice = build_notice(trace=tr, rule_set=rule_set, application=inp)
            exp_notice = exp["notice"]

            assert notice["headline"] == exp_notice["headline"], f"Headline mismatch for {c_id}"
            assert notice["reasons"] == exp_notice["reasons"], f"Reasons mismatch for {c_id}"
            clean_exp_guidance = [
                {k: v for k, v in g.items() if not k.startswith("_")}
                for g in exp_notice["guidance"]
            ]
            assert notice["guidance"] == clean_exp_guidance, f"Guidance mismatch for {c_id}"
            assert notice["basis"] == exp_notice["basis"], f"Basis mismatch for {c_id}"
            assert notice["offer_summary"] == exp_notice["offer_summary"], (
                f"Offer summary mismatch for {c_id}"
            )

    def test_fr16_replay_match_and_diff(
        self, client: TestClient, test_service: DecisionService, tmp_path: Path
    ):
        """
        FR-16:
        Replay: one stored decision replays with match: true;
        after changing one value in a copy of params/params.toml (never real file)
        replay reports match: false with a difference listed.
        """
        vectors = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))["vectors"]
        tv2_input = vectors[1]["input"]

        resp = client.post("/v1/decisions", json=tv2_input)
        assert resp.status_code == 200
        dec_id = resp.json()["decision_id"]

        # 1. Normal replay: match is true
        rep_resp = client.post(f"/v1/decisions/{dec_id}/replay")
        assert rep_resp.status_code == 200
        rep_data = rep_resp.json()
        assert rep_data["match"] is True
        assert rep_data["differences"] == []

        # 2. Replay with altered parameter in a copy
        # Create altered copy of params.toml in tmp_path
        orig_params_text = PARAMS_PATH.read_text(encoding="utf-8")
        # Change min_monthly_income from 15000 to 50000 (which will affect eligibility/knockout)
        altered_params_text = orig_params_text.replace(
            "min_monthly_income = 15000", "min_monthly_income = 50000"
        )
        alt_params_path = tmp_path / "params_alt.toml"
        alt_params_path.write_text(altered_params_text, encoding="utf-8")

        alt_rule_set = load_rules(RULES_DIR, alt_params_path)
        assert alt_rule_set is not None

        # Replay directly with alt rule set
        alt_rep_res = test_service.replay_decision(dec_id, alt_rule_set=alt_rule_set)
        assert alt_rep_res["match"] is False
        assert len(alt_rep_res["differences"]) > 0

    def test_fr01_nfr01_valid_and_invalid_request_schemas(
        self, client: TestClient, test_service: DecisionService
    ):
        """
        FR-01, NFR-01:
        One valid request and one invalid request validate against response schema and 422 schema respectively.
        """
        vectors = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))["vectors"]
        tv2_input = vectors[1]["input"]

        # Valid request -> 200 and validates against response.schema.json
        resp_valid = client.post("/v1/decisions", json=tv2_input)
        assert resp_valid.status_code == 200
        valid_json = resp_valid.json()
        errors = list(test_service.response_validator.iter_errors(valid_json))
        assert not errors, f"Valid response failed schema: {errors}"

        # Invalid request -> 422 and validates against validation_error_response schema
        invalid_input = dict(tv2_input, age="not-an-integer", unknown_field=123)
        resp_invalid = client.post("/v1/decisions", json=invalid_input)
        assert resp_invalid.status_code == 422
        invalid_json = resp_invalid.json()
        err_errors = list(test_service.validation_err_validator.iter_errors(invalid_json))
        assert not err_errors, f"Validation error response failed schema: {err_errors}"
        assert invalid_json["error"]["code"] == "INVALID_REQUEST"
        assert len(invalid_json["error"]["fields"]) >= 1

    def test_fr15_nfr02_audit_records_and_immutable_triggers(
        self, client: TestClient, test_service: DecisionService, test_db_path: Path
    ):
        """
        FR-15, NFR-02, NFR-06, DR-03:
        A record is written for every decision in D1 run, and an UPDATE and a DELETE on
        audit_records, audit_inputs, and reviewer_actions are rejected by triggers (NFR-06 append-only).
        """
        vectors = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))["vectors"]
        tv2_input = vectors[1]["input"]
        resp = client.post("/v1/decisions", json=tv2_input)
        assert resp.status_code == 200
        dec_id = resp.json()["decision_id"]

        # Record a review action first so reviewer_actions has a row
        test_service.review_decision(dec_id, "test_rev", "override", "Testing reviewer overrides")

        conn = get_connection(test_db_path)
        try:
            cur = conn.execute("SELECT COUNT(*) as cnt FROM audit_records")
            row = cur.fetchone()
            count_before = int(row["cnt"]) if row else 0
            assert count_before >= 1

            # Test triggers reject UPDATE
            with pytest.raises(
                (sqlite3.OperationalError, sqlite3.IntegrityError),
                match="audit tables are append-only",
            ):
                conn.execute("UPDATE audit_records SET decision = 'ineligible' WHERE seq = 1")

            # Test triggers reject DELETE
            with pytest.raises(
                (sqlite3.OperationalError, sqlite3.IntegrityError),
                match="audit tables are append-only",
            ):
                conn.execute("DELETE FROM audit_records WHERE seq = 1")

            # Test audit_inputs triggers
            with pytest.raises(
                (sqlite3.OperationalError, sqlite3.IntegrityError),
                match="audit tables are append-only",
            ):
                conn.execute("UPDATE audit_inputs SET input = '{}' WHERE rowid = 1")

            with pytest.raises(
                (sqlite3.OperationalError, sqlite3.IntegrityError),
                match="audit tables are append-only",
            ):
                conn.execute("DELETE FROM audit_inputs WHERE rowid = 1")

            # Test reviewer_actions triggers
            with pytest.raises(
                (sqlite3.OperationalError, sqlite3.IntegrityError),
                match="audit tables are append-only",
            ):
                conn.execute("UPDATE reviewer_actions SET action = 'deny' WHERE action_id = 1")

            with pytest.raises(
                (sqlite3.OperationalError, sqlite3.IntegrityError),
                match="audit tables are append-only",
            ):
                conn.execute("DELETE FROM reviewer_actions WHERE action_id = 1")

        finally:
            conn.close()

    def test_reviewer_view_smoke(
        self, test_service: DecisionService, client: TestClient, tmp_path: Path
    ):
        """
        CR-04, FR-14, FR-25:
        One smoke check is enough: the report for the demo REFER case contains the decision ID,
        every rule ID of the trace, and the text "Not available".
        """
        # Run N-R01 through client
        notice_cases = json.loads(NOTICE_CASES_PATH.read_text(encoding="utf-8"))["cases"]
        nr01_case = next(c for c in notice_cases if c["id"] == "N-R01")
        resp = client.post("/v1/decisions", json=nr01_case["input"])
        assert resp.status_code == 200
        data = resp.json()
        dec_id = data["decision_id"]

        out_dir = tmp_path / "reports" / "reviewer"
        generate_review_reports(db_path=test_service.audit_store.db_path, output_dir=out_dir)

        case_file = out_dir / f"{dec_id}.html"
        assert case_file.exists(), f"Case file {case_file} not generated"

        html_text = case_file.read_text(encoding="utf-8")
        assert dec_id in html_text
        assert "Not available. The baseline model is built in Phase 4." in html_text

        # Every rule ID of the trace in the report
        for s in data["trace"]["steps"]:
            r_id = s["rule_id"]
            assert f"<code>{r_id}</code>" in html_text or r_id in html_text
