"""Policy decision types and conservative aggregation.

This module is intentionally free of third-party dependencies so the core
decision logic can be reasoned about and unit-tested in isolation.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum


class PolicyDecision(str, Enum):
    """The outcome of evaluating a tool call against a policy.

    ALLOW  - safe to execute.
    WARN   - execute, but flag the call for attention.
    REVIEW - do not execute without explicit human approval.
    BLOCK  - never execute.
    """

    ALLOW = "allow"
    WARN = "warn"
    REVIEW = "review"
    BLOCK = "block"


# Higher severity wins when several policies disagree. The ordering encodes
# the project's core safety stance: BLOCK > REVIEW > WARN > ALLOW.
DECISION_SEVERITY: dict[PolicyDecision, int] = {
    PolicyDecision.ALLOW: 0,
    PolicyDecision.WARN: 1,
    PolicyDecision.REVIEW: 2,
    PolicyDecision.BLOCK: 3,
}


def worst_decision(decisions: Iterable[PolicyDecision]) -> PolicyDecision:
    """Return the most severe decision, defaulting to ALLOW when empty."""
    most_severe = PolicyDecision.ALLOW
    for decision in decisions:
        if DECISION_SEVERITY[decision] > DECISION_SEVERITY[most_severe]:
            most_severe = decision
    return most_severe


def is_executable(decision: PolicyDecision, review_approved: bool = False) -> bool:
    """Whether a decision permits execution.

    ALLOW and WARN execute directly. REVIEW executes only with approval.
    BLOCK never executes.
    """
    if decision in (PolicyDecision.ALLOW, PolicyDecision.WARN):
        return True
    if decision is PolicyDecision.REVIEW:
        return review_approved
    return False
