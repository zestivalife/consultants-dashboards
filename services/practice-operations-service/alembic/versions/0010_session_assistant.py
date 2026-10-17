"""External-only post-session suggestions and confirmations."""
from alembic import op
revision="0010_session_assistant"
down_revision="0009_template_library"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_session_action_suggestions (id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL, session_note_id UUID NOT NULL REFERENCES external_session_notes(id) ON DELETE RESTRICT, suggestion_type VARCHAR(40) NOT NULL, reason TEXT NOT NULL, source JSONB NOT NULL, proposed_payload JSONB NOT NULL DEFAULT '{}'::jsonb, confidence VARCHAR(20), status VARCHAR(20) NOT NULL DEFAULT 'PROPOSED', practitioner_id VARCHAR(120) NOT NULL, confirmed_by VARCHAR(120), confirmed_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, CONSTRAINT ck_external_session_suggestion_type CHECK (suggestion_type IN ('CREATE_FOLLOWUP','SCHEDULE_NEXT_SESSION','CREATE_TASK','UPDATE_GOAL','ASSIGN_ASSESSMENT','REVIEW_PLAN','CREATE_CLIENT_INSTRUCTION','PREPARE_MESSAGE')), CONSTRAINT ck_external_session_suggestion_status CHECK (status IN ('PROPOSED','ACCEPTED','EDITED_ACCEPTED','DISMISSED')))""")
    op.execute("CREATE INDEX ix_external_session_suggestions_scope ON external_session_action_suggestions(tenant_id,client_id,status,created_at DESC)")
    op.execute("CREATE UNIQUE INDEX uq_external_session_suggestion_type ON external_session_action_suggestions(tenant_id,session_note_id,suggestion_type)")

def downgrade():op.execute('DROP TABLE IF EXISTS external_session_action_suggestions')
