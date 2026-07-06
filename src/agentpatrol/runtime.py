"""The AgentPatrol runtime that ties everything together."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from pydantic import BaseModel, Field

from agentpatrol.agent import MockAgent
from agentpatrol.config import AgentPatrolConfig
from agentpatrol.decisions import PolicyDecision
from agentpatrol.policy import PolicyContext, PolicyEngine
from agentpatrol.registry import ToolRegistry
from agentpatrol.tool import BaseTool, ToolCall
from agentpatrol.trace import RunTrace, TraceLogger, TraceStep
from agentpatrol.validators import validate_call


def _summarise(output: Any, limit: int = 240) -> str:
    try:
        text = json.dumps(output, default=str)
    except (TypeError, ValueError):
        text = str(output)
    return text[:limit]


class StepReport(BaseModel):
    call_id: str
    tool_name: str
    decision: PolicyDecision
    reason: str
    executed: bool
    review_approved: bool | None = None
    output: dict[str, Any] | None = None
    error: str | None = None
    latency_ms: float = 0.0


class RunReport(BaseModel):
    run_id: str
    user_task: str
    steps: list[StepReport] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)


class AgentPatrolRuntime:
    """Runs an agent's plan through the full validation and policy pipeline."""

    def __init__(
        self,
        registry: ToolRegistry,
        engine: PolicyEngine,
        agent: MockAgent,
        trace_logger: TraceLogger,
        config: AgentPatrolConfig,
    ) -> None:
        self.registry = registry
        self.engine = engine
        self.agent = agent
        self.trace_logger = trace_logger
        self.config = config

    def run(self, task: dict[str, Any], approve_review: bool = False) -> RunReport:
        run_id = uuid.uuid4().hex[:12]
        user_task = task.get("task", "")
        calls = self.agent.plan(task)
        context = PolicyContext(config=self.config, call_counts={}, run_id=run_id)

        steps: list[StepReport] = []
        trace_steps: list[TraceStep] = []

        for call in calls:
            call.run_id = run_id
            call.call_id = uuid.uuid4().hex[:8]
            # Count this call so RateLimitPolicy can see prior repeats in the run.
            context.call_counts[call.tool_name] = (
                context.call_counts.get(call.tool_name, 0) + 1
            )
            step, trace_step = self._process_call(call, context, approve_review)
            steps.append(step)
            trace_steps.append(trace_step)

        trace = RunTrace(
            run_id=run_id,
            user_task=user_task,
            timestamp=datetime.now(UTC).isoformat(),
            steps=trace_steps,
        )
        self.trace_logger.write(trace)
        return RunReport(
            run_id=run_id,
            user_task=user_task,
            steps=steps,
            summary=self._summary(steps),
        )

    def _process_call(
        self, call: ToolCall, context: PolicyContext, approve_review: bool
    ) -> tuple[StepReport, TraceStep]:
        start = perf_counter()
        outcome = validate_call(self.registry, call)

        if not outcome.ok:
            latency = (perf_counter() - start) * 1000
            reason = f"schema validation failed: {outcome.error}"
            return (
                StepReport(
                    call_id=call.call_id or "",
                    tool_name=call.tool_name,
                    decision=PolicyDecision.BLOCK,
                    reason=reason,
                    executed=False,
                    latency_ms=latency,
                ),
                TraceStep(
                    call_id=call.call_id or "",
                    tool_name=call.tool_name,
                    args=call.args,
                    validation_status="invalid",
                    decision=PolicyDecision.BLOCK,
                    reason=reason,
                    policy_name="schema_validation",
                    risk_score=1.0,
                    execution_status="blocked",
                    latency_ms=latency,
                ),
            )

        tool = self.registry.get_tool(call.tool_name)
        result = self.engine.evaluate(call, tool, context)
        decision = result.decision

        executed = False
        review_approved: bool | None = None
        output: dict[str, Any] | None = None
        error: str | None = None

        if decision in (PolicyDecision.ALLOW, PolicyDecision.WARN):
            executed, output, error = self._execute(tool, call.args)
            execution_status = "executed" if error is None else "error"
        elif decision is PolicyDecision.REVIEW:
            review_approved = approve_review
            if approve_review:
                executed, output, error = self._execute(tool, call.args)
                execution_status = "executed" if error is None else "error"
            else:
                execution_status = "skipped"
        else:  # BLOCK
            execution_status = "blocked"

        latency = (perf_counter() - start) * 1000
        return (
            StepReport(
                call_id=call.call_id or "",
                tool_name=call.tool_name,
                decision=decision,
                reason=result.reason,
                executed=executed,
                review_approved=review_approved,
                output=output,
                error=error,
                latency_ms=latency,
            ),
            TraceStep(
                call_id=call.call_id or "",
                tool_name=call.tool_name,
                args=call.args,
                validation_status="valid",
                decision=decision,
                reason=result.reason,
                policy_name=result.policy_name,
                risk_score=result.risk_score,
                execution_status=execution_status,
                review_approved=review_approved,
                output_summary=_summarise(output) if output is not None else error,
                latency_ms=latency,
            ),
        )

    @staticmethod
    def _execute(
        tool: BaseTool, args: dict[str, Any]
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        try:
            return True, tool.execute(args), None
        except Exception as exc:  # noqa: BLE001 - recorded in the trace, not hidden
            return False, None, f"{type(exc).__name__}: {exc}"

    @staticmethod
    def _summary(steps: list[StepReport]) -> dict[str, int]:
        summary = {"allow": 0, "warn": 0, "review": 0, "block": 0, "executed": 0}
        for step in steps:
            summary[step.decision.value] = summary.get(step.decision.value, 0) + 1
            if step.executed:
                summary["executed"] += 1
        return summary
