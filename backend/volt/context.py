from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class ContextManager:
    max_tokens: int = 8192
    chars_per_token: int = 4
    def estimate(self, messages): return sum(len(str(m.get("content", ""))) for m in messages) // self.chars_per_token
    def summarize(self, messages):
        if not messages: return ""
        lines=[f"{m.get('role')}: {str(m.get('content',''))[:500]}" for m in messages]
        return "Conversation summary:\n" + "\n".join(lines[-20:])
    def build(self, system: str, messages: list[dict[str, Any]], extras: list[dict[str, Any]] | None=None):
        budget=max(512, self.max_tokens*self.chars_per_token); base=[{"role":"system","content":system}]
        for extra in extras or []:
            content=str(extra.get("content", ""))
            if len(str(base[0]["content"]))+len(content)<budget: base.append(extra)
        selected=[]; used=sum(len(str(x.get("content",""))) for x in base)
        for message in reversed(messages):
            size=len(str(message.get("content", "")))
            if used+size>budget: break
            selected.append(message); used+=size
        selected.reverse()
        if len(selected)<len(messages) and used+200<budget: base.append({"role":"system","content":self.summarize(messages[:-len(selected) or None])})
        return base+selected
