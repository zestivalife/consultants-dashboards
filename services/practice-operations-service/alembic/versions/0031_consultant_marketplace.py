"""P31 governed consultant marketplace (External-only, expand-only)."""
from alembic import op

revision="0031_consultant_marketplace";down_revision="0030_compliance_audit";branch_labels=None;depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_consultant_public_profiles(
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,consultant_user_id VARCHAR(120) NOT NULL,
      slug VARCHAR(180) NOT NULL UNIQUE,status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',public_visibility BOOLEAN NOT NULL DEFAULT FALSE,
      accepting_new_clients BOOLEAN NOT NULL DEFAULT FALSE,current_published_version INTEGER,working_version INTEGER NOT NULL DEFAULT 1,
      approved_version INTEGER,approval_valid BOOLEAN NOT NULL DEFAULT FALSE,suspended_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_marketplace_profile_owner UNIQUE(tenant_id,consultant_user_id),
      CONSTRAINT ck_marketplace_profile_status CHECK(status IN ('DRAFT','SUBMITTED_FOR_REVIEW','UNDER_REVIEW','CHANGES_REQUIRED','APPROVED','PUBLISHED','UNPUBLISHED','REJECTED','SUSPENDED')))
    """)
    op.execute("""CREATE TABLE external_consultant_public_profile_versions(
      id UUID PRIMARY KEY,profile_id UUID NOT NULL REFERENCES external_consultant_public_profiles(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL,version INTEGER NOT NULL,status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',projection JSONB NOT NULL,
      completeness INTEGER NOT NULL DEFAULT 0,missing_fields JSONB NOT NULL DEFAULT '[]'::jsonb,created_by VARCHAR(120) NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,submitted_at TIMESTAMPTZ,approved_at TIMESTAMPTZ,published_at TIMESTAMPTZ,
      CONSTRAINT uq_marketplace_profile_version UNIQUE(profile_id,version),CONSTRAINT ck_marketplace_version_completeness CHECK(completeness BETWEEN 0 AND 100))
    """)
    op.execute("""CREATE TABLE external_consultant_qualifications(
      id UUID PRIMARY KEY,profile_id UUID NOT NULL REFERENCES external_consultant_public_profiles(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL,qualification_type VARCHAR(80) NOT NULL,title VARCHAR(240) NOT NULL,institution VARCHAR(240) NOT NULL,
      award_year INTEGER NOT NULL,country VARCHAR(100),registration_number VARCHAR(160),issuing_body VARCHAR(240),expiry_date DATE,
      verification_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',credential_document_id UUID REFERENCES external_documents(id) ON DELETE RESTRICT,
      verified_by VARCHAR(120),verified_at TIMESTAMPTZ,rejection_reason VARCHAR(1000),created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_marketplace_qualification_status CHECK(verification_status IN ('PENDING','VERIFIED','REJECTED','EXPIRED')))
    """)
    op.execute("""CREATE TABLE external_consultant_marketplace_enrolments(
      id UUID PRIMARY KEY,profile_id UUID NOT NULL REFERENCES external_consultant_public_profiles(id),tenant_id VARCHAR(80) NOT NULL,
      lead_id UUID REFERENCES external_leads(id),service_id UUID,programme_id UUID,full_name VARCHAR(240) NOT NULL,email VARCHAR(320),phone VARCHAR(60),
      consultation_mode VARCHAR(40),location_id UUID,preferred_at TIMESTAMPTZ,message VARCHAR(1000),consent_acknowledged BOOLEAN NOT NULL,
      status VARCHAR(24) NOT NULL DEFAULT 'NEW',deduplication_key VARCHAR(64) NOT NULL,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_marketplace_enrolment_status CHECK(status IN ('NEW','CONTACTED','ACCEPTED','BOOKED','CONVERTED','DECLINED','CANCELLED')),
      CONSTRAINT uq_marketplace_enrolment_dedupe UNIQUE(profile_id,deduplication_key))
    """)
    op.execute("""CREATE TABLE external_consultant_reviews(
      id UUID PRIMARY KEY,profile_id UUID NOT NULL REFERENCES external_consultant_public_profiles(id),tenant_id VARCHAR(80) NOT NULL,
      client_id VARCHAR(120) NOT NULL,overall_rating SMALLINT NOT NULL,review_text VARCHAR(2000),communication_rating SMALLINT,
      professionalism_rating SMALLINT,support_experience_rating SMALLINT,verified_engagement BOOLEAN NOT NULL DEFAULT FALSE,
      status VARCHAR(24) NOT NULL DEFAULT 'SUBMITTED',consultant_response VARCHAR(1000),reported_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_marketplace_review_client UNIQUE(profile_id,client_id),CONSTRAINT ck_marketplace_review_rating CHECK(overall_rating BETWEEN 1 AND 5),
      CONSTRAINT ck_marketplace_review_status CHECK(status IN ('SUBMITTED','UNDER_MODERATION','PUBLISHED','REJECTED','HIDDEN')))
    """)
    op.execute("""CREATE TABLE external_consultant_review_events(id UUID PRIMARY KEY,review_id UUID NOT NULL REFERENCES external_consultant_reviews(id),tenant_id VARCHAR(80) NOT NULL,event_type VARCHAR(40) NOT NULL,actor_id VARCHAR(120) NOT NULL,reason VARCHAR(1000),created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("""CREATE TABLE external_consultant_marketplace_events(id UUID PRIMARY KEY,profile_id UUID NOT NULL REFERENCES external_consultant_public_profiles(id),tenant_id VARCHAR(80) NOT NULL,event_type VARCHAR(40) NOT NULL,anonymous_session_hash VARCHAR(64),metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL,CONSTRAINT ck_marketplace_event_type CHECK(event_type IN ('PROFILE_IMPRESSION','PROFILE_VIEW','ENROL_CLICK','BOOK_CLICK','ENROLMENT_SUBMITTED','BOOKING_COMPLETED','WAITLIST_JOINED')))""")
    op.execute("""CREATE TABLE external_consultant_marketplace_audit_events(id UUID PRIMARY KEY,profile_id UUID REFERENCES external_consultant_public_profiles(id),tenant_id VARCHAR(80) NOT NULL,event_type VARCHAR(50) NOT NULL,actor_id VARCHAR(120) NOT NULL,actor_role VARCHAR(80),reason VARCHAR(1000),metadata JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL)""")
    op.execute("CREATE INDEX ix_marketplace_public_directory ON external_consultant_public_profiles(status,public_visibility,approval_valid,accepting_new_clients)")
    op.execute("CREATE INDEX ix_marketplace_versions_projection ON external_consultant_public_profile_versions USING GIN(projection)")
    op.execute("CREATE INDEX ix_marketplace_enrolments_inbox ON external_consultant_marketplace_enrolments(tenant_id,status,created_at DESC)")
    op.execute("CREATE INDEX ix_marketplace_reviews_public ON external_consultant_reviews(profile_id,status,verified_engagement,created_at DESC)")
    op.execute("CREATE INDEX ix_marketplace_events_analytics ON external_consultant_marketplace_events(tenant_id,profile_id,event_type,created_at DESC)")

def downgrade():
    raise RuntimeError("Consultant marketplace is expand-only")
