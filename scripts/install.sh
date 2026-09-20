#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
mkdir -p data logs
printf 'Installed VOLT. Copy .env.example to .env and install Ollama separately.\n'
