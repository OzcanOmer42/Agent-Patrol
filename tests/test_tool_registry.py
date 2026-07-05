import pytest

from agentpatrol.tools import build_default_registry


def test_registered_tools_present(registry):
    names = {tool.name for tool in registry.list_tools()}
    assert {"calculator", "sql_query", "email_sender", "shell_command"} <= names


def test_get_unknown_tool_raises(registry):
    with pytest.raises(KeyError):
        registry.get_tool("does_not_exist")


def test_duplicate_registration_raises(config, tmp_path):
    registry = build_default_registry(config, db_path=tmp_path / "demo.db")
    from agentpatrol.tools.calculator import CalculatorTool

    with pytest.raises(ValueError):
        registry.register(CalculatorTool())


def test_contains_and_len(registry):
    assert "calculator" in registry
    assert len(registry) >= 8
