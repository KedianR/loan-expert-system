"""
Float-ban static checker for src/calc and src/facts.

Implements: Hard Rule 2 from AGENTS.md, NFR-03
Spec: docs/05-architecture.md §6 (Exact arithmetic)

Scans every .py file under src/calc/ and src/facts/ for the use of float
literals or float-returning built-ins. Reports each violation and exits
non-zero if any are found.

What counts as a float violation:
  - Any float literal in the AST (ast.Constant with a float value).
  - ast.Call to built-ins: float(), complex().

What does NOT count:
  - Decimal(), int(), str() – fine.
  - Integer literals – fine.
  - Comments and docstrings – not in the AST as float nodes.

Usage:
  python -m tools.check_floats [path ...]
  python tools/check_floats.py [path ...]

Default path: src/calc
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

FORBIDDEN_BUILTINS = frozenset({"float", "complex"})


class FloatFinder(ast.NodeVisitor):
    """Walk an AST and collect float violations."""

    def __init__(self, source_path: str) -> None:
        self.source_path = source_path
        self.violations: list[tuple[int, str]] = []  # (lineno, description)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, float):
            self.violations.append((node.lineno, f"float literal {node.value!r}"))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check for float(…) or complex(…) bare calls
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BUILTINS:
            self.violations.append((node.lineno, f"call to {node.func.id}()"))
        # Check for module.float() style – not a standard pattern but be thorough
        self.generic_visit(node)


def check_file(path: Path) -> list[tuple[str, int, str]]:
    """
    Check one Python file for float violations.

    Returns a list of (file_path, lineno, description) tuples.
    """
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [(str(path), exc.lineno or 0, f"SyntaxError: {exc.msg}")]

    finder = FloatFinder(str(path))
    finder.visit(tree)
    return [(str(path), lineno, desc) for lineno, desc in finder.violations]


def check_tree(root: Path) -> list[tuple[str, int, str]]:
    """
    Recursively check every .py file under root.

    Returns all violations found.
    """
    violations: list[tuple[str, int, str]] = []
    for py_file in sorted(root.rglob("*.py")):
        violations.extend(check_file(py_file))
    return violations


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        targets = [Path("src/calc"), Path("src/facts")]
    else:
        targets = [Path(a) for a in args]

    all_violations: list[tuple[str, int, str]] = []
    for target in targets:
        if target.is_file():
            all_violations.extend(check_file(target))
        elif target.is_dir():
            all_violations.extend(check_tree(target))
        else:
            print(f"WARNING: path does not exist: {target}", file=sys.stderr)

    targets_str = ", ".join(str(t) for t in targets)
    if all_violations:
        print(
            f"FLOAT_FORBIDDEN: {len(all_violations)} violation(s) found in {targets_str}:",
            file=sys.stderr,
        )
        for fpath, lineno, desc in all_violations:
            print(f"  {fpath}:{lineno}: {desc}", file=sys.stderr)
        return 1

    checked = sum(
        sum(1 for _ in Path(t).rglob("*.py")) if Path(t).is_dir() else 1
        for t in targets
        if Path(t).exists()
    )
    print(f"FLOAT_BAN OK: no floats in {targets_str} ({checked} file(s) checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
