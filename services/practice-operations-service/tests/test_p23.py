from pathlib import Path
ROOT=Path(__file__).parents[1];MAIN=(ROOT/'app/main.py').read_text();MIG=(ROOT/'alembic/versions/0023_document_vault.py').read_text();STORAGE=(ROOT/'app/document_storage.py').read_text()
def test_p23_vault_is_external_metadata_only():
    for table in ('external_documents','external_document_versions','external_document_links','external_document_access_events','external_document_share_grants','external_document_audit_events'):assert f'CREATE TABLE {table}' in MIG
    assert 'BYTEA' not in MIG and '0022_consent_esign' in MIG
def test_p23_uses_short_lived_authorised_object_access():
    assert 'generate_presigned_url' in STORAGE and 'ExpiresIn=600' in STORAGE and 'ExpiresIn=300' in STORAGE
    assert 'DOCUMENT_STORAGE_NOT_CONFIGURED' in MAIN and 'object_key_exposed":False' in MAIN
def test_p23_direct_resources_are_tenant_scoped_and_quarantine_denies_download():
    assert 'd.id=:id AND d.tenant_id=:tenant' in MAIN
    assert 'DOCUMENT_QUARANTINED' in MAIN and "'DOWNLOADED'" in MAIN
