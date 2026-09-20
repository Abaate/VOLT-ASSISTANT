from __future__ import annotations
import asyncio, json
from typing import Any, AsyncIterator
import httpx
from .config import Settings

class OllamaError(RuntimeError): pass

class OllamaProvider:
    def __init__(self, settings: Settings): self.settings = settings

    async def stream(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> AsyncIterator[tuple[dict[str, Any], bool]]:
        payload: dict[str, Any] = {"model": self.settings.model_name, "messages": messages, "stream": True,
            "options": {"temperature": self.settings.temperature, "top_p": self.settings.top_p,
                        "top_k": self.settings.top_k, "num_predict": self.settings.num_predict}}
        if tools: payload["tools"] = tools
        last: Exception | None = None
        for attempt in range(2):
            try:
                timeout = httpx.Timeout(self.settings.request_timeout, connect=10.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream("POST", f"{self.settings.ollama_host.rstrip('/')}/api/chat", json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line: continue
                            try:
                                data = json.loads(line)
                            except json.JSONDecodeError as exc:
                                raise OllamaError("Ollama returned invalid JSON") from exc
                            yield data.get("message", {}), bool(data.get("done"))
                return
            except (httpx.HTTPError, asyncio.TimeoutError, OllamaError) as exc:
                last = exc
                if attempt == 0: await asyncio.sleep(0.25)
        raise OllamaError(f"Ollama unavailable at {self.settings.ollama_host}: {last}") from last

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                return (await client.get(f"{self.settings.ollama_host.rstrip('/')}/api/tags")).is_success
        except httpx.HTTPError: return False
