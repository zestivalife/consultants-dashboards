from datetime import datetime,timedelta,timezone
from pathlib import Path
import pytest
from app.p40 import join_allowed,provider_status,validate_external_meeting_url

ROOT=Path(__file__).parents[1];MAIN=(ROOT/'app/main.py').read_text();MIGRATION=(ROOT/'alembic/versions/0040_teleconsultation.py').read_text()

def test_join_window_and_cancelled_appointment_fail_closed():
    now=datetime.now(timezone.utc);start=now+timedelta(minutes=10);end=now+timedelta(minutes=55)
    assert join_allowed(starts_at=start,ends_at=end,now=now,status='CONFIRMED')
    assert not join_allowed(starts_at=start,ends_at=end,now=now,status='CANCELLED')
    assert not join_allowed(starts_at=start+timedelta(days=1),ends_at=end+timedelta(days=1),now=now,status='CONFIRMED')

def test_external_urls_are_https_and_credential_free():
    assert validate_external_meeting_url('https://meet.example/session')
    for value in ('http://meet.example/session','https://user:pass@meet.example/session'):
        with pytest.raises(ValueError):validate_external_meeting_url(value)

def test_provider_absence_is_truthful():assert provider_status('PROVIDER_NOT_CONFIGURED')=='NOT_CONFIGURED'

def test_external_only_linear_migration():
    assert '0039_client_feedback' in MIGRATION
    assert 'external_teleconsult_sessions' in MIGRATION and 'external_teleconsult_events' in MIGRATION
    assert 'ALTER TABLE' not in MIGRATION

def test_portal_scope_state_machine_and_no_fake_presence():
    for value in ('_portal_scope(request,token,"READ",db)','JOIN_WINDOW_CLOSED','WAITING_FOR_CONSULTANT','SESSION_ACTIVE','SESSION_COMPLETED','presenceEvidence":False'):
        assert value in MAIN
    assert 'tenant_id=:tenant AND s.client_id=:client' in MAIN
