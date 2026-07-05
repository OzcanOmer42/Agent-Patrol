"""Policy governing file read/write tools."""

from __future__ import annotations

from agentpatrol.decisions import PolicyDecision
from agentpatrol.detectors import is_blocked_filename, resolve_within
from agentpatrol.policies.base import Policy, PolicyContext, PolicyResult
from agentpatrol.tool import BaseTool, ToolCall

READ_TOOLS = {"file_reader"}
WRITE_TOOLS = {"file_writer"}


class FilePolicy(Policy):
    """Confines file access to configured directories."""

    name = "file_policy"

    def evaluate(
        self, call: ToolCall, tool: BaseTool, context: PolicyContext
    ) -> PolicyResult:
        if call.tool_name not in READ_TOOLS | WRITE_TOOLS:
            return self.allow()

        cfg = context.config.file
        root = context.config.workspace_root
        path = str(call.args.get("path", ""))
        if not path:
            return self.result(PolicyDecision.BLOCK, "missing file path", 0.6)

        if is_blocked_filename(path, blocked_names=tuple(cfg.blocked_names)):
            return self.result(
                PolicyDecision.BLOCK, "access to credential/hidden file denied", 0.95
            )

        if call.tool_name in READ_TOOLS:
            allowed, _ = resolve_within(path, cfg.allowed_read_dirs, root=root)
            if not allowed:
                return self.result(
                    PolicyDecision.BLOCK, "read outside allowed directories", 0.8
                )
            return self.allow("read within allowed directory")

        # Write path.
        allowed, _ = resolve_within(path, cfg.allowed_write_dirs, root=root)
        if not allowed:
            return self.result(
                PolicyDecision.BLOCK, "write outside allowed workspace", 0.85
            )
        return self.result(PolicyDecision.REVIEW, "file write requires review", 0.5)
