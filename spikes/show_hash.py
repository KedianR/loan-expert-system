"""Quick script to show which files exist for the hash."""
from src.engine.ruleset_hash import compute_hash_from_root, HASH_FILE_ORDER
from pathlib import Path

root = Path(".")
print("Files in hash order:")
for f in HASH_FILE_ORDER:
    exists = (root / f).exists()
    status = "present" if exists else "future phase"
    print(f"  {f}: {status}")
h = compute_hash_from_root(root)
print(f"\nHash (over present files only): {h}")

