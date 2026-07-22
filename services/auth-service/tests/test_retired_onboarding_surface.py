from pathlib import Path


def test_auth_router_does_not_expose_public_registration_or_otp_onboarding():
    source = Path("app/api/v1/routes/auth.py").read_text()

    assert '@router.post("/register")' not in source
    assert '@router.post("/verify-otp")' not in source
    assert '@router.post("/resend-otp")' not in source
    assert '@router.post("/forgot-password")' not in source


def test_active_models_do_not_export_invitation_persistence():
    owner_access = Path("app/db/models/owner_access.py").read_text()
    model_exports = Path("app/db/models/__init__.py").read_text()

    assert "class UserInvitation" not in owner_access
    assert "class InvitationEmailOutbox" not in owner_access
    assert "UserInvitation" not in model_exports
    assert "InvitationEmailOutbox" not in model_exports
    assert "OTPVerification" not in model_exports


def test_forward_migration_retires_legacy_onboarding_tables_and_permission():
    migration = Path("alembic/versions/f1a2b3c4d5e6_retire_invitation_onboarding_domain.py").read_text()

    assert "DELETE FROM permissions WHERE key = 'users.invite'" in migration
    assert 'op.drop_table("invitation_email_outbox")' in migration
    assert 'op.drop_table("user_invitations")' in migration
    assert 'op.drop_table("otp_verifications")' in migration
    assert 'op.drop_column("onboarding_instances", "invitation_id")' in migration
