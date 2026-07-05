from agentpatrol.decisions import PolicyDecision as D


def test_drafting_allowed(decide):
    decision = decide(
        "email_drafter", {"to": ["a@b.example"], "subject": "hi", "body": "hello"}
    )
    assert decision is D.ALLOW


def test_sending_requires_review(decide):
    decision = decide(
        "email_sender", {"to": ["a@b.example"], "subject": "hi", "body": "hello"}
    )
    assert decision is D.REVIEW


def test_secret_in_send_blocked(decide):
    decision = decide(
        "email_sender",
        {"to": ["a@b.example"], "subject": "hi", "body": "password = supersecret123"},
    )
    assert decision is D.BLOCK


def test_bulk_send_reviewed(decide):
    recipients = [f"user{i}@x.example" for i in range(8)]
    decision = decide(
        "email_sender", {"to": recipients, "subject": "promo", "body": "sale"}
    )
    assert decision is D.REVIEW
