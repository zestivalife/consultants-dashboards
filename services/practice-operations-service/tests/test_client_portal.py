from pathlib import Path

from app.client_portal import PortalTokenError, issue_portal_token, portal_token_hash, validate_portal_token

ROOT = Path(__file__).parents[1]


def test_p11_migration_is_external_only_and_additive():
    source = (ROOT / "alembic/versions/0011_client_portal.py").read_text()
    for table in (
        "external_client_portal_access_grants",
        "external_client_portal_documents",
        "external_client_portal_audit_events",
    ):
        assert f"CREATE TABLE {table}" in source
    assert "ALTER TABLE" not in source
    assert "client_core" not in source.lower()


def test_portal_token_is_signed_scoped_and_action_limited():
    token = issue_portal_token(
        secret="test-secret", tenant_id="tenant-a", client_id="client-a",
        grant_id="grant-a", expires_at=2_000_000_000,
        allowed_actions=("READ", "COMPLETE_TASK"),
    )
    claims = validate_portal_token(
        token, secret="test-secret", required_action="READ", now=1_900_000_000
    )
    assert claims.tenant_id == "tenant-a"
    assert claims.client_id == "client-a"
    assert len(portal_token_hash(token)) == 64
    try:
        validate_portal_token(token, secret="test-secret", required_action="UPLOAD_DOCUMENT", now=1_900_000_000)
    except PortalTokenError:
        pass
    else:
        raise AssertionError("Unapproved portal action was accepted")


def test_portal_projection_excludes_private_and_draft_content():
    source = (ROOT / "app/main.py").read_text()
    assert "s.visibility='CLIENT_INSTRUCTION'" in source
    assert "v.status='PUBLISHED'" in source
    assert "external_session_private_notes" not in source[source.index('@app.get("/api/v1/client-portal/{token}")'):]
    assert "tenant_id=:tenant AND client_id=:client" in source


def test_portal_task_update_is_cross_client_safe():
    source = (ROOT / "app/main.py").read_text()
    fragment = source[source.index("async def client_portal_complete_task"):]
    assert "id=:id AND tenant_id=:tenant AND client_id=:client" in fragment
    assert "PORTAL_TASK_NOT_FOUND" in fragment
