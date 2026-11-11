"""
FastAPI application implementing the Loan Eligibility Decision API.

Implements: FR-01, FR-10 to FR-16, NFR-01, NFR-02, DR-02, DR-03, WP-14
Contract: api/openapi.yaml
Schemas: schemas/response.schema.json, schemas/trace.schema.json, schemas/input.schema.json
Fail closed: an error body never contains a decision field.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from src.api.service import DecisionService, DecisionServiceError

DECISION_ID_PATTERN = re.compile(r"^d-[0-9]{4,}$")
REVIEWER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def create_app(service: DecisionService | None = None) -> FastAPI:
    app = FastAPI(
        title="Loan Eligibility Decision API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
    )

    # Use provided service or instantiate default (loads rules, runs startup hygiene & pin checks)
    app.state.service = service if service is not None else DecisionService()

    @app.exception_handler(DecisionServiceError)
    async def decision_service_error_handler(request: Request, exc: DecisionServiceError):
        content: dict[str, Any] = {
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        }
        if exc.suggested_route:
            content["error"]["suggested_route"] = exc.suggested_route
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        content = {
            "error": {
                "code": "SYSTEM_ERROR",
                "message": str(exc.detail),
                "suggested_route": "refer",
            }
        }
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        content = {
            "error": {
                "code": "SYSTEM_ERROR",
                "message": f"Unexpected internal error: {exc}",
                "suggested_route": "refer",
            }
        }
        return JSONResponse(status_code=500, content=content)

    # -------------------------------------------------------------------------
    # POST /v1/decisions
    # -------------------------------------------------------------------------
    @app.post("/v1/decisions")
    async def create_decision(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Malformed JSON body",
                        "fields": [
                            {
                                "field": "$",
                                "code": "INVALID_BODY",
                                "message": "Failed to decode JSON",
                            }
                        ],
                    }
                },
            )

        svc: DecisionService = app.state.service
        field_errors = svc.validate_request_input(body)
        if field_errors:
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Request body failed schema validation",
                        "fields": field_errors,
                    }
                },
            )

        resp = svc.decide(body)
        return JSONResponse(status_code=200, content=resp)

    # -------------------------------------------------------------------------
    # GET /v1/decisions/{decision_id}
    # -------------------------------------------------------------------------
    @app.get("/v1/decisions/{decision_id}")
    async def get_decision(decision_id: str):
        if not DECISION_ID_PATTERN.match(decision_id):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Invalid decision ID format: '{decision_id}'",
                    }
                },
            )

        svc: DecisionService = app.state.service
        resp = svc.get_decision(decision_id)
        return JSONResponse(status_code=200, content=resp)

    # -------------------------------------------------------------------------
    # POST /v1/decisions/{decision_id}/replay
    # -------------------------------------------------------------------------
    @app.post("/v1/decisions/{decision_id}/replay")
    async def replay_decision_endpoint(decision_id: str):
        if not DECISION_ID_PATTERN.match(decision_id):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Invalid decision ID format: '{decision_id}'",
                    }
                },
            )

        svc: DecisionService = app.state.service
        resp = svc.replay_decision(decision_id)
        return JSONResponse(status_code=200, content=resp)

    # -------------------------------------------------------------------------
    # POST /v1/decisions/{decision_id}/review
    # -------------------------------------------------------------------------
    @app.post("/v1/decisions/{decision_id}/review")
    async def record_review_action(decision_id: str, request: Request):
        if not DECISION_ID_PATTERN.match(decision_id):
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Invalid decision ID format: '{decision_id}'",
                    }
                },
            )

        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Malformed JSON body",
                        "fields": [
                            {
                                "field": "$",
                                "code": "INVALID_BODY",
                                "message": "Failed to decode JSON",
                            }
                        ],
                    }
                },
            )

        if not isinstance(body, dict):
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Request body must be a JSON object",
                        "fields": [
                            {
                                "field": "$",
                                "code": "INVALID_BODY",
                                "message": "Expected JSON object",
                            }
                        ],
                    }
                },
            )

        reviewer = body.get("reviewer")
        action = body.get("action")
        reason = body.get("reason")

        errors: list[dict[str, str]] = []
        if (
            not reviewer
            or not isinstance(reviewer, str)
            or not REVIEWER_NAME_PATTERN.match(reviewer)
            or len(reviewer) > 64
        ):
            errors.append(
                {
                    "field": "reviewer",
                    "code": "INVALID_FIELD",
                    "message": "Reviewer must match pattern '^[A-Za-z0-9_.-]+$' and have length 1-64",
                }
            )
        if action not in ("approve", "deny", "override"):
            errors.append(
                {
                    "field": "action",
                    "code": "INVALID_CHOICE",
                    "message": "Action must be one of 'approve', 'deny', 'override'",
                }
            )
        if not isinstance(reason, str):
            errors.append(
                {
                    "field": "reason",
                    "code": "INVALID_TYPE",
                    "message": "Reason must be a string",
                }
            )

        if errors:
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Review request validation failed",
                        "fields": errors,
                    }
                },
            )

        svc: DecisionService = app.state.service
        resp = svc.review_decision(
            decision_id=decision_id,
            reviewer=reviewer,
            action=action,
            reason=reason,
        )
        return JSONResponse(status_code=200, content=resp)

    # -------------------------------------------------------------------------
    # GET /v1/review/queue
    # -------------------------------------------------------------------------
    @app.get("/v1/review/queue")
    async def get_review_queue(limit: int | None = Query(default=None, ge=1)):
        svc: DecisionService = app.state.service
        resp = svc.get_review_queue(limit=limit)
        return JSONResponse(status_code=200, content=resp)

    # -------------------------------------------------------------------------
    # GET /v1/health
    # -------------------------------------------------------------------------
    @app.get("/v1/health")
    async def get_health():
        svc: DecisionService = app.state.service
        resp = svc.get_health()
        return JSONResponse(status_code=200, content=resp)

    return app


app = create_app()
