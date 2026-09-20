from __future__ import annotations
import uuid
from .memory import Memory

class SessionManager:
    def __init__(self, memory: Memory): self.memory = memory
    def create(self, title="New session"):
        sid = str(uuid.uuid4()); self.memory.db.execute("INSERT INTO sessions VALUES(?,?,?)", (sid, self.memory.now(), title)); self.memory.db.commit(); return {"id": sid, "title": title}
    def ensure(self, sid):
        if not self.memory.db.execute("SELECT 1 FROM sessions WHERE id=?", (sid,)).fetchone(): self.memory.db.execute("INSERT INTO sessions VALUES(?,?,?)", (sid,self.memory.now(),"Session")); self.memory.db.commit()
        return sid
    def list(self): return [dict(x) for x in self.memory.db.execute("SELECT * FROM sessions ORDER BY created_at DESC")]
    def rename(self, sid, title): self.memory.db.execute("UPDATE sessions SET title=? WHERE id=?",(title,sid)); self.memory.db.commit()
    def delete(self, sid): self.memory.db.execute("DELETE FROM sessions WHERE id=?",(sid,)); self.memory.db.commit()
