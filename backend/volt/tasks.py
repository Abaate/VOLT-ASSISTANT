from __future__ import annotations
import uuid
from .memory import Memory

class TaskManager:
    def __init__(self, memory): self.memory: Memory = memory
    def create(self, description, origin="pc", priority=0, deadline=None, session_id=None, project=None):
        tid=str(uuid.uuid4()); now=self.memory.now(); logs=[]
        self.memory.db.execute("INSERT INTO tasks(id,description,state,progress,origin,logs,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",(tid,description,"queued",0,origin,str(logs),now,now)); self.memory.db.commit(); return self.get(tid)
    def get(self, tid):
        row=self.memory.db.execute("SELECT * FROM tasks WHERE id=?",(tid,)).fetchone(); return dict(row) if row else None
    def list(self): return [dict(x) for x in self.memory.db.execute("SELECT * FROM tasks ORDER BY updated_at DESC")]
    def update(self, tid, state=None, progress=None, log=None):
        task=self.get(tid)
        if not task: return None
        logs=eval(task["logs"]) if task["logs"] else []
        if log: logs.append(str(log))
        self.memory.db.execute("UPDATE tasks SET state=COALESCE(?,state),progress=COALESCE(?,progress),logs=?,updated_at=? WHERE id=?",(state,progress,str(logs),self.memory.now(),tid)); self.memory.db.commit(); return self.get(tid)
    def delete(self, tid): self.memory.db.execute("DELETE FROM tasks WHERE id=?",(tid,)); self.memory.db.commit()
