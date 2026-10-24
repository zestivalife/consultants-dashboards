from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parents[1]


def test_application_startup_cannot_run_or_reconcile_migrations():
    release = (ROOT / "release.sh").read_text()
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "alembic upgrade" not in release
    assert "alembic stamp" not in release
    assert "reconcile_auth_schema.py" not in release
    assert "RUN_DATABASE_MIGRATIONS" in release
    assert "AUTH_SCHEMA_RECONCILE" in release
    assert 'CMD ["./release.sh"]' in dockerfile


def test_separate_migration_operation_is_explicit_and_fail_closed():
    migration = (ROOT / "migrate.sh").read_text()

    assert 'MIGRATION_OPERATION_APPROVED:-}" != "YES"' in migration
    assert "MIGRATION_APPROVAL_REFERENCE" in migration
    assert "EXPECTED_CURRENT_REVISION" in migration
    assert "TARGET_REVISION" in migration
    assert 'alembic upgrade "${TARGET_REVISION}"' in migration
    assert '"${TARGET_REVISION}" = "head"' in migration
    assert "alembic stamp" not in migration
    assert "reconcile_auth_schema.py" not in migration


def test_repository_migration_helpers_require_explicit_approval():
    for relative_path in ("scripts/run-migrations.sh", "scripts/migrate-db.sh"):
        source = (REPOSITORY_ROOT / relative_path).read_text()
        assert "MIGRATION_OPERATION_APPROVED" in source
        assert "MIGRATION_APPROVAL_REFERENCE" in source
