from pathlib import Path
import re
class SkillManager:
    def __init__(self, root: Path): self.root=root
    def list(self):
        return [{"name":p.parent.name,"description":self._description(p)} for p in self.root.glob("*/SKILL.md")]
    def _description(self,p):
        for line in p.read_text(errors="ignore").splitlines():
            if line.strip() and not line.startswith("#"): return line.strip()
        return "Local skill"
    def load(self,name):
        p=self.root/name/"SKILL.md"
        if not p.is_file(): raise FileNotFoundError(name)
        return p.read_text()
