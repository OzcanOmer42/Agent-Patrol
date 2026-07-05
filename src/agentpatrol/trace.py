"""Replayable execution traces stored as JSONL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agentpatrol.decisions import PolicyDecision

DEFAULT_TRACE_PATH = "traces/traces.jsonl"


class TraceStep(BaseModel):
    call_id: str
    tool_name: str
    args: dict[str, Any]
    validation_status: str  # valid | invalid
    decision: PolicyDecision
    reason: str
    policy_name: str
    risk_score: float
    execution_status: str  # executed | skipped | blocked | error
    review_approved: bool | None = None
    output_summary: str | None = None
    latency_ms: float = 0.0


class RunTrace(BaseModel):
    run_id: str
    user_task: str
    timestamp: str
    steps: list[TraceStep] = Field(default_factory=list)


class TraceLogger:
    """Append-only JSONL trace store, one JSON object per run."""

    def __init__(self, path: str | Path = DEFAULT_TRACE_PATH) -> None:
        self.path = Path(path)

    def write(self, trace: RunTrace) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(trace.model_dump_json() + "\n")

    def load(self, run_id: str) -> RunTrace | None:
        """Return the most recent trace matching ``run_id``, if any."""
        if not self.path.exists():
            return None
        found: RunTrace | None = None
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("run_id") == run_id:
                    found = RunTrace.model_validate(record)
        return found

    def list_run_ids(self) -> list[str]:
        if not self.path.exists():
            return []
        ids: list[str] = []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    ids.append(json.loads(line).get("run_id", ""))
        return ids
