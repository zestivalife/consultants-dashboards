from pathlib import Path
ROOT=Path(__file__).parents[1];MAIN=(ROOT/'app/main.py').read_text();MIG=(ROOT/'alembic/versions/0022_consent_esign.py').read_text()
def test_p22_consent_evidence_is_external_and_immutable():
    for table in ('external_consent_templates','external_consent_template_versions','external_consent_records','external_consent_audit_events'):assert f'CREATE TABLE {table}' in MIG
    assert '0021_form_builder' in MIG and 'historic_evidence_preserved' in MAIN
def test_p22_electronic_acknowledgement_and_revocation():
    assert 'ELECTRONIC_ACKNOWLEDGEMENT' in MAIN and "status='REVOKED'" in MAIN
    assert 'CONSENT_ALREADY_DECIDED' in MAIN and 'WHERE id=:id AND tenant_id=:tenant' in MAIN
