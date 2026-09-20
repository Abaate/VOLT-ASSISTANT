from __future__ import annotations
import asyncio
from .llm import OllamaProvider
from .memory import Memory
from .tools import ToolRegistry
from .permissions import PermissionManager
from .context import ContextManager
from .sessions import SessionManager
from .tasks import TaskManager
from .skills import SkillManager

SYSTEM='''You are VOLT, a local personal AI agent. Tool calls perform real actions; never claim success without results. Respect risk permissions and ask for confirmation. For software work analyze, plan, modify, test, verify, and report honestly.'''
class Agent:
    def __init__(self, settings, session_id="default", auto=False, confirmer=None):
        self.settings=settings; self.session_id=session_id; self.memory=Memory(settings.database_path); self.sessions=SessionManager(self.memory); self.sessions.ensure(session_id); self.tasks=TaskManager(self.memory); self.llm=OllamaProvider(settings); self.tools=ToolRegistry(settings.workspace()); self.permissions=PermissionManager(settings,confirmer,auto); self.context=ContextManager(settings.max_context_tokens); self.skills=SkillManager(settings.skills_path)
    async def run(self, prompt):
        self.memory.add_message(self.session_id,"user",prompt)
        extras=[]; hits=self.memory.search(prompt)
        if hits: extras.append({"role":"system","content":"Relevant memory:\n"+"\n".join(x["content"] for x in hits)})
        context=self.context.build(SYSTEM,self.memory.recent(self.session_id),extras)
        for _ in range(self.settings.max_agent_steps):
            text=""; calls=[]
            async for msg,_ in self.llm.stream(context,self.tools.schemas()):
                text += msg.get("content",""); calls.extend(msg.get("tool_calls",[]))
                if msg.get("content"): yield {"type":"token","content":msg["content"]}
            if not calls:
                self.memory.add_message(self.session_id,"assistant",text); yield {"type":"message_end","content":text}; return
            context.append({"role":"assistant","content":text,"tool_calls":calls})
            for call in calls:
                fn=call.get("function",{}); name=fn.get("name"); args=fn.get("arguments",{}) or {}; call_id=call.get("id")
                if isinstance(args,str):
                    import json
                    try: args=json.loads(args)
                    except json.JSONDecodeError: args={}
                if name not in self.tools.tools: result={"error":f"Unknown tool: {name}"}
                else:
                    yield {"type":"tool_call","tool":name,"name":name,"arguments":args,"tool_call_id":call_id}
                    decision=await self.permissions.check(self.tools.tools[name].risk,f"{name} {args}")
                    if not decision.allowed:
                        yield {"type":"confirmation_required","action":f"{name} {args}","risk":self.tools.tools[name].risk.name}; result={"denied":decision.reason}
                    else:
                        try: result=await self.tools.call(name,args)
                        except Exception as exc: result={"error":str(exc)}
                context.append({"role":"tool","tool_call_id":call_id,"content":str(result)}); yield {"type":"tool_result","tool":name,"result":result,"tool_call_id":call_id}
        yield {"type":"error","content":"Maximum agent steps reached; execution stopped safely."}
