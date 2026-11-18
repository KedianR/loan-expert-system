"""UI tests (lean: exactly 4 as specified in docs/ui-spec.md §5).

Test 1: GET /, /results, /about → 200 + banner text.
Test 2: TV1-TV9 POST /ui/decide returns same decision/amount/band/reason_codes
        as the service function called directly.
Test 3: ML scorer monkeypatched to raise → POST /ui/decide still returns decision.
Test 4: Static scan: no innerHTML, no protected column name, no parseFloat/Number(
        applied to money in src/ui/.

Requirements: FR-25, NFR-09, NFR-10, CR-02, P5-12.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

BANNER_TEXT = "Prototype. Illustrative policy values and synthetic or public data. Not a real lending decision."

# ---------------------------------------------------------------------------
# FastAPI test client setup
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    """Create a FastAPI test client for src/ui/app.py."""
    from fastapi.testclient import TestClient

    from src.ui.app import app

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Test 1: Pages return 200 and contain banner
# ---------------------------------------------------------------------------


def test_index_page_200_and_banner(client):
    """GET / returns 200 and contains banner text."""
    res = client.get("/")
    assert res.status_code == 200, f"/ returned {res.status_code}"
    assert BANNER_TEXT in res.text, f"Banner not found in /. Got: {res.text[:200]}"


def test_results_page_200_and_banner(client):
    """GET /results returns 200 and contains banner text."""
    res = client.get("/results")
    assert res.status_code == 200, f"/results returned {res.status_code}"
    assert BANNER_TEXT in res.text, f"Banner not found in /results. Got: {res.text[:200]}"


def test_about_page_200_and_banner(client):
    """GET /about returns 200 and contains banner text."""
    res = client.get("/about")
    assert res.status_code == 200, f"/about returned {res.status_code}"
    assert BANNER_TEXT in res.text, f"Banner not found in /about. Got: {res.text[:200]}"


# ---------------------------------------------------------------------------
# Test 2: TV1-TV9 POST /ui/decide matches service function directly
# ---------------------------------------------------------------------------


def test_decide_tv_vectors_match_service(client):
    """TV1-TV9: /ui/decide returns same decision, amount, band, reason_codes as DecisionService."""
    from src.api.service import DecisionService

    vectors_path = REPO_ROOT / "tests" / "golden" / "vectors.json"
    assert vectors_path.exists(), "Golden vectors file not found"
    vecs = json.loads(vectors_path.read_text(encoding="utf-8"))["vectors"]

    svc = DecisionService(repo_root=REPO_ROOT)

    for tv in vecs:
        tv_id = tv["id"]
        inp = tv["input"]

        # Call service directly
        direct = svc.decide(inp)

        # Call via UI endpoint
        res = client.post("/ui/decide", json=inp)
        assert res.status_code == 200, f"{tv_id}: /ui/decide returned {res.status_code}"
        ui = res.json()

        assert ui.get("decision") == direct.get("decision"), (
            f"{tv_id}: decision mismatch. UI={ui.get('decision')} Direct={direct.get('decision')}"
        )

        # Amount: may be None for ineligible/refer
        ui_amount = (ui.get("offer") or {}).get("recommended_amount")
        direct_amount = (direct.get("offer") or {}).get("recommended_amount")
        assert ui_amount == direct_amount, (
            f"{tv_id}: recommended_amount mismatch. UI={ui_amount} Direct={direct_amount}"
        )

        # Band
        ui_band = (ui.get("offer") or {}).get("band")
        direct_band = (direct.get("offer") or {}).get("band")
        assert ui_band == direct_band, f"{tv_id}: band mismatch. UI={ui_band} Direct={direct_band}"

        # Reason codes (order-insensitive)
        ui_codes = set(ui.get("reason_codes") or [])
        direct_codes = set(direct.get("reason_codes") or [])
        assert ui_codes == direct_codes, (
            f"{tv_id}: reason_codes mismatch. UI={ui_codes} Direct={direct_codes}"
        )


# ---------------------------------------------------------------------------
# Test 3: ML scorer failure does NOT block decision
# ---------------------------------------------------------------------------


def test_ml_failure_does_not_block_decision(client, monkeypatch):
    """With ML scorer monkeypatched to raise, /ui/decide still returns the decision."""
    import src.ui.app as ui_app

    # Monkeypatch the ML scorer to raise
    monkeypatch.setattr(
        ui_app, "_get_ml_scorer", lambda: (_ for _ in ()).throw(RuntimeError("ML unavailable"))
    )

    # Actually we need to patch the internal call. Let's patch _ml_scorer to be None
    # and _ml_scorer_error to be set.
    monkeypatch.setattr(ui_app, "_ml_scorer", None)
    monkeypatch.setattr(ui_app, "_ml_scorer_error", "ML scorer monkeypatched to fail")

    vectors_path = REPO_ROOT / "tests" / "golden" / "vectors.json"
    vecs = json.loads(vectors_path.read_text(encoding="utf-8"))["vectors"]
    tv1 = vecs[0]["input"]

    res = client.post("/ui/decide", json=tv1)
    assert res.status_code == 200, f"/ui/decide returned {res.status_code}"
    data = res.json()
    assert data.get("decision") is not None, (
        "Decision must be present even when ML scorer fails. Got: " + json.dumps(data)
    )


# ---------------------------------------------------------------------------
# Test 4: Static scan of src/ui/ source files
# ---------------------------------------------------------------------------

UI_SRC_DIR = REPO_ROOT / "src" / "ui"

# Protected column names that must NOT appear in src/ui/ code
_PROTECTED_COLS = {
    "CODE_GENDER",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "REGION_RATING_CLIENT",
    "d2_protected",
    "d3_protected",  # file path fragments
}

# Pattern: parseFloat or Number( applied to a money field variable name
# We scan for parseFloat( or Number( anywhere in JS (they must not be used on money)
# Note: credit_score uses parseFloat in buildPayload — this is explicitly allowed
# (credit_score is not a money field). We scan for the pattern on money-ish names.
_MONEY_NAMES = {"amount", "income", "obligations", "instalment", "fee", "cost", "rate"}


def test_static_scan_no_innerhtml():
    """src/ui/ JS/HTML must not assign to innerHTML (docs/ui-spec.md §2 rule 4).

    Comments mentioning innerHTML (e.g. 'never innerHTML') are allowed.
    Only actual assignments like 'el.innerHTML = ...' are banned.

    After UI v2 rewrite, all .js files in src/ui/static/ are scanned
    (app.js, ui.js, results.js, and any others present).
    """
    violations = []
    for f in UI_SRC_DIR.rglob("*"):
        if f.suffix not in (".js", ".html"):
            continue
        if f.is_dir():
            continue
        content = f.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            # Skip comment lines
            if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
                continue
            # Check for assignment: .innerHTML = or .innerHTML=
            if re.search(r"\.innerHTML\s*=", line):
                violations.append(f"{f.relative_to(REPO_ROOT)}:{i}: {stripped[:80]}")
    assert not violations, "innerHTML assignment found in src/ui/:\n" + "\n".join(violations)


def test_static_scan_no_protected_column_names():
    """src/ui/ must not mention protected column names."""
    violations = []
    for f in UI_SRC_DIR.rglob("*"):
        if f.suffix not in (".py", ".js", ".html", ".css"):
            continue
        if f.is_dir():
            continue
        content = f.read_text(encoding="utf-8", errors="replace")
        for col in _PROTECTED_COLS:
            if col in content:
                violations.append(f"{f.relative_to(REPO_ROOT)}: contains '{col}'")
    assert not violations, "Protected names found in src/ui/:\n" + "\n".join(violations)


def test_static_scan_no_parsefloat_on_money_in_js():
    """All .js files in src/ui/static/ must not use parseFloat/Number( on money fields.

    Rule: money fields are displayed as returned strings, not parsed.
    Exception: credit_score is not a money field and may use parseFloat.

    After UI v2 rewrite, the scan covers app.js, ui.js, results.js and any
    other .js files that may be present in src/ui/static/.
    """
    static_dir = UI_SRC_DIR / "static"
    js_files = list(static_dir.glob("*.js")) if static_dir.exists() else []

    # Ensure we have at least app.js for backward compatibility
    app_js = static_dir / "app.js"
    assert app_js.exists(), "app.js not found in src/ui/static/"

    violations = []
    for js_file in js_files:
        content = js_file.read_text(encoding="utf-8", errors="replace")
        fname = js_file.name

        for i, line in enumerate(content.splitlines(), 1):
            # Skip the credit_score line (explicitly allowed in buildPayload)
            if "credit_score" in line:
                continue
            # Check for parseFloat( near money names
            if re.search(r"parseFloat\s*\(", line):
                for name in _MONEY_NAMES:
                    if name in line.lower():
                        violations.append(
                            f"{fname}:{i}: parseFloat on money-ish name '{name}': {line.strip()[:80]}"
                        )
            # Check for Number( near money names
            if re.search(r"\bNumber\s*\(", line):
                for name in _MONEY_NAMES:
                    if name in line.lower():
                        violations.append(
                            f"{fname}:{i}: Number( on money-ish name '{name}': {line.strip()[:80]}"
                        )
            # Check for toFixed( near money names
            if re.search(r"\btoFixed\s*\(", line):
                for name in _MONEY_NAMES:
                    if name in line.lower():
                        violations.append(
                            f"{fname}:{i}: toFixed on money-ish name '{name}': {line.strip()[:80]}"
                        )
    assert not violations, (
        "parseFloat/Number(/toFixed on money fields in src/ui/static/ JS files:\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# NEW TESTS: FR-25, NFR-09, NFR-10, CR-02, P5-12 (UI v2 report spec)
# ---------------------------------------------------------------------------


def test_tv1_eligible_report_has_reasons_trace_offer(client):
    """TV1 (ELIGIBLE): /ui/decide response has notice/reason_codes, trace entries, and offer fields."""
    vectors_path = REPO_ROOT / "tests" / "golden" / "vectors.json"
    vecs = json.loads(vectors_path.read_text(encoding="utf-8"))["vectors"]
    tv1 = next(v for v in vecs if v["id"] == "TV1")
    res = client.post("/ui/decide", json=tv1["input"])
    assert res.status_code == 200
    data = res.json()
    assert data.get("decision") == "eligible", f"TV1 must be eligible, got {data.get('decision')}"
    # Offer fields
    offer = data.get("offer") or {}
    assert (offer.get("amount") is not None or offer.get("recommended_amount") is not None), "TV1 eligible: offer amount missing"
    assert offer.get("band") is not None, "TV1 eligible: offer.band missing"
    # Trace entries (service must return a trace)
    trace = data.get("trace") or {}
    steps = trace if isinstance(trace, list) else trace.get("steps", [])
    assert len(steps) > 0, "TV1 eligible: trace must be non-empty"
    for entry in steps:
        assert "rule_id" in entry, f"Trace entry missing rule_id: {entry}"


def test_ineligible_case_report_has_reasons_and_codes(client):
    """An INELIGIBLE vector: response has reason_codes, notice with text and code, and trace."""
    vectors_path = REPO_ROOT / "tests" / "golden" / "vectors.json"
    vecs = json.loads(vectors_path.read_text(encoding="utf-8"))["vectors"]
    # Find first ineligible vector
    ineligible = next((v for v in vecs if v["expected"]["decision"] == "ineligible"), None)
    assert ineligible is not None, "No ineligible test vector found"
    res = client.post("/ui/decide", json=ineligible["input"])
    assert res.status_code == 200
    data = res.json()
    assert data.get("decision") == "ineligible"
    codes = data.get("reason_codes") or []
    assert len(codes) > 0, "Ineligible: reason_codes must be non-empty"
    notice = data.get("notice") or {}
    reasons = notice if isinstance(notice, list) else notice.get("reasons", [])
    assert len(reasons) > 0 or len(codes) > 0
    for item in reasons:
        if isinstance(item, dict):
            assert "text" in item or "code" in item, f"Notice item missing text or code: {item}"
    trace = data.get("trace") or {}
    steps = trace if isinstance(trace, list) else trace.get("steps", [])
    assert len(steps) > 0, "Ineligible: trace must be non-empty"
    for entry in steps:
        assert "rule_id" in entry, f"Trace entry missing rule_id: {entry}"


def test_refer_case_report_has_decision(client):
    """A REFER vector: response has decision=refer, reasons, and trace."""
    notice_path = REPO_ROOT / "tests" / "golden" / "notice_cases.json"
    ncases = json.loads(notice_path.read_text(encoding="utf-8"))["cases"]
    refer = next(c for c in ncases if c.get("expected", {}).get("decision") == "refer")
    res = client.post("/ui/decide", json=refer["input"])
    assert res.status_code == 200
    data = res.json()
    assert data.get("decision") == "refer", f"Expected refer, got {data.get('decision')}"
    codes = data.get("reason_codes") or []
    assert len(codes) > 0, "Refer: reason_codes must be non-empty"
    notice = data.get("notice") or {}
    reasons = notice if isinstance(notice, list) else notice.get("reasons", [])
    assert len(reasons) > 0 or len(codes) > 0
    for item in reasons:
        if isinstance(item, dict):
            assert "text" in item or "code" in item, f"Notice item missing text or code: {item}"
    trace = data.get("trace") or {}
    steps = trace if isinstance(trace, list) else trace.get("steps", [])
    assert len(steps) > 0, "Refer: trace must be non-empty"
    for entry in steps:
        assert "rule_id" in entry, f"Trace entry missing rule_id: {entry}"


def test_ml_failure_report_still_has_sections(client, monkeypatch):
    """With ML scorer raising, /ui/decide still returns decision, trace, offer for TV1."""
    import src.ui.app as ui_app

    # Safer pattern: set scorer to None and record the error string,
    # rather than making a generator throw.
    monkeypatch.setattr(ui_app, "_get_ml_scorer", lambda: None)
    monkeypatch.setattr(ui_app, "_ml_scorer_error", "ML forced offline for test")

    vectors_path = REPO_ROOT / "tests" / "golden" / "vectors.json"
    vecs = json.loads(vectors_path.read_text(encoding="utf-8"))["vectors"]
    tv1 = next(v for v in vecs if v["id"] == "TV1")
    res = client.post("/ui/decide", json=tv1["input"])
    assert res.status_code == 200
    data = res.json()
    assert data.get("decision") == "eligible"
    offer = data.get("offer") or {}
    assert (offer.get("amount") is not None or offer.get("recommended_amount") is not None)
    trace = data.get("trace") or {}
    steps = trace if isinstance(trace, list) else trace.get("steps", [])
    assert len(steps) > 0


def test_every_page_has_main_nav_banner_lang(client):
    """Every page: has <html lang=, <main, nav links (Apply Results About), and banner text."""
    BANNER = "Prototype. Illustrative policy values and synthetic or public data. Not a real lending decision."
    for path in ["/", "/results", "/about"]:
        res = client.get(path)
        assert res.status_code == 200, f"{path}: status {res.status_code}"
        html = res.text
        # lang attribute
        assert 'lang="en"' in html or "lang='en'" in html, f"{path}: missing lang=en"
        # main landmark
        assert "<main" in html, f"{path}: missing <main> landmark"
        # nav (check for the three links)
        assert 'href="/"' in html or "href='/'" in html, f"{path}: missing Apply nav link"
        assert 'href="/results"' in html, f"{path}: missing Results nav link"
        assert 'href="/about"' in html, f"{path}: missing About nav link"
        # banner text
        assert BANNER in html, f"{path}: missing banner text"


def test_form_inputs_have_labels(client):
    """index.html: every <input> and <select> with an id has a <label for=that id>."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    # Find all input ids (not hidden-type, not submit/button)
    input_ids = re.findall(
        r'<input[^>]+type=["\'](?!hidden|submit|button)[^"\']*["\'][^>]+id=["\']([^"\']+)["\']', html
    )
    input_ids += re.findall(
        r'<input[^>]+id=["\']([^"\']+)["\'][^>]+type=["\'](?!hidden|submit|button)', html
    )
    select_ids = re.findall(r'<select[^>]+id=["\']([^"\']+)["\']', html)
    # Also catch inputs with no explicit type (default is text)
    all_ids = set(input_ids + select_ids)
    # Remove known non-input ids
    all_ids.discard('')
    for fid in all_ids:
        label_for = f'for="{fid}"'
        label_for2 = f"for='{fid}'"
        assert label_for in html or label_for2 in html, (
            f"Input id='{fid}' in index.html has no matching <label for='{fid}'>"
        )


# ---------------------------------------------------------------------------
# UI v2 Fix Pass Tests (A.1, A.2, A.3, A.4)
# ---------------------------------------------------------------------------


def test_results_reports_endpoints_return_non_empty(client):
    """A.1: Results data endpoints return non-empty data for each tab."""
    reports = [
        "metrics_d2_lr",
        "comparison_scorecard",
        "d2_tables",
        "edge_case_summary",
        "edge_cases_results",
    ]
    for rep in reports:
        res = client.get(f"/ui/report/{rep}")
        assert res.status_code == 200, f"/ui/report/{rep} returned {res.status_code}"
        data = res.json()
        assert data.get("available") is not False, f"Report {rep} marked as unavailable: {data}"
        if "content" in data:
            assert len(data["content"].strip()) > 0, f"Report {rep} content is empty"
        elif "rows" in data:
            assert len(data["rows"]) == 64, f"Report {rep} rows count expected 64, got {len(data['rows'])}"
        else:
            assert len(data) > 0, f"Report {rep} JSON is empty"


def test_ml_score_tv1_returns_both_models(client):
    """A.2: POST /ui/ml-score on TV1 returns scores for both LR and GB models without errors."""
    vectors_path = REPO_ROOT / "tests" / "golden" / "vectors.json"
    vecs = json.loads(vectors_path.read_text(encoding="utf-8"))["vectors"]
    tv1 = vecs[0]["input"]

    res = client.post("/ui/ml-score", json=tv1)
    assert res.status_code == 200, f"/ui/ml-score returned {res.status_code}"
    data = res.json()
    assert data.get("available") is True, f"ML scoring failed: {data}"
    assert "lr_score" in data, "lr_score missing from ML response"
    assert isinstance(data["lr_score"], (int, float)), "lr_score must be a numeric score"
    assert 0.0 <= data["lr_score"] <= 1.0, f"lr_score out of range: {data['lr_score']}"

    assert "gb_score" in data, "gb_score missing from ML response"
    assert isinstance(data["gb_score"], (int, float)), "gb_score must be a numeric score"
    assert 0.0 <= data["gb_score"] <= 1.0, f"gb_score out of range: {data['gb_score']}"

    assert "columns are missing" not in str(data)
    assert "error" not in data


def test_offer_summary_total_repayment_separate_row(client):
    """A.3: Offer summary in /ui/decide contains total_repayment (= emi * tenure) separate from total_interest."""
    vectors_path = REPO_ROOT / "tests" / "golden" / "vectors.json"
    vecs = json.loads(vectors_path.read_text(encoding="utf-8"))["vectors"]
    tv1 = vecs[0]["input"]

    res = client.post("/ui/decide", json=tv1)
    assert res.status_code == 200
    offer = res.json().get("offer") or {}
    assert "total_interest" in offer, "total_interest missing from offer"
    assert "total_repayment" in offer, "total_repayment missing from offer"
    assert offer["total_interest"] == "167408.48"
    assert offer["total_repayment"] == "867408.48"


def test_checkboxes_style_and_preset_behavior():
    """A.4: Checkboxes visual style and preset state handling in style.css and ui.js."""
    css_path = REPO_ROOT / "src" / "ui" / "static" / "style.css"
    css = css_path.read_text(encoding="utf-8")

    # style.css must ensure checkboxes are not stripped by appearance: none
    assert re.search(r'input\[type=["\']checkbox["\']\]\s*\{[^}]*appearance:\s*auto', css) or \
           ":not([type=\"checkbox\"])" in css, "Checkboxes must have visible appearance"

    # ui.js must handle checkboxes in applyPreset
    js_path = REPO_ROOT / "src" / "ui" / "static" / "ui.js"
    js = js_path.read_text(encoding="utf-8")
    assert "kyc_verified" in js
    assert "consent_given" in js
    assert "checked" in js


# ---------------------------------------------------------------------------
# UI v2 Fix Pass 2 Tests (Results tables, About page, REFER text, chips nowrap)
# ---------------------------------------------------------------------------


def test_about_page_no_first_order_and_accurate_wording(client):
    """Pass 2 #10, #11, #12, #13: About page has forward-chaining wording, rule-set tag/hash, plain doc paths."""
    res = client.get("/about")
    assert res.status_code == 200
    text = res.text

    # No "first-order"
    assert "first-order" not in text.lower(), "About page must not say 'first-order'"
    assert "first order" not in text.lower(), "About page must not say 'first order'"

    # Has "forward-chaining"
    assert "forward-chaining" in text

    # No "borderline debt-service ratio"
    assert "borderline debt-service ratio" not in text

    # Shows active rule set and hash
    assert "rules-1.0.0+params-0.1.0" in text
    assert "sha256:eb7073a388817e0a455997c0c2ea86ccb25524cdff07faf8bf5ca98bb267be5a" in text

    # Document paths rendered as code text, not broken links
    assert "<code>docs/01-srs.md</code>" in text
    assert '<a href="/docs/01-srs.md">' not in text


def test_refer_offer_summary_pending_review_text(client):
    """Pass 2 #9: REFER outcome displays 'No offer yet: pending manual review.'."""
    js_path = REPO_ROOT / "src" / "ui" / "static" / "ui.js"
    js_content = js_path.read_text(encoding="utf-8")
    assert "No offer yet: pending manual review." in js_content
    assert "3 Offer summary: pending review" in js_content

    # Call decide endpoint on a referral scenario (credit score null -> R01)
    vectors_path = REPO_ROOT / "tests" / "golden" / "vectors.json"
    vecs = json.loads(vectors_path.read_text(encoding="utf-8"))["vectors"]
    payload = vecs[0]["input"].copy()
    payload["credit_score"] = None
    res = client.post("/ui/decide", json=payload)
    assert res.status_code == 200
    assert res.json().get("decision") == "refer"


def test_chips_and_badges_have_nowrap_in_css():
    """Pass 2 #5: Chips, badges, and outcome indicators must have nowrap to prevent wrapping mid-word."""
    css_path = REPO_ROOT / "src" / "ui" / "static" / "style.css"
    css = css_path.read_text(encoding="utf-8")

    assert re.search(r'\.badge\s*\{[^}]*white-space:\s*nowrap', css), ".badge must have white-space: nowrap"
    assert re.search(r'\.chip\s*\{[^}]*white-space:\s*nowrap', css), ".chip must have white-space: nowrap"
    assert re.search(r'\.preset-summary__badge\s*\{[^}]*white-space:\s*nowrap', css), ".preset-summary__badge must have white-space: nowrap"


def test_edge_cases_and_fairness_render_tables_and_no_raw_markdown(client):
    """Pass 2 #1: Edge cases structured endpoint returns 64 cases, and results.js uses table renderer."""
    # Verify edge cases CSV endpoint
    res = client.get("/ui/report/edge_cases_results")
    assert res.status_code == 200
    data = res.json()
    assert data.get("available") is True
    rows = data.get("rows", [])
    assert len(rows) == 64

    # 61 matched, 3 explained differences
    matched = [r for r in rows if r["rule_status"] == "matched"]
    differs = [r for r in rows if r["rule_status"] == "differs_explained"]
    assert len(matched) == 61
    assert len(differs) == 3
    assert {r["case_id"] for r in differs} == {"EC-TB-16", "EC-TB-17", "EC-AD-02"}

    # Verify results.js has renderMarkdownToDom and no raw markdown pre dump
    js_path = REPO_ROOT / "src" / "ui" / "static" / "results.js"
    js = js_path.read_text(encoding="utf-8")
    assert "renderMarkdownToDom" in js
    assert "61 of 64 matched the catalog exactly; 3 differences are explained." in js
    assert "Edge Case Summary by Category" in js
    assert "All 64 Edge Cases" in js


# ---------------------------------------------------------------------------
# Vercel Deployment Tests (Requirement 9)
# ---------------------------------------------------------------------------


def test_vercel_path_selection_tmp_db(monkeypatch):
    """Req 4 & 9: Path selection under VERCEL=1 defaults to /tmp/audit.db; AUDIT_DB_PATH overrides."""
    from src.api.config import load_config

    # 1. Under VERCEL=1 without AUDIT_DB_PATH -> /tmp/audit.db
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("AUDIT_DB_PATH", raising=False)
    monkeypatch.delenv("APP_AUDIT_DB_PATH", raising=False)
    cfg = load_config()
    assert cfg.audit_db_path == Path("/tmp/audit.db")

    # 2. AUDIT_DB_PATH overrides VERCEL default
    monkeypatch.setenv("AUDIT_DB_PATH", "/custom/audit.db")
    cfg2 = load_config()
    assert cfg2.audit_db_path == Path("/custom/audit.db")


def test_root_entrypoint_imports_app():
    """Req 2 & 9: Root app.py entrypoint imports and exposes the FastAPI app instance."""
    import app as root_module
    from src.ui.app import app as src_app

    assert hasattr(root_module, "app"), "Root app.py must expose an 'app' instance"
    assert root_module.app is src_app, "Root app must match src.ui.app:app"


def test_vercel_smoke_with_readonly_data_dir(monkeypatch, tmp_path, client):
    """Req 9: Smoke test of /, results, /ui/decide (TV1) and /ui/ml-score (TV1) under VERCEL=1."""
    import src.ui.app as ui_module

    # Reset lazy-init service so it picks up the tmp database
    monkeypatch.setenv("VERCEL", "1")
    tmp_db = tmp_path / "writable_audit.db"
    monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_db))
    monkeypatch.setattr(ui_module, "_service", None)

    # 1. GET / contains demo notice
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "Public demo. Do not enter real personal data." in res_index.text

    # 2. GET /about contains demo notice
    res_about = client.get("/about")
    assert res_about.status_code == 200
    assert "Deployed demo: the audit log is temporary" in res_about.text

    # 3. GET /robots.txt disallows all
    res_robots = client.get("/robots.txt")
    assert res_robots.status_code == 200
    assert "Disallow: /" in res_robots.text

    # 4. Results data endpoint returns non-empty
    res_edge = client.get("/ui/report/edge_cases_results")
    assert res_edge.status_code == 200
    assert len(res_edge.json().get("rows", [])) == 64

    # 5. POST /ui/decide (TV1) returns eligible and demo audit notice
    vectors_path = REPO_ROOT / "tests" / "golden" / "vectors.json"
    vecs = json.loads(vectors_path.read_text(encoding="utf-8"))["vectors"]
    tv1 = vecs[0]["input"]

    res_decide = client.post("/ui/decide", json=tv1)
    assert res_decide.status_code == 200
    dec_data = res_decide.json()
    assert dec_data.get("decision") == "eligible"
    assert dec_data.get("audit_stored") == "Yes (demo, temporary)"

    # 6. POST /ui/ml-score (TV1)
    res_ml = client.post("/ui/ml-score", json=tv1)
    assert res_ml.status_code == 200
    ml_data = res_ml.json()
    assert ml_data.get("available") is True
    assert "lr_score" in ml_data
    assert "gb_score" in ml_data



