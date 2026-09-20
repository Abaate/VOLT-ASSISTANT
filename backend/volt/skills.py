from pathlib import Path
import json
class SkillManager:
    def __init__(self, root: Path):
        self.root = root; self.root.mkdir(parents=True, exist_ok=True); self.state_file = self.root / ".enabled.json"
        try: self.enabled = set(json.loads(self.state_file.read_text()))
        except (OSError, json.JSONDecodeError): self.enabled = {p.parent.name for p in self.root.glob("*/SKILL.md")}
    def _save(self): self.state_file.write_text(json.dumps(sorted(self.enabled)))
    def _path(self, name):
        if not name or name in {".", ".."} or "/" in name or "\\" in name: raise ValueError("invalid skill name")
        return self.root / name / "SKILL.md"
    def list(self): return [{"name":p.parent.name,"description":self._description(p),"enabled":p.parent.name in self.enabled} for p in sorted(self.root.glob("*/SKILL.md"))]
    def _description(self, p):
        for line in p.read_text(errors="ignore").splitlines():
            if line.strip() and not line.lstrip().startswith("#"): return line.strip()
        return "Local skill"
    def load(self, name):
        p=self._path(name)
        if not p.is_file(): raise FileNotFoundError(name)
        return p.read_text()
    def info(self,name): return {"name":name,"enabled":name in self.enabled,"content":self.load(name)}
    def enable(self,name): self.load(name); self.enabled.add(name); self._save(); return self.info(name)
    def disable(self,name): self.enabled.discard(name); self._save(); return {"name":name,"enabled":False}
    def install(self,name,content):
        p=self._path(name); p.parent.mkdir(parents=True, exist_ok=False); p.write_text(content); self.enabled.add(name); self._save(); return self.info(name)
    def remove(self,name):
        import shutil
        p=self._path(name).parent
        if not p.exists(): raise FileNotFoundError(name)
        shutil.rmtree(p); self.enabled.discard(name); self._save()
    def relevant(self,prompt,limit=2):
        words=set(prompt.lower().split()); out=[]
        for item in self.list():
            if item["enabled"] and (item["name"].lower() in prompt.lower() or any(w in item["description"].lower() for w in words)):
                out.append(self.load(item["name"]))
        return out[:limit]
