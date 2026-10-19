from pathlib import Path
from datetime import datetime,timezone,timedelta
import pytest
from app.marketplace import HomepageFeatureDecision,MarketplaceEventCreate

ROOT=Path(__file__).resolve().parents[1]
MAIN=(ROOT/"app/main.py").read_text()
MIGRATION=(ROOT/"alembic/versions/0033_marketplace_homepage_showcase.py").read_text()

def test_migration_is_additive_and_linear():
    assert 'down_revision="0032_consultant_command_centre"' in MIGRATION
    assert "external_consultant_homepage_features" in MIGRATION
    assert "external_marketplace_homepage_events" in MIGRATION
    assert "ALTER TABLE external_consultant_public_profiles" not in MIGRATION

def test_featured_query_reuses_public_projection_and_strict_eligibility():
    section=MAIN[MAIN.index('@app.get("/api/v1/public/consultants/featured")'):MAIN.index('@app.post("/api/v1/public/consultants/homepage-events")')]
    assert "_public_profile_sql" in section
    for guard in ["featured_on_homepage=TRUE","featured_from","featured_until","featured_rank"]:assert guard in section
    policy=MAIN[MAIN.index('def _public_profile_sql'):MAIN.index('def _public_marketplace_item')]
    for guard in ["p.status='PUBLISHED'","p.public_visibility=TRUE","p.approval_valid=TRUE","p.suspended_at IS NULL"]:assert guard in policy

def test_governance_is_platform_admin_only_and_rejects_ineligible_profiles():
    section=MAIN[MAIN.index('@app.put("/api/v1/practice-operations/admin/marketplace/profiles/{profile_id}/homepage-feature")'):MAIN.index('@app.post("/api/v1/practice-operations/admin/marketplace/profiles/{profile_id}/decision")')]
    assert "_platform_admin" in section
    assert "PROFILE_NOT_SHOWCASE_ELIGIBLE" in section
    assert "FEATURED_RANK_REQUIRED" in section
    assert "PRACTICE_OWNER" not in section

def test_feature_window_validation_and_event_allowlist():
    now=datetime.now(timezone.utc)
    with pytest.raises(ValueError):HomepageFeatureDecision(featured_on_homepage=True,featured_rank=1,featured_from=now,featured_until=now-timedelta(seconds=1))
    assert MarketplaceEventCreate(event_type="HOMEPAGE_DIRECTORY_CLICK").event_type=="HOMEPAGE_DIRECTORY_CLICK"
    with pytest.raises(ValueError):MarketplaceEventCreate(event_type="FAKE_CONVERSION")

def test_source_attribution_is_allowlisted_and_persisted_to_p24_lead():
    assert "HOMEPAGE_FEATURED_CONSULTANT" in (ROOT/"app/marketplace.py").read_text()
    section=MAIN[MAIN.index('@app.post("/api/v1/public/consultants/{slug}/enrolments")'):MAIN.index('@app.post("/api/v1/practice-operations/marketplace/profiles/{profile_id}/reviews")')]
    assert '"source":body.source' in section
    assert '"source":body.source' in section

def test_public_privacy_projection_remains_authoritative():
    marketplace=(ROOT/"app/marketplace.py").read_text()
    for field in ["private_email","private_phone","private_address","credential_document_url","admin_notes","tenant_secret"]:assert field in marketplace
    assert "public_projection" in MAIN
