from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from volt.config import Settings
from volt.agent import Agent

settings=Settings(); app=FastAPI(title="VOLT Assistant",version="0.2.0"); bearer=HTTPBearer(auto_error=False)
def auth(c: HTTPAuthorizationCredentials|None=Depends(bearer)):
    if settings.api_token and (not c or c.credentials != settings.api_token): raise HTTPException(401,"invalid token")
    return True
class Chat(BaseModel): prompt:str=Field(min_length=1); session_id:str="default"; device_id:str="pc"; auto:bool=False
class Task(BaseModel): description:str; origin:str="api"
@app.get('/health')
async def health(): return {'ok':True,'service':'volt'}
@app.get('/status')
async def status(_:bool=Depends(auth)): return {'model':settings.model_name,'ollama':await Agent(settings).llm.health()}
@app.post('/chat')
async def chat(body:Chat,_:bool=Depends(auth)):
    async def stream():
        async for event in Agent(settings,body.session_id,body.auto).run(body.prompt): yield json_line(event)
    from json import dumps
    def json_line(x): return dumps(x)+"\n"
    return StreamingResponse(stream(),media_type='application/x-ndjson')
@app.post('/command')
async def command(body:Chat,_:bool=Depends(auth)): return await chat(body,_)
@app.get('/memory')
async def memory(q:str='',_:bool=Depends(auth)): return Agent(settings).memory.search(q or 'volt')
@app.get('/sessions')
async def sessions(_:bool=Depends(auth)): return Agent(settings).sessions.list()
@app.get('/tasks')
async def tasks(_:bool=Depends(auth)): return Agent(settings).tasks.list()
@app.post('/tasks')
async def create_task(body:Task,_:bool=Depends(auth)): return Agent(settings).tasks.create(body.description,body.origin)
@app.websocket('/ws')
async def websocket(ws:WebSocket):
    token=ws.query_params.get('token') or ws.headers.get('authorization','').removeprefix('Bearer ').strip()
    if settings.api_token and token!=settings.api_token: await ws.close(code=1008); return
    await ws.accept(); await ws.send_json({'type':'connected','model':settings.model_name})
    try:
        while True:
            data=await ws.receive_json()
            if data.get('type')=='ping': await ws.send_json({'type':'pong'}); continue
            body=Chat(**data)
            async for event in Agent(settings,body.session_id,body.auto).run(body.prompt): await ws.send_json(event)
    except WebSocketDisconnect: pass
