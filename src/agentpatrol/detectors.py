"""Pure detection helpers used by policies and tools.

Everything here operates on plain strings and standard-library types only.
Keeping detection separate from the pydantic/framework layer makes the
safety-critical logic small, readable, and directly testable.
"""

from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# SQL classification
# --------------------------------------------------------------------------- #

# Any statement whose intent is to modify data or schema is rejected outright.
SQL_WRITE_KEYWORDS: frozenset[str] = frozenset(
    {
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "replace",
        "merge",
        "grant",
        "revoke",
        "attach",
        "detach",
        "pragma",
        "vacuum",
    }
)

DEFAULT_SENSITIVE_FIELDS: tuple[str, ...] = (
    "password",
    "passwd",
    "token",
    "api_key",
    "apikey",
    "ssn",
    "secret",
    "credit_card",
)

_LIMIT_RE = re.compile(r"\blimit\s+(\d+)", re.IGNORECASE)
_SELECT_STAR_RE = re.compile(r"select\s+\*", re.IGNORECASE)
_TABLE_RE = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][\w]*)", re.IGNORECASE)
_WORD_RE = re.compile(r"[a-zA-Z_][\w]*")


@dataclass
class SqlAssessment:
    is_select: bool
    has_write_keyword: bool
    multi_statement: bool
    touches_sensitive_field: bool
    is_select_star: bool
    limit: int | None
    tables: list[str] = field(default_factory=list)
    forbidden_keywords: list[str] = field(default_factory=list)


def _split_statements(query: str) -> list[str]:
    return [part.strip() for part in query.split(";") if part.strip()]


def classify_sql(
    query: str,
    sensitive_fields: tuple[str, ...] | list[str] = DEFAULT_SENSITIVE_FIELDS,
) -> SqlAssessment:
    """Classify a SQL string using conservative keyword analysis.

    This is deliberately allow-list oriented: only single-statement SELECT
    queries can pass. It does not attempt to be a full SQL parser.
    """
    statements = _split_statements(query)
    multi_statement = len(statements) > 1

    words = [w.lower() for w in _WORD_RE.findall(query)]
    word_set = set(words)

    forbidden = sorted(word_set & SQL_WRITE_KEYWORDS)
    has_write = bool(forbidden)

    first_word = words[0] if words else ""
    is_select = first_word == "select" and not has_write and not multi_statement

    lowered = query.lower()
    touches_sensitive = any(field_name.lower() in lowered for field_name in sensitive_fields)

    limit_match = _LIMIT_RE.search(query)
    limit = int(limit_match.group(1)) if limit_match else None

    tables = [t.lower() for t in _TABLE_RE.findall(query)]

    return SqlAssessment(
        is_select=is_select,
        has_write_keyword=has_write,
        multi_statement=multi_statement,
        touches_sensitive_field=touches_sensitive,
        is_select_star=bool(_SELECT_STAR_RE.search(query)),
        limit=limit,
        tables=tables,
        forbidden_keywords=forbidden,
    )


# --------------------------------------------------------------------------- #
# Shell classification
# --------------------------------------------------------------------------- #

_DESTRUCTIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\brm\s+(-[a-z]*\s+)*-?[a-z]*[rf]", re.IGNORECASE),
    re.compile(r"\brm\s+-[rf]", re.IGNORECASE),
    re.compile(r"\b(shutdown|reboot|halt|poweroff|init\s+0)\b", re.IGNORECASE),
    re.compile(r"\b(kill|killall|pkill)\b", re.IGNORECASE),
    re.compile(r"\bchmod\s+(-r\s+)?777\b", re.IGNORECASE),
    re.compile(r"\bchmod\s+-r\b", re.IGNORECASE),
    re.compile(r"\bchown\b", re.IGNORECASE),
    re.compile(r"\bmkfs", re.IGNORECASE),
    re.compile(r"\bdd\s+if=", re.IGNORECASE),
    re.compile(r">\s*/dev/sd", re.IGNORECASE),
    re.compile(r":\(\)\s*\{", re.IGNORECASE),  # fork bomb
)

_SECRET_ACCESS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bprintenv\b", re.IGNORECASE),
    re.compile(r"(^|\s)env(\s|$)", re.IGNORECASE),
    re.compile(r"\$\{?[A-Za-z_]*(SECRET|TOKEN|KEY|PASS|CRED|AWS)", re.IGNORECASE),
    re.compile(r"\$[A-Z_]{2,}"),
    re.compile(
        r"(cat|less|more|head|tail)\s+[^\s]*(\.env|id_rsa|credentials|secrets)",
        re.IGNORECASE,
    ),
)

_NETWORK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(curl|wget|nc|netcat|ssh|scp|sftp|ftp|telnet)\b", re.IGNORECASE),
)

DEFAULT_SAFE_COMMANDS: tuple[str, ...] = (
    "echo",
    "pwd",
    "ls",
    "cat",
    "date",
    "whoami",
    "head",
    "tail",
    "wc",
    "sort",
    "uniq",
)


@dataclass
class ShellAssessment:
    category: str  # destructive | secret_access | network | safe | unknown
    base_command: str
    matched: str | None = None


def classify_shell(
    command: str,
    safe_commands: tuple[str, ...] | list[str] = DEFAULT_SAFE_COMMANDS,
) -> ShellAssessment:
    """Classify a shell command by risk category (priority ordered)."""
    stripped = command.strip()
    base = stripped.split()[0] if stripped.split() else ""

    for pattern in _DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return ShellAssessment("destructive", base, pattern.pattern)
    for pattern in _SECRET_ACCESS_PATTERNS:
        if pattern.search(command):
            return ShellAssessment("secret_access", base, pattern.pattern)
    for pattern in _NETWORK_PATTERNS:
        if pattern.search(command):
            return ShellAssessment("network", base, pattern.pattern)
    if base in set(safe_commands):
        return ShellAssessment("safe", base, None)
    return ShellAssessment("unknown", base, None)


# --------------------------------------------------------------------------- #
# Secret and PII detection
# --------------------------------------------------------------------------- #

_SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "api_token": re.compile(r"\b(?:sk|pk|api|tok|ghp|xox[baprs])[-_][A-Za-z0-9]{16,}\b"),
    "bearer_token": re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]{16,}", re.IGNORECASE),
    "assigned_secret": re.compile(
        r"\b(password|passwd|secret|api[_-]?key|token)\b\s*[:=]\s*\S{4,}", re.IGNORECASE
    ),
}

_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?\d{1,2}[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}

# PII categories that are treated as high-severity leaks.
SENSITIVE_PII: frozenset[str] = frozenset({"ssn"})


def find_secrets(text: str) -> list[str]:
    """Return the labels of secret patterns found in ``text``."""
    return sorted(label for label, pattern in _SECRET_PATTERNS.items() if pattern.search(text))


def find_pii(text: str) -> list[str]:
    """Return the labels of PII patterns found in ``text``."""
    return sorted(label for label, pattern in _PII_PATTERNS.items() if pattern.search(text))


# --------------------------------------------------------------------------- #
# Safe arithmetic (calculator tool)
# --------------------------------------------------------------------------- #

_ARITH_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_arith_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ARITH_OPS:
        if isinstance(node.op, ast.Pow):
            right = _eval_arith_node(node.right)
            if right > 100:
                raise ValueError("exponent too large")
            return _ARITH_OPS[type(node.op)](_eval_arith_node(node.left), right)
        return _ARITH_OPS[type(node.op)](
            _eval_arith_node(node.left), _eval_arith_node(node.right)
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ARITH_OPS:
        return _ARITH_OPS[type(node.op)](_eval_arith_node(node.operand))
    raise ValueError("unsupported expression")


def safe_arithmetic(expression: str) -> float:
    """Evaluate a numeric expression without using eval/exec.

    Only numeric literals and the standard arithmetic operators are allowed.
    Any name, call, attribute access, or other construct raises ValueError.
    """
    try:
        parsed = ast.parse(expression, mode="eval")
    except SyntaxError as exc:  # pragma: no cover - defensive
        raise ValueError(f"invalid expression: {exc}") from exc
    return _eval_arith_node(parsed.body)


# --------------------------------------------------------------------------- #
# File path safety
# --------------------------------------------------------------------------- #

DEFAULT_BLOCKED_FILE_NAMES: tuple[str, ...] = (
    ".env",
    "id_rsa",
    "id_dsa",
    "credentials",
    "secrets",
    ".netrc",
    ".pgpass",
)

_BLOCKED_SUFFIXES: tuple[str, ...] = (".pem", ".key", ".p12", ".pfx")


def is_blocked_filename(
    path: str,
    blocked_names: tuple[str, ...] | list[str] = DEFAULT_BLOCKED_FILE_NAMES,
) -> bool:
    """Return True if the path points at a credential-like or hidden file."""
    name = Path(path).name
    lowered = name.lower()
    if name in set(blocked_names):
        return True
    if lowered in {n.lower() for n in blocked_names}:
        return True
    if name.startswith(".") and name not in {".", ".."}:
        return True
    return any(lowered.endswith(suffix) for suffix in _BLOCKED_SUFFIXES)


def resolve_within(
    path: str, allowed_dirs: list[str] | tuple[str, ...], root: str = "."
) -> tuple[bool, Path]:
    """Resolve ``path`` and check it stays inside one of ``allowed_dirs``.

    Returns ``(is_allowed, resolved_path)``. Path traversal via ``..`` cannot
    escape an allowed directory because comparison happens after resolution.
    """
    root_path = Path(root).resolve()
    candidate = Path(path)
    target = candidate.resolve() if candidate.is_absolute() else (root_path / candidate).resolve()

    for allowed in allowed_dirs:
        base = (root_path / allowed).resolve()
        if target == base or base in target.parents:
            return True, target
    return False, target
