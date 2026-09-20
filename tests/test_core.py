import pytest
from volt.config import Settings
from volt.permissions import PermissionManager,Risk
from volt.tools import ToolRegistry

def test_safe_path(tmp_path):
    t=ToolRegistry(tmp_path); (tmp_path/'x.txt').write_text('hello VOLT')
    assert t.tools['read_file'].fn('x.txt')=='hello VOLT'
    with pytest.raises(ValueError): t.safe_path('../outside')

def test_critical_denied():
    s=Settings(); p=PermissionManager(s)
    assert __import__('asyncio').run(p.check(Risk.CRITICAL,'delete')) .allowed is False
