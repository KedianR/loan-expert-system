"""Phase 5 manifest: hashes of all report files, rule-set hash, params hash, plan pin (WP-21).

Usage: python tools/phase5_manifest.py  (called by make phase5)
Output: reports/phase5_manifest.json
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"
OUTPUT = REPORTS_DIR / "phase5_manifest.json"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    report_files = []
    for f in sorted(REPORTS_DIR.rglob("*")):
        if f.is_file() and f != OUTPUT:
            report_files.append(f)

    file_hashes = {}
    for f in report_files:
        rel = str(f.relative_to(REPO_ROOT))
        file_hashes[rel] = sha256_file(f)

    # Rule-set hash from pin
    pin_path = REPO_ROOT / "tests" / "golden" / "rule_set_pin.json"
    rule_set_hash = None
    rule_set_version = None
    if pin_path.exists():
        pin = json.loads(pin_path.read_text(encoding="utf-8"))
        rule_set_hash = pin.get("rule_set_hash")
        rule_set_version = pin.get("rule_set_version")

    # Params hash
    params_path = REPO_ROOT / "params" / "params.toml"
    params_hash = sha256_file(params_path)

    # Fairness plan pin
    fairness_pin_path = REPORTS_DIR / "fairness" / "plan_pin.json"
    fairness_plan_pin = None
    if fairness_pin_path.exists():
        fairness_plan_pin = json.loads(fairness_pin_path.read_text(encoding="utf-8"))

    manifest = {
        "phase": "5",
        "rule_set_hash": rule_set_hash,
        "rule_set_version": rule_set_version,
        "params_hash": params_hash,
        "fairness_plan_pin": fairness_plan_pin,
        "report_file_hashes": file_hashes,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Phase 5 manifest written to {OUTPUT}")
    print(f"  Rule-set hash: {rule_set_hash}")
    print(f"  Params hash: {params_hash}")
    print(f"  Report files hashed: {len(file_hashes)}")


if __name__ == "__main__":
    main()
