import asyncio, typer
from rich.console import Console
from rich.markdown import Markdown
from .config import Settings
from .agent import Agent
app=typer.Typer(add_completion=False); console=Console()
@app.command()
def doctor():
    s=Settings(); console.print(f"workspace: {s.workspace()}\nmodel: {s.model_name}\nconfig: OK\ndatabase: {s.database_path}")
@app.command()
def server():
    import uvicorn; s=Settings(); uvicorn.run("server.app:app",host=s.server_host,port=s.server_port)
@app.callback(invoke_without_command=True)
def main(ctx:typer.Context,auto:bool=typer.Option(False,"--auto")):
    if ctx.invoked_subcommand: return
    asyncio.run(chat(auto))
async def chat(auto=False):
    s=Settings(); console.print("[bold cyan]VOLT[/bold cyan]\nLocal Personal AI Agent\nModel: "+s.model_name+"\n")
    agent=Agent(s,auto=auto)
    while True:
        try: prompt=input("volt > ").strip()
        except (EOFError,KeyboardInterrupt): print(); return
        if prompt in ("/exit","/quit"): return
        if prompt=="/help": console.print("/help /clear /status /memory /skills /tools /permissions /exit"); continue
        if prompt=="/status": console.print(f"model={s.model_name} workspace={s.workspace()}"); continue
        if not prompt: continue
        async for e in agent.run(prompt):
            if e["type"]=="token": print(e["content"],end="",flush=True)
            elif e["type"]=="message_end": print()
            elif e["type"]=="tool_call": console.print(f"\n[ yellow]tool: {e['name']} {e['arguments']}[/yellow]")
            elif e["type"]=="tool_result": console.print(f"[dim]{e['result']}[/dim]")
            elif e["type"]=="error": console.print(f"[red]{e['content']}[/red]")
if __name__=="__main__": main()
