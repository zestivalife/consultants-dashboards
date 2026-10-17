"""External-only structured session notes."""
from alembic import op

revision="0007_structured_notes"
down_revision="0006_profession_plan_engine"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_session_notes (id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, profession_code VARCHAR(80) NOT NULL, consultation_id VARCHAR(120), note_type VARCHAR(60) NOT NULL, title VARCHAR(240) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'DRAFT', current_version INTEGER NOT NULL DEFAULT 1, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_external_session_note_status CHECK (status IN ('DRAFT','SAVED','FINALISED','AMENDED')))""")
    op.execute("CREATE INDEX ix_external_session_notes_scope ON external_session_notes(tenant_id,client_id,status,updated_at DESC)")
    op.execute("""CREATE TABLE external_session_note_versions (id UUID PRIMARY KEY, note_id UUID NOT NULL REFERENCES external_session_notes(id) ON DELETE RESTRICT, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, version INTEGER NOT NULL, status VARCHAR(20) NOT NULL, title VARCHAR(240) NOT NULL, amendment_reason TEXT, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, finalised_at TIMESTAMPTZ, CONSTRAINT uq_external_session_note_version UNIQUE(note_id,version), CONSTRAINT ck_external_session_note_version_status CHECK (status IN ('DRAFT','SAVED','FINALISED','AMENDED')))""")
    op.execute("""CREATE TABLE external_session_note_sections (id UUID PRIMARY KEY, note_version_id UUID NOT NULL REFERENCES external_session_note_versions(id) ON DELETE CASCADE, tenant_id VARCHAR(80) NOT NULL, section_key VARCHAR(100) NOT NULL, title VARCHAR(240) NOT NULL, content JSONB NOT NULL DEFAULT '{}'::jsonb, visibility VARCHAR(24) NOT NULL DEFAULT 'PRACTITIONER', sort_order INTEGER NOT NULL, CONSTRAINT ck_external_session_note_visibility CHECK (visibility IN ('PRACTITIONER','CLIENT_INSTRUCTION')), CONSTRAINT uq_external_session_note_section UNIQUE(note_version_id,section_key))""")
    op.execute("""CREATE TABLE external_session_private_notes (id UUID PRIMARY KEY, note_id UUID NOT NULL REFERENCES external_session_notes(id) ON DELETE RESTRICT, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, encrypted_content TEXT NOT NULL, created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_external_session_private_notes_scope ON external_session_private_notes(tenant_id,client_id,note_id,created_at DESC)")

def downgrade():
    for table in ('external_session_private_notes','external_session_note_sections','external_session_note_versions','external_session_notes'):
        op.execute(f'DROP TABLE IF EXISTS {table}')
