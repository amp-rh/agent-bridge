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

# Authenticate gh CLI — fetch token from GCP Secret Manager (no plaintext secrets needed)
if ! gh auth status &>/dev/null; then
  GCP_PROJECT="${GCP_PROJECT:-claude-connectors}"
  SECRET_NAME="github-token"

  echo "Fetching GitHub token from Secret Manager..."
  # Get an access token from the GCE metadata service (works in Cloud Run / GCP environments)
  GCLOUD_TOKEN=$(curl -sf \
    -H "Metadata-Flavor: Google" \
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || true)

  if [ -z "$GCLOUD_TOKEN" ]; then
    echo "WARNING: Could not reach GCE metadata service. gh CLI will not be authenticated." >&2
    echo "Ensure the session runs in a GCP environment with access to Secret Manager." >&2
  else
    GH_TOKEN=$(curl -sf \
      -H "Authorization: Bearer $GCLOUD_TOKEN" \
      "https://secretmanager.googleapis.com/v1/projects/${GCP_PROJECT}/secrets/${SECRET_NAME}/versions/latest:access" \
      | python3 -c "import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)['payload']['data']).decode())" 2>/dev/null || true)

    if [ -z "$GH_TOKEN" ]; then
      echo "WARNING: Secret '${SECRET_NAME}' not found or not accessible in project '${GCP_PROJECT}'." >&2
      echo "Create it with: echo -n '<token>' | gcloud secrets create ${SECRET_NAME} --data-file=- --project=${GCP_PROJECT}" >&2
    else
      echo "Authenticating gh CLI..."
      echo "$GH_TOKEN" | gh auth login --with-token
      echo "gh CLI authenticated as: $(gh api user --jq '.login')"
    fi
  fi
else
  echo "gh CLI already authenticated"
fi
