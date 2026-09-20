# Architecture

The runtime is a single local agent core shared by CLI and FastAPI/WebSocket transports. The core composes bounded recent messages, relevant SQLite memories, tool schemas, and the system policy before streaming to Ollama. Tool calls are risk checked before execution. Android is a thin authenticated client; long-running work belongs to the server/PC process and can be represented by persistent task records.

## Event protocol

WebSocket events are `token`, `tool_call`, `tool_result`, `message_end`, and `error`. A production Android client should persist its device ID and reconnect with exponential backoff.
