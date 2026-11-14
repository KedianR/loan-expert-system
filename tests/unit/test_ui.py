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
    """src/ui/static/app.js must not use parseFloat/Number( on money fields.

    Rule: money fields are displayed as returned strings, not parsed.
    Exception: credit_score is not a money field and may use parseFloat.
    """
    js_file = UI_SRC_DIR / "static" / "app.js"
    assert js_file.exists(), "app.js not found"
    content = js_file.read_text(encoding="utf-8")

    # Scan each line for parseFloat( or Number( near money-ish variable names
    violations = []
    for i, line in enumerate(content.splitlines(), 1):
        # Skip the credit_score line (explicitly allowed in buildPayload)
        if "credit_score" in line:
            continue
        # Check for parseFloat( near money names
        if re.search(r"parseFloat\s*\(", line):
            for name in _MONEY_NAMES:
                if name in line.lower():
                    violations.append(
                        f"app.js:{i}: parseFloat on money-ish name '{name}': {line.strip()[:80]}"
                    )
        # Check for Number( near money names
        if re.search(r"\bNumber\s*\(", line):
            for name in _MONEY_NAMES:
                if name in line.lower():
                    violations.append(
                        f"app.js:{i}: Number( on money-ish name '{name}': {line.strip()[:80]}"
                    )
        # Check for toFixed( near money names
        if re.search(r"\btoFixed\s*\(", line):
            for name in _MONEY_NAMES:
                if name in line.lower():
                    violations.append(
                        f"app.js:{i}: toFixed on money-ish name '{name}': {line.strip()[:80]}"
                    )
    assert not violations, "parseFloat/Number(/toFixed on money fields in app.js:\n" + "\n".join(
        violations
    )
