"""FastAPI application exposing the AgentPatrol runtime."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from agentpatrol import __version__, build_evaluator, build_runtime
from agentpatrol.policies import build_default_policies

_STATIC_DIR = Path(__file__).parent / "static"

_CONFIG_PATH = os.environ.get("AGENTPATROL_CONFIG") or None
_DB_PATH = os.environ.get("AGENTPATROL_DB", "data/demo.db")
_TRACE_PATH = os.environ.get("AGENTPATROL_TRACE", "traces/traces.jsonl")
_SCENARIOS_PATH = os.environ.get("AGENTPATROL_SCENARIOS", "examples/eval_scenarios.json")

app = FastAPI(title="Agent Patrol", version=__version__)

_runtime = build_runtime(_CONFIG_PATH, db_path=_DB_PATH, trace_path=_TRACE_PATH)
_evaluator = build_evaluator(_CONFIG_PATH, db_path=_DB_PATH)


class RunRequest(BaseModel):
    task: str = ""
    requested_by: str = "api"
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    approve_review: bool = False


@app.get("/")
def status() -> dict[str, Any]:
    return {
        "name": "Agent Patrol",
        "version": __version__,
        "status": "ok",
        "ui": "/ui",
        "tools_registered": len(_runtime.registry),
        "policies_active": len(_runtime.engine.policies),
    }


@app.get("/ui", response_class=HTMLResponse)
def dashboard() -> str:
    """Serve the browser console."""
    return (_STATIC_DIR / "dashboard.html").read_text(encoding="utf-8")


@app.get("/tools")
def list_tools() -> dict[str, Any]:
    return {"tools": [tool.describe() for tool in _runtime.registry.list_tools()]}


@app.get("/policies")
def list_policies() -> dict[str, Any]:
    return {"policies": [policy.name for policy in build_default_policies()]}


@app.post("/run")
def run_task(request: RunRequest) -> dict[str, Any]:
    task: dict[str, Any] = {"task": request.task, "requested_by": request.requested_by}
    if request.tool_calls:
        task["tool_calls"] = request.tool_calls
    report = _runtime.run(task, approve_review=request.approve_review)
    return report.model_dump()


@app.get("/traces/{run_id}")
def get_trace(run_id: str) -> dict[str, Any]:
    trace = _runtime.trace_logger.load(run_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"no trace for run id {run_id}")
    return trace.model_dump()


@app.post("/evaluate")
def evaluate() -> dict[str, Any]:
    path = Path(_SCENARIOS_PATH)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"scenarios not found: {path}")
    scenarios = json.loads(path.read_text())["scenarios"]
    _, metrics = _evaluator.run(scenarios)
    return metrics.model_dump()
