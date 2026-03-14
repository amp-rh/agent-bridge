import pytest

from agent_bridge.domain.exceptions import ConfigError
from agent_bridge.domain.model import AgentCard, AgentConfig, TaskResult


class TestAgentConfig:
    def test_defaults(self):
        config = AgentConfig()
        assert config.name == "agent"
        assert config.description == "Claude agent"
        assert config.timeout == 300
        assert config.public_url == ""
        assert config.prompt_text is None
        assert config.mcp_servers is None

    def test_custom_values(self):
        config = AgentConfig(name="myagent", description="My agent", timeout=60)
        assert config.name == "myagent"
        assert config.timeout == 60

    def test_empty_name_raises(self):
        with pytest.raises(ConfigError, match="name must not be empty"):
            AgentConfig(name="")

    def test_zero_timeout_raises(self):
        with pytest.raises(ConfigError, match="timeout must be positive"):
            AgentConfig(timeout=0)

    def test_negative_timeout_raises(self):
        with pytest.raises(ConfigError, match="timeout must be positive"):
            AgentConfig(timeout=-1)

    def test_immutable(self):
        config = AgentConfig()
        with pytest.raises(AttributeError):
            config.name = "other"


class TestTaskResult:
    def test_completed(self):
        result = TaskResult.completed("task-1", "output text")
        assert result.task_id == "task-1"
        assert result.state == "completed"
        assert result.output == "output text"

    def test_failed(self):
        result = TaskResult.failed("task-2", "error msg")
        assert result.task_id == "task-2"
        assert result.state == "failed"
        assert result.output == "error msg"

    def test_immutable(self):
        result = TaskResult.completed("t", "o")
        with pytest.raises(AttributeError):
            result.state = "failed"


class TestAgentCard:
    def test_to_dict(self):
        config = AgentConfig(name="test", description="Test agent", public_url="http://localhost")
        card = AgentCard(config=config).to_dict()

        assert card["name"] == "test"
        assert card["description"] == "Test agent"
        assert card["url"] == "http://localhost/a2a"
        assert card["capabilities"]["streaming"] is False
        assert len(card["skills"]) == 1
        assert card["skills"][0]["id"] == "run_task"
        assert "test" in card["skills"][0]["description"]

    def test_empty_public_url(self):
        config = AgentConfig()
        card = AgentCard(config=config).to_dict()
        assert card["url"] == "/a2a"
