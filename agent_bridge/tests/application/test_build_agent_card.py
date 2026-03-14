from agent_bridge.application.build_agent_card import BuildAgentCard
from agent_bridge.domain.model import AgentConfig


class TestBuildAgentCard:
    def test_returns_card_dict(self):
        config = AgentConfig(name="test", description="Test agent")
        card = BuildAgentCard(config).execute()

        assert card["name"] == "test"
        assert card["description"] == "Test agent"
        assert "skills" in card
        assert "capabilities" in card
