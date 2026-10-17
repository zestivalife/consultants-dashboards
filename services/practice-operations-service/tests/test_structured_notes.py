from pathlib import Path

ROOT=Path(__file__).parents[1]

def test_structured_note_migration_is_external_only_and_additive():
    source=(ROOT/'alembic/versions/0007_structured_notes.py').read_text()
    for table in ('external_session_notes','external_session_note_versions','external_session_note_sections','external_session_private_notes'):
        assert f'CREATE TABLE {table}' in source
    assert 'ALTER TABLE' not in source

def test_finalised_notes_are_versioned_and_immutable():
    source=(ROOT/'app/main.py').read_text()
    for route in ('clients/{client_id}/session-notes','session-notes/{note_id}/finalise','session-notes/{note_id}/amendments'):
        assert route in source
    assert 'FINALISED_NOTE_IMMUTABLE' in source
    assert 'current_version' in source

def test_private_notes_are_capability_gated_and_encrypted():
    source=(ROOT/'app/main.py').read_text()
    assert 'require_capability(request,db,ctx,"PRIVATE_NOTES")' in source
    assert '_private_note_cipher().encrypt' in source
    assert 'encrypted_content' in source
    config=(ROOT/'app/config.py').read_text()
    assert 'PRIVATE_NOTES_ENCRYPTION_KEY must be set in production' in config

