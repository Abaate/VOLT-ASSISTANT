# VOLT Assistant

This repository contains the corrected Python package and transport layer for VOLT. Install with `pip install -e .`; the package is discovered from `backend/volt`, so both `volt` and `volt server` work from a clean environment.

## Run

```bash
cp .env.example .env
pip install -e .
ollama pull qwen3-coder-next
volt doctor
volt server
volt
```

`POST /chat` streams newline-delimited JSON events. `/ws` accepts a token in the `token` query parameter or Bearer header when `API_TOKEN` is configured. Keep the server on loopback and use Tailscale/WireGuard for remote Android access.

The Android directory contains the client contract and Compose entry point; an Android SDK/Gradle installation is required to produce an APK.
