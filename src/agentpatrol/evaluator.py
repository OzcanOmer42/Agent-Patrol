"""Evaluation harness that scores policy behaviour on labelled scenarios."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from pydantic import BaseModel, Field

from agentpatrol.config import AgentPatrolConfig
from agentpatrol.decisions import PolicyDecision
from agentpatrol.policy import PolicyContext, PolicyEngine
from agentpatrol.registry import ToolRegistry
from agentpatrol.tool import ToolCall
from agentpatrol.validators import validate_call


class ScenarioResult(BaseModel):
    name: str
    category: str
    expected: PolicyDecision
    actual: PolicyDecision
    correct: bool
    schema_failed: bool
    latency_ms: float


class EvalMetrics(BaseModel):
    total: int
    correct: int
    policy_accuracy: float
    false_allow_rate: float
    false_block_rate: float
    review_precision: float | None
    schema_validation_failure_count: int
    average_policy_latency_ms: float
    by_category: dict[str, dict[str, int]] = Field(default_factory=dict)


class Evaluator:
    """Scores a set of scenarios against the configured policy engine.

    Each scenario is evaluated exactly as the runtime would decide it (schema
    validation followed by policy aggregation) but without executing tools, so
    the reported metrics reflect the real implementation.
    """

    def __init__(
        self, registry: ToolRegistry, engine: PolicyEngine, config: AgentPatrolConfig
    ) -> None:
        self.registry = registry
        self.engine = engine
        self.config = config

    def evaluate_scenario(self, scenario: dict[str, Any]) -> ScenarioResult:
        expected = PolicyDecision(scenario["expected_decision"])
        call = ToolCall(
            tool_name=scenario["tool_name"],
            args=scenario.get("args", {}),
            requested_by="evaluator",
        )
        outcome = validate_call(self.registry, call)
        if not outcome.ok:
            actual = PolicyDecision.BLOCK
            return ScenarioResult(
                name=scenario["name"],
                category=scenario.get("category", "uncategorised"),
                expected=expected,
                actual=actual,
                correct=actual == expected,
                schema_failed=True,
                latency_ms=0.0,
            )

        # Optional context lets scenarios simulate repeated calls in a run.
        call_count = int(scenario.get("context", {}).get("call_count", 1))
        context = PolicyContext(
            config=self.config,
            call_counts={scenario["tool_name"]: call_count},
        )
        tool = self.registry.get_tool(scenario["tool_name"])

        start = perf_counter()
        result = self.engine.evaluate(call, tool, context)
        latency = (perf_counter() - start) * 1000

        actual = result.decision
        return ScenarioResult(
            name=scenario["name"],
            category=scenario.get("category", "uncategorised"),
            expected=expected,
            actual=actual,
            correct=actual == expected,
            schema_failed=False,
            latency_ms=latency,
        )

    def run(
        self, scenarios: list[dict[str, Any]]
    ) -> tuple[list[ScenarioResult], EvalMetrics]:
        results = [self.evaluate_scenario(s) for s in scenarios]
        return results, self._metrics(results)

    @staticmethod
    def _metrics(results: list[ScenarioResult]) -> EvalMetrics:
        total = len(results)
        correct = sum(1 for r in results if r.correct)

        should_restrict = [r for r in results if r.expected is not PolicyDecision.ALLOW]
        false_allows = sum(
            1 for r in should_restrict if r.actual is PolicyDecision.ALLOW
        )

        safe = [r for r in results if r.expected is PolicyDecision.ALLOW]
        false_blocks = sum(1 for r in safe if r.actual is PolicyDecision.BLOCK)

        predicted_review = [r for r in results if r.actual is PolicyDecision.REVIEW]
        correct_review = sum(
            1 for r in predicted_review if r.expected is PolicyDecision.REVIEW
        )

        policy_latencies = [r.latency_ms for r in results if not r.schema_failed]

        by_category: dict[str, dict[str, int]] = {}
        for r in results:
            bucket = by_category.setdefault(r.category, {"total": 0, "correct": 0})
            bucket["total"] += 1
            bucket["correct"] += int(r.correct)

        return EvalMetrics(
            total=total,
            correct=correct,
            policy_accuracy=correct / total if total else 0.0,
            false_allow_rate=false_allows / len(should_restrict) if should_restrict else 0.0,
            false_block_rate=false_blocks / len(safe) if safe else 0.0,
            review_precision=(
                correct_review / len(predicted_review) if predicted_review else None
            ),
            schema_validation_failure_count=sum(1 for r in results if r.schema_failed),
            average_policy_latency_ms=(
                sum(policy_latencies) / len(policy_latencies) if policy_latencies else 0.0
            ),
            by_category=by_category,
        )
