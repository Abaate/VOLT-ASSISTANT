from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from .config import Settings
from .agent import Agent

settings=Settings(); app=FastAPI(title="VOLT Assistant",version="0.1.0"); bearer=HTTPBearer(auto_error=False)
def auth(c: HTTPAuthorizationCredentials|None=Depends(bearer)):
    if settings.api_token and (not c or c.credentials != settings.api_token): raise HTTPException(401,"invalid token")
class Chat(BaseModel): prompt:str; session_id:str="default"; auto:bool=False
@app.get("/health")
async def health(): return {"ok":True}
@app.get("/status")
async def status(): return {"model":settings.model_name,"ollama":await Agent(settings).llm.health()}
@app.post("/chat")
async def chat(body:Chat,_=Depends(auth)):
    async def events():
        async for e in Agent(settings,body.session_id,body.auto).run(body.prompt): yield e
    return {"events":[e async for e in events()]}
@app.get("/memory")
async def memory(q:str="",_=Depends(auth)): return Agent(settings).memory.search(q or "a")
@app.websocket("/ws")
async def websocket(ws:WebSocket):
    await ws.accept()
    try:
        while True:
            data=await ws.receive_json(); body=Chat(**data)
            async for event in Agent(settings,body.session_id,body.auto).run(body.prompt): await ws.send_json(event)
    except WebSocketDisconnect: pass
