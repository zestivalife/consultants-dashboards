from pathlib import Path
import pytest
from app.p41 import validate_message
ROOT=Path(__file__).parents[1];MAIN=(ROOT/'app/main.py').read_text();MIGRATION=(ROOT/'alembic/versions/0041_secure_messaging.py').read_text()
def test_reference_policy_and_private_url_denial():
    assert validate_message('TEXT','Hello')
    assert validate_message('DOCUMENT_REFERENCE',reference_id='doc-1')
    with pytest.raises(ValueError):validate_message('DOCUMENT_REFERENCE',body='https://s3.example/private?X-Amz-Signature=x')
def test_linear_external_only_schema():
    assert '0040_teleconsultation' in MIGRATION
    assert 'external_secure_conversations' in MIGRATION and 'external_secure_messages' in MIGRATION
    assert 'PRIVATE_NOTE' not in MIGRATION and 'ALTER TABLE' not in MIGRATION
def test_truthful_status_and_exact_scope():
    assert "'SENT'" in MAIN and '"delivered":False' in MAIN and '"read":False' in MAIN
    assert "MESSAGE_READ" in MAIN and 'client_id=:client' in MAIN
    assert '_portal_scope(request,token,"READ",db)' in MAIN
