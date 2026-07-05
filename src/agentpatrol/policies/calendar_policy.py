"""Policy governing calendar tools."""

from __future__ import annotations

from agentpatrol.decisions import PolicyDecision
from agentpatrol.policies.base import Policy, PolicyContext, PolicyResult
from agentpatrol.tool import BaseTool, ToolCall

READ_TOOLS = {"calendar_reader"}
WRITE_TOOLS = {"calendar_writer"}


class CalendarPolicy(Policy):
    """Reading the calendar is allowed; creating events requires review."""

    name = "calendar_policy"

    def evaluate(
        self, call: ToolCall, tool: BaseTool, context: PolicyContext
    ) -> PolicyResult:
        if call.tool_name in READ_TOOLS:
            return self.allow("reading the calendar is permitted")
        if call.tool_name in WRITE_TOOLS:
            return self.result(
                PolicyDecision.REVIEW, "creating a calendar event requires review", 0.4
            )
        return self.allow()
