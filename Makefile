IMAGE ?= agent-runner
TAG   ?= latest

AGENT_PROMPT_FILE ?=
MCP_CONFIG_FILE   ?=
AGENT_CONFIG_FILE ?=

.PHONY: build run test

build:
	podman build -f Containerfile -t $(IMAGE):$(TAG) .

run:
	podman run --rm -it \
	  -e ANTHROPIC_API_KEY \
	  -e AGENT_NAME \
	  -e AGENT_DESCRIPTION \
	  -e AGENT_TIMEOUT \
	  -p 8080:8080 \
	  $(if $(AGENT_PROMPT_FILE),-v $(abspath $(AGENT_PROMPT_FILE)):/run/agent/system_prompt.md:ro) \
	  $(if $(MCP_CONFIG_FILE),-v $(abspath $(MCP_CONFIG_FILE)):/run/agent/mcp_config.json:ro) \
	  $(if $(AGENT_CONFIG_FILE),-v $(abspath $(AGENT_CONFIG_FILE)):/run/agent/config.yaml:ro) \
	  $(IMAGE):$(TAG)

test:
	uv run --with pytest --with pyyaml --with mcp --with httpx --with uvicorn pytest tests/ -v
