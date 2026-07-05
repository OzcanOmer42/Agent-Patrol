"""Shared fixtures for the test suite."""

from __future__ import annotations

import pytest

from agentpatrol.config import AgentPatrolConfig
from agentpatrol.decisions import PolicyDecision
from agentpatrol.policies import build_default_policies
from agentpatrol.policy import PolicyContext, PolicyEngine
from agentpatrol.tool import ToolCall
from agentpatrol.tools import build_default_registry
from agentpatrol.validators import validate_call


@pytest.fixture
def config() -> AgentPatrolConfig:
    return AgentPatrolConfig()


@pytest.fixture
def registry(config, tmp_path):
    return build_default_registry(config, db_path=tmp_path / "demo.db")


@pytest.fixture
def engine(config) -> PolicyEngine:
    return PolicyEngine(build_default_policies(config))


@pytest.fixture
def decide(registry, engine, config):
    """Return decide(tool_name, args, call_count=1) -> PolicyDecision."""

    def _decide(tool_name: str, args: dict, call_count: int = 1) -> PolicyDecision:
        call = ToolCall(tool_name=tool_name, args=args, requested_by="test")
        outcome = validate_call(registry, call)
        if not outcome.ok:
            return PolicyDecision.BLOCK
        context = PolicyContext(config=config, call_counts={tool_name: call_count})
        tool = registry.get_tool(tool_name)
        return engine.evaluate(call, tool, context).decision

    return _decide
