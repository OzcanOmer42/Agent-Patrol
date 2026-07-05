"""File reader and writer tools, confined to configured directories."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from agentpatrol.config import AgentPatrolConfig
from agentpatrol.detectors import is_blocked_filename, resolve_within
from agentpatrol.tool import BaseTool, SideEffectLevel

_MAX_READ_CHARS = 4000


class FileReaderArgs(BaseModel):
    path: str


class FileWriterArgs(BaseModel):
    path: str
    content: str


class FileReaderTool(BaseTool):
    name = "file_reader"
    description = "Read a text file from an allowed directory."
    args_schema = FileReaderArgs
    side_effect_level = SideEffectLevel.LOW

    def __init__(self, config: AgentPatrolConfig) -> None:
        self.config = config

    def run(self, args: FileReaderArgs) -> dict[str, Any]:  # type: ignore[override]
        cfg = self.config.file
        if is_blocked_filename(args.path, blocked_names=tuple(cfg.blocked_names)):
            raise PermissionError("blocked file")
        allowed, resolved = resolve_within(
            args.path, cfg.allowed_read_dirs, root=self.config.workspace_root
        )
        if not allowed:
            raise PermissionError("path outside allowed read directories")
        text = resolved.read_text()
        return {
            "path": str(resolved),
            "content": text[:_MAX_READ_CHARS],
            "truncated": len(text) > _MAX_READ_CHARS,
        }


class FileWriterTool(BaseTool):
    name = "file_writer"
    description = "Write a text file into the allowed workspace."
    args_schema = FileWriterArgs
    side_effect_level = SideEffectLevel.MEDIUM

    def __init__(self, config: AgentPatrolConfig) -> None:
        self.config = config

    def run(self, args: FileWriterArgs) -> dict[str, Any]:  # type: ignore[override]
        cfg = self.config.file
        allowed, resolved = resolve_within(
            args.path, cfg.allowed_write_dirs, root=self.config.workspace_root
        )
        if not allowed:
            raise PermissionError("path outside allowed write directories")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(args.content)
        return {"path": str(resolved), "bytes_written": len(args.content)}
