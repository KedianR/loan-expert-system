"""
Condition language tokenizer, AST, parser and type-checker.

Implements: docs/09-file-formats.md section 4
Error codes:
  CONDITION_SYNTAX
  MAGIC_NUMBER
  UNKNOWN_NAME
  TYPE_MISMATCH
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


class ConditionParseError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------
# AST Nodes
# ---------------------------------------------------------------------------


class ASTNode:
    def evaluate(self, env: dict[str, Any]) -> Any:
        raise NotImplementedError

    def get_fields_read(self) -> set[str]:
        raise NotImplementedError

    def get_params_read(self) -> set[str]:
        raise NotImplementedError


@dataclass
class OrNode(ASTNode):
    operands: list[ASTNode]

    def evaluate(self, env: dict[str, Any]) -> Any:
        return any(bool(op.evaluate(env)) for op in self.operands)

    def get_fields_read(self) -> set[str]:
        fields: set[str] = set()
        for op in self.operands:
            fields.update(op.get_fields_read())
        return fields

    def get_params_read(self) -> set[str]:
        params: set[str] = set()
        for op in self.operands:
            params.update(op.get_params_read())
        return params


@dataclass
class AndNode(ASTNode):
    operands: list[ASTNode]

    def evaluate(self, env: dict[str, Any]) -> Any:
        return all(bool(op.evaluate(env)) for op in self.operands)

    def get_fields_read(self) -> set[str]:
        fields: set[str] = set()
        for op in self.operands:
            fields.update(op.get_fields_read())
        return fields

    def get_params_read(self) -> set[str]:
        params: set[str] = set()
        for op in self.operands:
            params.update(op.get_params_read())
        return params


@dataclass
class NotNode(ASTNode):
    operand: ASTNode

    def evaluate(self, env: dict[str, Any]) -> Any:
        return not bool(self.operand.evaluate(env))

    def get_fields_read(self) -> set[str]:
        return self.operand.get_fields_read()

    def get_params_read(self) -> set[str]:
        return self.operand.get_params_read()


@dataclass
class ComparisonNode(ASTNode):
    op: str  # '<', '<=', '>', '>=', '==', '!='
    left: ASTNode
    right: ASTNode

    def evaluate(self, env: dict[str, Any]) -> Any:
        l_val = self.left.evaluate(env)
        r_val = self.right.evaluate(env)
        if l_val is None or r_val is None:
            return False
        if self.op == "<":
            return l_val < r_val
        elif self.op == "<=":
            return l_val <= r_val
        elif self.op == ">":
            return l_val > r_val
        elif self.op == ">=":
            return l_val >= r_val
        elif self.op == "==":
            return l_val == r_val
        elif self.op == "!=":
            return l_val != r_val
        raise ValueError(f"Unknown comparison operator: {self.op}")

    def get_fields_read(self) -> set[str]:
        return self.left.get_fields_read() | self.right.get_fields_read()

    def get_params_read(self) -> set[str]:
        return self.left.get_params_read() | self.right.get_params_read()


@dataclass
class ArithmeticNode(ASTNode):
    op: str  # '+', '-'
    left: ASTNode
    right: ASTNode

    def evaluate(self, env: dict[str, Any]) -> Any:
        l_val = self.left.evaluate(env)
        r_val = self.right.evaluate(env)
        if l_val is None or r_val is None:
            return None
        if self.op == "+":
            return l_val + r_val
        elif self.op == "-":
            return l_val - r_val
        raise ValueError(f"Unknown arithmetic operator: {self.op}")

    def get_fields_read(self) -> set[str]:
        return self.left.get_fields_read() | self.right.get_fields_read()

    def get_params_read(self) -> set[str]:
        return self.left.get_params_read() | self.right.get_params_read()


@dataclass
class BuiltinNode(ASTNode):
    name: str  # 'known', 'unknown', 'any_required_unknown', 'no_blocking_outcome'
    arg: str | None = None

    def evaluate(self, env: dict[str, Any]) -> Any:
        if self.name == "known":
            return self.arg in env and env[self.arg] is not None
        elif self.name == "unknown":
            return (self.arg not in env) or (env[self.arg] is None)
        elif self.name == "any_required_unknown":
            req_fields = env.get("__required_fields__", [])
            return any((f not in env or env[f] is None) for f in req_fields)
        elif self.name == "no_blocking_outcome":
            return not bool(env.get("__has_blocking_outcome__", False))
        raise ValueError(f"Unknown builtin: {self.name}")

    def get_fields_read(self) -> set[str]:
        if self.name in ("known", "unknown") and self.arg:
            return {self.arg}
        return set()

    def get_params_read(self) -> set[str]:
        return set()


@dataclass
class VariableNode(ASTNode):
    name: str
    kind: str  # 'field', 'param', 'enum', 'literal_bool'
    resolved_type: str  # 'int', 'decimal', 'bool', 'enum', 'string'
    enum_name: str | None = None

    def evaluate(self, env: dict[str, Any]) -> Any:
        if self.kind == "literal_bool":
            return self.name == "true"
        elif self.kind == "enum":
            return self.name
        return env.get(self.name)

    def get_fields_read(self) -> set[str]:
        if self.kind == "field":
            return {self.name}
        return set()

    def get_params_read(self) -> set[str]:
        if self.kind == "param":
            return {self.name}
        return set()


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

TOKEN_SPEC = [
    ("MAGIC_NUMBER", r"\b\d+(\.\d+)?\b"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("COMPARE_OP", r"(<=|>=|==|!=|<|>)"),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("COMMA", r","),
    ("NAME", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("WS", r"\s+"),
    ("MISMATCH", r"."),
]

TOKEN_RE = re.compile("|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in TOKEN_SPEC))


@dataclass
class Token:
    type: str
    value: str
    pos: int


def tokenize(code: str) -> list[Token]:
    tokens: list[Token] = []
    for mo in TOKEN_RE.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        pos = mo.start()
        if kind == "WS":
            continue
        elif kind == "MAGIC_NUMBER":
            raise ConditionParseError(
                "MAGIC_NUMBER",
                f"Numeric literal '{value}' forbidden in rule condition at pos {pos}. Use parameter names.",
            )
        elif kind == "MISMATCH":
            raise ConditionParseError(
                "CONDITION_SYNTAX",
                f"Unexpected character '{value}' at pos {pos}.",
            )
        tokens.append(Token(kind, value, pos))
    return tokens


# ---------------------------------------------------------------------------
# Parser and Type-Checker
# ---------------------------------------------------------------------------


class ConditionParser:
    """
    Parses condition expressions into AST and type-checks against fields and params.
    """

    def __init__(
        self,
        field_types: dict[str, tuple[str, str | None]],  # field_name -> (type, enum_name)
        param_types: dict[str, str],  # param_name -> type ('int', 'decimal', 'bool', etc.)
        enum_values: dict[
            str, str
        ],  # enum_value -> enum_field_name (e.g. 'salaried' -> 'employment_type')
        required_fields: set[str],
    ):
        self.field_types = field_types
        self.param_types = param_types
        self.enum_values = enum_values
        self.required_fields = required_fields
        self.tokens: list[Token] = []
        self.pos = 0

    def parse(self, text: str) -> ASTNode:
        self.tokens = tokenize(text)
        self.pos = 0
        if not self.tokens:
            raise ConditionParseError("CONDITION_SYNTAX", "Empty condition")
        node = self._parse_or()
        if self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            raise ConditionParseError(
                "CONDITION_SYNTAX", f"Unexpected token '{tok.value}' at pos {tok.pos}"
            )
        # Verify node produces a boolean result
        node_type = self._get_node_type(node)
        if node_type != "bool":
            raise ConditionParseError(
                "TYPE_MISMATCH",
                f"Condition must evaluate to bool, got '{node_type}'",
            )
        return node

    def _current(self) -> Token | None:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _consume(self, expected_type: str | None = None, expected_val: str | None = None) -> Token:
        tok = self._current()
        if tok is None:
            raise ConditionParseError("CONDITION_SYNTAX", "Unexpected end of condition")
        if expected_type and tok.type != expected_type:
            raise ConditionParseError(
                "CONDITION_SYNTAX",
                f"Expected {expected_type}, got '{tok.value}' at pos {tok.pos}",
            )
        if expected_val and tok.value != expected_val:
            raise ConditionParseError(
                "CONDITION_SYNTAX",
                f"Expected '{expected_val}', got '{tok.value}' at pos {tok.pos}",
            )
        self.pos += 1
        return tok

    def _parse_or(self) -> ASTNode:
        left = self._parse_and()
        operands = [left]
        while self._current() and self._current().value == "or":
            self._consume("NAME", "or")
            right = self._parse_and()
            operands.append(right)
        if len(operands) == 1:
            return operands[0]
        for op in operands:
            if self._get_node_type(op) != "bool":
                raise ConditionParseError(
                    "TYPE_MISMATCH",
                    f"Operands of 'or' must be bool, got '{self._get_node_type(op)}'",
                )
        return OrNode(operands)

    def _parse_and(self) -> ASTNode:
        left = self._parse_not()
        operands = [left]
        while self._current() and self._current().value == "and":
            self._consume("NAME", "and")
            right = self._parse_not()
            operands.append(right)
        if len(operands) == 1:
            return operands[0]
        for op in operands:
            if self._get_node_type(op) != "bool":
                raise ConditionParseError(
                    "TYPE_MISMATCH",
                    f"Operands of 'and' must be bool, got '{self._get_node_type(op)}'",
                )
        return AndNode(operands)

    def _parse_not(self) -> ASTNode:
        tok = self._current()
        if tok and tok.value == "not":
            self._consume("NAME", "not")
            operand = self._parse_not()
            if self._get_node_type(operand) != "bool":
                raise ConditionParseError(
                    "TYPE_MISMATCH",
                    f"Operand of 'not' must be bool, got '{self._get_node_type(operand)}'",
                )
            return NotNode(operand)
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        tok = self._current()
        if tok is None:
            raise ConditionParseError("CONDITION_SYNTAX", "Unexpected end of expression")

        # Parenthesized condition: '(' condition ')'
        if tok.type == "LPAREN":
            self._consume("LPAREN")
            inner = self._parse_or()
            self._consume("RPAREN")
            return inner

        # Builtins: known(name), unknown(name), any_required_unknown, no_blocking_outcome
        if tok.value in ("known", "unknown"):
            b_name = tok.value
            self._consume("NAME", b_name)
            self._consume("LPAREN")
            arg_tok = self._consume("NAME")
            if arg_tok.value not in self.field_types:
                raise ConditionParseError(
                    "UNKNOWN_NAME",
                    f"Unknown field '{arg_tok.value}' in {b_name}() at pos {arg_tok.pos}",
                )
            self._consume("RPAREN")
            return BuiltinNode(b_name, arg_tok.value)

        if tok.value == "any_required_unknown":
            self._consume("NAME", "any_required_unknown")
            return BuiltinNode("any_required_unknown")

        if tok.value == "no_blocking_outcome":
            self._consume("NAME", "no_blocking_outcome")
            return BuiltinNode("no_blocking_outcome")

        # Otherwise: comparison = value [ compare_op value ]
        left_val = self._parse_value()
        next_tok = self._current()
        if next_tok and next_tok.type == "COMPARE_OP":
            op = self._consume("COMPARE_OP").value
            right_val = self._parse_value()
            self._check_comparison_types(op, left_val, right_val)
            return ComparisonNode(op, left_val, right_val)

        # Standalone value: must be boolean (e.g. `consent_given` or `true`)
        val_type = self._get_node_type(left_val)
        if val_type != "bool":
            raise ConditionParseError(
                "TYPE_MISMATCH",
                f"Standalone value in condition must be bool, got '{val_type}' for {left_val}",
            )
        return left_val

    def _parse_value(self) -> ASTNode:
        left = self._parse_operand()
        while self._current() and self._current().type in ("PLUS", "MINUS"):
            op_tok = self._consume()
            op = op_tok.value
            right = self._parse_operand()
            l_t = self._get_node_type(left)
            r_t = self._get_node_type(right)
            if l_t not in ("int", "decimal") or r_t not in ("int", "decimal"):
                raise ConditionParseError(
                    "TYPE_MISMATCH",
                    f"Operator '{op}' requires numeric operands, got '{l_t}' and '{r_t}'",
                )
            left = ArithmeticNode(op, left, right)
        return left

    def _parse_operand(self) -> ASTNode:
        tok = self._current()
        if tok is None:
            raise ConditionParseError("CONDITION_SYNTAX", "Unexpected end of operand")

        if tok.value == "true" or tok.value == "false":
            self._consume("NAME")
            return VariableNode(tok.value, "literal_bool", "bool")

        if tok.type == "NAME":
            name = tok.value
            self._consume("NAME")
            # 1. Field
            if name in self.field_types:
                ftype, enum_name = self.field_types[name]
                return VariableNode(name, "field", ftype, enum_name)
            # 2. Parameter
            if name in self.param_types:
                ptype = self.param_types[name]
                return VariableNode(name, "param", ptype)
            # 3. Enum value
            if name in self.enum_values:
                enum_field = self.enum_values[name]
                return VariableNode(name, "enum", "enum", enum_field)

            raise ConditionParseError(
                "UNKNOWN_NAME",
                f"Unknown identifier '{name}' at pos {tok.pos}",
            )

        raise ConditionParseError(
            "CONDITION_SYNTAX",
            f"Unexpected token '{tok.value}' in operand at pos {tok.pos}",
        )

    def _get_node_type(self, node: ASTNode) -> str:
        if isinstance(node, (OrNode, AndNode, NotNode, ComparisonNode, BuiltinNode)):
            return "bool"
        if isinstance(node, ArithmeticNode):
            l_t = self._get_node_type(node.left)
            r_t = self._get_node_type(node.right)
            if "decimal" in (l_t, r_t):
                return "decimal"
            return "int"
        if isinstance(node, VariableNode):
            return node.resolved_type
        raise ValueError(f"Unknown AST node {type(node)}")

    def _check_comparison_types(self, op: str, left: ASTNode, right: ASTNode) -> None:
        l_t = self._get_node_type(left)
        r_t = self._get_node_type(right)

        # Equality: ==, !=
        if op in ("==", "!="):
            if l_t in ("int", "decimal") and r_t in ("int", "decimal"):
                return
            if l_t == "bool" and r_t == "bool":
                return
            if l_t == "enum" and r_t == "enum":
                # Must be for the same enum
                l_enum = getattr(left, "enum_name", None)
                r_enum = getattr(right, "enum_name", None)
                if l_enum == r_enum:
                    return
            raise ConditionParseError(
                "TYPE_MISMATCH",
                f"Cannot compare '{l_t}' and '{r_t}' with '{op}'",
            )

        # Ordering: <, <=, >, >=
        if op in ("<", "<=", ">", ">="):
            if l_t in ("int", "decimal") and r_t in ("int", "decimal"):
                return
            raise ConditionParseError(
                "TYPE_MISMATCH",
                f"Ordering comparison '{op}' requires numeric types, got '{l_t}' and '{r_t}'",
            )
