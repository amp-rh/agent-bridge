FROM registry.access.redhat.com/ubi9/ubi-minimal:latest AS base

RUN microdnf install -y which tar gzip \
      --nodocs --setopt=install_weak_deps=0 && \
    microdnf clean all

FROM base AS install-uv

ENV UV_PYTHON_INSTALL_DIR=/usr/local/lib/uv/python

RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh && \
    uv python install 3.11 && \
    chmod -R 755 /usr/local/lib/uv && \
    for f in /usr/local/lib/uv/python/cpython-3.11*/bin/python3.11; do \
      ln -sf "$f" /usr/local/bin/python3.11; break; \
    done

FROM install-uv AS install-claude-cli

RUN curl -fsSL https://claude.ai/install.sh | bash && \
    cp /root/.local/bin/claude /usr/local/bin/claude && \
    rm -rf /root/.local

FROM install-claude-cli AS install-packages

COPY agent_bridge /tmp/agent_bridge
RUN UV_PYTHON_INSTALL_MIRROR="" uv pip install --system --python python3.11 --break-system-packages \
      /tmp/agent_bridge && \
    rm -rf /tmp/agent_bridge && \
    find /usr/local/lib/uv/python -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
    true

FROM install-packages AS final

ENV HOME=/home/user \
    AGENT_NAME=agent \
    AGENT_DESCRIPTION="Claude agent" \
    AGENT_TIMEOUT=300 \
    PORT=8080 \
    MCP_CONFIG_FILE= \
    AGENT_CONFIG_FILE=

RUN mkdir -p /home/user/.claude/agents && chown -R 1001:1001 /home/user

USER 1001:1001

EXPOSE 8080

ENTRYPOINT ["agent-bridge", "serve"]
