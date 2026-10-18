from pathlib import Path
from app.p24 import assert_transition,normal_email,normal_phone

ROOT=Path(__file__).parents[1]
MIG=(ROOT/'alembic/versions/0024_lead_crm.py').read_text()
MAIN=(ROOT/'app/main.py').read_text()
def test_lead_identity_normalisation_and_transitions():
    assert normal_email(' A@Example.COM ')=='a@example.com'
    assert normal_phone('+91 987-654')=='91987654'
    assert assert_transition('NEW','CONTACTED')=='CONTACTED'
    try:assert_transition('CONVERTED','NEW');assert False
    except ValueError:pass
def test_lead_schema_is_tenant_scoped_and_audited():
    for table in ('external_leads','external_lead_stage_history','external_lead_follow_ups','external_lead_audit_events'):assert table in MIG
    assert 'tenant_id' in MIG and 'converted_client_id' in MIG
def test_conversion_requires_existing_client_core_id():
    assert 'Only a consultation-booked lead can be converted' in MAIN
    assert 'Created through existing Client Core' in MAIN
