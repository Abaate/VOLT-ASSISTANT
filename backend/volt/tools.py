from __future__ import annotations
import json, re
from typing import Any
from .permissions import Risk, assess_command

class Tool:
    def __init__(self,name,description,risk,fn,properties=None,required=None): self.name=name; self.description=description; self.risk=risk; self.fn=fn; self.properties=properties or {}; self.required=required or []
    def schema(self): return {"type":"function","function":{"name":self.name,"description":self.description,"parameters":{"type":"object","properties":self.properties,"required":self.required,"additionalProperties":False}}}

class ToolRegistry:
    def __init__(self,workspace):
        self.workspace=workspace.resolve(); self.workspace.mkdir(parents=True,exist_ok=True); self.tools={}; self.processes={}; self.register_defaults()
    def safe_path(self,value):
        from pathlib import Path
        p=Path(str(value)); target=(self.workspace/p).resolve() if not p.is_absolute() else p.resolve()
        if target!=self.workspace and self.workspace not in target.parents: raise ValueError("path is outside workspace")
        return target
    def add(self,t): self.tools[t.name]=t
    def register_defaults(self):
        p={"path":{"type":"string"}}
        self.add(Tool("list_directory","List directory entries",Risk.SAFE,lambda path='.' : [x.name for x in self.safe_path(path).iterdir()],p))
        self.add(Tool("read_file","Read UTF-8 text",Risk.SAFE,lambda path:self.safe_path(path).read_text(),p,["path"]))
        self.add(Tool("write_file","Write UTF-8 text",Risk.MEDIUM,lambda path,content:self._write(path,content),{**p,"content":{"type":"string"}},["path","content"]))
        self.add(Tool("create_file","Create a new file and fail if it exists",Risk.MEDIUM,lambda path,content:self._create(path,content),{**p,"content":{"type":"string"}},["path","content"]))
        self.add(Tool("edit_file","Replace text in a file",Risk.MEDIUM,self.edit,{**p,"old":{"type":"string"},"new":{"type":"string"}},["path","old","new"]))
        self.add(Tool("delete_file","Delete a file",Risk.CRITICAL,lambda path:self.safe_path(path).unlink(),p,["path"]))
        self.add(Tool("copy_file","Copy file",Risk.MEDIUM,self.copy,{**p,"destination":{"type":"string"}},["path","destination"]))
        self.add(Tool("move_file","Move file",Risk.HIGH,self.move,{**p,"destination":{"type":"string"}},["path","destination"]))
        self.add(Tool("create_directory","Create directory",Risk.LOW,lambda path:self.safe_path(path).mkdir(parents=True,exist_ok=True),p,["path"]))
        self.add(Tool("search_text","Search text",Risk.LOW,self.search,{"query":{"type":"string"},**p},["query"]))
        self.add(Tool("find_files","Find files by glob",Risk.SAFE,lambda pattern='*',path='.' : [str(x.relative_to(self.workspace)) for x in self.safe_path(path).rglob(pattern)],{"pattern":{"type":"string"},**p}))
        self.add(Tool("file_info","File metadata",Risk.SAFE,lambda path:self.info(path),p,["path"]))
        self.add(Tool("execute_command","Execute command after policy approval",Risk.HIGH,self.execute,{"command":{"type":"string"}},["command"]))
        for name,args,risk in [("git_status",["status","--short"],Risk.LOW),("git_diff",["diff"],Risk.LOW),("git_log",["log","-10","--oneline"],Risk.LOW),("git_branch",["branch"],Risk.LOW),("git_checkout",["checkout"],Risk.HIGH),("git_add",["add"],Risk.MEDIUM),("git_commit",["commit"],Risk.HIGH),("git_push",["push"],Risk.HIGH),("git_pull",["pull"],Risk.HIGH)]: self.add(Tool(name,"Run git "+name[4:],risk,lambda args=args:self.execute(["git"]+args),{"args":{"type":"array","items":{"type":"string"}}}))
        self.add(Tool("system_info","Basic system information",Risk.SAFE,lambda:{"workspace":str(self.workspace),"free_bytes":__import__('shutil').disk_usage(self.workspace).free}))
        self.add(Tool("run_tests","Run project tests",Risk.HIGH,lambda command="python -m pytest":self.execute(command),{"command":{"type":"string"}}))
        self.add(Tool("run_python","Run Python command",Risk.HIGH,lambda command:self.execute(command),{"command":{"type":"string"}},["command"]))
        self.add(Tool("inspect_project","Inspect common project files",Risk.SAFE,lambda:[str(x.relative_to(self.workspace)) for x in self.workspace.iterdir()]))
        self.add(Tool("detect_project_type","Detect project type",Risk.SAFE,lambda:self.detect()))
        self.add(Tool("package_project","Run package script",Risk.HIGH,lambda:self.execute("./scripts/package.sh"),{"command":{"type":"string"}}))
        self.add(Tool("cpu_info","CPU info",Risk.SAFE,lambda:self._read_proc("/proc/cpuinfo")))
        self.add(Tool("memory_info","Memory info",Risk.SAFE,lambda:self._read_proc("/proc/meminfo")))
        self.add(Tool("disk_info","Disk info",Risk.SAFE,lambda:__import__('shutil').disk_usage(self.workspace)._asdict()))
        self.add(Tool("processes","Process list",Risk.SAFE,lambda:self.execute("ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -30")))
    def _write(self,path,content): p=self.safe_path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content); return {"written":str(p)}
    def _create(self,path,content): p=self.safe_path(path); p.parent.mkdir(parents=True,exist_ok=True); p.touch(exist_ok=False); p.write_text(content); return {"created":str(p)}
    def edit(self,path,old,new): p=self.safe_path(path); text=p.read_text(); count=text.count(old); p.write_text(text.replace(old,new,1)); return {"edited":str(p),"replacements":count}
    def copy(self,path,destination): import shutil; shutil.copy2(self.safe_path(path),self.safe_path(destination)); return {"copied":destination}
    def move(self,path,destination): import shutil; shutil.move(self.safe_path(path),self.safe_path(destination)); return {"moved":destination}
    def search(self,query,path='.'):
        out=[]
        for f in self.safe_path(path).rglob('*'):
            if f.is_file() and not f.is_symlink() and f.stat().st_size<2_000_000:
                try:
                    for n,line in enumerate(f.read_text(errors='ignore').splitlines(),1):
                        if query.lower() in line.lower():out.append({'file':str(f.relative_to(self.workspace)),'line':n,'text':line})
                except OSError:pass
        return out[:200]
    def info(self,path):
        p=self.safe_path(path); s=p.stat(); return {'path':str(p),'size':s.st_size,'is_file':p.is_file(),'is_dir':p.is_dir()}
    def detect(self): return {'python':(self.workspace/'pyproject.toml').exists() or (self.workspace/'requirements.txt').exists(),'node':(self.workspace/'package.json').exists(),'android':(self.workspace/'settings.gradle.kts').exists()}
    def _read_proc(self,path):
        try:return open(path).read()[:5000]
        except OSError:return 'unavailable'
    def execute(self,command,timeout=120):
        import subprocess
        if isinstance(command,list): argv=command
        else: argv=['/bin/sh','-lc',str(command)]
        p=subprocess.run(argv,cwd=self.workspace,text=True,capture_output=True,timeout=timeout); return {'returncode':p.returncode,'stdout':p.stdout[-10000:],'stderr':p.stderr[-10000:]}
    async def call(self,name,args):
        if name not in self.tools: raise KeyError(name)
        result=self.tools[name].fn(**args); return result
    def schemas(self): return [x.schema() for x in self.tools.values()]
