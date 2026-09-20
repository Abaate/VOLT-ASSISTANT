import json
from pathlib import Path
from typing import Any
import httpx
from .config import Settings

class OllamaError(RuntimeError): pass

class OllamaProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def stream(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None):
        payload = {"model": self.settings.model_name, "messages": messages, "stream": True,
                   "options": {"temperature": self.settings.temperature, "top_p": self.settings.top_p,
                               "top_k": self.settings.top_k, "num_predict": self.settings.num_predict}}
        if tools: payload["tools"] = tools
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", f"{self.settings.ollama_host}/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            yield data.get("message", {}), bool(data.get("done"))
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama unavailable at {self.settings.ollama_host}: {exc}") from exc

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                return (await client.get(f"{self.settings.ollama_host}/api/tags")).is_success
        except httpx.HTTPError: return False
