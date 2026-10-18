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
    assert 'DOCUMENT_NOT_AVAILABLE' in MAIN and "'DOWNLOADED'" in MAIN
    assert "row[\"status\"]!='AVAILABLE'" in MAIN

def test_p23_upload_is_pending_until_storage_verification():
    assert "'PENDING_UPLOAD'" in MAIN and 'verify_uploaded_object' in MAIN
    assert "status='AVAILABLE'" in MAIN and 'UPLOAD_VERIFIED' in MAIN
    assert "status VARCHAR(24) NOT NULL DEFAULT 'PENDING_UPLOAD'" in MIG

def test_p23_content_policy_and_limits_are_enforced():
    assert 'MAX_DOCUMENT_BYTES = 50 * 1024 * 1024' in STORAGE
    assert 'ALLOWED_CONTENT_TYPES' in STORAGE and 'extension does not match' in STORAGE
    assert 'Empty documents are not allowed' in STORAGE

def test_p23_object_paths_include_version_and_are_not_browser_selected():
    assert 'external-vault/{tenant_id}/{document_id}/{version_id}/' in STORAGE
    assert 'object_key_exposed":False' in MAIN

def test_p23_versions_are_pending_verified_and_immutable():
    assert '/documents/{document_id}/versions' in MAIN
    assert "v.status version_status" in MAIN
    assert "UPDATE external_document_versions SET status='AVAILABLE'" in MAIN
    assert "UNIQUE(document_id,version)" in MIG

def test_p23_literal_collection_routes_precede_legacy_resource_router():
    literal=MAIN.index('@app.get("/api/v1/practice-operations/documents")')
    generic=MAIN.index('@app.get("/api/v1/practice-operations/{resource}")')
    assert literal < generic
    assert 'document_collection_create_route' in MAIN[:generic]
