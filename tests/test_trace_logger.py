from agentpatrol.decisions import PolicyDecision
from agentpatrol.trace import RunTrace, TraceLogger, TraceStep


def _sample_trace(run_id="abc123"):
    return RunTrace(
        run_id=run_id,
        user_task="demo",
        timestamp="2025-04-01T00:00:00Z",
        steps=[
            TraceStep(
                call_id="c1",
                tool_name="calculator",
                args={"expression": "1+1"},
                validation_status="valid",
                decision=PolicyDecision.ALLOW,
                reason="ok",
                policy_name="policy_engine",
                risk_score=0.0,
                execution_status="executed",
                output_summary="2",
                latency_ms=0.1,
            )
        ],
    )


def test_write_and_load_roundtrip(tmp_path):
    logger = TraceLogger(tmp_path / "traces.jsonl")
    logger.write(_sample_trace("run1"))
    loaded = logger.load("run1")
    assert loaded is not None
    assert loaded.run_id == "run1"
    assert loaded.steps[0].tool_name == "calculator"


def test_load_missing_returns_none(tmp_path):
    logger = TraceLogger(tmp_path / "traces.jsonl")
    assert logger.load("nope") is None


def test_list_run_ids(tmp_path):
    logger = TraceLogger(tmp_path / "traces.jsonl")
    logger.write(_sample_trace("run1"))
    logger.write(_sample_trace("run2"))
    assert logger.list_run_ids() == ["run1", "run2"]
