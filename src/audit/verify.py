"""
CLI entrypoint for make audit-verify.

Implements: WP-13, docs/audit-log-spec.md
Spec: Verifies audit hash chain integrity from row 1.
"""

from __future__ import annotations

import sys
from pathlib import Path

from src.api.config import load_config
from src.audit.store import AuditStore


def main() -> None:
    config = load_config()
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(config.audit_db_path)

    if not db_path.exists():
        print(f"audit-verify: Database not found at {db_path} (0 records verified).")
        sys.exit(0)

    store = AuditStore(db_path)
    is_ok, count_or_seq, msg = store.verify_chain()
    if is_ok:
        print(f"audit-verify: OK ({count_or_seq} record(s) verified). {msg}")
        sys.exit(0)
    else:
        print(f"audit-verify: FAILED at sequence {count_or_seq}: {msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
