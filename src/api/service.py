"""
Decision service layer coordinating engine, explain, and audit.

Implements: FR-01, FR-10 to FR-16, NFR-01, NFR-02, WP-14
Spec: docs/05-architecture.md, docs/audit-log-spec.md §6
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import referencing
from jsonschema import Draft202012Validator

from src.api.config import AppConfig, load_config
from src.audit.canonical import compute_applicant_ref, compute_input_hash
from src.audit.replay import replay_decision
from src.audit.store import AuditStore
from src.engine.engine import decide as engine_decide
from src.engine.hygiene import run_hygiene_analysis
from src.engine.rule_loader import RuleSet, load_rules
from src.engine.ruleset_hash import compute_hash_from_root
from src.explain.notice import build_notice
from src.explain.trace import build_trace, validate_trace
from src.facts.fact_builder import get_validator as get_input_validator


class DecisionServiceError(Exception):
    def __init__(
        self, code: str, message: str, status_code: int = 500, suggested_route: str | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.suggested_route = suggested_route


class DecisionService:
    def __init__(
        self,
        config: AppConfig | None = None,
        repo_root: Path | str | None = None,
        audit_store: AuditStore | None = None,
        clock_fn: Callable[[], str] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root else Path(".")
        self.config = config or load_config()
        self.audit_store = audit_store or AuditStore(self.config.audit_db_path)
        self.clock_fn = clock_fn or (lambda: datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))

        # 1. Load rule set
        rules_dir = self.repo_root / "rules"
        params_path = self.repo_root / "params" / "params.toml"
        self.rule_set = load_rules(rules_dir, params_path)
        if self.rule_set is None:
            raise RuntimeError("Failed to load rule set")

        # 2. Check rule set version and hash pin
        import tomllib

        params_meta = tomllib.loads(params_path.read_text(encoding="utf-8")).get("meta", {})
        params_ver = params_meta.get("params_version", "0.1.0")
        rules_ver = self.rule_set.manifest.rules_version
        self.rule_set_version = f"rules-{rules_ver}+params-{params_ver}"
        self.rule_set_hash = compute_hash_from_root(self.repo_root)

        pin_path = self.repo_root / "tests" / "golden" / "rule_set_pin.json"
        if pin_path.exists():
            pin_data = json.loads(pin_path.read_text(encoding="utf-8"))
            if self.rule_set_hash != pin_data.get("rule_set_hash"):
                raise RuntimeError(
                    f"Rule set hash mismatch: current {self.rule_set_hash} != pin {pin_data.get('rule_set_hash')}"
                )
            if self.rule_set_version != pin_data.get("rule_set_version"):
                raise RuntimeError(
                    f"Rule set version mismatch: current {self.rule_set_version} != pin {pin_data.get('rule_set_version')}"
                )

        # 3. Startup hygiene check
        findings, _ = run_hygiene_analysis(self.rule_set, self.repo_root)
        if findings:
            raise RuntimeError(f"Hygiene check failed at startup: {[str(f) for f in findings]}")

        # 4. Cache response validators
        self._init_response_validators()

    def _init_response_validators(self) -> None:
        resp_schema_path = self.repo_root / "schemas" / "response.schema.json"
        trace_schema_path = self.repo_root / "schemas" / "trace.schema.json"

        resp_schema = json.loads(resp_schema_path.read_text(encoding="utf-8"))
        trace_schema = json.loads(trace_schema_path.read_text(encoding="utf-8"))

        registry = referencing.Registry().with_resource(
            "loan-decision-trace.schema.json",
            referencing.Resource.from_contents(trace_schema),
        )

        self.response_validator = Draft202012Validator(resp_schema, registry=registry)

        def _make_sub_validator(def_name: str) -> Draft202012Validator:
            sub = {
                "$schema": resp_schema.get("$schema"),
                "$defs": resp_schema.get("$defs"),
                "$ref": f"#/$defs/{def_name}",
            }
            return Draft202012Validator(sub, registry=registry)

        self.validation_err_validator = _make_sub_validator("validation_error_response")
        self.error_validator = _make_sub_validator("error_response")
        self.replay_validator = _make_sub_validator("replay_result")
        self.review_validator = _make_sub_validator("review_response")
        self.queue_validator = _make_sub_validator("queue_response")
        self.health_validator = _make_sub_validator("health_response")

    def validate_request_input(self, body: Any) -> list[dict[str, str]]:
        """Validate input body against schemas/input.schema.json."""
        if not isinstance(body, dict):
            return [
                {
                    "field": "$",
                    "code": "INVALID_BODY",
                    "message": "Request body must be a JSON object",
                }
            ]

        input_validator = get_input_validator(self.repo_root / "schemas" / "input.schema.json")
        errors = list(input_validator.iter_errors(body))
        if not errors:
            return []

        field_errors: list[dict[str, str]] = []
        for err in errors:
            field = ".".join(str(p) for p in err.path) if err.path else "$"
            v = err.validator
            if v == "type":
                code = "INVALID_TYPE"
            elif v in ("minimum", "exclusiveMinimum"):
                code = "VALUE_BELOW_MINIMUM"
            elif v in ("maximum", "exclusiveMaximum"):
                code = "VALUE_ABOVE_MAXIMUM"
            elif v == "enum":
                code = "INVALID_CHOICE"
            elif v == "pattern":
                code = "PATTERN_MISMATCH"
            elif v == "required":
                code = "REQUIRED_FIELD_MISSING"
                if "is a required property" in err.message:
                    # e.g. 'applicant_id' is a required property
                    import re

                    m = re.search(r"'([^']+)' is a required property", err.message)
                    if m:
                        field = m.group(1)
            elif v == "additionalProperties":
                code = "UNKNOWN_FIELD"
                import re

                m = re.search(
                    r"Additional properties are not allowed \('([^']+)' was unexpected\)",
                    err.message,
                )
                if m:
                    field = m.group(1)
            else:
                code = f"INVALID_{v.upper()}" if v else "INVALID_FIELD"

            field_errors.append({"field": field, "code": code, "message": err.message})

        return field_errors

    def decide(self, body: dict[str, Any]) -> dict[str, Any]:
        """
        Evaluate application, build trace and notice, write audit record, return response.
        Fail closed: an error body never contains a decision.
        """
        # 1. Check audit chain integrity before proceeding
        is_ok, _, msg = self.audit_store.verify_chain()
        if not is_ok:
            raise DecisionServiceError(
                code="AUDIT_UNAVAILABLE",
                message=f"Audit chain verification failed: {msg}",
                status_code=503,
                suggested_route="refer",
            )

        # 2. Evaluate rules
        try:
            engine_result = engine_decide(body, self.rule_set)
        except Exception as e:
            raise DecisionServiceError(
                code="SYSTEM_ERROR",
                message=f"Engine evaluation failed: {e}",
                status_code=500,
                suggested_route="refer",
            ) from e

        # 3. Compute hashes
        applicant_ref = compute_applicant_ref(str(body["applicant_id"]))
        input_hash = compute_input_hash(body)

        # 4. Build trace and notice
        try:
            trace = build_trace(
                engine_result=engine_result,
                rule_set=self.rule_set,
                applicant_ref=applicant_ref,
                input_hash=input_hash,
                rule_set_version=self.rule_set_version,
                rule_set_hash=self.rule_set_hash,
            )
            notice = build_notice(
                trace=trace,
                rule_set=self.rule_set,
                application=body,
            )
        except Exception as e:
            raise DecisionServiceError(
                code="SYSTEM_ERROR",
                message=f"Explanation or notice generation failed: {e}",
                status_code=500,
                suggested_route="refer",
            ) from e

        # 5. Append to audit store
        evaluated_at = self.clock_fn()
        try:
            decision_id, _ = self.audit_store.append_decision(
                applicant_ref=applicant_ref,
                input_hash=input_hash,
                rule_set_version=self.rule_set_version,
                rule_set_hash=self.rule_set_hash,
                evaluated_at=evaluated_at,
                decision=engine_result["decision"],
                reason_codes=engine_result.get("reason_codes", []),
                offer=trace.get("offer"),
                trace=trace,
                notice=notice,
                validated_input=body,
                system_flags={},
                store_input_snapshot=self.config.store_input_snapshot,
            )
        except Exception as e:
            raise DecisionServiceError(
                code="AUDIT_UNAVAILABLE",
                message=f"Audit log write failed: {e}",
                status_code=503,
                suggested_route="refer",
            ) from e

        # 6. Populate decision_id and evaluated_at in trace
        trace["decision_id"] = decision_id
        trace["evaluated_at"] = evaluated_at
        validate_trace(trace, self.repo_root / "schemas" / "trace.schema.json")

        # 7. Construct response body
        response_body: dict[str, Any] = {
            "decision_id": decision_id,
            "evaluated_at": evaluated_at,
            "rule_set_version": self.rule_set_version,
            "rule_set_hash": self.rule_set_hash,
            "decision": engine_result["decision"],
            "reason_codes": engine_result.get("reason_codes", []),
            "offer": trace.get("offer"),
            "notice": notice,
            "trace": trace,
        }

        if engine_result["decision"] == "refer":
            response_body["review"] = {
                "status": "pending",
                "action_id": None,
                "reviewer": None,
                "reason": None,
                "acted_at": None,
            }

        # 8. Validate response against schema
        errors = list(self.response_validator.iter_errors(response_body))
        if errors:
            err_msg = "; ".join(f"{e.json_path}: {e.message}" for e in errors)
            raise DecisionServiceError(
                code="SYSTEM_ERROR",
                message=f"Response schema validation failed: {err_msg}",
                status_code=500,
                suggested_route="refer",
            )

        return response_body

    def get_decision(self, decision_id: str) -> dict[str, Any]:
        record = self.audit_store.get_decision(decision_id)
        if not record:
            raise DecisionServiceError(
                code="NOT_FOUND",
                message=f"Decision '{decision_id}' not found",
                status_code=404,
            )

        response_body: dict[str, Any] = {
            "decision_id": record["decision_id"],
            "evaluated_at": record["evaluated_at"],
            "rule_set_version": record["rule_set_version"],
            "rule_set_hash": record["rule_set_hash"],
            "decision": record["decision"],
            "reason_codes": record["reason_codes"],
            "offer": record["offer"],
            "notice": record["notice"],
            "trace": record["trace"],
        }

        if record["decision"] == "refer":
            action = self.audit_store.get_reviewer_action(decision_id)
            if action:
                response_body["review"] = {
                    "status": action["effective_outcome"],
                    "action_id": action["action_id"],
                    "reviewer": action["reviewer"],
                    "reason": action["reason"],
                    "acted_at": action["acted_at"],
                }
            else:
                response_body["review"] = {
                    "status": "pending",
                    "action_id": None,
                    "reviewer": None,
                    "reason": None,
                    "acted_at": None,
                }

        errors = list(self.response_validator.iter_errors(response_body))
        if errors:
            err_msg = "; ".join(f"{e.json_path}: {e.message}" for e in errors)
            raise DecisionServiceError(
                code="SYSTEM_ERROR",
                message=f"Stored decision response schema validation failed: {err_msg}",
                status_code=500,
                suggested_route="refer",
            )

        return response_body

    def replay_decision(
        self, decision_id: str, alt_rule_set: RuleSet | None = None
    ) -> dict[str, Any]:
        """
        Replay a decision using the current (or alternative) rule set.
        """
        active_rule_set = alt_rule_set or self.rule_set
        active_ver = (
            self.rule_set_version
            if alt_rule_set is None
            else f"rules-{active_rule_set.manifest.rules_version}+params-0.1.0"
        )
        active_hash = (
            compute_hash_from_root(self.repo_root) if alt_rule_set is None else "custom_hash"
        )

        def _rebuild(
            validated_input: dict[str, Any], dec_id: str, eval_at: str
        ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, str]:
            eng_res = engine_decide(validated_input, active_rule_set)
            app_ref = compute_applicant_ref(str(validated_input["applicant_id"]))
            inp_hash = compute_input_hash(validated_input)
            tr = build_trace(
                engine_result=eng_res,
                rule_set=active_rule_set,
                applicant_ref=app_ref,
                input_hash=inp_hash,
                rule_set_version=active_ver,
                rule_set_hash=active_hash,
                decision_id=dec_id,
                evaluated_at=eval_at,
            )
            notc = build_notice(trace=tr, rule_set=active_rule_set, application=validated_input)
            res_fields = {
                "decision": eng_res["decision"],
                "reason_codes": eng_res.get("reason_codes", []),
                "offer": tr.get("offer"),
            }
            return res_fields, tr, notc, active_ver, active_hash

        try:
            result = replay_decision(
                decision_id=decision_id,
                db_path=self.audit_store.db_path,
                rebuild_fn=_rebuild,
            )
        except ValueError as e:
            raise DecisionServiceError(
                code="NOT_FOUND",
                message=str(e),
                status_code=404,
            ) from e

        errors = list(self.replay_validator.iter_errors(result))
        if errors:
            err_msg = "; ".join(f"{e.json_path}: {e.message}" for e in errors)
            raise DecisionServiceError(
                code="SYSTEM_ERROR",
                message=f"Replay result schema validation failed: {err_msg}",
                status_code=500,
                suggested_route="refer",
            )

        return result

    def review_decision(
        self,
        decision_id: str,
        reviewer: str,
        action: str,
        reason: str,
    ) -> dict[str, Any]:
        """
        Record reviewer action according to docs/human-oversight-policy.md §4.
        """
        record = self.audit_store.get_decision(decision_id)
        if not record:
            raise DecisionServiceError(
                code="NOT_FOUND",
                message=f"Decision '{decision_id}' not found",
                status_code=404,
            )

        # Check already reviewed
        existing = self.audit_store.get_reviewer_action(decision_id)
        if existing:
            raise DecisionServiceError(
                code="ALREADY_REVIEWED",
                message=f"Decision '{decision_id}' already has a reviewer action",
                status_code=409,
            )

        # Check reason length
        trimmed_reason = reason.strip() if reason else ""
        if len(trimmed_reason) < self.config.min_reason_length:
            raise DecisionServiceError(
                code="REASON_REQUIRED",
                message=f"Reason must be at least {self.config.min_reason_length} characters after trimming",
                status_code=422,
            )

        # Check action permissions
        decision = record["decision"]
        if decision == "refer":
            if action == "approve":
                effective_outcome = "approved"
            elif action == "deny":
                effective_outcome = "denied"
            else:
                raise DecisionServiceError(
                    code="ACTION_NOT_ALLOWED",
                    message="Action 'override' is not allowed for refer decisions",
                    status_code=422,
                )
        elif decision == "ineligible":
            if action == "override":
                effective_outcome = "approved"
            else:
                raise DecisionServiceError(
                    code="ACTION_NOT_ALLOWED",
                    message=f"Action '{action}' is not allowed for ineligible decisions; use 'override'",
                    status_code=422,
                )
        elif decision == "eligible":
            if action == "override":
                effective_outcome = "denied"
            else:
                raise DecisionServiceError(
                    code="ACTION_NOT_ALLOWED",
                    message=f"Action '{action}' is not allowed for eligible decisions; use 'override'",
                    status_code=422,
                )
        else:
            raise DecisionServiceError(
                code="ACTION_NOT_ALLOWED",
                message=f"Decisions with outcome '{decision}' cannot be reviewed",
                status_code=422,
            )

        acted_at = self.clock_fn()
        action_id = self.audit_store.append_reviewer_action(
            decision_id=decision_id,
            reviewer=reviewer,
            action=action,
            reason=reason,
            acted_at=acted_at,
            effective_outcome=effective_outcome,
        )

        resp = {
            "decision_id": decision_id,
            "action_id": action_id,
            "reviewer": reviewer,
            "action": action,
            "reason": reason,
            "acted_at": acted_at,
            "effective_outcome": effective_outcome,
        }

        errors = list(self.review_validator.iter_errors(resp))
        if errors:
            err_msg = "; ".join(f"{e.json_path}: {e.message}" for e in errors)
            raise DecisionServiceError(
                code="SYSTEM_ERROR",
                message=f"Review response schema validation failed: {err_msg}",
                status_code=500,
                suggested_route="refer",
            )

        return resp

    def get_review_queue(self, limit: int | None = None) -> dict[str, Any]:
        eff_limit = limit if limit is not None else self.config.queue_default_limit
        items = self.audit_store.get_pending_review_queue(limit=eff_limit)
        total_pending = self.audit_store.count_pending_review_queue()

        resp = {
            "items": items,
            "total_pending": total_pending,
        }

        errors = list(self.queue_validator.iter_errors(resp))
        if errors:
            err_msg = "; ".join(f"{e.json_path}: {e.message}" for e in errors)
            raise DecisionServiceError(
                code="SYSTEM_ERROR",
                message=f"Queue response schema validation failed: {err_msg}",
                status_code=500,
                suggested_route="refer",
            )

        return resp

    def get_health(self) -> dict[str, Any]:
        is_ok, _, _ = self.audit_store.verify_chain()
        resp = {
            "status": "ok",
            "rule_set_version": self.rule_set_version,
            "rule_set_hash": self.rule_set_hash,
            "audit_chain_ok": is_ok,
        }

        errors = list(self.health_validator.iter_errors(resp))
        if errors:
            err_msg = "; ".join(f"{e.json_path}: {e.message}" for e in errors)
            raise DecisionServiceError(
                code="SYSTEM_ERROR",
                message=f"Health response schema validation failed: {err_msg}",
                status_code=500,
                suggested_route="refer",
            )

        return resp
