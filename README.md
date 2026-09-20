# VOLT Assistant

VOLT is a local-first personal AI agent. It provides a terminal CLI, a FastAPI/WebSocket server, persistent SQLite memory, permission-aware tools, skills, and an Android Compose client that connects to the same server.

## Quick start

```bash
./scripts/install.sh
cp .env.example .env
# install Ollama, then: ollama pull qwen3-coder-next
volt doctor
volt
```

Run the server with `volt server` or `./scripts/server.sh`. The API is bound to localhost by default and requires `API_TOKEN` when configured. For remote phone access, use a VPN such as Tailscale; do not expose the port directly.

## Layout

- `backend/volt`: agent, Ollama provider, context, SQLite memory, tools, skills, permissions, tasks, and sessions.
- `server`: FastAPI transport and token authentication.
- `cli`: terminal entry point (the installed `volt` command).
- `android/VOLT`: Kotlin/Compose reference client.
- `skills`: on-demand Markdown instructions.
- `tests`: safe unit and API tests.

## Commands

`volt`, `volt server`, `volt doctor`, `volt --auto`. In the interactive prompt use `/help`, `/clear`, `/status`, `/memory`, `/skills`, `/tools`, `/permissions`, `/session`, `/tasks`, `/reset`, `/exit`.

## Security and privacy

The default model and memory are local. Tools are risk-rated. SAFE tools can be auto-approved; MEDIUM and above require confirmation according to configuration, and CRITICAL tools remain protected even with `--auto`. Tokens and secrets are never logged.

See `docs/` for architecture, installation, Ollama tuning, Android setup, voice, security, networking, and troubleshooting.
