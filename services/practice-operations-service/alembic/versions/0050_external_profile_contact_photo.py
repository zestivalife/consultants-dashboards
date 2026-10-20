"""External consultant contact and durable profile-photo metadata."""
from alembic import op

revision='0050_ext_profile_contact_photo';down_revision='0049_global_search_activity';branch_labels=None;depends_on=None

def upgrade():
    op.execute("""CREATE TABLE external_consultant_contact_profiles(
      id UUID PRIMARY KEY,tenant_id VARCHAR(80) NOT NULL,consultant_user_id VARCHAR(120) NOT NULL,
      country_iso2 VARCHAR(2) NOT NULL,country_code VARCHAR(5) NOT NULL,national_number VARCHAR(20) NOT NULL,
      phone_e164 VARCHAR(16) NOT NULL,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_external_consultant_contact UNIQUE(tenant_id,consultant_user_id),
      CONSTRAINT ck_external_phone_e164 CHECK(phone_e164 ~ '^\\+[1-9][0-9]{7,14}$'))""")
    op.execute("""CREATE TABLE external_consultant_profile_photos(
      id UUID PRIMARY KEY,profile_id UUID NOT NULL REFERENCES external_consultant_public_profiles(id) ON DELETE RESTRICT,
      tenant_id VARCHAR(80) NOT NULL,object_key TEXT NOT NULL,filename VARCHAR(255) NOT NULL,
      content_type VARCHAR(40) NOT NULL,size_bytes BIGINT NOT NULL,status VARCHAR(24) NOT NULL,
      created_by VARCHAR(120) NOT NULL,created_at TIMESTAMPTZ NOT NULL,uploaded_at TIMESTAMPTZ,replaced_at TIMESTAMPTZ,
      CONSTRAINT uq_external_profile_photo_object UNIQUE(tenant_id,object_key),
      CONSTRAINT ck_external_profile_photo_status CHECK(status IN ('PENDING_UPLOAD','AVAILABLE','UPLOAD_FAILED','REPLACED')),
      CONSTRAINT ck_external_profile_photo_size CHECK(size_bytes > 0 AND size_bytes <= 5242880))""")
    op.execute("CREATE UNIQUE INDEX uq_external_profile_current_photo ON external_consultant_profile_photos(profile_id) WHERE status='AVAILABLE' AND replaced_at IS NULL")

def downgrade():
    raise RuntimeError('External consultant profile persistence is expand-only')
