import pytest
from app.p47 import safe_context
def test_support_context_allowlist():assert safe_context({'module':'Billing','route':'/x'})=={'module':'Billing','route':'/x'}
def test_support_context_rejects_secrets():
 with pytest.raises(ValueError):safe_context({'access_token':'secret'})
def test_support_context_drops_unknown():assert safe_context({'module':'x','clinical_record':'no'})=={'module':'x'}
