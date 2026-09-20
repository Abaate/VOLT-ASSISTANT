from enum import IntEnum
from dataclasses import dataclass

class Risk(IntEnum): SAFE=0; LOW=1; MEDIUM=2; HIGH=3; CRITICAL=4
@dataclass
class Decision: allowed: bool; reason: str

class PermissionManager:
    def __init__(self, settings, confirmer=None, auto=False): self.s=settings; self.confirmer=confirmer; self.auto=auto
    async def check(self, risk: Risk, description: str) -> Decision:
        flags={Risk.SAFE:self.s.auto_approve_safe_tools, Risk.LOW:self.s.auto_approve_safe_tools,
               Risk.MEDIUM:self.s.auto_approve_medium_tools, Risk.HIGH:self.s.auto_approve_high_tools,
               Risk.CRITICAL:False}
        if self.auto and risk < Risk.CRITICAL: return Decision(True,"auto mode")
        if flags[risk]: return Decision(True,"configured approval")
        if self.confirmer: return Decision(await self.confirmer(description, risk.name),"user decision")
        return Decision(False,f"confirmation required ({risk.name})")
