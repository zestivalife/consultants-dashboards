import pytest
from app.p49 import resolve_command
def test_safe_commands_are_fixed():assert resolve_command("Open Marketplace")=='OPEN_MARKETPLACE'
def test_natural_language_execution_denied():
 with pytest.raises(ValueError):resolve_command('delete every invoice')
