from pathlib import Path
import pytest
from app.p19 import ALLOWED_SCOPES,referral_transition,validate_scopes

ROOT=Path(__file__).parents[1]

def test_referral_scope_policy_denies_sensitive_domains():
    assert validate_scopes(["BASIC_PROFILE","GOALS"])==["BASIC_PROFILE","GOALS"]
    for scope in ("PRIVATE_NOTES","RAW_SESSION_NOTES","INTERNAL_INTELLIGENCE","BILLING","TEAM_NOTES"):
        with pytest.raises(ValueError):validate_scopes([scope])
    assert "PROGRESS_SUMMARY" in ALLOWED_SCOPES

def test_referral_transitions_require_consent_ready_state():
    assert referral_transition("DRAFT","REQUEST_CONSENT")=="CONSENT_PENDING"
    assert referral_transition("READY_TO_SEND","SEND")=="SENT"
    with pytest.raises(ValueError):referral_transition("DRAFT","SEND")

def test_p19_migration_is_external_only_and_expand_only():
    source=(ROOT/"alembic/versions/0019_referrals.py").read_text()
    assert 'down_revision="0018_practice_analytics"' in source
    for table in ("external_referrals","external_referral_consents","external_referral_shared_scopes","external_referral_events","external_referral_audit_events"):
        assert f"CREATE TABLE {table}" in source
    assert "expand-only" in source
    assert "ALTER TABLE" not in source

def test_p19_routes_are_tenant_consent_and_recipient_scoped():
    source=(ROOT/"app/main.py").read_text();section=source[source.index('# P19 is referral-scoped'):]
    assert '"REFERRAL_MANAGE"' in section and '"REFERRAL_VIEW"' in section
    assert "REFERRAL_CONSENT_REQUIRED" in section
    assert "receiving_tenant_id=:tenant" in section
    assert '"PRIVATE_NOTES"' in section and '"BILLING"' in section
    assert "client ownership" in section

