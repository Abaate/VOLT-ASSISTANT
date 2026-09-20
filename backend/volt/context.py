from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class ContextManager:
    max_tokens: int = 8192
    chars_per_token: int = 4

    def build(self, system: str, messages: list[dict[str, Any]], extras: list[dict[str, Any]] | None = None):
        budget = max(512, self.max_tokens * self.chars_per_token)
        result = [{"role": "system", "content": system}]
        for message in (extras or []) + messages[::-1]:
            content = str(message.get("content", ""))
            if sum(len(str(x.get("content", ""))) for x in result) + len(content) > budget:
                break
            result.insert(1, message)
        return result
