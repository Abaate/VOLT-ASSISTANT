from .llm import OllamaProvider
from .memory import Memory
from .tools import ToolRegistry
from .permissions import PermissionManager

SYSTEM='''You are VOLT, a local personal AI agent. Tools perform real actions: never claim an action succeeded without its result. Respect permissions and ask before risky operations. For programming: analyze, plan, modify, test, verify, correct, then summarize honestly.'''
class Agent:
    def __init__(self, settings, session_id="default", auto=False, confirmer=None):
        self.settings=settings; self.session_id=session_id; self.memory=Memory(settings.database_path); self.llm=OllamaProvider(settings); self.tools=ToolRegistry(settings.workspace()); self.permissions=PermissionManager(settings,confirmer,auto)
    async def run(self, prompt):
        self.memory.add_message(self.session_id,"user",prompt)
        context=[{"role":"system","content":SYSTEM}]+self.memory.recent(self.session_id)
        memories=self.memory.search(prompt)
        if memories: context.insert(1,{"role":"system","content":"Relevant memory:\n"+"\n".join(x["content"] for x in memories)})
        for _ in range(self.settings.max_agent_steps):
            text=""; calls=[]
            async for msg,done in self.llm.stream(context,self.tools.schemas()):
                text += msg.get("content",""); calls += msg.get("tool_calls",[])
                if msg.get("content"): yield {"type":"token","content":msg["content"]}
            if not calls:
                self.memory.add_message(self.session_id,"assistant",text); yield {"type":"message_end","content":text}; return
            context.append({"role":"assistant","content":text,"tool_calls":calls})
            for call in calls:
                fn=call.get("function",{}); name=fn.get("name"); args=fn.get("arguments",{})
                if name not in self.tools.tools: yield {"type":"error","content":f"Unknown tool: {name}"}; continue
                yield {"type":"tool_call","name":name,"arguments":args}
                decision=await self.permissions.check(self.tools.tools[name].risk,f"{name} {args}")
                if not decision.allowed: result={"denied":decision.reason}
                else:
                    try: result=await self.tools.call(name,args)
                    except Exception as exc: result={"error":str(exc)}
                context.append({"role":"tool","content":str(result)}); yield {"type":"tool_result","name":name,"result":result}
        yield {"type":"error","content":"Maximum agent steps reached."}
