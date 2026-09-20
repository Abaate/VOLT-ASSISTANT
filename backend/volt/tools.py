import asyncio, os, shutil, subprocess
from pathlib import Path
from .permissions import Risk

class Tool:
    def __init__(self,name,description,risk,fn): self.name=name; self.description=description; self.risk=risk; self.fn=fn
    def schema(self): return {"type":"function","function":{"name":self.name,"description":self.description,"parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"},"command":{"type":"string"}},"additionalProperties":True}}}

class ToolRegistry:
    def __init__(self, workspace: Path):
        self.workspace=workspace; self.tools={}; self.register_defaults()
    def safe_path(self, p):
        target=(self.workspace/p).resolve() if not Path(p).is_absolute() else Path(p).resolve()
        if self.workspace not in target.parents and target != self.workspace: raise ValueError("path is outside workspace")
        return target
    def add(self,t): self.tools[t.name]=t
    def register_defaults(self):
        self.add(Tool("list_directory","List files in the workspace",Risk.SAFE,lambda path=".": [x.name for x in self.safe_path(path).iterdir()]))
        self.add(Tool("read_file","Read a UTF-8 text file",Risk.SAFE,lambda path: self.safe_path(path).read_text()))
        self.add(Tool("search_text","Search text in workspace files",Risk.LOW,self.search_text))
        self.add(Tool("write_file","Write a UTF-8 file",Risk.MEDIUM,lambda path,content: self._write(path,content)))
        self.add(Tool("execute_command","Execute a shell command in the workspace",Risk.HIGH,self.execute))
        self.add(Tool("delete_file","Delete a file",Risk.CRITICAL,lambda path: self.safe_path(path).unlink()))
        for name in ("git_status","git_diff","git_log"):
            self.add(Tool(name,f"Run {name.replace('_',' ')}",Risk.MEDIUM,lambda name=name: self.execute(["git",name[4:]], timeout=30)))
        self.add(Tool("system_info","Get basic system information",Risk.SAFE,lambda: {"cwd":str(self.workspace),"disk":shutil.disk_usage(self.workspace).free}))
    def _write(self,path,content): p=self.safe_path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content); return {"written":str(p)}
    def search_text(self, query, path="."):
        out=[]
        for f in self.safe_path(path).rglob("*"):
            if f.is_file() and f.stat().st_size < 2_000_000:
                try:
                    for n,line in enumerate(f.read_text(errors="ignore").splitlines(),1):
                        if query.lower() in line.lower(): out.append({"file":str(f.relative_to(self.workspace)),"line":n,"text":line})
                except OSError: pass
        return out[:200]
    def execute(self, command, timeout=120):
        if isinstance(command,str): command=["/bin/sh","-lc",command]
        p=subprocess.run(command,cwd=self.workspace,text=True,capture_output=True,timeout=timeout)
        return {"returncode":p.returncode,"stdout":p.stdout[-10000:],"stderr":p.stderr[-10000:]}
    async def call(self,name,args):
        result=self.tools[name].fn(**args); return await result if asyncio.iscoroutine(result) else result
    def schemas(self): return [t.schema() for t in self.tools.values()]
