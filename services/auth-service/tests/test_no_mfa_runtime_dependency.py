from pathlib import Path

from app.db.models.user import User


ROOT = Path(__file__).resolve().parents[1]


def test_user_runtime_projection_matches_schema_without_mfa_columns():
    projected_columns = set(User.__table__.columns.keys())
    assert "mfa_enabled" not in projected_columns
    assert "mfa_secret_encrypted" not in projected_columns
    assert "mfa_last_accepted_step" not in projected_columns


def test_auth_runtime_contains_no_mfa_or_totp_dependency():
    runtime_files = [
        ROOT / "app/db/models/user.py",
        ROOT / "app/services/auth_service.py",
        ROOT / "app/services/internal_privileged_iam_service.py",
        ROOT / "app/services/people_access_service.py",
        ROOT / "app/api/v1/routes/auth.py",
        ROOT / "app/api/v1/routes/internal_privileged_iam.py",
        ROOT / "app/schemas/auth.py",
        ROOT / "app/config.py",
    ]
    source = "\n".join(path.read_text() for path in runtime_files).lower()
    for forbidden in ("mfa_", "totp", "two_factor", "authenticator code", "confirm-mfa"):
        assert forbidden not in source
