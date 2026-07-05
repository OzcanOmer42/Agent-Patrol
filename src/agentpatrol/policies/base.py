"""Shared utilities for concrete policies."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from agentpatrol.policy import Policy, PolicyContext, PolicyResult

__all__ = ["Policy", "PolicyContext", "PolicyResult", "iter_string_values"]


def iter_string_values(value: Any) -> Iterator[str]:
    """Yield every string found in a nested args structure."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_string_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from iter_string_values(item)
