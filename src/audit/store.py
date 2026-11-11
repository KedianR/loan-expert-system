"""
Audit log store and hash chain management.

Implements: FR-15, NFR-02, NFR-08, DR-03, WP-13
Spec: docs/audit-log-spec.md
AGENTS.md: Interface rules (calls go downward only; src/audit imports nothing from src/engine, src/explain, src/calc).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.audit.canonical import canonical_json

INIT_SQL = """
CREATE TABLE IF NOT EXISTS audit_records (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT UNIQUE NOT NULL,
    applicant_ref TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    rule_set_version TEXT NOT NULL,
    rule_set_hash TEXT NOT NULL,
    evaluated_at TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason_codes TEXT NOT NULL,
    offer TEXT,
    trace TEXT NOT NULL,
    notice TEXT NOT NULL,
    system_flags TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    record_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_inputs (
    input_hash TEXT PRIMARY KEY,
    input TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviewer_actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    acted_at TEXT NOT NULL,
    effective_outcome TEXT NOT NULL
);

-- Append-only triggers: abort on UPDATE or DELETE
CREATE TRIGGER IF NOT EXISTS trg_audit_records_no_update
BEFORE UPDATE ON audit_records
BEGIN
    SELECT RAISE(ABORT, 'audit tables are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_audit_records_no_delete
BEFORE DELETE ON audit_records
BEGIN
    SELECT RAISE(ABORT, 'audit tables are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_audit_inputs_no_update
BEFORE UPDATE ON audit_inputs
BEGIN
    SELECT RAISE(ABORT, 'audit tables are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_audit_inputs_no_delete
BEFORE DELETE ON audit_inputs
BEGIN
    SELECT RAISE(ABORT, 'audit tables are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_reviewer_actions_no_update
BEFORE UPDATE ON reviewer_actions
BEGIN
    SELECT RAISE(ABORT, 'audit tables are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_reviewer_actions_no_delete
BEFORE DELETE ON reviewer_actions
BEGIN
    SELECT RAISE(ABORT, 'audit tables are append-only');
END;
"""


def get_connection(db_path: Path | str) -> sqlite3.Connection:
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_audit_db(db_path: Path | str) -> None:
    """Initialize audit database tables and append-only triggers."""
    conn = get_connection(db_path)
    try:
        conn.executescript(INIT_SQL)
        conn.commit()
    finally:
        conn.close()


def calculate_record_hash(prev_hash: str, row_dict: dict[str, Any]) -> str:
    """
    Compute record_hash:
    'sha256:' + hex(SHA-256(prev_hash + '\n' + canonical(row without record_hash)))
    """
    import hashlib

    canon = canonical_json(row_dict)
    payload = f"{prev_hash}\n{canon}".encode()
    digest = hashlib.sha256(payload).hexdigest()
    return f"sha256:{digest}"


class AuditStore:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        init_audit_db(self.db_path)

    def append_decision(
        self,
        applicant_ref: str,
        input_hash: str,
        rule_set_version: str,
        rule_set_hash: str,
        evaluated_at: str,
        decision: str,
        reason_codes: list[str],
        offer: dict[str, Any] | None,
        trace: dict[str, Any],
        notice: dict[str, Any],
        validated_input: dict[str, Any] | None = None,
        system_flags: dict[str, Any] | None = None,
        store_input_snapshot: bool = True,
    ) -> tuple[str, str]:
        """
        Append a decision record to the audit store in a single transaction.
        Returns (decision_id, record_hash).
        """
        flags = system_flags or {}
        conn = get_connection(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")

            # 1. Store input snapshot if enabled
            if store_input_snapshot and validated_input is not None:
                canon_input = canonical_json(validated_input)
                conn.execute(
                    "INSERT OR IGNORE INTO audit_inputs (input_hash, input) VALUES (?, ?)",
                    (input_hash, canon_input),
                )

            # 2. Get next seq
            cur = conn.execute("SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq FROM audit_records")
            row = cur.fetchone()
            next_seq = int(row["next_seq"])
            decision_id = f"d-{next_seq:04d}"

            # 3. Get previous record_hash
            if next_seq == 1:
                prev_hash = "sha256:" + "0" * 64
            else:
                cur = conn.execute(
                    "SELECT record_hash FROM audit_records WHERE seq = ?", (next_seq - 1,)
                )
                prev_row = cur.fetchone()
                if not prev_row:
                    raise RuntimeError(f"Missing predecessor record at seq {next_seq - 1}")
                prev_hash = prev_row["record_hash"]

            # Update decision_id and evaluated_at in trace copy
            trace_copy = dict(trace)
            trace_copy["decision_id"] = decision_id
            trace_copy["evaluated_at"] = evaluated_at

            # Prepare row_dict for hashing
            row_dict: dict[str, Any] = {
                "seq": next_seq,
                "decision_id": decision_id,
                "applicant_ref": applicant_ref,
                "input_hash": input_hash,
                "rule_set_version": rule_set_version,
                "rule_set_hash": rule_set_hash,
                "evaluated_at": evaluated_at,
                "decision": decision,
                "reason_codes": reason_codes,
                "offer": offer,
                "trace": trace_copy,
                "notice": notice,
                "system_flags": flags,
                "prev_hash": prev_hash,
            }

            record_hash = calculate_record_hash(prev_hash, row_dict)

            # Insert record
            conn.execute(
                """
                INSERT INTO audit_records (
                    seq, decision_id, applicant_ref, input_hash, rule_set_version,
                    rule_set_hash, evaluated_at, decision, reason_codes, offer,
                    trace, notice, system_flags, prev_hash, record_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    next_seq,
                    decision_id,
                    applicant_ref,
                    input_hash,
                    rule_set_version,
                    rule_set_hash,
                    evaluated_at,
                    decision,
                    canonical_json(reason_codes),
                    canonical_json(offer) if offer is not None else None,
                    canonical_json(trace_copy),
                    canonical_json(notice),
                    canonical_json(flags),
                    prev_hash,
                    record_hash,
                ),
            )

            conn.commit()
            return decision_id, record_hash

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        conn = get_connection(self.db_path)
        try:
            cur = conn.execute("SELECT * FROM audit_records WHERE decision_id = ?", (decision_id,))
            row = cur.fetchone()
            if not row:
                return None

            record = dict(row)
            record["reason_codes"] = json.loads(record["reason_codes"])
            record["offer"] = json.loads(record["offer"]) if record["offer"] else None
            record["trace"] = json.loads(record["trace"])
            record["notice"] = json.loads(record["notice"])
            record["system_flags"] = json.loads(record["system_flags"])
            return record
        finally:
            conn.close()

    def get_input(self, input_hash: str) -> dict[str, Any] | None:
        conn = get_connection(self.db_path)
        try:
            cur = conn.execute("SELECT input FROM audit_inputs WHERE input_hash = ?", (input_hash,))
            row = cur.fetchone()
            if not row:
                return None
            return json.loads(row["input"])
        finally:
            conn.close()

    def append_reviewer_action(
        self,
        decision_id: str,
        reviewer: str,
        action: str,
        reason: str,
        acted_at: str,
        effective_outcome: str,
    ) -> int:
        conn = get_connection(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute(
                """
                INSERT INTO reviewer_actions (
                    decision_id, reviewer, action, reason, acted_at, effective_outcome
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (decision_id, reviewer, action, reason, acted_at, effective_outcome),
            )
            action_id = cur.lastrowid
            conn.commit()
            return action_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_reviewer_action(self, decision_id: str) -> dict[str, Any] | None:
        conn = get_connection(self.db_path)
        try:
            cur = conn.execute(
                "SELECT * FROM reviewer_actions WHERE decision_id = ? ORDER BY action_id DESC LIMIT 1",
                (decision_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_pending_review_queue(self, limit: int = 50) -> list[dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cur = conn.execute(
                """
                SELECT r.decision_id, r.evaluated_at, r.applicant_ref, r.reason_codes, r.rule_set_version
                FROM audit_records r
                WHERE r.decision = 'refer'
                  AND NOT EXISTS (
                      SELECT 1 FROM reviewer_actions a WHERE a.decision_id = r.decision_id
                  )
                ORDER BY r.seq ASC
                LIMIT ?
                """,
                (limit,),
            )
            items = []
            for row in cur.fetchall():
                d = dict(row)
                d["reason_codes"] = json.loads(d["reason_codes"])
                items.append(d)
            return items
        finally:
            conn.close()

    def count_pending_review_queue(self) -> int:
        conn = get_connection(self.db_path)
        try:
            cur = conn.execute(
                """
                SELECT COUNT(*) as cnt
                FROM audit_records r
                WHERE r.decision = 'refer'
                  AND NOT EXISTS (
                      SELECT 1 FROM reviewer_actions a WHERE a.decision_id = r.decision_id
                  )
                """
            )
            row = cur.fetchone()
            return int(row["cnt"]) if row else 0
        finally:
            conn.close()

    def verify_chain(self) -> tuple[bool, int, str]:
        """
        Verify hash chain from row 1.
        Returns (is_ok, count_or_failing_seq, message).
        """
        conn = get_connection(self.db_path)
        try:
            cur = conn.execute("SELECT * FROM audit_records ORDER BY seq ASC")
            rows = cur.fetchall()
            if not rows:
                return True, 0, "OK 0 records"

            prev_expected_hash = "sha256:" + "0" * 64

            for row in rows:
                seq = row["seq"]
                if row["prev_hash"] != prev_expected_hash:
                    return (
                        False,
                        seq,
                        f"Break at seq {seq}: prev_hash {row['prev_hash']} != expected {prev_expected_hash}",
                    )

                row_dict: dict[str, Any] = {
                    "seq": seq,
                    "decision_id": row["decision_id"],
                    "applicant_ref": row["applicant_ref"],
                    "input_hash": row["input_hash"],
                    "rule_set_version": row["rule_set_version"],
                    "rule_set_hash": row["rule_set_hash"],
                    "evaluated_at": row["evaluated_at"],
                    "decision": row["decision"],
                    "reason_codes": json.loads(row["reason_codes"]),
                    "offer": json.loads(row["offer"]) if row["offer"] else None,
                    "trace": json.loads(row["trace"]),
                    "notice": json.loads(row["notice"]),
                    "system_flags": json.loads(row["system_flags"]),
                    "prev_hash": row["prev_hash"],
                }

                calc_hash = calculate_record_hash(row["prev_hash"], row_dict)
                if calc_hash != row["record_hash"]:
                    return (
                        False,
                        seq,
                        f"Break at seq {seq}: record_hash {row['record_hash']} != computed {calc_hash}",
                    )

                prev_expected_hash = row["record_hash"]

            return True, len(rows), f"OK {len(rows)} records"
        finally:
            conn.close()
