from __future__ import annotations

import os
from typing import Any

from agent_bridge.domain.model import AgentConfig


def load_config(config_file: str | None = None) -> AgentConfig:
    if config_file and os.path.exists(config_file):
        return _load_yaml(config_file)
    return _load_env()


def _load_yaml(path: str) -> AgentConfig:
    import yaml

    with open(path) as f:
        data = yaml.safe_load(f)

    if not data:
        return _load_env()

    kwargs: dict[str, Any] = {}
    if "name" in data:
        kwargs["name"] = str(data["name"])
    if "description" in data:
        kwargs["description"] = str(data["description"])
    if "timeout" in data:
        kwargs["timeout"] = int(data["timeout"])
    if "public_url" in data:
        kwargs["public_url"] = str(data["public_url"])
    if "system_prompt" in data:
        kwargs["prompt_text"] = str(data["system_prompt"])
    if "mcp_servers" in data:
        kwargs["mcp_servers"] = data["mcp_servers"]

    return AgentConfig(**kwargs)


def _load_env() -> AgentConfig:
    kwargs: dict[str, Any] = {}

    if name := os.environ.get("AGENT_NAME"):
        kwargs["name"] = name
    if description := os.environ.get("AGENT_DESCRIPTION"):
        kwargs["description"] = description
    if timeout := os.environ.get("AGENT_TIMEOUT"):
        kwargs["timeout"] = int(timeout)
    if public_url := os.environ.get("PUBLIC_URL"):
        kwargs["public_url"] = public_url

    return AgentConfig(**kwargs)
