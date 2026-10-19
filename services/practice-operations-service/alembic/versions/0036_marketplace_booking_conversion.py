"""P36 marketplace booking conversion on governed P13/P24 records."""
from alembic import op

revision = "0036_marketplace_booking"
down_revision = "0035_consultant_finder"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("ALTER TABLE external_scheduled_appointments ALTER COLUMN client_id DROP NOT NULL")
    op.execute("ALTER TABLE external_scheduled_appointments ADD COLUMN lead_id UUID REFERENCES external_leads(id), ADD COLUMN marketplace_enrolment_id UUID REFERENCES external_consultant_marketplace_enrolments(id), ADD COLUMN marketplace_source VARCHAR(60), ADD COLUMN management_token_hash VARCHAR(64), ADD COLUMN management_token_expires_at TIMESTAMPTZ, ADD COLUMN cancelled_at TIMESTAMPTZ, ADD COLUMN original_appointment_id UUID REFERENCES external_scheduled_appointments(id)")
    op.execute("CREATE UNIQUE INDEX uq_external_marketplace_slot ON external_scheduled_appointments(tenant_id,starts_at) WHERE status IN ('BOOKED','CONFIRMED')")
    op.execute("CREATE UNIQUE INDEX uq_external_booking_management_token ON external_scheduled_appointments(management_token_hash) WHERE management_token_hash IS NOT NULL")
    op.execute("ALTER TABLE external_scheduling_waitlist ALTER COLUMN client_id DROP NOT NULL")
    op.execute("ALTER TABLE external_scheduling_waitlist ADD COLUMN lead_id UUID REFERENCES external_leads(id), ADD COLUMN profile_id UUID REFERENCES external_consultant_public_profiles(id), ADD COLUMN location_id UUID, ADD COLUMN consultation_mode VARCHAR(40), ADD COLUMN marketplace_source VARCHAR(60), ADD COLUMN time_preference VARCHAR(120)")
    # Execute the JSON literal at the driver level so SQLAlchemy does not
    # interpret JSON colons as named bind parameters during online upgrades.
    op.get_bind().exec_driver_sql("ALTER TABLE external_appointment_types ADD COLUMN public_booking_policy JSONB NOT NULL DEFAULT '{\"request_enrolment_enabled\":true,\"direct_booking_enabled\":false,\"minimum_notice_minutes\":60,\"advance_window_days\":60,\"cancellation_window_hours\":24,\"reschedule_window_hours\":24,\"new_clients_allowed\":true,\"existing_clients_allowed\":true}'::jsonb")
    op.execute("ALTER TABLE external_consultant_marketplace_enrolments ADD COLUMN appointment_id UUID REFERENCES external_scheduled_appointments(id)")
    op.execute("ALTER TABLE external_communication_preparations ALTER COLUMN client_id DROP NOT NULL")
    op.execute("ALTER TABLE external_communication_preparations ADD COLUMN lead_id UUID REFERENCES external_leads(id), ADD CONSTRAINT ck_communication_subject CHECK(client_id IS NOT NULL OR lead_id IS NOT NULL)")
    op.execute("ALTER TABLE external_consultant_marketplace_events DROP CONSTRAINT ck_marketplace_event_type")
    op.execute("ALTER TABLE external_consultant_marketplace_events ADD CONSTRAINT ck_marketplace_event_type CHECK(event_type IN ('PROFILE_IMPRESSION','PROFILE_VIEW','ENROL_CLICK','BOOK_CLICK','ENROLMENT_SUBMITTED','BOOKING_COMPLETED','WAITLIST_JOINED','SERVICE_SELECTED','BOOKING_STARTED','MODE_SELECTED','LOCATION_SELECTED','SLOT_SELECTED','DETAILS_COMPLETED','BOOKING_SUBMITTED','BOOKING_CONFIRMED','BOOKING_FAILED_SLOT_CONFLICT'))")

def downgrade():
    raise RuntimeError("Marketplace booking conversion is expand-only")
