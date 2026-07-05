"""Schema validation helpers shared by the runtime and evaluator."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from agentpatrol.registry import ToolRegistry
from agentpatrol.tool import ToolCall


@dataclass
class ValidationOutcome:
    ok: bool
    model: BaseModel | None
    error: str | None


def validate_call(registry: ToolRegistry, call: ToolCall) -> ValidationOutcome:
    """Validate a tool call's args against the registered tool schema."""
    try:
        model = registry.validate_tool_call(call.tool_name, call.args)
        return ValidationOutcome(ok=True, model=model, error=None)
    except KeyError:
        return ValidationOutcome(ok=False, model=None, error=f"unknown tool: {call.tool_name}")
    except ValidationError as exc:
        return ValidationOutcome(ok=False, model=None, error=str(exc))
