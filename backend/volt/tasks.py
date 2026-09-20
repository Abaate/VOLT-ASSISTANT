from __future__ import annotations
import json, uuid
from .memory import Memory
class TaskManager:
    STATES={"queued","running","waiting_confirmation","completed","failed","cancelled"}
    def __init__(self,memory): self.memory=memory
    def create(self,description,origin="pc",priority=0,deadline=None,session_id=None,project=None):
        if not description.strip(): raise ValueError("description cannot be empty")
        tid=str(uuid.uuid4()); now=self.memory.now(); self.memory.db.execute("INSERT INTO tasks(id,description,state,progress,origin,logs,priority,deadline,session_id,project,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(tid,description,"queued",0,origin,"[]",int(priority),deadline,session_id,project,now,now)); self.memory.db.commit(); return self.get(tid)
    def get(self,tid):
        row=self.memory.db.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone(); return dict(row) if row else None
    def list(self,state=None):
        q="SELECT * FROM tasks"; args=[]
        if state:q+=" WHERE state=?"; args.append(state)
        return [dict(x) for x in self.memory.db.execute(q+" ORDER BY priority DESC,updated_at DESC",args)]
    def update(self,tid,state=None,progress=None,log=None,priority=None,deadline=None):
        if state is not None and state not in self.STATES: raise ValueError("invalid task state")
        task=self.get(tid)
        if not task:return None
        logs=json.loads(task.get("logs") or "[]")
        if not isinstance(logs,list): logs=[]
        if log:logs.append(str(log))
        self.memory.db.execute("UPDATE tasks SET state=COALESCE(?,state),progress=COALESCE(?,progress),logs=?,priority=COALESCE(?,priority),deadline=COALESCE(?,deadline),updated_at=? WHERE id=?",(state,progress,json.dumps(logs),priority,deadline,self.memory.now(),tid)); self.memory.db.commit(); return self.get(tid)
    def delete(self,tid): self.memory.db.execute("DELETE FROM tasks WHERE id=?",(tid,)); self.memory.db.commit()
    def complete(self,tid): return self.update(tid,"completed",100)
    def cancel(self,tid): return self.update(tid,"cancelled")
