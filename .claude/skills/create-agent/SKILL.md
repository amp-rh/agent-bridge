---
name: create-agent
description: Create and serve a containerized Claude agent with MCP and A2A endpoints.
user-invocable: true
---

You are guiding the user through creating and running a containerized Claude agent. The agent-runner project is at the current working directory.

Follow these steps in order. Ask the user questions at each step before proceeding.

## Step 1: Gather Agent Details

Ask the user for:

1. **Agent name** — lowercase, hyphen-separated (e.g. `code-reviewer`). Becomes the YAML `name` field and config filename.
2. **Agent purpose** — one sentence describing what the agent does.
3. **System prompt** — ask if they want to provide their own or have one generated from the purpose. If generating, write a focused system prompt under 30 lines.
4. **MCP servers** — ask if the agent needs tool servers. Offer these common options:
   - **Filesystem** — read/write access to a directory (`npx -y @modelcontextprotocol/server-filesystem <path>`)
   - **GitHub** — GitHub API access (`npx -y @modelcontextprotocol/server-github`)
   - **Fetch** — HTTP fetching (`npx -y @modelcontextprotocol/server-fetch`)
   - **Custom** — user provides command, args, and env
   - **None** — no MCP servers

## Step 2: Generate the YAML Config

Write the config to `configs/<agent-name>.yaml` (create the `configs/` directory if needed).

The YAML must follow this schema exactly — **only these three keys are supported** by `agent_config.py`:

```yaml
name: <agent-name>
system_prompt: |
    <system prompt text>
mcp_servers:
    <server-name>:
        command: <command>
        args: [<args>]
        env: {}
```

Do NOT include any other keys (no `model`, `description`, `allowed_tools`, `permission_mode`, `max_turns`, etc.). They will be silently ignored.

Omit `mcp_servers` entirely if none were requested. Show the generated YAML to the user and confirm before writing the file.

## Step 3: Build the Container Image

Check if the image exists and whether it's stale (older than the source files):

```bash
podman image exists agent-runner:latest && \
  podman inspect --format '{{.Created}}' agent-runner:latest
```

```bash
stat -c '%Y' Containerfile server.py entrypoint.sh agent_config.py | sort -rn | head -1
```

If the image does not exist, build it. If the image exists but is older than any source file, recommend rebuilding. Run:

```bash
make build
```

## Step 4: Run the Agent

Verify `ANTHROPIC_API_KEY` is set:

```bash
test -n "$ANTHROPIC_API_KEY" && echo "set" || echo "missing"
```

If missing, tell the user to export it. Then run:

```bash
make run AGENT_CONFIG_FILE=./configs/<agent-name>.yaml
```

## Step 5: Report Endpoints

After starting, tell the user:

```
Agent "<agent-name>" is running:

  MCP:        http://localhost:8080/mcp
  A2A:        http://localhost:8080/a2a
  Agent Card: http://localhost:8080/.well-known/agent.json

Test with:
  curl -4 http://localhost:8080/.well-known/agent.json

Add as MCP server in Claude Code settings:
  {
    "mcpServers": {
      "<agent-name>": {
        "url": "http://localhost:8080/mcp"
      }
    }
  }

Config: configs/<agent-name>.yaml
Re-run: make run AGENT_CONFIG_FILE=./configs/<agent-name>.yaml
```

## Rules

- Confirm the YAML content with the user before writing.
- Never put API keys in config files or commands.
- To modify an existing agent, read its config from `configs/`, apply changes, and rewrite.
