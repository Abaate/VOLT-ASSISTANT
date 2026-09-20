from __future__ import annotations
import asyncio, json
from .llm import OllamaProvider, OllamaError
from .memory import Memory
from .tools import ToolRegistry
from .permissions import PermissionManager
from .context import ContextManager
from .sessions import SessionManager
from .tasks import TaskManager
from .skills import SkillManager
from .devices import DeviceManager

SYSTEM = '''You are VOLT, a local personal AI agent. Tool calls perform real actions; never claim success without results. Respect permissions and ask for confirmation. For software work analyze, plan, modify, test, verify, and report honestly.'''

class Agent:
    def __init__(self, settings, session_id="default", auto=False, confirmer=None):
        self.settings = settings
        self.session_id = session_id
        self.memory = Memory(settings.database_path)
        self.sessions = SessionManager(self.memory)
        self.sessions.ensure(session_id)
        self.tasks = TaskManager(self.memory)
        self.devices = DeviceManager(self.memory)
        self.llm = OllamaProvider(settings)
        self.tools = ToolRegistry(settings.workspace())
        self.permissions = PermissionManager(settings, confirmer, auto)
        self.context = ContextManager(settings.max_context_tokens)
        self.skills = SkillManager(settings.skills_path)

    async def run(self, prompt):
        self.memory.add_message(self.session_id, "user", prompt)
        extras = []
        hits = self.memory.search(prompt)
        if hits:
            extras.append({"role": "system", "content": "Relevant memory:\n" + "\n".join(x["content"] for x in hits)})
        skills = self.skills.relevant(prompt)
        if skills:
            extras.append({"role": "system", "content": "Relevant skill instructions:\n" + "\n---\n".join(skills)})
        context = self.context.build(SYSTEM, self.memory.recent(self.session_id), extras)
        try:
            for _ in range(self.settings.max_agent_steps):
                text, calls = "", []
                async for msg, _done in self.llm.stream(context, self.tools.schemas()):
                    text += msg.get("content", "")
                    calls.extend(msg.get("tool_calls", []) or [])
                    if msg.get("content"):
                        yield {"type": "token", "content": msg["content"]}
                if not calls:
                    self.memory.add_message(self.session_id, "assistant", text)
                    yield {"type": "message_end", "content": text}
                    return
                context.append({"role": "assistant", "content": text, "tool_calls": calls})
                for call in calls:
                    fn = call.get("function") or {}
                    name, call_id = fn.get("name"), call.get("id") or call.get("tool_call_id") or "unknown"
                    raw_args = fn.get("arguments", {})
                    try:
                        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                        if not isinstance(args, dict): raise ValueError("arguments must be an object")
                    except (json.JSONDecodeError, ValueError, TypeError) as exc:
                        result = {"error": "invalid tool arguments", "detail": str(exc)}
                        yield {"type": "tool_result", "tool": name, "tool_call_id": call_id, "result": result}
                        context.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps(result)})
                        continue
                    yield {"type": "tool_call", "tool": name, "arguments": args, "tool_call_id": call_id}
                    if name not in self.tools.tools:
                        result = {"error": "unknown tool", "tool": name}
                    else:
                        decision = await self.permissions.check(self.tools.tools[name].risk, f"{name} {args}")
                        if not decision.allowed:
                            yield {"type": "confirmation_required", "action": f"{name} {args}", "risk": self.tools.tools[name].risk.name}
                            result = {"denied": decision.reason}
                        else:
                            try:
                                result = await self.tools.call(name, args)
                            except asyncio.CancelledError: raise
                            except Exception as exc:
                                result = {"error": type(exc).__name__, "detail": str(exc)}
                    self.memory.db.execute("INSERT INTO tool_history(session_id,tool,arguments,result,created_at) VALUES(?,?,?,?,?)", (self.session_id, name or "", json.dumps(args), json.dumps(result, default=str), self.memory.now()))
                    self.memory.db.commit()
                    context.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps(result, default=str)})
                    yield {"type": "tool_result", "tool": name, "tool_call_id": call_id, "result": result}
        except asyncio.CancelledError:
            yield {"type": "error", "error": "generation cancelled"}
        except OllamaError as exc:
            yield {"type": "error", "error": str(exc)}
        yield {"type": "error", "error": "maximum agent steps reached; execution stopped safely"}
