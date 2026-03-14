import pytest

from agent_bridge.domain.exceptions import AgentExecutionError


MOCK_OUTPUT = "Hello from the agent"


@pytest.mark.anyio
async def test_a2a_task_send(client, fake_executor):
    fake_executor.response = MOCK_OUTPUT
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
async def test_a2a_agent_failure(client, fake_executor):
    fake_executor.set_error(AgentExecutionError("boom"))
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
