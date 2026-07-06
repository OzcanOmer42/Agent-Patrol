import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from agentpatrol.api import app  # noqa: E402

client = TestClient(app)


def test_status_ok():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_tools():
    response = client.get("/tools")
    assert response.status_code == 200
    names = {tool["name"] for tool in response.json()["tools"]}
    assert "calculator" in names


def test_list_policies():
    response = client.get("/policies")
    assert response.status_code == 200
    assert "sql_policy" in response.json()["policies"]


def test_run_blocks_destructive_shell():
    payload = {
        "task": "cleanup",
        "tool_calls": [{"tool_name": "shell_command", "args": {"command": "rm -rf /"}}],
    }
    response = client.post("/run", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["steps"][0]["decision"] == "block"


def test_trace_not_found():
    assert client.get("/traces/unknownrun").status_code == 404


def test_dashboard_served():
    response = client.get("/ui")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Agent Patrol" in response.text
