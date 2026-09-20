# Installation

Install Python 3.11+, Ollama, and (optionally) NVIDIA drivers. Run `scripts/install.sh`, copy `.env.example` to `.env`, then `ollama pull qwen3-coder-next`. Set `VOLT_WORKSPACE` to the project you want the agent to inspect. Keep `SERVER_HOST=127.0.0.1`; use Tailscale/WireGuard for phone access.
