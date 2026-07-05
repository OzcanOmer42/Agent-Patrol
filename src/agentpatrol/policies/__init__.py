"""Policy implementations and a default policy-set builder."""

from __future__ import annotations

from agentpatrol.config import AgentPatrolConfig
from agentpatrol.policies.calendar_policy import CalendarPolicy
from agentpatrol.policies.email_policy import EmailPolicy
from agentpatrol.policies.file_policy import FilePolicy
from agentpatrol.policies.pii_policy import PIIPolicy
from agentpatrol.policies.rate_limit_policy import RateLimitPolicy
from agentpatrol.policies.shell_policy import ShellPolicy
from agentpatrol.policies.sql_policy import SQLPolicy
from agentpatrol.policy import Policy

__all__ = [
    "CalendarPolicy",
    "EmailPolicy",
    "FilePolicy",
    "PIIPolicy",
    "RateLimitPolicy",
    "ShellPolicy",
    "SQLPolicy",
    "build_default_policies",
]


def build_default_policies(config: AgentPatrolConfig | None = None) -> list[Policy]:
    """Return the standard set of policies in evaluation order."""
    return [
        SQLPolicy(),
        ShellPolicy(),
        EmailPolicy(),
        FilePolicy(),
        CalendarPolicy(),
        PIIPolicy(),
        RateLimitPolicy(),
    ]
