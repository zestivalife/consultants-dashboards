"""P38 External-only post-consultation orchestration persistence."""
from alembic import op
revision="0038_post_consultation";down_revision="0037_preconsultation";branch_labels=None;depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_post_session_checklists (
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,
      consultation_id VARCHAR(120) NOT NULL,session_note_id UUID REFERENCES external_session_notes(id) ON DELETE RESTRICT,
      profession_code VARCHAR(80) NOT NULL,service_id UUID,client_package_id UUID REFERENCES external_client_packages(id) ON DELETE RESTRICT,
      lifecycle_state VARCHAR(40) NOT NULL DEFAULT 'POST_SESSION_STARTED' CHECK(lifecycle_state IN ('POST_SESSION_STARTED','IN_PROGRESS','SESSION_OPERATIONALLY_CLOSED','PAUSED')),
      action_requirements JSONB NOT NULL DEFAULT '[]'::jsonb,started_at TIMESTAMPTZ NOT NULL,operationally_closed_at TIMESTAMPTZ,
      created_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,UNIQUE(tenant_id,consultation_id))""")
    op.execute("CREATE INDEX ix_post_session_client ON external_post_session_checklists(tenant_id,client_id,lifecycle_state,updated_at)")
    op.execute("""CREATE TABLE external_post_session_events (
      id UUID PRIMARY KEY,checklist_id UUID NOT NULL REFERENCES external_post_session_checklists(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,consultation_id VARCHAR(120) NOT NULL,
      event_type VARCHAR(80) NOT NULL CHECK(event_type IN ('POST_SESSION_STARTED','POST_SESSION_ACTION_COMPLETED','FOLLOWUP_CREATED','HOMEWORK_ASSIGNED','RESOURCE_ASSIGNED','NEXT_SESSION_BOOKED','PROGRESS_REVIEW_CREATED','RENEWAL_PREPARED','SESSION_OPERATIONALLY_CLOSED','POST_SESSION_PAUSED')),
      action_key VARCHAR(40),actor_id VARCHAR(120),actor_type VARCHAR(40) NOT NULL,metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_post_session_events ON external_post_session_events(tenant_id,checklist_id,created_at)")

def downgrade():raise RuntimeError("Post-consultation retention is expand-only")
