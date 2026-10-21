"""Idempotently repair an interrupted Internal privileged IAM migration."""
from alembic import op
import sqlalchemy as sa

revision = "a5b6c7d8e9f0"
down_revision = "a4b5c6d7e8f9"

INTERNAL_PERMISSIONS = (
    ("internal.users.read", "View internal workforce identities"),
    ("internal.users.manage", "Manage internal workforce identities"),
    ("internal.invitations.manage", "Manage internal privileged invitations"),
    ("internal.roles.assign", "Assign approved internal roles"),
    ("internal.verification.manage", "Manage internal professional verification"),
    ("internal.operations.manage", "Manage internal operational configuration"),
    ("internal.audit.view", "View internal privileged audit events"),
)

def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_secret_encrypted TEXT")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_last_accepted_step INTEGER")
    op.execute("""
        CREATE TABLE IF NOT EXISTS internal_privileged_invitations (
            id UUID PRIMARY KEY, email VARCHAR(255) NOT NULL, phone VARCHAR(20) NOT NULL,
            first_name VARCHAR(100) NOT NULL, last_name VARCHAR(100) NOT NULL,
            role_name VARCHAR(80) NOT NULL, token_hash VARCHAR(64) UNIQUE,
            activation_hash VARCHAR(64) UNIQUE, status VARCHAR(40) NOT NULL,
            initiated_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            approved_by_user_id UUID REFERENCES users(id) ON DELETE RESTRICT,
            user_id UUID REFERENCES users(id) ON DELETE RESTRICT,
            expires_at TIMESTAMPTZ, approved_at TIMESTAMPTZ, accepted_at TIMESTAMPTZ,
            activated_at TIMESTAMPTZ, revoked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
            CONSTRAINT ck_internal_privileged_role CHECK (role_name = 'internal_super_admin'),
            CONSTRAINT ck_internal_privileged_status CHECK (status IN
              ('PENDING_APPROVAL','APPROVED','ENROLLING_MFA','ACTIVE','REVOKED','EXPIRED'))
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_internal_privileged_invitations_email ON internal_privileged_invitations (email)")
    op.execute("INSERT INTO roles(id,name,description,created_at,updated_at) VALUES (gen_random_uuid(),'internal_super_admin','Internal Consultant Dashboard Super Admin',now(),now()) ON CONFLICT(name) DO NOTHING")
    for key, description in INTERNAL_PERMISSIONS:
        op.execute(sa.text("INSERT INTO permissions(id,key,module,label,description,created_at,updated_at) VALUES (gen_random_uuid(),:key,'internal_iam',:key,:description,now(),now()) ON CONFLICT(key) DO NOTHING").bindparams(key=key, description=description))
        op.execute(sa.text("INSERT INTO role_permissions(id,role_id,permission_id,created_at) SELECT gen_random_uuid(),r.id,p.id,now() FROM roles r CROSS JOIN permissions p WHERE r.name='internal_super_admin' AND p.key=:key ON CONFLICT(role_id,permission_id) DO NOTHING").bindparams(key=key))

def downgrade():
    pass
