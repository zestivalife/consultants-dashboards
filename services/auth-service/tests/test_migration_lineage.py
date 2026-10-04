from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_production_auth_revision_is_present_in_current_lineage():
    migration = Path(
        "alembic/versions/c1e2f3a4b5c6_govern_fiteatsy_qa_identity_authority.py"
    ).read_text()

    assert 'revision = "c1e2f3a4b5c6"' in migration
    assert 'down_revision = "b0d2f6a8c401"' in migration

    script = ScriptDirectory.from_config(Config("alembic.ini"))
    assert script.get_heads() == ["c3e4f5a6b7c8"]


def test_people_access_seed_uses_postgres_compatible_expanding_bind_parameters():
    migration = Path(
        "alembic/versions/b7d9e3f1a204_seed_people_access_population.py"
    ).read_text()

    assert "email IN :emails" in migration
    assert "name IN :names" in migration
    assert "ANY(:emails)" not in migration
    assert "ANY(:names)" not in migration


def test_platform_owner_restore_populates_required_permissions_column():
    migration = Path(
        "alembic/versions/f7b8c9d0e1f2_restore_platform_owner_bootstrap.py"
    ).read_text()

    assert 'if "permissions" in users_columns:' in migration
    assert 'insert_values.append("\'[]\'::json")' in migration
    assert '("mobile_verified", "remember_me", "mfa_enabled")' in migration
    assert '("current_session_version", "refresh_token_version")' in migration
