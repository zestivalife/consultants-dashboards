from pathlib import Path

from app.p17 import PERMISSIONS, ROLE_PERMISSIONS, can_manage_role, resolve_permissions


ROOT = Path(__file__).parents[1]


def test_canonical_role_registry_is_complete():
    assert set(ROLE_PERMISSIONS) == {"PRACTICE_OWNER", "PRACTICE_ADMIN", "PRACTITIONER", "ASSISTANT", "RECEPTIONIST"}
    assert {"TEAM_VIEW", "CLIENT_ASSIGN", "PRIVATE_NOTE_VIEW", "ANALYTICS_VIEW"} <= PERMISSIONS


def test_receptionist_and_assistant_cannot_read_private_notes():
    assert "PRIVATE_NOTE_VIEW" not in ROLE_PERMISSIONS["RECEPTIONIST"]
    assert "PRIVATE_NOTE_VIEW" not in ROLE_PERMISSIONS["ASSISTANT"]
    assert "PROFESSIONAL_NOTE_VIEW" not in ROLE_PERMISSIONS["RECEPTIONIST"]


def test_owner_and_admin_do_not_receive_private_notes_by_default():
    assert "PRIVATE_NOTE_VIEW" not in ROLE_PERMISSIONS["PRACTICE_OWNER"]
    assert "PRIVATE_NOTE_VIEW" not in ROLE_PERMISSIONS["PRACTICE_ADMIN"]


def test_profession_capability_is_required_as_well_as_role_permission():
    assert "ASSESSMENT_VIEW" not in resolve_permissions("PRACTITIONER", capabilities={"SESSION_NOTES"})
    assert "ASSESSMENT_VIEW" in resolve_permissions("PRACTITIONER", capabilities={"ASSESSMENTS"})


def test_restrictive_overrides_remove_default_permissions():
    resolved = resolve_permissions("PRACTITIONER", restrictions={"PLAN_PUBLISH"}, capabilities={"PRIVATE_NOTES"})
    assert "PLAN_PUBLISH" not in resolved


def test_self_and_admin_owner_escalation_policy_is_closed():
    assert not can_manage_role("PRACTICE_ADMIN", "PRACTITIONER", "PRACTICE_OWNER")
    assert not can_manage_role("PRACTICE_ADMIN", "PRACTICE_ADMIN", "PRACTITIONER")
    assert can_manage_role("PRACTICE_OWNER", "PRACTITIONER", "RECEPTIONIST")


def test_migration_is_external_only_and_expand_only():
    source = (ROOT / "alembic/versions/0017_team_practice_rbac.py").read_text()
    assert 'down_revision = "0016_workflow_automation"' in source
    for table in ("external_practice_role_profiles", "external_team_invitations", "external_client_team_assignments", "external_team_audit_events", "external_team_locations"):
        assert f"CREATE TABLE {table}" in source
    assert "organization_memberships" not in source
    assert "team_memberships" not in source
    assert "password" not in source.lower()
    assert "expand-only" in source


def test_tenant_scoping_assignment_and_audit_are_mandatory():
    source = (ROOT / "app/main.py").read_text()
    assert "CLIENT_ASSIGNMENT_REQUIRED" in source
    assert "SELF_ROLE_ESCALATION_DENIED" in source
    assert "INVITATION_EMAIL_MISMATCH" in source
    assert "AUTH_IDENTITY_UNAVAILABLE" in source
    assert "/api/v1/auth/me" in source
    assert "external_team_audit_events" in source
    assert "WHERE id=:id AND tenant_id=:tenant" in source


def test_private_note_contract_is_owner_scoped_and_assignment_guarded():
    source = (ROOT / "app/main.py").read_text()
    private = source[source.index('@app.get("/api/v1/practice-operations/session-notes/{note_id}/private")'):source.index("async def _progress_guard")]
    assert '"PRIVATE_NOTE_VIEW"' in private
    assert '"PRIVATE_NOTE_CREATE"' in private
    assert "created_by=:actor" in private


def test_frontend_has_permission_gated_team_workspace_and_false_zero_protection():
    workspace = (ROOT.parents[1] / "nuetra-frontend/components/external/ExternalSaaSWorkspace.jsx").read_text()
    team = (ROOT.parents[1] / "nuetra-frontend/components/external/ExternalTeam.jsx").read_text()
    assert "teamAccess?.permissions?.includes('TEAM_VIEW')" in workspace
    assert "Team access unavailable" in team
    assert "Roles & access" in team
    assert "Private notes are not included" in team
