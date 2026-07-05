"""AgentPatrol: a validation and policy layer between an agent and its tools."""

from __future__ import annotations

from pathlib import Path

from agentpatrol.agent import MockAgent
from agentpatrol.config import AgentPatrolConfig, load_config
from agentpatrol.decisions import PolicyDecision
from agentpatrol.evaluator import Evaluator
from agentpatrol.policies import build_default_policies
from agentpatrol.policy import PolicyEngine
from agentpatrol.registry import ToolRegistry
from agentpatrol.runtime import AgentPatrolRuntime, RunReport
from agentpatrol.tool import BaseTool, SideEffectLevel, ToolCall
from agentpatrol.tools import DEFAULT_DB_PATH, build_default_registry
from agentpatrol.trace import DEFAULT_TRACE_PATH, TraceLogger

__version__ = "0.1.0"

__all__ = [
    "AgentPatrolConfig",
    "AgentPatrolRuntime",
    "BaseTool",
    "Evaluator",
    "MockAgent",
    "PolicyDecision",
    "PolicyEngine",
    "RunReport",
    "SideEffectLevel",
    "ToolCall",
    "ToolRegistry",
    "TraceLogger",
    "build_default_policies",
    "build_default_registry",
    "build_evaluator",
    "build_runtime",
    "load_config",
]


def build_runtime(
    config_path: str | Path | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
    trace_path: str | Path = DEFAULT_TRACE_PATH,
) -> AgentPatrolRuntime:
    """Assemble a runtime with the default tools and policies."""
    config = load_config(config_path)
    registry = build_default_registry(config, db_path=db_path)
    engine = PolicyEngine(build_default_policies(config))
    return AgentPatrolRuntime(
        registry=registry,
        engine=engine,
        agent=MockAgent(),
        trace_logger=TraceLogger(trace_path),
        config=config,
    )


def build_evaluator(
    config_path: str | Path | None = None, db_path: str | Path = DEFAULT_DB_PATH
) -> Evaluator:
    """Assemble an evaluator with the default tools and policies."""
    config = load_config(config_path)
    registry = build_default_registry(config, db_path=db_path)
    engine = PolicyEngine(build_default_policies(config))
    return Evaluator(registry=registry, engine=engine, config=config)
