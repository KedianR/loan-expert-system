"""
Rule-set hash and version tag computation.

Implements: FR-16, FR-17, WP-03
Spec: docs/09-file-formats.md section 6

The hash is sha256: followed by 64 hex characters. It is computed over a fixed
ordered set of files, with CRLF and lone CR normalised to LF. Generated files
(build/) are not included; only source files are hashed.

File order (fixed by spec):
  1. params/params.toml
  2. rules/manifest.toml
  3. rules/fields.toml
  4. rules/reason_codes.toml
  5. rules/validation.toml
  6. rules/knockout.toml
  7. rules/referral.toml
  8. rules/eligibility.toml
  9. rules/amount.toml
 10. rules/pricing.toml
 11. rules/experimental.toml

For Phase 0, only params/params.toml exists. The hash function accepts a list of
(relative_path, content_bytes) pairs to allow easy testing without real files.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

# The fixed file order from section 6.
HASH_FILE_ORDER = [
    "params/params.toml",
    "rules/manifest.toml",
    "rules/fields.toml",
    "rules/reason_codes.toml",
    "rules/validation.toml",
    "rules/knockout.toml",
    "rules/referral.toml",
    "rules/eligibility.toml",
    "rules/amount.toml",
    "rules/pricing.toml",
    "rules/experimental.toml",
]


def normalise_line_endings(content: bytes) -> bytes:
    """
    Remove a UTF-8 BOM if present, then turn every CRLF or lone CR into LF.
    The file is otherwise unchanged (spaces, comments, etc. all count).
    """
    # Remove UTF-8 BOM
    if content.startswith(b"\xef\xbb\xbf"):
        content = content[3:]
    # Normalise line endings: CRLF -> LF, then lone CR -> LF
    content = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return content


def compute_hash(file_entries: list[tuple[str, bytes]]) -> str:
    """
    Compute the rule-set hash over a list of (relative_path, raw_bytes) pairs.

    The relative path must use forward slashes, matching the spec.
    Files that do not exist are skipped (the hash covers only what is present).

    Returns 'sha256:<64 hex chars>'.
    """
    h = hashlib.sha256()
    for rel_path, raw_bytes in file_entries:
        normalised = normalise_line_endings(raw_bytes)
        # Form: relative_path LF length LF content
        header = f"{rel_path}\n{len(normalised)}\n".encode()
        h.update(header)
        h.update(normalised)
    return f"sha256:{h.hexdigest()}"


def compute_hash_from_root(repo_root: Path) -> str:
    """
    Compute the rule-set hash by reading files from the repository root.

    Files that do not exist are silently skipped, so the function works
    during Phase 0 when only params/params.toml is present.
    """
    entries: list[tuple[str, bytes]] = []
    for rel_path in HASH_FILE_ORDER:
        full_path = repo_root / rel_path
        if full_path.exists():
            entries.append((rel_path, full_path.read_bytes()))
    return compute_hash(entries)


def build_version_tag(params_version: str, rules_version: str = "0.1.0") -> str:
    """
    Build the human-readable version tag.
    Format: rules-<rules_version>+params-<params_version>
    """
    return f"rules-{rules_version}+params-{params_version}"


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    hash_val = compute_hash_from_root(root)
    print(hash_val)
