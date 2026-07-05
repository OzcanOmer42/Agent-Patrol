"""Sandboxed mock shell tool.

This tool never spawns a real subprocess. It simulates output for a small set
of harmless commands and refuses everything else, so even a policy misconfig
cannot lead to real command execution.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from agentpatrol.detectors import classify_shell
from agentpatrol.tool import BaseTool, SideEffectLevel

_SIMULATED = {
    "echo": lambda parts: " ".join(parts[1:]),
    "pwd": lambda parts: "/workspace",
    "ls": lambda parts: "examples\ndata\nworkspace",
    "date": lambda parts: "2025-04-01T00:00:00Z",
    "whoami": lambda parts: "agentpatrol",
}


class ShellCommandArgs(BaseModel):
    command: str


class ShellCommandTool(BaseTool):
    name = "shell_command"
    description = "Simulate a harmless shell command (sandboxed, never executes)."
    args_schema = ShellCommandArgs
    side_effect_level = SideEffectLevel.HIGH

    def run(self, args: ShellCommandArgs) -> dict[str, Any]:  # type: ignore[override]
        assessment = classify_shell(args.command)
        if assessment.category != "safe" or assessment.base_command not in _SIMULATED:
            raise ValueError(f"execution refused: '{assessment.base_command}' is not simulated")
        parts = args.command.split()
        stdout = _SIMULATED[assessment.base_command](parts)
        return {"command": args.command, "stdout": stdout, "executed": False, "sandboxed": True}
