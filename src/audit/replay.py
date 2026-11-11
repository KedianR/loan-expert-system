"""
Audit record replay and verification.

Implements: FR-16, WP-13
Spec: docs/audit-log-spec.md §7
AGENTS.md: Hard rule 2 (no floats), Interface rules (no imports from src/engine, src/explain, src/calc).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.audit.store import AuditStore


def _diff_structures(
    recorded: Any, replayed: Any, path: str, ignored_paths: set[str]
) -> list[dict[str, Any]]:
    """Recursively find differences between two JSON structures."""
    if path in ignored_paths:
        return []

    diffs: list[dict[str, Any]] = []

    if type(recorded) is not type(replayed):
        diffs.append({"path": path, "recorded": recorded, "replayed": replayed})
        return diffs

    if isinstance(recorded, dict):
        all_keys = sorted(set(recorded.keys()) | set(replayed.keys()))
        for k in all_keys:
            subpath = f"{path}.{k}" if path else k
            if subpath in ignored_paths:
                continue
            if k not in recorded:
                diffs.append({"path": subpath, "recorded": None, "replayed": replayed[k]})
            elif k not in replayed:
                diffs.append({"path": subpath, "recorded": recorded[k], "replayed": None})
            else:
                diffs.extend(_diff_structures(recorded[k], replayed[k], subpath, ignored_paths))

    elif isinstance(recorded, list):
        if len(recorded) != len(replayed):
            diffs.append(
                {"path": f"{path}.length", "recorded": len(recorded), "replayed": len(replayed)}
            )
        min_len = min(len(recorded), len(replayed))
        for i in range(min_len):
            subpath = f"{path}[{i}]"
            diffs.extend(_diff_structures(recorded[i], replayed[i], subpath, ignored_paths))

    else:
        if recorded != replayed:
            diffs.append({"path": path, "recorded": recorded, "replayed": replayed})

    return diffs


def replay_decision(
    decision_id: str,
    db_path: Path | str,
    rebuild_fn: Callable[
        [dict[str, Any], str, str], tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, str]
    ],
) -> dict[str, Any]:
    """
    Replay a stored decision against the rebuild function.
    rebuild_fn(input, decision_id, evaluated_at) -> (result_fields, trace, notice, current_version, current_hash)
    """
    store = AuditStore(db_path)
    record = store.get_decision(decision_id)
    if not record:
        raise ValueError(f"Decision '{decision_id}' not found in audit log")

    rule_set_version_recorded = record["rule_set_version"]
    rule_set_hash_recorded = record["rule_set_hash"]
    input_hash = record["input_hash"]

    # 1. Load input snapshot
    validated_input = store.get_input(input_hash)
    if validated_input is None:
        return {
            "decision_id": decision_id,
            "match": False,
            "rule_set_version_recorded": rule_set_version_recorded,
            "rule_set_hash_recorded": rule_set_hash_recorded,
            "rule_set_hash_current": rule_set_hash_recorded,
            "differences": [],
            "notice_match": False,
            "note": "no input snapshot",
        }

    evaluated_at = record["evaluated_at"]

    # 2. Rebuild decision using provided callback
    result_fields, replayed_trace, replayed_notice, current_version, current_hash = rebuild_fn(
        validated_input, decision_id, evaluated_at
    )

    differences: list[dict[str, Any]] = []
    ignored_paths = {
        "decision_id",
        "evaluated_at",
        "trace.decision_id",
        "trace.evaluated_at",
    }

    # Compare decision
    if record["decision"] != result_fields.get("decision"):
        differences.append(
            {
                "path": "decision",
                "recorded": record["decision"],
                "replayed": result_fields.get("decision"),
            }
        )

    # Compare reason_codes
    if record["reason_codes"] != result_fields.get("reason_codes"):
        differences.append(
            {
                "path": "reason_codes",
                "recorded": record["reason_codes"],
                "replayed": result_fields.get("reason_codes"),
            }
        )

    # Compare offer
    if record["offer"] != result_fields.get("offer"):
        differences.extend(
            _diff_structures(record["offer"], result_fields.get("offer"), "offer", ignored_paths)
        )

    # Compare full trace
    differences.extend(_diff_structures(record["trace"], replayed_trace, "trace", ignored_paths))

    # Compare notice
    recorded_notice = record["notice"]
    notice_diffs = _diff_structures(recorded_notice, replayed_notice, "notice", ignored_paths)
    notice_match = len(notice_diffs) == 0

    note = None
    if rule_set_hash_recorded != current_hash:
        note = "recorded rule-set hash differs from current; replaying with current rule set"

    if not notice_match:
        rec_ver = recorded_notice.get("notice_version")
        rep_ver = replayed_notice.get("notice_version")
        if rec_ver != rep_ver:
            if not note:
                note = "notice wording version changed"
        else:
            differences.extend(notice_diffs)

    match = len(differences) == 0

    res: dict[str, Any] = {
        "decision_id": decision_id,
        "match": match,
        "rule_set_version_recorded": rule_set_version_recorded,
        "rule_set_hash_recorded": rule_set_hash_recorded,
        "rule_set_hash_current": current_hash,
        "differences": differences,
        "notice_match": notice_match,
    }
    if note:
        res["note"] = note

    return res
