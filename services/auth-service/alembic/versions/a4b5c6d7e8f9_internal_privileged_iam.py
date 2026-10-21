"""Internal-only privileged IAM role, invitation and MFA state."""
from alembic import op
import sqlalchemy as sa

revision = "a4b5c6d7e8f9"
down_revision = ("f1a2b3c4d5e6", "e6f7a8b9c0d1")

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
    op.add_column("users", sa.Column("mfa_secret_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("mfa_last_accepted_step", sa.Integer(), nullable=True))
    op.create_table(
        "internal_privileged_invitations",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("email", sa.String(255), nullable=False, index=True),
        sa.Column("phone", sa.String(20), nullable=False), sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False), sa.Column("role_name", sa.String(80), nullable=False),
        sa.Column("token_hash", sa.String(64), unique=True), sa.Column("activation_hash", sa.String(64), unique=True),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("initiated_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("approved_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("expires_at", sa.DateTime(timezone=True)), sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("accepted_at", sa.DateTime(timezone=True)), sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role_name = 'internal_super_admin'", name="ck_internal_privileged_role"),
        sa.CheckConstraint("status in ('PENDING_APPROVAL','APPROVED','ENROLLING_MFA','ACTIVE','REVOKED','EXPIRED')", name="ck_internal_privileged_status"),
    )
    op.execute("INSERT INTO roles(id,name,description,created_at,updated_at) VALUES (gen_random_uuid(),'internal_super_admin','Internal Consultant Dashboard Super Admin',now(),now()) ON CONFLICT(name) DO NOTHING")
    for key, description in INTERNAL_PERMISSIONS:
        op.execute(sa.text("INSERT INTO permissions(id,key,module,label,description,created_at,updated_at) VALUES (gen_random_uuid(),:key,'internal_iam',:key,:description,now(),now()) ON CONFLICT(key) DO NOTHING").bindparams(key=key, description=description))
        op.execute(sa.text("INSERT INTO role_permissions(id,role_id,permission_id,created_at) SELECT gen_random_uuid(),r.id,p.id,now() FROM roles r CROSS JOIN permissions p WHERE r.name='internal_super_admin' AND p.key=:key ON CONFLICT(role_id,permission_id) DO NOTHING").bindparams(key=key))

def downgrade():
    op.drop_table("internal_privileged_invitations")
    op.drop_column("users", "mfa_last_accepted_step")
    op.drop_column("users", "mfa_secret_encrypted")
