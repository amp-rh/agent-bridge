import json
import os
from pathlib import Path

from agent_bridge.domain.model import AgentConfig
from agent_bridge.infrastructure.prompt_installer import PromptInstaller


class TestPromptInstaller:
    def test_installs_prompt_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        config = AgentConfig(name="test", prompt_text="You are helpful.")
        PromptInstaller().install(config)

        prompt_path = tmp_path / ".claude" / "agents" / "test.md"
        assert prompt_path.exists()
        assert prompt_path.read_text() == "You are helpful."

    def test_skips_prompt_when_none(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        config = AgentConfig(name="test")
        PromptInstaller().install(config)

        agents_dir = tmp_path / ".claude" / "agents"
        assert not agents_dir.exists()

    def test_installs_mcp_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        mcp = {"fs": {"command": "npx"}}
        config = AgentConfig(name="test", mcp_servers=mcp)
        PromptInstaller().install(config)

        mcp_file = os.environ.get("MCP_CONFIG_FILE")
        assert mcp_file
        with open(mcp_file) as f:
            data = json.load(f)
        assert data["mcpServers"] == mcp

    def test_skips_mcp_when_none(self, monkeypatch):
        monkeypatch.delenv("MCP_CONFIG_FILE", raising=False)
        config = AgentConfig(name="test")
        PromptInstaller().install(config)
