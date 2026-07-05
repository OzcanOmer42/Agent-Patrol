"""Policy governing email tools."""

from __future__ import annotations

from agentpatrol.decisions import PolicyDecision
from agentpatrol.detectors import find_secrets
from agentpatrol.policies.base import Policy, PolicyContext, PolicyResult, iter_string_values
from agentpatrol.tool import BaseTool, ToolCall

DRAFT_TOOLS = {"email_drafter"}
SEND_TOOLS = {"email_sender"}


def _recipient_count(args: dict) -> int:
    to = args.get("to")
    if isinstance(to, (list, tuple)):
        return len(to)
    if isinstance(to, str) and to.strip():
        return len([part for part in to.split(",") if part.strip()])
    return 0


class EmailPolicy(Policy):
    """Drafting is allowed; sending needs review; secrets are blocked."""

    name = "email_policy"

    def evaluate(
        self, call: ToolCall, tool: BaseTool, context: PolicyContext
    ) -> PolicyResult:
        if call.tool_name not in DRAFT_TOOLS | SEND_TOOLS:
            return self.allow()

        content = " ".join(iter_string_values(call.args))
        secrets = find_secrets(content)
        if secrets:
            return self.result(
                PolicyDecision.BLOCK,
                f"email content contains secrets: {', '.join(secrets)}",
                0.95,
            )

        if call.tool_name in DRAFT_TOOLS:
            return self.allow("drafting an email is permitted")

        # Sending path.
        recipients = _recipient_count(call.args)
        threshold = context.config.email.bulk_recipient_threshold
        if recipients > threshold:
            return self.result(
                PolicyDecision.REVIEW,
                f"bulk send to {recipients} recipients requires review",
                0.6,
                recipients=recipients,
            )
        return self.result(
            PolicyDecision.REVIEW, "sending email requires review", 0.5,
            recipients=recipients,
        )
