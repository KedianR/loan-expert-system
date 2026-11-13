"""Demo UI application (WP-22).

Implements: FR-25, NFR-09, NFR-10, CR-02, P5-12.
Spec: docs/ui-spec.md.

Hard rules:
  - UI never computes a decision, amount, rate or money figure
  - ML score never feeds the decision; ML block says "Not available" on failure
  - No protected attribute collected, shown, stored or mentioned
  - Every API string inserted with textContent, never innerHTML (enforced in app.js)
  - Banner on every page: "Prototype. Illustrative policy values..."
  - ML block: "This score does not feed the decision..."
  - No new dependency beyond FastAPI + uvicorn (already used by src/api/)
  - Does NOT touch src/api, src/engine, src/calc, src/explain, src/audit
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

# Import the service function (FR-25; docs/ui-spec.md §4)
from src.api.service import DecisionService  # noqa: E402

app = FastAPI(title="Loan Eligibility Demo UI", version="1.0.0")

# Mount static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Allowed report files (no path traversal — docs/ui-spec.md §4)
_ALLOWED_REPORTS = {
    "comparison_scorecard": REPO_ROOT / "reports" / "comparison" / "scorecard.json",
    "edge_case_summary": REPO_ROOT / "reports" / "edge_cases" / "summary.md",
    "d2_tables": REPO_ROOT / "reports" / "fairness" / "d2_tables.md",
    "d3_tables": REPO_ROOT / "reports" / "fairness" / "d3_tables.md",
    "d2_rule_system": REPO_ROOT / "reports" / "fairness" / "d2_rule_system.json",
    "d3_rule_system": REPO_ROOT / "reports" / "fairness" / "d3_rule_system.json",
    "metrics_d2_lr": REPO_ROOT / "reports" / "ml" / "metrics_d2_lr.json",
    "metrics_d2_gb": REPO_ROOT / "reports" / "ml" / "metrics_d2_gb.json",
    "metrics_d3_lr": REPO_ROOT / "reports" / "ml" / "metrics_d3_lr.json",
    "metrics_d3_gb": REPO_ROOT / "reports" / "ml" / "metrics_d3_gb.json",
}

BANNER = "Prototype. Illustrative policy values and synthetic or public data. Not a real lending decision."

# Lazy-init service to avoid loading rules at import time (useful for tests)
_service: DecisionService | None = None


def _get_service() -> DecisionService:
    global _service
    if _service is None:
        _service = DecisionService(repo_root=REPO_ROOT)
    return _service


# Lazy-init ML scorer
_ml_scorer = None
_ml_scorer_error: str | None = None


def _get_ml_scorer():
    global _ml_scorer, _ml_scorer_error
    if _ml_scorer is not None:
        return _ml_scorer
    if _ml_scorer_error is not None:
        return None
    try:
        import joblib

        from src.ml.baseline import explain_logistic_regression
        from src.ml.features import load_ml_config

        model_path = REPO_ROOT / "models" / "d3_lr.joblib"
        if not model_path.exists():
            _ml_scorer_error = "Not available; run `make baseline`"
            return None
        model_data = joblib.load(model_path)
        ml_cfg = load_ml_config(REPO_ROOT / "config" / "ml.toml")
        _ml_scorer = {
            "model_data": model_data,
            "ml_cfg": ml_cfg,
            "explain_fn": explain_logistic_regression,
        }
    except Exception as exc:
        _ml_scorer_error = f"Not available ({exc})"
    return _ml_scorer


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index_page():
    """Serve the main application form page."""
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/results", response_class=HTMLResponse)
async def results_page():
    """Serve the project results page."""
    html_path = STATIC_DIR / "results.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/about", response_class=HTMLResponse)
async def about_page():
    """Serve the about page."""
    html_path = STATIC_DIR / "about.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Decision API (calls service, returns result unchanged — FR-25)
# ---------------------------------------------------------------------------


@app.post("/ui/decide")
async def ui_decide(request: Request):
    """Call the service function; return its result unchanged.

    The UI never computes a decision — it only shows what the service returns.
    ML score is a separate call (see /ui/ml-score).
    """
    body = await request.json()
    svc = _get_service()
    try:
        result = svc.decide(body)
        return JSONResponse(content=result)
    except Exception as exc:
        # Return structured error so the UI can show it
        return JSONResponse(
            status_code=422,
            content={"error": str(exc), "decision": None},
        )


# ---------------------------------------------------------------------------
# ML score API (separate from decision — docs/ui-spec.md §2 rule 2)
# ---------------------------------------------------------------------------


@app.post("/ui/ml-score")
async def ui_ml_score(request: Request):
    """Score the application with the D3 LR model; return score and top-3 contributions.

    If the model is not available, returns {"available": false, "message": "..."}.
    ML score never feeds the decision.
    """
    scorer = _get_ml_scorer()
    if scorer is None:
        return JSONResponse(
            content={
                "available": False,
                "message": _ml_scorer_error or "Not available; run `make baseline`",
                "caveat": "This score does not feed the decision. It is a ranking score, not a probability.",
            }
        )

    body = await request.json()
    try:
        import pandas as pd

        from src.ml.features import prepare_dataframe

        df = pd.DataFrame([body])
        ml_cfg = scorer["ml_cfg"]
        df_feat = prepare_dataframe(df, ml_cfg)
        exclude = {"applicant_id", "TARGET", "sim_default", "split", "income_band"}
        feat_cols = [c for c in df_feat.columns if c not in exclude]
        pipeline = scorer["model_data"]["pipeline"]
        proba = float(pipeline.predict_proba(df_feat[feat_cols])[0, 1])

        # Top-3 feature contributions via explain function
        try:
            explain_fn = scorer["explain_fn"]
            contributions = explain_fn(pipeline, df_feat[feat_cols], top_n=3)
        except Exception:
            contributions = []

        return JSONResponse(
            content={
                "available": True,
                "score": round(proba, 4),
                "caveat": "This score does not feed the decision. It is a ranking score, not a probability.",
                "contributions": contributions,
            }
        )
    except Exception as exc:
        return JSONResponse(
            content={
                "available": False,
                "message": f"Not available ({exc})",
                "caveat": "This score does not feed the decision. It is a ranking score, not a probability.",
            }
        )


# ---------------------------------------------------------------------------
# Presets API (TV1-TV9 from golden vectors)
# ---------------------------------------------------------------------------


@app.get("/ui/presets")
async def ui_presets():
    """Return TV1-TV9 presets from the golden test vectors."""
    vectors_path = REPO_ROOT / "tests" / "golden" / "vectors.json"
    if not vectors_path.exists():
        return JSONResponse(content={"presets": []})
    data = json.loads(vectors_path.read_text(encoding="utf-8"))
    presets = [
        {"id": v["id"], "description": v.get("description", ""), "input": v["input"]}
        for v in data.get("vectors", [])
    ]
    return JSONResponse(content={"presets": presets})


# ---------------------------------------------------------------------------
# Report file API (allow-list only — docs/ui-spec.md §4)
# ---------------------------------------------------------------------------


@app.get("/ui/report/{name}")
async def ui_report(name: str):
    """Serve a report file from the allow-list. No path traversal allowed."""
    if name not in _ALLOWED_REPORTS:
        raise HTTPException(status_code=404, detail=f"Report '{name}' not in allow-list.")
    path = _ALLOWED_REPORTS[name]
    if not path.exists():
        return JSONResponse(
            content={"available": False, "message": "Not generated yet; run `make phase5`"}
        )
    if path.suffix == ".json":
        return JSONResponse(content=json.loads(path.read_text(encoding="utf-8")))
    else:
        return JSONResponse(content={"content": path.read_text(encoding="utf-8")})
