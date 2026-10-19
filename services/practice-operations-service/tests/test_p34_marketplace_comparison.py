from pathlib import Path

import pytest

from app.marketplace import MarketplaceComparisonEvent


ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "app/main.py").read_text()
MIGRATION = (ROOT / "alembic/versions/0034_marketplace_shortlist.py").read_text()


def test_p34_migration_is_external_only_additive_and_linear():
    assert 'down_revision="0033_marketplace_home_showcase"' in MIGRATION
    assert "external_marketplace_comparison_events" in MIGRATION
    assert "CREATE TABLE" in MIGRATION
    assert "ALTER TABLE" not in MIGRATION
    assert "saved_consultants" not in MIGRATION


def test_compare_reuses_strict_public_projection_and_returns_partial_truth():
    section = MAIN[MAIN.index('@app.get("/api/v1/public/consultants/compare")'):MAIN.index('@app.post("/api/v1/public/consultants/comparison-events")')]
    assert "_public_profile_sql" in section
    assert "unavailable_count" in section
    assert "verified_qualifications" in section
    assert "AVAILABLE_WINDOWS" in section
    policy = MAIN[MAIN.index("def _public_profile_sql"):MAIN.index("def _public_marketplace_item")]
    for guard in ["p.status='PUBLISHED'", "p.public_visibility=TRUE", "p.approval_valid=TRUE", "p.suspended_at IS NULL"]:
        assert guard in policy


def test_comparison_event_allowlist_rejects_fake_conversion():
    assert MarketplaceComparisonEvent(event_type="CONSULTANT_SAVED").event_type == "CONSULTANT_SAVED"
    assert MarketplaceComparisonEvent(event_type="COMPARISON_OPENED", compared_profile_ids=["a", "b"]).event_type == "COMPARISON_OPENED"
    with pytest.raises(ValueError):
        MarketplaceComparisonEvent(event_type="FAKE_CONVERSION")
    with pytest.raises(ValueError):
        MarketplaceComparisonEvent(event_type="COMPARISON_OPENED", compared_profile_ids=["1", "2", "3", "4", "5"])


def test_comparison_analytics_are_neutral_and_profile_scoped():
    for value in ["times_saved", "comparison_appearances", "comparison_profile_clicks", "comparison_enrol_clicks", "Marketplace engagement"]:
        assert value in MAIN
    assert "clinical_rank" not in MAIN


def test_comparison_event_persists_public_identifiers_only():
    section = MAIN[MAIN.index('@app.post("/api/v1/public/consultants/comparison-events")'):MAIN.index('@app.get("/api/v1/public/consultants")')]
    assert "external_marketplace_comparison_events" in section
    for forbidden in ["email", "phone", "medical", "clinical_note", "credential_document_url"]:
        assert forbidden not in section
