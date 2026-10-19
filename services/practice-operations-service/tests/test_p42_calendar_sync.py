from datetime import datetime,timezone
from pathlib import Path
import pytest
from app.p42 import external_change_action,project_busy_block,provider_state

ROOT=Path(__file__).parents[1];MAIN=(ROOT/'app/main.py').read_text();MIGRATION=(ROOT/'alembic/versions/0042_calendar_sync.py').read_text()

def test_provider_absence_is_truthful_and_provider_neutral():
    assert provider_state('GOOGLE',False)=='NOT_CONFIGURED'
    assert provider_state('MICROSOFT',True)=='CONNECTED'
    with pytest.raises(ValueError):provider_state('UNKNOWN',False)

def test_busy_projection_never_exposes_external_title():
    row={'id':'b1','starts_at':datetime.now(timezone.utc),'ends_at':datetime.now(timezone.utc),'title':'Private therapy'}
    result=project_busy_block(row)
    assert result['visibility']=='BUSY' and 'title' not in result

def test_external_changes_require_confirmation_and_do_not_mutate_appointment():
    assert external_change_action('CANCEL')=='PRACTITIONER_CONFIRMATION_REQUIRED'
    assert 'appointmentChanged":False' in MAIN
    assert "'EXTERNAL_CHANGE_DETECTED'" in MAIN

def test_linear_external_only_secret_safe_schema():
    assert '0041_secure_messaging' in MIGRATION
    for table in ('external_calendar_connections','external_calendar_busy_blocks','external_calendar_sync_events'):assert table in MIGRATION
    assert 'credential_secret_reference' in MIGRATION and 'refresh_token' not in MIGRATION
    assert 'ALTER TABLE' not in MIGRATION
