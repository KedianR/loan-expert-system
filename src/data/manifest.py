"""Build data/manifest.json containing SHA-256 hashes of all Phase 4 artifacts.

Implements: WP-17, DR-04, DR-05.
Spec: docs/ml-baseline-spec.md §9, docs/experiment-protocol.md §6.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def file_sha256(path: Path | str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_manifest(
    manifest_path: Path | str = "data/manifest.json",
    raw_checksums_path: Path | str = "data/checksums/home_credit.sha256",
    d2_mapped_path: Path | str = "data/mapped/d2_mapped.csv",
    d3_population_path: Path | str = "data/synthetic/d3_population.csv",
    d2_split_path: Path | str = "data/splits/d2_split.csv",
    d3_split_path: Path | str = "data/splits/d3_split.csv",
    rule_set_pin_path: Path | str = "tests/golden/rule_set_pin.json",
    params_path: Path | str = "params/params.toml",
) -> dict[str, Any]:
    """Compile SHA-256 manifest."""
    # Parse raw checksums file
    raw_hashes: dict[str, str] = {}
    rc_p = Path(raw_checksums_path)
    if rc_p.exists():
        for line in rc_p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                raw_hashes[parts[1].lstrip("*")] = parts[0]

    with open(rule_set_pin_path, "rb") as fh:
        pin_data = json.load(fh)
    rule_set_hash = pin_data.get("rule_set_hash")
    rule_set_version = pin_data.get("rule_set_version")

    manifest = {
        "raw_files": raw_hashes,
        "d2_mapped": {
            "path": str(d2_mapped_path),
            "sha256": file_sha256(d2_mapped_path),
        },
        "d3_population": {
            "path": str(d3_population_path),
            "sha256": file_sha256(d3_population_path),
        },
        "splits": {
            "d2": {
                "path": str(d2_split_path),
                "sha256": file_sha256(d2_split_path),
            },
            "d3": {
                "path": str(d3_split_path),
                "sha256": file_sha256(d3_split_path),
            },
        },
        "policy": {
            "params_sha256": file_sha256(params_path),
            "rule_set_hash": rule_set_hash,
            "rule_set_version": rule_set_version,
        },
    }

    out_p = Path(manifest_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest written to {out_p}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate data/manifest.json")
    parser.add_argument("--output", default="data/manifest.json")
    args = parser.parse_args()
    build_manifest(manifest_path=args.output)


if __name__ == "__main__":
    main()
