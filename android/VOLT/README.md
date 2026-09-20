# VOLT Android client

The Android client is a Kotlin/Compose application. Configure the server URL, token, device ID and session in the app. It uses a WebSocket event protocol: `connected`, `token`, `tool_call`, `tool_result`, `confirmation_required`, `message_end`, `ping`, `pong`, and `error`. Voice uses Android SpeechRecognizer and TextToSpeech; Android actions use official intents and never bypass permissions.
