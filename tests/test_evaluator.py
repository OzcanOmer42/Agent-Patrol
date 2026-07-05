import json
from pathlib import Path

from agentpatrol import build_evaluator
from agentpatrol.decisions import PolicyDecision
from agentpatrol.evaluator import Evaluator
from agentpatrol.policies import build_default_policies
from agentpatrol.policy import PolicyEngine


def test_metric_math_is_computed():
    from agentpatrol.evaluator import ScenarioResult

    D = PolicyDecision

    def sr(name, expected, actual, correct, schema_failed):
        return ScenarioResult(
            name=name,
            category="x",
            expected=expected,
            actual=actual,
            correct=correct,
            schema_failed=schema_failed,
            latency_ms=1.0,
        )

    results = [
        sr("a", D.ALLOW, D.ALLOW, True, False),
        sr("b", D.BLOCK, D.ALLOW, False, False),
        sr("c", D.REVIEW, D.REVIEW, True, False),
        sr("d", D.BLOCK, D.BLOCK, True, True),
    ]
    metrics = Evaluator._metrics(results)
    assert metrics.total == 4
    assert metrics.correct == 3
    assert abs(metrics.policy_accuracy - 0.75) < 1e-9
    # one dangerous scenario (b) was allowed out of three non-allow scenarios
    assert abs(metrics.false_allow_rate - (1 / 3)) < 1e-9
    assert metrics.schema_validation_failure_count == 1
    assert metrics.review_precision == 1.0


def test_real_scenarios_high_accuracy(tmp_path):
    evaluator = build_evaluator(db_path=tmp_path / "demo.db")
    scenarios = json.loads(Path("examples/eval_scenarios.json").read_text())["scenarios"]
    results, metrics = evaluator.run(scenarios)
    assert metrics.total == len(scenarios)
    assert metrics.policy_accuracy == 1.0
    assert metrics.false_allow_rate == 0.0


def test_engine_is_wired(config):
    engine = PolicyEngine(build_default_policies(config))
    assert len(engine.policies) == 7
