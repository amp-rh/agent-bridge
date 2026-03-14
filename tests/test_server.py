"""Tests for the MCP + A2A server."""

import subprocess
from unittest.mock import patch

import httpx
import pytest


@pytest.fixture
def client():
    from server import app
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


MOCK_OUTPUT = "Hello from the agent"


@pytest.mark.anyio
async def test_agent_card(client):
    resp = await client.get("/.well-known/agent.json")

    assert resp.status_code == 200
    card = resp.json()
    assert card["name"] == "agent"
    assert "skills" in card
    assert card["capabilities"]["streaming"] is False


@pytest.mark.anyio
async def test_a2a_task_send(client):
    with patch("server.execute_agent", return_value=MOCK_OUTPUT):
        resp = await client.post("/a2a", json={
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tasks/send",
            "params": {
                "id": "task-1",
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": "hello"}],
                },
            },
        })

    assert resp.status_code == 200
    result = resp.json()["result"]
    assert result["id"] == "task-1"
    assert result["status"]["state"] == "completed"
    assert result["artifacts"][0]["parts"][0]["text"] == MOCK_OUTPUT


@pytest.mark.anyio
async def test_a2a_task_send_no_text(client):
    resp = await client.post("/a2a", json={
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/send",
        "params": {
            "message": {"role": "user", "parts": []},
        },
    })

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == -32602


@pytest.mark.anyio
async def test_a2a_unknown_method(client):
    resp = await client.post("/a2a", json={
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tasks/unknown",
        "params": {},
    })

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == -32601


@pytest.mark.anyio
async def test_a2a_invalid_json(client):
    resp = await client.post(
        "/a2a",
        content=b"not json",
        headers={"content-type": "application/json"},
    )

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == -32700


@pytest.mark.anyio
async def test_a2a_agent_failure(client):
    with patch("server.execute_agent", side_effect=RuntimeError("boom")):
        resp = await client.post("/a2a", json={
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tasks/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": "hello"}],
                },
            },
        })

    assert resp.status_code == 200
    result = resp.json()["result"]
    assert result["status"]["state"] == "failed"
    assert "boom" in result["artifacts"][0]["parts"][0]["text"]


def test_execute_agent_calls_claude():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="output", stderr="",
        )
        from server import execute_agent
        result = execute_agent("test prompt")

    assert result == "output"
    args = mock_run.call_args[0][0]
    assert "claude" in args
    assert "--agent" in args
    assert "test prompt" in args


def test_execute_agent_raises_on_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="error msg",
        )
        from server import execute_agent
        with pytest.raises(RuntimeError, match="error msg"):
            execute_agent("test prompt")
