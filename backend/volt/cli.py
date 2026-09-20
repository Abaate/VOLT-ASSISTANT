from __future__ import annotations
import asyncio, json, os
import typer
from rich.console import Console
from rich.markdown import Markdown
from .config import Settings
from .agent import Agent
from .doctor import run_doctor
app=typer.Typer(add_completion=False); console=Console()
async def confirm(action,risk):
    answer=await asyncio.to_thread(input,f"\nVOLT wants to {action}\nRisk: {risk}\nAllow? [y/N] ")
    return answer.strip().lower() in {'y','yes'}
def show_doctor(results):
    for x in results: console.print(f"[{'green' if x['ok'] else 'red'}]{'OK' if x['ok'] else 'ERROR'}[/] {x['name']}: {x['detail']}")
@app.command()
def doctor(): show_doctor(asyncio.run(run_doctor(Settings())))
@app.command()
def server():
    import uvicorn; s=Settings(); uvicorn.run('server.app:app',host=s.server_host,port=s.server_port)
@app.callback(invoke_without_command=True)
def main(ctx:typer.Context,auto:bool=typer.Option(False,'--auto')):
    if ctx.invoked_subcommand is None: asyncio.run(chat(auto))
async def chat(auto=False):
    s=Settings(); agent=Agent(s,auto=auto,confirmer=None if auto else confirm); console.print(f"[bold cyan]VOLT[/] | {s.model_name} | {s.workspace()}")
    while True:
        try: prompt=await asyncio.to_thread(input,'volt > ')
        except (EOFError,KeyboardInterrupt): console.print(); return
        prompt=prompt.strip()
        if prompt in {'/exit','/quit'}: return
        if prompt=='/help': console.print('/clear /status /model /memory /skills /skill /tools /permissions /config /context /session /tasks /reset /version /exit'); continue
        if prompt=='/clear': console.clear(); continue
        if prompt=='/status': console.print({'model':s.model_name,'workspace':str(s.workspace()),'session':agent.session_id}); continue
        if prompt=='/model': console.print(s.model_name); continue
        if prompt=='/memory': console.print(agent.memory.search('volt')); continue
        if prompt=='/skills': console.print(agent.skills.list()); continue
        if prompt=='/tools': console.print(sorted(agent.tools.tools)); continue
        if prompt=='/permissions': console.print('SAFE/LOW automatic by configuration; MEDIUM/HIGH confirmation; CRITICAL never automatic'); continue
        if prompt=='/config': console.print(s.model_dump()); continue
        if prompt=='/context': console.print(f'max tokens: {s.max_context_tokens}'); continue
        if prompt=='/version': console.print('VOLT Assistant 0.3.0'); continue
        if prompt.startswith('/session'):
            console.print(agent.sessions.list()); continue
        if prompt.startswith('/tasks'):
            console.print(agent.tasks.list()); continue
        if prompt=='/reset': agent=Agent(s,auto=auto,confirmer=None if auto else confirm); continue
        if not prompt: continue
        try:
            async for event in agent.run(prompt):
                kind=event.get('type')
                if kind=='token': print(event.get('content',''),end='',flush=True)
                elif kind=='message_end': print()
                elif kind=='tool_call': console.print(f"\n[yellow]tool {event.get('tool')} {event.get('arguments')}[/]")
                elif kind=='tool_result': console.print(f"[dim]{event.get('result')}[/]")
                elif kind=='confirmation_required': console.print(f"[red]confirmation required: {event}[/]")
                elif kind=='error': console.print(f"[red]{event.get('error') or event.get('content')}[/]")
        except KeyboardInterrupt: console.print('\nCancelled.')
if __name__=='__main__': main()
