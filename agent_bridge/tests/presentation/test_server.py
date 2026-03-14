import pytest


@pytest.mark.anyio
async def test_agent_card(client):
    resp = await client.get("/.well-known/agent.json")

    assert resp.status_code == 200
    card = resp.json()
    assert card["name"] == "agent"
    assert "skills" in card
    assert card["capabilities"]["streaming"] is False
