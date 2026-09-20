from __future__ import annotations
import json, re, shlex
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

class Risk(IntEnum): SAFE=0; LOW=1; MEDIUM=2; HIGH=3; CRITICAL=4

@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str

@dataclass(frozen=True)
class CommandAssessment:
    risk: Risk
    reasons: tuple[str, ...]

class PermissionManager:
    def __init__(self, settings, confirmer=None, auto=False):
        self.settings, self.confirmer, self.auto = settings, confirmer, auto

    async def check(self, risk: Risk, description: str) -> Decision:
        configured = {Risk.SAFE:self.settings.auto_approve_safe_tools, Risk.LOW:self.settings.auto_approve_safe_tools,
                      Risk.MEDIUM:self.settings.auto_approve_medium_tools, Risk.HIGH:self.settings.auto_approve_high_tools,
                      Risk.CRITICAL:False}
        if risk == Risk.CRITICAL: return Decision(False, "critical actions always require explicit confirmation")
        if self.auto and risk < Risk.CRITICAL: return Decision(True, "auto mode")
        if configured[risk]: return Decision(True, "configured approval")
        if self.confirmer is None: return Decision(False, f"confirmation required ({risk.name})")
        return Decision(bool(await self.confirmer(description, risk.name)), "user decision")

def assess_command(command: str, workspace: str | None = None) -> CommandAssessment:
    text=command.lower(); reasons=[]; risk=Risk.LOW
    critical=(r"\bmkfs(?:\.|\s)", r"\bdd\s+if=", r"/dev/(?:sd|nvme|mmcblk)", r"\b(shutdown|reboot|poweroff)\b", r":\(\)\s*\{", r"\bchmod\s+[-+]?rwx\s+/\b")
    destructive=(r"\brm\s+(-[^ ]*r|-rf|-fr)", r"\bfind\b.*-delete", r"\btruncate\b", r"\bgit\s+(reset|clean|push)\b")
    for pattern in critical:
        if re.search(pattern,text): reasons.append("system or irreversible destruction"); risk=Risk.CRITICAL
    if risk < Risk.CRITICAL:
        for pattern in destructive:
            if re.search(pattern,text): reasons.append("destructive filesystem or git operation"); risk=Risk.HIGH
    if "sudo" in text or "pacman -r" in text or "apt remove" in text: reasons.append("privileged/package change"); risk=max(risk,Risk.HIGH)
    if workspace and any(x in text for x in ("/etc/", "/boot/", "/usr/", "/home/")):
        reasons.append("path may be outside workspace"); risk=max(risk,Risk.HIGH)
    if not reasons: reasons.append("command execution")
    return CommandAssessment(risk, tuple(reasons))
