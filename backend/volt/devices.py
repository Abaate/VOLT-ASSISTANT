from __future__ import annotations
from .memory import Memory
class DeviceManager:
    def __init__(self,memory): self.memory=memory
    def upsert(self,device_id,name="Unknown",device_type="unknown",session_id=None,status="online"):
        self.memory.db.execute("INSERT INTO devices(id,name,type,last_seen,status,session_id) VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,type=excluded.type,last_seen=excluded.last_seen,status=excluded.status,session_id=excluded.session_id",(device_id,name,device_type,self.memory.now(),status,session_id)); self.memory.db.commit(); return self.get(device_id)
    def get(self,device_id):
        row=self.memory.db.execute("SELECT * FROM devices WHERE id=?",(device_id,)).fetchone(); return dict(row) if row else None
    def list(self): return [dict(x) for x in self.memory.db.execute("SELECT * FROM devices ORDER BY last_seen DESC")]
    def offline(self,device_id): self.memory.db.execute("UPDATE devices SET status=?,last_seen=? WHERE id=?",("offline",self.memory.now(),device_id)); self.memory.db.commit()
