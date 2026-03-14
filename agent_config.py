#!/usr/bin/env python3
"""
Reads a YAML agent config file and emits shell export statements.

Consumed by entrypoint.sh via: eval "$(python3 agent_config.py)"

YAML schema:
    name: myagent
    system_prompt: |
        You are a helpful assistant.
    mcp_servers:
        filesystem:
            command: npx
            args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            env: {}
"""
import json
import os
import shlex
import sys
import tempfile

try:
    import yaml
except ImportError:
    sys.exit(0)

config_file = os.environ.get("AGENT_CONFIG_FILE", "/run/agent/config.yaml")

if not os.path.exists(config_file):
    sys.exit(0)

with open(config_file) as f:
    config = yaml.safe_load(f)

if not config:
    sys.exit(0)

exports = {}

if "name" in config:
    exports["AGENT_NAME"] = str(config["name"])

if "system_prompt" in config:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    tmp.write(config["system_prompt"])
    tmp.close()
    exports["AGENT_PROMPT_FILE"] = tmp.name

if "mcp_servers" in config:
    mcp_json = {"mcpServers": config["mcp_servers"]}
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(mcp_json, tmp)
    tmp.close()
    exports["MCP_CONFIG_FILE"] = tmp.name

for key, value in exports.items():
    print(f"export {key}={shlex.quote(value)}")
