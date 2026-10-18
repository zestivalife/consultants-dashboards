from pathlib import Path
ROOT=Path(__file__).parents[1];MIG=(ROOT/'alembic/versions/0025_communication_centre.py').read_text();MAIN=(ROOT/'app/main.py').read_text()
def test_p25_truthful_channels_and_states():
    for channel in ('WHATSAPP_DEEP_LINK','EMAIL_PREPARATION','SMS_PREPARATION','CLIENT_PORTAL_NOTIFICATION'):assert channel in MIG
    assert "'PREPARED','WHATSAPP_OPENED','CANCELLED'" in MIG
    assert 'sent":False' in MAIN and 'delivered":False' in MAIN and 'read":False' in MAIN
def test_p25_reminders_are_idempotent_and_automation_bounded():
    assert 'UNIQUE(tenant_id,idempotency_key)' in MIG
    assert 'automation_execution":False' in MAIN
    assert 'tenant_id=:tenant' in MAIN
