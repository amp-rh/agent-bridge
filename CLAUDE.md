# Agent Bridge

Container image that bridges a Claude agent to MCP (Streamable HTTP) and A2A (Agent-to-Agent) protocols.

## File Structure

- `Containerfile` — Multi-stage UBI9-minimal build (base → uv → claude-cli → packages → final)
- `agent_bridge/` — Standalone Python package (Clean Architecture)
  - `src/agent_bridge/domain/` — Value objects, ports, exceptions
  - `src/agent_bridge/application/` — Use cases (ExecuteTask, BuildAgentCard)
  - `src/agent_bridge/infrastructure/` — Claude subprocess executor, config loader, prompt installer
  - `src/agent_bridge/presentation/` — ASGI server, MCP, A2A routes, CLI entry point
  - `tests/` — pytest test suite
- `Makefile` — build, run, test targets

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AGENT_NAME` | `agent` | Agent name (matches `.claude/agents/<name>.md`) |
| `AGENT_DESCRIPTION` | `Claude agent` | A2A agent card description |
| `AGENT_TIMEOUT` | `300` | Claude subprocess timeout (seconds) |
| `PORT` | `8080` | Server listen port |
| `PUBLIC_URL` | _(empty)_ | Base URL for A2A agent card |
| `AGENT_CONFIG_FILE` | — | Path to YAML agent config |
| `ANTHROPIC_API_KEY` | _(required)_ | Anthropic API key |

## Container Build Conventions

- UBI9-minimal base; `curl-minimal` ships by default — do NOT install `curl` (conflicts)
- `USER 1001:1001` must be the LAST instruction before ENTRYPOINT
- Claude CLI: copy to `/usr/local/bin` then `rm -rf /root/.local` in SAME RUN layer
- `UV_INSTALL_DIR=/usr/local/bin` for world-accessible uv
- `uv pip install --system --break-system-packages` required for system-level installs
- Package installed from `agent_bridge/` subdirectory during build

## Testing

```sh
make test
```

Tests use pytest with dependency injection (FakeExecutor) and httpx ASGITransport (server tests).

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
