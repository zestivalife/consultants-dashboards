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
    assert script.get_heads() == ["c1e2f3a4b5c6"]
