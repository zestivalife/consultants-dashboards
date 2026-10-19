"""P39 External-only private client experience feedback."""
from alembic import op
revision="0039_client_feedback";down_revision="0038_post_consultation";branch_labels=None;depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_client_feedback_requests(
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,consultant_id VARCHAR(120) NOT NULL,
      feedback_type VARCHAR(60) NOT NULL CHECK(feedback_type IN ('POST_SESSION_FEEDBACK','PROGRAMME_FEEDBACK','PRACTICE_EXPERIENCE_FEEDBACK','SUPPORT_EXPERIENCE_FEEDBACK','BOOKING_EXPERIENCE_FEEDBACK','ONBOARDING_EXPERIENCE_FEEDBACK','CUSTOM_FEEDBACK')),
      consultation_id VARCHAR(120),service_id UUID,programme_id UUID,template_id UUID,template_version INTEGER,
      status VARCHAR(30) NOT NULL DEFAULT 'REQUESTED' CHECK(status IN ('REQUESTED','OPENED','SUBMITTED','ACKNOWLEDGED','ACTION_REQUIRED','RESOLVED','ARCHIVED')),
      expires_at TIMESTAMPTZ NOT NULL,opened_at TIMESTAMPTZ,submitted_at TIMESTAMPTZ,created_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
      UNIQUE(tenant_id,client_id,feedback_type,consultation_id))""")
    op.execute("CREATE INDEX ix_feedback_requests_scope ON external_client_feedback_requests(tenant_id,consultant_id,status,created_at DESC)")
    op.execute("""CREATE TABLE external_client_feedback_submissions(
      id UUID PRIMARY KEY,request_id UUID NOT NULL UNIQUE REFERENCES external_client_feedback_requests(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,overall_experience SMALLINT NOT NULL CHECK(overall_experience BETWEEN 1 AND 5),
      communication_rating SMALLINT CHECK(communication_rating BETWEEN 1 AND 5),professionalism_rating SMALLINT CHECK(professionalism_rating BETWEEN 1 AND 5),
      booking_experience_rating SMALLINT CHECK(booking_experience_rating BETWEEN 1 AND 5),support_experience_rating SMALLINT CHECK(support_experience_rating BETWEEN 1 AND 5),
      went_well TEXT,could_improve TEXT,experience_label VARCHAR(30) NOT NULL CHECK(experience_label IN ('POSITIVE','NEUTRAL','NEEDS_ATTENTION','INSUFFICIENT_DATA')),
      source VARCHAR(30) NOT NULL DEFAULT 'CLIENT_SELF_REPORTED',submitted_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_feedback_submissions_scope ON external_client_feedback_submissions(tenant_id,client_id,submitted_at DESC)")
    op.execute("""CREATE TABLE external_client_feedback_actions(
      id UUID PRIMARY KEY,request_id UUID NOT NULL REFERENCES external_client_feedback_requests(id) ON DELETE RESTRICT,tenant_id VARCHAR(80) NOT NULL,
      action_type VARCHAR(50) NOT NULL CHECK(action_type IN ('ACKNOWLEDGE','PRIVATE_ACTION_NOTE','FOLLOWUP_CREATED','CLIENT_MESSAGE_PREPARED','RESOLVE','ESCALATE_GRIEVANCE','PUBLIC_REVIEW_INVITATION_PREPARED')),
      private_note TEXT,source_record_id VARCHAR(120),grievance_reference VARCHAR(120),actor_id VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_feedback_actions_scope ON external_client_feedback_actions(tenant_id,request_id,created_at)")
    op.execute("""CREATE TABLE external_client_feedback_audit_events(
      id UUID PRIMARY KEY,request_id UUID NOT NULL REFERENCES external_client_feedback_requests(id) ON DELETE RESTRICT,tenant_id VARCHAR(80) NOT NULL,client_id VARCHAR(120) NOT NULL,
      event_type VARCHAR(60) NOT NULL CHECK(event_type IN ('FEEDBACK_REQUESTED','FEEDBACK_OPENED','FEEDBACK_SUBMITTED','FEEDBACK_ACKNOWLEDGED','FEEDBACK_ACTION_CREATED','FEEDBACK_RESOLVED','FEEDBACK_ESCALATED','PUBLIC_REVIEW_INVITATION_PREPARED')),
      actor_id VARCHAR(120),actor_type VARCHAR(30) NOT NULL,metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_feedback_audit_scope ON external_client_feedback_audit_events(tenant_id,request_id,created_at)")

def downgrade():raise RuntimeError("Client experience feedback is expand-only")
