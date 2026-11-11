"""
Canonical JSON serialization and hashing functions.

Implements: FR-15, DR-03, NFR-08
Spec: docs/audit-log-spec.md §3, docs/data-dictionary.md §1
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any


def _check_no_floats(obj: Any) -> None:
    if isinstance(obj, float):
        raise TypeError(f"Floats forbidden in canonical JSON: {obj!r}")
    elif isinstance(obj, dict):
        for v in obj.values():
            _check_no_floats(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _check_no_floats(item)


class _DecimalEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)


def canonical_json(obj: Any) -> str:
    """
    Produce canonical JSON string:
    - UTF-8
    - Keys sorted
    - Separators ',' and ':' with no spaces
    - ensure_ascii=False
    - No floats anywhere (forbids float types)
    """
    _check_no_floats(obj)
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        cls=_DecimalEncoder,
    )


def compute_input_hash(validated_input: dict[str, Any]) -> str:
    """
    Compute input_hash over the validated input exactly as received:
    'sha256:' + hex(SHA-256(canonical(input)))
    """
    canon = canonical_json(validated_input)
    digest = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def compute_applicant_ref(applicant_id: str) -> str:
    """
    Compute applicant_ref:
    'sha256:' + hex(SHA-256(UTF-8 bytes of applicant_id))
    """
    digest = hashlib.sha256(str(applicant_id).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
