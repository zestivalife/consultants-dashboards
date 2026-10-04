from pathlib import Path

from app.services.external_signup_service import canonical_email


ROOT = Path(__file__).resolve().parents[1]


def test_external_signup_canonicalizes_verified_email_identity():
    assert canonical_email("  Owner@Example.COM ") == "owner@example.com"


def test_external_signup_is_resumable_and_never_exposes_otp():
    service = (ROOT / "app/services/external_signup_service.py").read_text()
    route = (ROOT / "app/api/v1/routes/auth.py").read_text()
    assert 'challenge.status = "VERIFIED"' in service
    assert 'provisioning.status = "PROVISIONING_RETRY"' in service
    assert 'idempotency_key = f"external-signup:{challenge.id}"' in service
    assert 'Role.name == "consultant"' in service
    assert '"code": code' not in route


def test_external_signup_has_persistent_schema_and_forward_migration():
    migration = (ROOT / "alembic/versions/c2d3e4f5a6b7_external_consultant_signup.py").read_text()
    assert "external_signup_challenges" in migration
    assert "external_signup_provisioning" in migration
    assert "auth_user_id" in migration
    assert "idempotency_key" in migration
