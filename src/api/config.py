"""
Application configuration loader.

Spec: config/app.toml, docs/05-architecture.md §6
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    audit_db_path: Path
    store_input_snapshot: bool
    host: str
    port: int
    min_reason_length: int
    queue_default_limit: int
    review_report_dir: Path


def load_config(config_path: Path | str | None = None) -> AppConfig:
    p = Path(config_path) if config_path else Path("config/app.toml")
    data: dict = {}
    if p.exists():
        data = tomllib.loads(p.read_text(encoding="utf-8"))

    audit_db = os.environ.get(
        "APP_AUDIT_DB_PATH", data.get("audit_db_path", "data/audit/audit.sqlite")
    )
    snapshot_str = os.environ.get("APP_STORE_INPUT_SNAPSHOT")
    if snapshot_str is not None:
        store_snapshot = snapshot_str.lower() in ("true", "1", "yes")
    else:
        store_snapshot = bool(data.get("store_input_snapshot", True))

    host = os.environ.get("APP_HOST", data.get("host", "127.0.0.1"))
    port = int(os.environ.get("APP_PORT", data.get("port", 8000)))
    min_reason = int(os.environ.get("APP_MIN_REASON_LENGTH", data.get("min_reason_length", 10)))
    queue_limit = int(
        os.environ.get("APP_QUEUE_DEFAULT_LIMIT", data.get("queue_default_limit", 50))
    )
    report_dir = os.environ.get(
        "APP_REVIEW_REPORT_DIR", data.get("review_report_dir", "reports/reviewer")
    )

    return AppConfig(
        audit_db_path=Path(audit_db),
        store_input_snapshot=store_snapshot,
        host=host,
        port=port,
        min_reason_length=min_reason,
        queue_default_limit=queue_limit,
        review_report_dir=Path(report_dir),
    )
