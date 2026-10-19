"""P37 pre-consultation orchestration over existing governed domains."""
from alembic import op

revision = "0037_preconsultation"
down_revision = "0036_marketplace_booking"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_preconsultation_checklists (
      id UUID PRIMARY KEY,
      tenant_id VARCHAR(80) NOT NULL,
      client_id VARCHAR(120) NOT NULL,
      lead_id UUID REFERENCES external_leads(id),
      appointment_id UUID REFERENCES external_scheduled_appointments(id),
      enrolment_id UUID REFERENCES external_consultant_marketplace_enrolments(id),
      profession_code VARCHAR(80) NOT NULL,
      service_id UUID,
      acquisition_source VARCHAR(80),
      lifecycle_state VARCHAR(50) NOT NULL DEFAULT 'CLIENT_CREATED'
        CHECK(lifecycle_state IN ('CLIENT_CREATED','ONBOARDING_INVITED','ONBOARDING_IN_PROGRESS','ONBOARDING_COMPLETE','READY_FOR_CONSULTATION','PAUSED')),
      requirements JSONB NOT NULL DEFAULT '{}'::jsonb,
      invited_at TIMESTAMPTZ,
      completed_at TIMESTAMPTZ,
      ready_at TIMESTAMPTZ,
      created_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE(tenant_id,client_id)
    )""")
    op.execute("CREATE INDEX ix_preconsultation_appointment ON external_preconsultation_checklists(tenant_id,appointment_id) WHERE appointment_id IS NOT NULL")
    op.execute("""CREATE TABLE external_preconsultation_events (
      id UUID PRIMARY KEY,
      checklist_id UUID NOT NULL REFERENCES external_preconsultation_checklists(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL,
      client_id VARCHAR(120) NOT NULL,
      event_type VARCHAR(80) NOT NULL CHECK(event_type IN ('PROSPECT_CONVERTED_TO_CLIENT','ONBOARDING_INVITED','INTAKE_ASSIGNED','INTAKE_COMPLETED','CONSENT_REQUESTED','CONSENT_COMPLETED','DOCUMENT_REQUESTED','DOCUMENT_UPLOADED','ASSESSMENT_ASSIGNED','ASSESSMENT_COMPLETED','ONBOARDING_STARTED','ONBOARDING_COMPLETED','READY_FOR_CONSULTATION','REQUIREMENTS_RECALCULATED','ONBOARDING_PAUSED')),
      actor_id VARCHAR(120),
      actor_type VARCHAR(40) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    op.execute("CREATE INDEX ix_preconsultation_events ON external_preconsultation_events(tenant_id,checklist_id,created_at)")


def downgrade():
    raise RuntimeError("Pre-consultation onboarding is expand-only")
