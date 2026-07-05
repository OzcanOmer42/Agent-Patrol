from agentpatrol.decisions import PolicyDecision as D


def test_rm_rf_blocked(decide):
    assert decide("shell_command", {"command": "rm -rf /"}) is D.BLOCK


def test_shutdown_blocked(decide):
    assert decide("shell_command", {"command": "shutdown now"}) is D.BLOCK


def test_env_read_blocked(decide):
    assert decide("shell_command", {"command": "printenv"}) is D.BLOCK


def test_network_command_reviewed(decide):
    assert decide("shell_command", {"command": "curl http://example.com"}) is D.REVIEW


def test_echo_allowed(decide):
    assert decide("shell_command", {"command": "echo hello"}) is D.ALLOW


def test_unknown_command_reviewed(decide):
    assert decide("shell_command", {"command": "python train.py"}) is D.REVIEW
