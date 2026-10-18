"""P13 External-only scheduling, self-booking, no-show, and waitlist."""
from alembic import op

revision = "0013_scheduling"
down_revision = "0012_packages_programmes"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE external_appointment_types (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, name VARCHAR(160) NOT NULL,
      description VARCHAR(1000), duration_minutes INTEGER NOT NULL, buffer_before_minutes INTEGER NOT NULL DEFAULT 0,
      buffer_after_minutes INTEGER NOT NULL DEFAULT 0, location_type VARCHAR(20) NOT NULL,
      location_details VARCHAR(500), active BOOLEAN NOT NULL DEFAULT TRUE, created_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_appointment_duration CHECK (duration_minutes BETWEEN 5 AND 480),
      CONSTRAINT ck_external_appointment_location CHECK (location_type IN ('ONLINE','IN_PERSON','PHONE','OTHER'))
    )""")
    op.execute("CREATE INDEX ix_external_appointment_types_tenant ON external_appointment_types(tenant_id,active)")
    op.execute("""CREATE TABLE external_availability_rules (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, weekday INTEGER NOT NULL,
      start_time TIME NOT NULL, end_time TIME NOT NULL, timezone VARCHAR(80) NOT NULL,
      effective_from DATE, effective_until DATE, active BOOLEAN NOT NULL DEFAULT TRUE,
      created_by VARCHAR(120) NOT NULL, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_external_availability_weekday CHECK (weekday BETWEEN 0 AND 6),
      CONSTRAINT ck_external_availability_window CHECK (end_time > start_time)
    )""")
    op.execute("CREATE INDEX ix_external_availability_tenant ON external_availability_rules(tenant_id,weekday,active)")
    op.execute("""CREATE TABLE external_booking_links (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, appointment_type_id UUID NOT NULL,
      client_id VARCHAR(120),
      token_hash VARCHAR(64) NOT NULL UNIQUE, label VARCHAR(160), expires_at TIMESTAMPTZ,
      active BOOLEAN NOT NULL DEFAULT TRUE, created_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL, revoked_at TIMESTAMPTZ,
      CONSTRAINT fk_external_booking_link_type FOREIGN KEY (appointment_type_id) REFERENCES external_appointment_types(id)
    )""")
    op.execute("CREATE INDEX ix_external_booking_links_tenant ON external_booking_links(tenant_id,active)")
    op.execute("""CREATE TABLE external_scheduled_appointments (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      appointment_type_id UUID NOT NULL, booking_link_id UUID, starts_at TIMESTAMPTZ NOT NULL,
      ends_at TIMESTAMPTZ NOT NULL, status VARCHAR(24) NOT NULL, attendance_status VARCHAR(20),
      booked_by_type VARCHAR(20) NOT NULL, cancellation_reason VARCHAR(500), created_by VARCHAR(120),
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT fk_external_scheduled_type FOREIGN KEY (appointment_type_id) REFERENCES external_appointment_types(id),
      CONSTRAINT fk_external_scheduled_link FOREIGN KEY (booking_link_id) REFERENCES external_booking_links(id),
      CONSTRAINT ck_external_scheduled_status CHECK (status IN ('BOOKED','CONFIRMED','COMPLETED','CANCELLED','NO_SHOW')),
      CONSTRAINT ck_external_attendance_status CHECK (attendance_status IS NULL OR attendance_status IN ('ATTENDED','NO_SHOW')),
      CONSTRAINT ck_external_scheduled_window CHECK (ends_at > starts_at)
    )""")
    op.execute("CREATE INDEX ix_external_scheduled_tenant_time ON external_scheduled_appointments(tenant_id,starts_at,status)")
    op.execute("CREATE INDEX ix_external_scheduled_client ON external_scheduled_appointments(tenant_id,client_id,starts_at)")
    op.execute("""CREATE TABLE external_scheduling_waitlist (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, client_id VARCHAR(120) NOT NULL,
      appointment_type_id UUID NOT NULL, preferred_from TIMESTAMPTZ, preferred_until TIMESTAMPTZ,
      status VARCHAR(20) NOT NULL DEFAULT 'WAITING', notes VARCHAR(1000), created_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT fk_external_waitlist_type FOREIGN KEY (appointment_type_id) REFERENCES external_appointment_types(id),
      CONSTRAINT ck_external_waitlist_status CHECK (status IN ('WAITING','OFFERED','BOOKED','CANCELLED','EXPIRED'))
    )""")
    op.execute("CREATE INDEX ix_external_waitlist_tenant ON external_scheduling_waitlist(tenant_id,status,created_at)")
    op.execute("""CREATE TABLE external_scheduling_audit_events (
      id UUID PRIMARY KEY, tenant_id VARCHAR(80) NOT NULL, appointment_id UUID,
      event_type VARCHAR(40) NOT NULL, actor_id VARCHAR(120), actor_type VARCHAR(20) NOT NULL,
      details JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL
    )""")
    op.execute("CREATE INDEX ix_external_scheduling_audit_tenant ON external_scheduling_audit_events(tenant_id,created_at)")


def downgrade():
    op.execute("DROP TABLE external_scheduling_audit_events")
    op.execute("DROP TABLE external_scheduling_waitlist")
    op.execute("DROP TABLE external_scheduled_appointments")
    op.execute("DROP TABLE external_booking_links")
    op.execute("DROP TABLE external_availability_rules")
    op.execute("DROP TABLE external_appointment_types")
