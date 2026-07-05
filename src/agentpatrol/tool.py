"""Tool abstraction and the tool-call model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SideEffectLevel(str, Enum):
    """How consequential a tool's side effects are.

    Used by policies (notably PIIPolicy) to scale a decision's severity.
    """

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ToolCall(BaseModel):
    """A single proposed tool invocation from an agent."""

    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    requested_by: str = "agent"
    run_id: str | None = None
    call_id: str | None = None


class BaseTool(ABC):
    """Base class for every tool.

    Subclasses set the class attributes below and implement :meth:`run`.
    External input always passes through :meth:`validate_args` first, so the
    body of :meth:`run` can assume a validated pydantic model.
    """

    name: str
    description: str
    args_schema: type[BaseModel]
    output_schema: type[BaseModel] | None = None
    side_effect_level: SideEffectLevel = SideEffectLevel.NONE

    def validate_args(self, args: dict[str, Any]) -> BaseModel:
        """Validate raw args against the tool's schema (raises on failure)."""
        return self.args_schema.model_validate(args)

    @abstractmethod
    def run(self, args: BaseModel) -> dict[str, Any]:
        """Execute the tool with validated arguments."""

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Validate and execute in one step."""
        return self.run(self.validate_args(args))

    def describe(self) -> dict[str, Any]:
        """Return a JSON-serialisable description of the tool."""
        return {
            "name": self.name,
            "description": self.description,
            "side_effect_level": self.side_effect_level.value,
            "args_schema": self.args_schema.model_json_schema(),
        }
