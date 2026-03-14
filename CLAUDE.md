# Agent Runner

Container image that runs a Claude agent as a service, exposed via MCP (Streamable HTTP) and A2A (Agent-to-Agent) protocols.

## File Structure

- `Containerfile` — Multi-stage UBI9-minimal build (base → uv → claude-cli → packages → final)
- `server.py` — Dual-protocol ASGI server (MCP at `/mcp`, A2A at `/a2a`, agent card at `/.well-known/agent.json`)
- `entrypoint.sh` — Sources YAML config, copies agent prompt, starts server
- `agent_config.py` — Parses YAML config into shell exports for entrypoint.sh
- `Makefile` — build, run, test targets

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AGENT_NAME` | `agent` | Agent name (matches `.claude/agents/<name>.md`) |
| `AGENT_DESCRIPTION` | `Claude agent` | A2A agent card description |
| `AGENT_TIMEOUT` | `300` | Claude subprocess timeout (seconds) |
| `PORT` | `8080` | Server listen port |
| `PUBLIC_URL` | _(empty)_ | Base URL for A2A agent card |
| `AGENT_PROMPT_FILE` | — | Path to system prompt markdown file |
| `MCP_CONFIG_FILE` | — | Path to MCP servers JSON config |
| `AGENT_CONFIG_FILE` | — | Path to YAML agent config |
| `ANTHROPIC_API_KEY` | _(required)_ | Anthropic API key |

## Container Build Conventions

- UBI9-minimal base; `curl-minimal` ships by default — do NOT install `curl` (conflicts)
- `USER 1001:1001` must be the LAST instruction before ENTRYPOINT
- Claude CLI: copy to `/usr/local/bin` then `rm -rf /root/.local` in SAME RUN layer
- `UV_INSTALL_DIR=/usr/local/bin` for world-accessible uv
- `uv pip install --system --break-system-packages` required for system-level installs
- `CLOUDSDK_PYTHON` not needed — only Python 3.11 via uv

## Testing

```sh
make test
```

Tests use pytest with a fake claude binary (entrypoint tests) and httpx ASGITransport (server tests).

## YAML Agent Config Schema

```yaml
name: myagent
system_prompt: |
    You are a helpful assistant.
mcp_servers:
    filesystem:
        command: npx
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        env: {}
```
