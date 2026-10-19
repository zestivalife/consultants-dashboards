import pytest
from app.p48 import category,digest_mode,effective_channels
def test_categories_existing_events():assert category('APPOINTMENT_DUE')=='APPOINTMENT' and category('unknown')=='SYSTEM'
def test_provider_gating():assert effective_channels({'email':True,'sms':True},'TASK_DUE',{'email':False,'sms':True})=={'in_app':True,'email':False,'sms':True,'whatsapp':False}
def test_mandatory_notice_cannot_disable_in_app():assert effective_channels({'in_app':False},'SECURITY',{})['in_app'] is True
def test_digest_allowlist():
 with pytest.raises(ValueError):digest_mode('HOURLY')
