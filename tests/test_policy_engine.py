from agentpatrol.decisions import PolicyDecision as D
from agentpatrol.policy import PolicyEngine, PolicyResult


def _result(decision, name="p", risk=0.5):
    return PolicyResult(decision=decision, reason="r", policy_name=name, risk_score=risk)


def test_priority_block_beats_all():
    combined = PolicyEngine._combine(
        [_result(D.ALLOW), _result(D.WARN), _result(D.REVIEW), _result(D.BLOCK)]
    )
    assert combined.decision is D.BLOCK


def test_priority_review_beats_warn():
    combined = PolicyEngine._combine([_result(D.WARN), _result(D.REVIEW)])
    assert combined.decision is D.REVIEW


def test_all_allow_is_allow():
    combined = PolicyEngine._combine([_result(D.ALLOW), _result(D.ALLOW)])
    assert combined.decision is D.ALLOW
    assert "allow" in combined.reason


def test_file_policy_blocks_dotenv(decide):
    assert decide("file_reader", {"path": "workspace/.env"}) is D.BLOCK


def test_file_policy_allows_examples(decide):
    assert decide("file_reader", {"path": "examples/report.txt"}) is D.ALLOW


def test_pii_policy_blocks_secret_in_high_side_effect(decide):
    decision = decide(
        "email_sender",
        {"to": ["x@y.example"], "subject": "s", "body": "api_key = sk-ABCDEF1234567890ABCD"},
    )
    assert decision is D.BLOCK


def test_rate_limit_blocks_beyond_hard_limit(decide):
    assert decide("calculator", {"expression": "1+1"}, call_count=8) is D.BLOCK


def test_calendar_writer_requires_review(decide):
    decision = decide(
        "calendar_writer",
        {"title": "Sync", "start": "2025-04-01T09:00", "end": "2025-04-01T09:30"},
    )
    assert decision is D.REVIEW
