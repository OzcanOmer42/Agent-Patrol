"""Deterministic mock agent.

The MVP intentionally avoids real model calls: AgentPatrol's value is in the
validation, policy, trace, and evaluation layers, not in plan quality. Swapping
this for an LLM planner only requires producing a list of ToolCall objects.
"""

from __future__ import annotations

from typing import Any

from agentpatrol.tool import ToolCall


class MockAgent:
    """Turns a task description into a list of proposed tool calls."""

    def plan(self, task: dict[str, Any]) -> list[ToolCall]:
        requested_by = task.get("requested_by", "mock_agent")
        explicit = task.get("tool_calls")
        if explicit:
            return [
                ToolCall(
                    tool_name=item["tool_name"],
                    args=item.get("args", {}),
                    requested_by=requested_by,
                )
                for item in explicit
            ]
        return self._heuristic(task.get("task", ""), requested_by)

    def _heuristic(self, description: str, requested_by: str) -> list[ToolCall]:
        text = description.lower()
        calls: list[ToolCall] = []
        if "overdue" in text and "invoice" in text:
            calls.append(
                ToolCall(
                    tool_name="sql_query",
                    args={
                        "query": (
                            "SELECT id, customer_email, amount FROM invoices "
                            "WHERE status = 'overdue' LIMIT 10"
                        )
                    },
                    requested_by=requested_by,
                )
            )
            calls.append(
                ToolCall(
                    tool_name="email_drafter",
                    args={
                        "to": ["billing@acme.example"],
                        "subject": "Overdue invoice reminder",
                        "body": "Your invoice is overdue. Please arrange payment.",
                    },
                    requested_by=requested_by,
                )
            )
        elif "calendar" in text:
            calls.append(
                ToolCall(tool_name="calendar_reader", args={}, requested_by=requested_by)
            )
        else:
            calls.append(
                ToolCall(
                    tool_name="calculator",
                    args={"expression": "1 + 1"},
                    requested_by=requested_by,
                )
            )
        return calls
