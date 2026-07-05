"""Policy governing shell command tools."""

from __future__ import annotations

from agentpatrol.decisions import PolicyDecision
from agentpatrol.detectors import classify_shell
from agentpatrol.policies.base import Policy, PolicyContext, PolicyResult
from agentpatrol.tool import BaseTool, ToolCall

SHELL_TOOLS = {"shell_command"}


class ShellPolicy(Policy):
    """Blocks destructive and secret-reading commands; reviews the uncertain."""

    name = "shell_policy"

    def evaluate(
        self, call: ToolCall, tool: BaseTool, context: PolicyContext
    ) -> PolicyResult:
        if call.tool_name not in SHELL_TOOLS:
            return self.allow()

        command = str(call.args.get("command", ""))
        assessment = classify_shell(
            command, safe_commands=tuple(context.config.shell.allowed_commands)
        )

        if assessment.category == "destructive":
            return self.result(
                PolicyDecision.BLOCK, "destructive shell command", 0.98,
                base_command=assessment.base_command,
            )
        if assessment.category == "secret_access":
            return self.result(
                PolicyDecision.BLOCK, "command reads environment/secrets", 0.9,
                base_command=assessment.base_command,
            )
        if assessment.category == "network":
            return self.result(
                PolicyDecision.REVIEW, "network command requires review", 0.5,
                base_command=assessment.base_command,
            )
        if assessment.category == "safe":
            return self.allow("whitelisted harmless command")

        return self.result(
            PolicyDecision.REVIEW, "unrecognised command requires review", 0.4,
            base_command=assessment.base_command,
        )
