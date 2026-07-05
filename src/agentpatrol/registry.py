"""Registry of available tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from agentpatrol.tool import BaseTool


class ToolRegistry:
    """Holds the set of tools an agent is permitted to reference."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def validate_tool_call(self, tool_name: str, args: dict[str, Any]) -> BaseModel:
        """Validate ``args`` against the named tool's schema."""
        return self.get_tool(tool_name).validate_args(args)

    def __contains__(self, name: object) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
