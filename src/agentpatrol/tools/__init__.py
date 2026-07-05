"""Tool implementations and a default registry builder."""

from __future__ import annotations

from pathlib import Path

from agentpatrol.config import AgentPatrolConfig
from agentpatrol.registry import ToolRegistry
from agentpatrol.tools.calculator import CalculatorTool
from agentpatrol.tools.calendar_tools import CalendarReaderTool, CalendarWriterTool
from agentpatrol.tools.email_tools import EmailDrafterTool, EmailSenderTool
from agentpatrol.tools.file_tools import FileReaderTool, FileWriterTool
from agentpatrol.tools.shell_tools import ShellCommandTool
from agentpatrol.tools.sql_tools import SqlQueryTool

__all__ = [
    "CalculatorTool",
    "CalendarReaderTool",
    "CalendarWriterTool",
    "EmailDrafterTool",
    "EmailSenderTool",
    "FileReaderTool",
    "FileWriterTool",
    "ShellCommandTool",
    "SqlQueryTool",
    "build_default_registry",
]

DEFAULT_DB_PATH = "data/demo.db"


def build_default_registry(
    config: AgentPatrolConfig | None = None, db_path: str | Path = DEFAULT_DB_PATH
) -> ToolRegistry:
    """Register the standard tool set and return the registry."""
    config = config or AgentPatrolConfig()
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(FileReaderTool(config))
    registry.register(FileWriterTool(config))
    registry.register(SqlQueryTool(db_path))
    registry.register(EmailDrafterTool())
    registry.register(EmailSenderTool())
    registry.register(CalendarReaderTool())
    registry.register(CalendarWriterTool())
    registry.register(ShellCommandTool())
    return registry
