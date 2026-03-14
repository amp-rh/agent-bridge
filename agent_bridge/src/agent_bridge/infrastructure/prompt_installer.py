from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from agent_bridge.domain.model import AgentConfig


class PromptInstaller:
    def install(self, config: AgentConfig) -> None:
        if config.prompt_text:
            self._install_prompt(config.name, config.prompt_text)
        if config.mcp_servers:
            self._install_mcp_config(config.mcp_servers)

    def _install_prompt(self, agent_name: str, prompt_text: str) -> None:
        agents_dir = Path.home() / ".claude" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = agents_dir / f"{agent_name}.md"
        prompt_path.write_text(prompt_text)

    def _install_mcp_config(self, mcp_servers: dict) -> None:
        mcp_json = {"mcpServers": mcp_servers}
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(mcp_json, tmp)
        tmp.close()
        os.environ["MCP_CONFIG_FILE"] = tmp.name
