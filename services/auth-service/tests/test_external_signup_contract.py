from pathlib import Path

from app.core.mobile_identity import canonical_mobile, provider_mobile


ROOT = Path(__file__).resolve().parents[1]


def test_external_signup_canonicalizes_verified_mobile_identity():
    assert canonical_mobile("+91 97620 06688") == "+919762006688"
    assert provider_mobile("+91 97620 06688") == "919762006688"


def test_external_signup_is_resumable_and_never_exposes_otp():
    service = (ROOT / "app/services/external_signup_service.py").read_text()
    route = (ROOT / "app/api/v1/routes/auth.py").read_text()
    assert 'challenge.status = "MOBILE_VERIFIED"' in service
    assert 'provisioning.status = "PROVISIONING_RETRY"' in service
    assert 'provisioning.status in {"MOBILE_VERIFIED", "PROVISIONING_RETRY"}' in service
    assert 'idempotency_key=f"external-signup-mobile:{mobile}"'.replace(" ", "") in service.replace(" ", "")
    assert 'Role.name == "consultant"' in service
    assert '"code": code' not in route


def test_external_signup_has_persistent_schema_and_forward_migration():
    foundation = (ROOT / "alembic/versions/c2d3e4f5a6b7_external_consultant_signup.py").read_text()
    mobile = (ROOT / "alembic/versions/c3e4f5a6b7c8_mobile_otp_external_consultants.py").read_text()
    assert "external_signup_challenges" in foundation
    assert "external_signup_provisioning" in foundation
    assert "auth_user_id" in foundation
    assert "idempotency_key" in foundation
    assert "mobile_normalized" in mobile
    assert "email_normalized" in mobile and "nullable=True" in mobile
    assert "OTP_PENDING" in mobile
    assert "MOBILE_VERIFIED" in mobile
    assert "OTP_EXPIRED" in mobile
