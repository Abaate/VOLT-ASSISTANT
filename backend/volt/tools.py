from __future__ import annotations
import asyncio, json, os, shutil, subprocess
from pathlib import Path
from .permissions import Risk
class Tool:
    def __init__(self,name,description,risk,fn,properties=None): self.name=name; self.description=description; self.risk=risk; self.fn=fn; self.properties=properties or {}
    def schema(self): return {"type":"function","function":{"name":self.name,"description":self.description,"parameters":{"type":"object","properties":self.properties,"required":[k for k in self.properties if k in {"path","query","content","command"}],"additionalProperties":False}}}
class ToolRegistry:
    def __init__(self,workspace): self.workspace=workspace.resolve(); self.tools={}; self.register_defaults()
    def safe_path(self,p):
        target=(self.workspace/str(p)).resolve() if not Path(p).is_absolute() else Path(p).resolve()
        if self.workspace not in target.parents and target != self.workspace: raise ValueError("path is outside workspace")
        return target
    def add(self,t): self.tools[t.name]=t
    def register_defaults(self):
        path={"path":{"type":"string"}}
        self.add(Tool("list_directory","List workspace directory",Risk.SAFE,lambda path=".":[x.name for x in self.safe_path(path).iterdir()],path))
        self.add(Tool("read_file","Read a UTF-8 text file",Risk.SAFE,lambda path:self.safe_path(path).read_text(),path))
        self.add(Tool("search_text","Search text in files",Risk.LOW,self.search_text,{"query":{"type":"string"},**path}))
        self.add(Tool("write_file","Write a text file",Risk.MEDIUM,lambda path,content:self._write(path,content),{**path,"content":{"type":"string"}}))
        self.add(Tool("delete_file","Delete a file",Risk.CRITICAL,lambda path:self.safe_path(path).unlink(),path))
        self.add(Tool("execute_command","Execute a shell command in workspace",Risk.HIGH,self.execute,{"command":{"type":"string"}}))
        for key,cmd in (("git_status",["status","--short"]),("git_diff",["diff"]),("git_log",["log","-10","--oneline"]),("git_branch",["branch"]),("git_add",["add"]),("git_commit",["commit"])): self.add(Tool(key,f"Run git {key[4:]}",Risk.HIGH if key in {"git_add","git_commit"} else Risk.MEDIUM,lambda cmd=cmd:self.execute(["git"]+cmd),{"command":{"type":"string"}}))
        self.add(Tool("system_info","Get system information",Risk.SAFE,lambda:{"workspace":str(self.workspace),"free_bytes":shutil.disk_usage(self.workspace).free}))
    def _write(self,path,content): p=self.safe_path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content); return {"written":str(p)}
    def search_text(self,query,path="."):
        out=[]
        for f in self.safe_path(path).rglob("*"):
            if f.is_file() and not f.is_symlink() and f.stat().st_size<2_000_000:
                try:
                    for n,line in enumerate(f.read_text(errors="ignore").splitlines(),1):
                        if query.lower() in line.lower(): out.append({"file":str(f.relative_to(self.workspace)),"line":n,"text":line})
                except OSError: pass
        return out[:200]
    def execute(self,command,timeout=120):
        if isinstance(command,str): command=["/bin/sh","-lc",command]
        p=subprocess.run(command,cwd=self.workspace,text=True,capture_output=True,timeout=timeout); return {"returncode":p.returncode,"stdout":p.stdout[-10000:],"stderr":p.stderr[-10000:]}
    async def call(self,name,args):
        result=self.tools[name].fn(**args); return await result if asyncio.iscoroutine(result) else result
    def schemas(self): return [t.schema() for t in self.tools.values()]
