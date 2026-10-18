from pathlib import Path
ROOT=Path(__file__).parents[1];MAIN=(ROOT/'app/main.py').read_text();CONTRACTS=(ROOT/'app/contracts.py').read_text();MIG=(ROOT/'alembic/versions/0027_client_portal_v2.py').read_text()
def test_portal_v2_reuses_signed_grant_and_dedicated_mutation_actions():
    assert 'allow_form_response' in CONTRACTS and 'allow_consent_decision' in CONTRACTS
    assert 'actions.append("SUBMIT_FORM")' in MAIN and 'actions.append("DECIDE_CONSENT")' in MAIN
    assert '_portal_scope(request,token,"SUBMIT_FORM",db)' in MAIN
    assert '_portal_scope(request,token,"DECIDE_CONSENT",db)' in MAIN
    assert '_portal_scope(request,token,"READ",db)' in MAIN
def test_portal_v2_projects_modules_without_private_notes():
    for key in ('forms','consents','notifications','activity','documentsConfigured'):assert f'"{key}"' in MAIN
    portal=MAIN[MAIN.index('@app.get("/api/v1/client-portal/{token}")'):MAIN.index('@app.post("/api/v1/client-portal/{token}/vault-documents')]
    assert 'external_session_private_notes' not in portal
    assert 'external_documents' in portal and "visibility='CLIENT_VISIBLE'" in portal
def test_portal_v2_schema_remains_tenant_client_scoped():
    assert 'external_client_portal_preferences' in MIG and 'external_client_portal_notification_reads' in MIG
    assert 'UNIQUE(tenant_id,client_id)' in MIG
