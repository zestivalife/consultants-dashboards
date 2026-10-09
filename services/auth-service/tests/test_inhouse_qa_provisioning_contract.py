from pathlib import Path

from app.services.inhouse_qa_provisioning_service import ROLE_MAP, TENANT_ROLE_MAP


EXPECTED = {
    "user", "consultant", "provider", "dietician", "senior_consultant",
    "practitioner", "mentor", "admin", "super_admin", "platform_owner",
}


def test_complete_role_matrix_and_global_platform_authority():
    assert set(ROLE_MAP) == EXPECTED
    assert ROLE_MAP["user"] == "member"
    assert ROLE_MAP["admin"] == "organization_admin"
    assert ROLE_MAP["super_admin"] == "platform_owner"
    assert TENANT_ROLE_MAP["platform_owner"] is None
    assert TENANT_ROLE_MAP["super_admin"] is None
    assert all(TENANT_ROLE_MAP[role] for role in EXPECTED - {"super_admin", "platform_owner"})


def test_service_is_internal_fail_closed_and_never_returns_password():
    source = Path("app/services/inhouse_qa_provisioning_service.py").read_text()
    script = Path("scripts/provision_inhouse_qa_identity.py").read_text()
    assert "fiteatsy.qa.identity.create" in source
    assert '"purpose": "qa_provisioning"' in source
    assert '"actor_type": "platform_owner"' in source
    assert "await session.rollback()" in source
    assert "return existing" in source
    assert "FITEATSY_QA_PROVISIONING_PASSWORD" in script
    assert "plain_password" not in script
    assert "password=" not in script.split("print(", 1)[-1]


def test_retry_does_not_change_role_or_reset_credential():
    source = Path("app/services/inhouse_qa_provisioning_service.py").read_text()
    existing_path = source[source.index("if existing is not None:"):source.index("auth_role =")]
    assert "canonical_role != command.canonical_role" in existing_path
    assert "return existing" in existing_path
    assert "password_hash" not in existing_path


def test_expand_safe_migration_has_no_real_user_backfill():
    migration = Path("alembic/versions/d5e6f7a8b9c0_governed_inhouse_qa_identity.py").read_text().lower()
    assert "governed_qa_inhouse" in migration
    assert "production_user" in migration
    assert "update users" not in migration
    assert "inhouse_qa_provisioning" in migration
