from external_migrations.runner import (
    CANONICAL_BASELINE,
    LEDGER_TABLE,
    MIGRATIONS,
    PRECONDITIONS,
    apply_external_migrations,
)


class Transaction:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class Cursor:
    def __init__(self, canonical=CANONICAL_BASELINE, ledger=()):
        self.canonical = canonical
        self.ledger = list(ledger)
        self.executed = []
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, statement, params=None):
        self.executed.append((statement, params))
        if "SELECT version_num" in statement:
            self._result = [(self.canonical,)]
        elif "SELECT migration_id, checksum_sha256" in statement:
            self._result = self.ledger
        elif statement in PRECONDITIONS.values():
            self._result = [(True,)]
        else:
            self._result = []

    def fetchall(self):
        return self._result

    def fetchone(self):
        return self._result[0]


class Connection:
    def __init__(self, cursor):
        self._cursor = cursor

    def transaction(self):
        return Transaction()

    def cursor(self):
        return self._cursor


def test_external_lineage_contains_only_required_external_changes():
    assert [migration.migration_id for migration in MIGRATIONS] == [
        "external_0050_contact_photo",
        "external_0051_multi_diet_plans",
        "external_0053_client_profile",
        "external_0054_nutrition_foundation",
        "external_0055_client_measurements",
        "external_0056_smart_intake_requests",
    ]
    sql = "\n".join(statement for migration in MIGRATIONS for statement in migration.statements).lower()
    assert "internal_" not in sql
    assert "practice_operations_alembic_version" not in sql
    assert "drop table" not in sql
    assert "delete from" not in sql
    assert "truncate" not in sql


def test_external_migrations_apply_in_one_transaction_and_record_checksums():
    cursor = Cursor()
    applied = apply_external_migrations(Connection(cursor))
    assert applied == [migration.migration_id for migration in MIGRATIONS]
    inserts = [(sql, params) for sql, params in cursor.executed if f"INSERT INTO {LEDGER_TABLE}" in sql]
    assert [params for _, params in inserts] == [
        (migration.migration_id, migration.checksum) for migration in MIGRATIONS
    ]


def test_repeated_execution_is_a_checksum_verified_noop():
    cursor = Cursor(ledger=[(migration.migration_id, migration.checksum) for migration in MIGRATIONS])
    assert apply_external_migrations(Connection(cursor)) == []
    executed = "\n".join(sql for sql, _ in cursor.executed)
    assert "CREATE TABLE IF NOT EXISTS external_nutrition_assessments" not in executed


def test_wrong_canonical_head_fails_closed_before_schema_changes():
    cursor = Cursor(canonical="0051_multi_diet_plans")
    try:
        apply_external_migrations(Connection(cursor))
    except RuntimeError as error:
        assert "canonical migration baseline" in str(error)
    else:
        raise AssertionError("wrong baseline did not fail")
    assert not any(f"INSERT INTO {LEDGER_TABLE}" in sql for sql, _ in cursor.executed)


def test_checksum_drift_fails_closed():
    first = MIGRATIONS[0]
    cursor = Cursor(ledger=[(first.migration_id, "0" * 64)])
    try:
        apply_external_migrations(Connection(cursor))
    except RuntimeError as error:
        assert "checksum mismatch" in str(error)
    else:
        raise AssertionError("checksum drift did not fail")
