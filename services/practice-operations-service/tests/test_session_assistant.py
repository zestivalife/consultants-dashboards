from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_p9_migration_is_external_only_and_additive():
    source=(ROOT/'alembic/versions/0010_session_assistant.py').read_text();assert 'CREATE TABLE external_session_action_suggestions' in source;assert 'ALTER TABLE' not in source

def test_p9_briefing_is_factual_source_linked_and_tenant_scoped():
    source=(ROOT/'app/main.py').read_text()
    for value in ('client_summary','since_last_session','items_to_review','outstanding_actions','recent_progress','source_refs','session-briefing'):assert value in source
    assert 'tenant_id=:tenant' in source

def test_p9_requires_finalised_session_and_explicit_confirmation():
    source=(ROOT/'app/main.py').read_text()
    for value in ('COMPLETED_SESSION_REQUIRED','PROPOSED','ACCEPTED','EDITED_ACCEPTED','DISMISSED','action_executed'):assert value in source
    for prohibited in ('autonomous diagnosis','AUTO_EXECUTE'):assert prohibited not in source
