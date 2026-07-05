import pytest
from pydantic import ValidationError

from agentpatrol.tool import ToolCall
from agentpatrol.validators import validate_call


def test_valid_args_pass(registry):
    model = registry.validate_tool_call("calculator", {"expression": "1+1"})
    assert model.expression == "1+1"


def test_missing_required_arg_fails(registry):
    with pytest.raises(ValidationError):
        registry.validate_tool_call("calculator", {"expr": "1+1"})


def test_validate_call_reports_invalid(registry):
    call = ToolCall(tool_name="sql_query", args={}, requested_by="test")
    outcome = validate_call(registry, call)
    assert outcome.ok is False
    assert outcome.error


def test_validate_call_unknown_tool(registry):
    call = ToolCall(tool_name="ghost", args={}, requested_by="test")
    outcome = validate_call(registry, call)
    assert outcome.ok is False
    assert "unknown tool" in outcome.error
