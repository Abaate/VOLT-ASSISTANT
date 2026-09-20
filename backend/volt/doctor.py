from __future__ import annotations
import asyncio, json
from pathlib import Path
from .config import Settings
async def run_doctor(settings: Settings):
    checks=[]
    checks.append(("python",True,"running Python")); checks.append(("workspace",settings.workspace().is_dir(),str(settings.workspace())))
    try:
        from .memory import Memory
        m=Memory(settings.database_path); m.close(); checks.append(("sqlite",True,str(settings.database_path)))
    except Exception as exc: checks.append(("sqlite",False,str(exc)))
    try:
        from .llm import OllamaProvider
        ok=await OllamaProvider(settings).health(); checks.append(("ollama",ok,settings.ollama_host))
    except Exception as exc: checks.append(("ollama",False,str(exc)))
    import shutil
    checks.append(("disk",shutil.disk_usage(settings.workspace()).free>0,"free space available"))
    return [{"name":n,"ok":ok,"detail":d} for n,ok,d in checks]
