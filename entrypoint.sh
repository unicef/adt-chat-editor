#!/bin/bash
set -e

# Log in to Codex automatically at container start
if [ -n "$OPENAI_API_KEY" ]; then
    codex login --api-key "$OPENAI_API_KEY" || true
fi

# Execute the original command
exec "$@"