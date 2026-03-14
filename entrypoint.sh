#!/bin/sh
set -e

_AGENT_CONFIG_SCRIPT="${AGENT_CONFIG_SCRIPT:-/usr/local/bin/agent_config.py}"
if [ -f "$_AGENT_CONFIG_SCRIPT" ] && command -v python3 >/dev/null 2>&1; then
    eval "$(python3 "$_AGENT_CONFIG_SCRIPT")"
fi

PROMPT_FILE="${AGENT_PROMPT_FILE:-/run/agent/system_prompt.md}"
if [ -f "$PROMPT_FILE" ]; then
    mkdir -p "$HOME/.claude/agents"
    cp "$PROMPT_FILE" "$HOME/.claude/agents/${AGENT_NAME}.md"
fi

exec python3.11 /usr/local/bin/server.py
