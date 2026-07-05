"""Policy limiting repeated calls to the same tool within a run."""

from __future__ import annotations

from agentpatrol.decisions import PolicyDecision
from agentpatrol.policies.base import Policy, PolicyContext, PolicyResult
from agentpatrol.tool import BaseTool, ToolCall


class RateLimitPolicy(Policy):
    """Caps per-tool call counts using the run context.

    The runtime records how many times each tool has been proposed in the
    current run. Beyond ``soft_limit`` calls require review; beyond
    ``hard_limit`` they are blocked.
    """

    name = "rate_limit_policy"

    def evaluate(
        self, call: ToolCall, tool: BaseTool, context: PolicyContext
    ) -> PolicyResult:
        count = context.call_counts.get(call.tool_name, 0)
        cfg = context.config.rate_limit

        if count > cfg.hard_limit:
            return self.result(
                PolicyDecision.BLOCK,
                f"call {count} exceeds hard limit {cfg.hard_limit} for {call.tool_name}",
                0.8,
                count=count,
            )
        if count > cfg.soft_limit:
            return self.result(
                PolicyDecision.REVIEW,
                f"call {count} exceeds soft limit {cfg.soft_limit} for {call.tool_name}",
                0.4,
                count=count,
            )
        return self.allow()
