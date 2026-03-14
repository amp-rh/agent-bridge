#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install Python dependencies using uv
if command -v uv &>/dev/null; then
  echo "Installing Python dependencies..."
  uv pip install --system -e ".[dev]" --quiet
else
  echo "uv not found, skipping Python dependency install"
fi

# Authenticate gh CLI using GH_TOKEN if available and not already logged in
if [ -n "${GH_TOKEN:-}" ]; then
  if ! gh auth status &>/dev/null; then
    echo "Authenticating gh CLI..."
    echo "$GH_TOKEN" | gh auth login --with-token
    echo "gh CLI authenticated as: $(gh api user --jq '.login')"
  else
    echo "gh CLI already authenticated"
  fi
else
  echo "WARNING: GH_TOKEN is not set. gh CLI will not be authenticated." >&2
  echo "Set GH_TOKEN in your Claude Code web environment settings to enable gh CLI login." >&2
fi
