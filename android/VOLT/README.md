# Android client

This Compose entry point is intentionally dependency-light. Configure a standard Android Studio project with Compose, add INTERNET and RECORD_AUDIO permissions, then implement the authenticated WebSocket client against `/ws`, Android SpeechRecognizer, TextToSpeech, notification channels, and confirmation dialogs. The server protocol is documented in `docs/architecture.md`.
