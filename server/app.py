from __future__ import annotations
import asyncio, json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from volt.config import Settings
from volt.agent import Agent

settings=Settings(); app=FastAPI(title="VOLT Assistant",version="0.3.0"); bearer=HTTPBearer(auto_error=False)
def auth(c: HTTPAuthorizationCredentials|None=Depends(bearer)):
    if settings.api_token and (not c or c.credentials != settings.api_token): raise HTTPException(401,"invalid token")
    return True
class Chat(BaseModel): prompt:str=Field(min_length=1); session_id:str="default"; device_id:str="pc"; auto:bool=False
class Task(BaseModel): description:str=Field(min_length=1); origin:str="api"; priority:int=0; deadline:str|None=None
class Device(BaseModel): device_id:str=Field(min_length=1); name:str="Unknown"; device_type:str="unknown"; session_id:str|None=None

def agent(body): return Agent(settings,body.session_id,body.auto)
@app.get('/health')
async def health(): return {'ok':True,'service':'volt'}
@app.get('/status')
async def status(_:bool=Depends(auth)): return {'model':settings.model_name,'ollama':await agent(Chat(prompt='status')).llm.health()}
@app.post('/chat')
async def chat(body:Chat,_:bool=Depends(auth)):
    async def stream():
        try:
            async for event in agent(body).run(body.prompt): yield json.dumps(event,ensure_ascii=False)+"\n"
        except asyncio.CancelledError: return
        except Exception as exc: yield json.dumps({'type':'error','error':str(exc)})+"\n"
    return StreamingResponse(stream(),media_type='application/x-ndjson')
@app.post('/command')
async def command(body:Chat,_:bool=Depends(auth)): return await chat(body,_)
@app.get('/memory')
async def memory(q:str='',_:bool=Depends(auth)): return agent(Chat(prompt='memory')).memory.search(q or 'volt')
@app.get('/sessions')
async def sessions(_:bool=Depends(auth)): return agent(Chat(prompt='sessions')).sessions.list()
@app.get('/tasks')
async def tasks(_:bool=Depends(auth)): return agent(Chat(prompt='tasks')).tasks.list()
@app.post('/tasks')
async def create_task(body:Task,_:bool=Depends(auth)): return agent(Chat(prompt='task')).tasks.create(body.description,body.origin,body.priority,body.deadline)
@app.patch('/tasks/{task_id}')
async def update_task(task_id:str, body:dict, _:bool=Depends(auth)):
    result=agent(Chat(prompt='task')).tasks.update(task_id,**{k:v for k,v in body.items() if k in {'state','progress','log','priority','deadline'}})
    if not result: raise HTTPException(404,'task not found')
    return result
@app.delete('/tasks/{task_id}')
async def delete_task(task_id:str,_:bool=Depends(auth)): agent(Chat(prompt='task')).tasks.delete(task_id); return {'deleted':task_id}
@app.get('/devices')
async def devices(_:bool=Depends(auth)): return agent(Chat(prompt='devices')).devices.list()
@app.post('/devices')
async def register_device(body:Device,_:bool=Depends(auth)): return agent(Chat(prompt='device')).devices.upsert(body.device_id,body.name,body.device_type,body.session_id)
@app.websocket('/ws')
async def websocket(ws:WebSocket):
    token=ws.query_params.get('token') or ws.headers.get('authorization','').removeprefix('Bearer ').strip()
    if settings.api_token and token!=settings.api_token: await ws.close(code=1008,reason='authentication required'); return
    await ws.accept(); device_id=ws.query_params.get('device_id','android'); session_id=ws.query_params.get('session_id','default'); a=Agent(settings,session_id); a.devices.upsert(device_id,device_id,'android',session_id)
    await ws.send_json({'type':'connected','model':settings.model_name,'device_id':device_id,'session_id':session_id})
    try:
        while True:
            try: data=await asyncio.wait_for(ws.receive_json(),timeout=90)
            except asyncio.TimeoutError: await ws.send_json({'type':'ping'}); continue
            if not isinstance(data,dict): await ws.send_json({'type':'error','error':'message must be an object'}); continue
            if data.get('type') in {'ping','pong'}: await ws.send_json({'type':'pong'}); continue
            try: body=Chat(**data)
            except Exception as exc: await ws.send_json({'type':'error','error':str(exc)}); continue
            async for event in Agent(settings,body.session_id,body.auto).run(body.prompt): await ws.send_json(event)
    except WebSocketDisconnect: a.devices.offline(device_id)
