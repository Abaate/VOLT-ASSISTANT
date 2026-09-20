#!/usr/bin/env bash
set -euo pipefail
exec python -m uvicorn server.app:app --host "${SERVER_HOST:-127.0.0.1}" --port "${SERVER_PORT:-8080}"
