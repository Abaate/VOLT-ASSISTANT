from __future__ import annotations
import ast, json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

class Memory:
    def __init__(self,path:Path):
        path.parent.mkdir(parents=True,exist_ok=True); self.db=sqlite3.connect(path,check_same_thread=False); self.db.row_factory=sqlite3.Row; self._init()
    def _init(self):
        self.db.executescript('''CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,created_at TEXT,title TEXT);
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,session_id TEXT,role TEXT,content TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY,kind TEXT,content TEXT UNIQUE,importance INTEGER DEFAULT 1,created_at TEXT);
        CREATE TABLE IF NOT EXISTS facts(id INTEGER PRIMARY KEY,key TEXT UNIQUE,value TEXT);
        CREATE TABLE IF NOT EXISTS preferences(id INTEGER PRIMARY KEY,key TEXT UNIQUE,value TEXT);
        CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY,name TEXT UNIQUE,path TEXT);
        CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,description TEXT,state TEXT,progress INTEGER,origin TEXT,logs TEXT,priority INTEGER DEFAULT 0,deadline TEXT,session_id TEXT,project TEXT,created_at TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS tool_history(id INTEGER PRIMARY KEY,session_id TEXT,tool TEXT,arguments TEXT,result TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS devices(id TEXT PRIMARY KEY,name TEXT,type TEXT,last_seen TEXT,status TEXT,session_id TEXT)'''); self.db.commit()
    @staticmethod
    def now(): return datetime.now(timezone.utc).isoformat()
    def add_message(self,sid,role,content): self.db.execute("INSERT INTO messages(session_id,role,content,created_at) VALUES(?,?,?,?)",(sid,role,content,self.now())); self.db.commit()
    def recent(self,sid,limit=20): return [dict(x) for x in self.db.execute("SELECT role,content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",(sid,limit))[::-1]]
    def remember(self,content,kind="fact",importance=1): self.db.execute("INSERT OR IGNORE INTO memories(kind,content,importance,created_at) VALUES(?,?,?,?)",(kind,content,importance,self.now())); self.db.commit()
    def search(self,query,limit=8):
        terms=[x for x in query.lower().split() if len(x)>2][:8]
        if not terms:return []
        rows=self.db.execute("SELECT kind,content,importance FROM memories ORDER BY importance DESC, id DESC LIMIT 500")
        scored=[]
        for row in rows:
            score=sum(term in row['content'].lower() for term in terms)
            if score: scored.append((score,row))
        return [dict(x) for _,x in sorted(scored,key=lambda item:item[0],reverse=True)[:limit]]
    def close(self): self.db.close()
