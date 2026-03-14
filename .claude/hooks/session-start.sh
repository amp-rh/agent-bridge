#!/bin/bash
set -euo pipefail

# Only run in remote (web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install uv package manager
if ! command -v uv &>/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# Persist uv on PATH for the session
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi

# Install GitHub CLI
if ! command -v gh &>/dev/null; then
  (type -p wget >/dev/null || (sudo apt-get update && sudo apt-get install -y wget)) \
    && sudo mkdir -p -m 755 /etc/apt/keyrings \
    && out=$(mktemp) \
    && wget -nv -O "$out" https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    && cat "$out" | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && sudo apt-get update \
    && sudo apt-get install -y gh \
    && rm -f "$out"
fi

# Install Google Cloud SDK
if ! command -v gcloud &>/dev/null; then
  curl -sSL https://sdk.cloud.google.com > /tmp/install-gcloud.sh
  bash /tmp/install-gcloud.sh --disable-prompts --install-dir="$HOME" 2>/dev/null
  rm -f /tmp/install-gcloud.sh
fi

# Persist gcloud on PATH for the session
if [ -d "$HOME/google-cloud-sdk/bin" ] && [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

# Install project dependencies (including dev extras)
cd "$CLAUDE_PROJECT_DIR"
uv pip install --system -e ".[dev]"
