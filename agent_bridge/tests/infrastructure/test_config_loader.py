import os

import pytest

from agent_bridge.domain.model import AgentConfig
from agent_bridge.infrastructure.config_loader import load_config


class TestLoadConfigFromYaml:
    def test_loads_full_config(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "name: myagent\n"
            "description: My agent\n"
            "timeout: 60\n"
            "system_prompt: You are helpful.\n"
            "mcp_servers:\n"
            "  fs:\n"
            "    command: npx\n"
        )
        config = load_config(str(config_file))

        assert config.name == "myagent"
        assert config.description == "My agent"
        assert config.timeout == 60
        assert config.prompt_text == "You are helpful."
        assert config.mcp_servers == {"fs": {"command": "npx"}}

    def test_partial_config(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("name: partial\n")
        config = load_config(str(config_file))

        assert config.name == "partial"
        assert config.description == "Claude agent"

    def test_empty_yaml_falls_back_to_env(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")
        monkeypatch.setenv("AGENT_NAME", "envagent")
        config = load_config(str(config_file))

        assert config.name == "envagent"

    def test_missing_file_falls_back_to_env(self, monkeypatch):
        monkeypatch.setenv("AGENT_NAME", "envagent")
        config = load_config("/nonexistent/path.yaml")

        assert config.name == "envagent"


class TestLoadConfigFromEnv:
    def test_loads_from_env(self, monkeypatch):
        monkeypatch.setenv("AGENT_NAME", "envname")
        monkeypatch.setenv("AGENT_DESCRIPTION", "envdesc")
        monkeypatch.setenv("AGENT_TIMEOUT", "120")
        monkeypatch.setenv("PUBLIC_URL", "http://localhost")
        config = load_config()

        assert config.name == "envname"
        assert config.description == "envdesc"
        assert config.timeout == 120
        assert config.public_url == "http://localhost"

    def test_defaults_when_no_env(self, monkeypatch):
        monkeypatch.delenv("AGENT_NAME", raising=False)
        monkeypatch.delenv("AGENT_DESCRIPTION", raising=False)
        monkeypatch.delenv("AGENT_TIMEOUT", raising=False)
        monkeypatch.delenv("PUBLIC_URL", raising=False)
        config = load_config()

        assert config.name == "agent"
        assert config.timeout == 300

    def test_none_config_file_uses_env(self, monkeypatch):
        monkeypatch.setenv("AGENT_NAME", "fromenv")
        config = load_config(None)

        assert config.name == "fromenv"
