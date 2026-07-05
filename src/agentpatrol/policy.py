"""Policy result model, policy base class, and the aggregating engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from agentpatrol.config import AgentPatrolConfig
from agentpatrol.decisions import PolicyDecision, worst_decision
from agentpatrol.tool import BaseTool, ToolCall


class PolicyResult(BaseModel):
    """The outcome of evaluating a single policy (or the combined engine)."""

    decision: PolicyDecision
    reason: str
    policy_name: str
    risk_score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass
class PolicyContext:
    """Mutable per-run context passed to every policy."""

    config: AgentPatrolConfig
    call_counts: dict[str, int] = field(default_factory=dict)
    run_id: str | None = None


class Policy(ABC):
    """Base class for all policies."""

    name: str = "policy"

    @abstractmethod
    def evaluate(
        self, call: ToolCall, tool: BaseTool, context: PolicyContext
    ) -> PolicyResult:
        """Return this policy's decision for a given tool call."""

    # Convenience constructors --------------------------------------------- #

    def allow(self, reason: str = "policy not applicable", **metadata: Any) -> PolicyResult:
        return PolicyResult(
            decision=PolicyDecision.ALLOW,
            reason=reason,
            policy_name=self.name,
            risk_score=0.0,
            metadata=metadata,
        )

    def result(
        self,
        decision: PolicyDecision,
        reason: str,
        risk_score: float,
        **metadata: Any,
    ) -> PolicyResult:
        return PolicyResult(
            decision=decision,
            reason=reason,
            policy_name=self.name,
            risk_score=risk_score,
            metadata=metadata,
        )


class PolicyEngine:
    """Evaluates a tool call against all policies and combines the results.

    Aggregation is conservative: the final decision is the most severe of the
    individual decisions (BLOCK > REVIEW > WARN > ALLOW). Reasons and risk
    scores from the decisive policies are surfaced for auditability.
    """

    def __init__(self, policies: list[Policy]) -> None:
        self.policies = policies

    def evaluate(
        self, call: ToolCall, tool: BaseTool, context: PolicyContext
    ) -> PolicyResult:
        results = [policy.evaluate(call, tool, context) for policy in self.policies]
        return self._combine(results)

    @staticmethod
    def _combine(results: list[PolicyResult]) -> PolicyResult:
        final = worst_decision(r.decision for r in results)
        breakdown = [
            {
                "policy": r.policy_name,
                "decision": r.decision.value,
                "reason": r.reason,
                "risk_score": r.risk_score,
            }
            for r in results
        ]

        if final is PolicyDecision.ALLOW:
            return PolicyResult(
                decision=final,
                reason="all policies allow",
                policy_name="policy_engine",
                risk_score=max((r.risk_score for r in results), default=0.0),
                metadata={"policy_results": breakdown},
            )

        deciding = [r for r in results if r.decision is final]
        reason = "; ".join(f"{r.policy_name}: {r.reason}" for r in deciding)
        return PolicyResult(
            decision=final,
            reason=reason,
            policy_name=",".join(r.policy_name for r in deciding),
            risk_score=max(r.risk_score for r in deciding),
            metadata={"policy_results": breakdown},
        )
