"""
CLI entrypoint for make decide INPUT=file.json.

Implements: FR-01, FR-10, WP-14
Spec: Reads input file, computes decision with trace, writes to audit log, and prints JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.api.service import DecisionService, DecisionServiceError


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m src.api.decide <path_to_input_json>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Failed to read JSON: {e}", file=sys.stderr)
        sys.exit(1)

    service = DecisionService()
    field_errors = service.validate_request_input(data)
    if field_errors:
        print(
            json.dumps({"error": {"code": "INVALID_REQUEST", "fields": field_errors}}, indent=2),
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        response = service.decide(data)
        print(json.dumps(response, indent=2))
    except DecisionServiceError as e:
        err_dict = {"code": e.code, "message": e.message}
        if e.suggested_route:
            err_dict["suggested_route"] = e.suggested_route
        print(json.dumps({"error": err_dict}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
