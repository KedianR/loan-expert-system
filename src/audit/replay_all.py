"""
CLI entrypoint for make replay-all.

Implements: WP-13, docs/audit-log-spec.md §7
Spec: Replays all stored decisions against current rule set and reports matches.
"""

from __future__ import annotations

import sys
from pathlib import Path

from src.api.config import load_config
from src.api.service import DecisionService
from src.audit.store import AuditStore, get_connection


def main() -> None:
    config = load_config()
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(config.audit_db_path)

    if not db_path.exists():
        print(f"replay-all: Database not found at {db_path} (0 decisions replayed).")
        sys.exit(0)

    store = AuditStore(db_path)
    service = DecisionService(config=config, audit_store=store)

    conn = get_connection(db_path)
    try:
        cur = conn.execute("SELECT decision_id FROM audit_records ORDER BY seq ASC")
        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        print("replay-all: OK (0 decisions in audit store).")
        sys.exit(0)

    total = len(rows)
    matched = 0
    differed = 0
    failures = []

    for r in rows:
        d_id = r["decision_id"]
        res = service.replay_decision(d_id)
        if res["match"]:
            matched += 1
        else:
            differed += 1
            failures.append((d_id, res.get("differences", []), res.get("note")))

    if differed > 0:
        print(
            f"replay-all: FAILED ({total} replayed, {matched} matched, {differed} differed)",
            file=sys.stderr,
        )
        for d_id, diffs, note in failures:
            print(f"  {d_id}: {diffs} (note: {note})", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"replay-all: OK ({total} decisions replayed, {matched} matched, 0 differed).")
        sys.exit(0)


if __name__ == "__main__":
    main()
