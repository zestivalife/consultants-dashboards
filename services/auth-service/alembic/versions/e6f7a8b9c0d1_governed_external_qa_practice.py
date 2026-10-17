"""Governed External Consultant QA practice provisioning."""
from alembic import op
import sqlalchemy as sa

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None
PERMISSION_KEY = "qa.external_practice.provision"


def upgrade() -> None:
    op.drop_constraint("ck_users_account_classification", "users", type_="check")
    op.create_check_constraint("ck_users_account_classification", "users", "account_classification in ('PRODUCTION_USER','GOVERNED_QA_INHOUSE','GOVERNED_QA_EXTERNAL')")
    op.create_table("external_qa_practice_provisioning",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("fixture_key", sa.String(96), nullable=False, unique=True),
        sa.Column("auth_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("fiteatsy_user_id", sa.String(180), unique=True), sa.Column("tenant_id", sa.String(80), unique=True),
        sa.Column("profession_code", sa.String(80), nullable=False), sa.Column("tenant_name", sa.String(160), nullable=False),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("client_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("client_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("provisioning_source", sa.String(80), nullable=False, server_default="PLATFORM_OWNER_GOVERNED_EXTERNAL_QA"),
        sa.Column("created_by_reference", sa.String(180), nullable=False), sa.Column("last_error_code", sa.String(80)),
        sa.Column("deactivation_reason", sa.Text()), sa.Column("deactivated_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status in ('PENDING','WORKSPACE_READY','READY','FAILED','DEACTIVATED')", name="ck_external_qa_practice_status"),
        sa.CheckConstraint("profession_code in ('DIABETES_EDUCATOR','PSYCHOLOGIST','WELLNESS_CONSULTANT','HEALTH_COACH','BEHAVIOURAL_THERAPIST','OCCUPATIONAL_THERAPIST','PHYSIOTHERAPIST','MENTAL_WELLNESS_THERAPIST')", name="ck_external_qa_practice_profession"))
    conn = op.get_bind()
    conn.execute(sa.text("INSERT INTO permissions(id,key,module,label,description,created_at,updated_at) VALUES(gen_random_uuid(),:key,'qa','Provision External QA Practice','Provision governed synthetic External Consultant QA practices',now(),now()) ON CONFLICT(key) DO NOTHING"), {"key": PERMISSION_KEY})
    conn.execute(sa.text("INSERT INTO role_permissions(id,role_id,permission_id,created_at) SELECT gen_random_uuid(),r.id,p.id,now() FROM roles r CROSS JOIN permissions p WHERE lower(r.name) in ('platform_owner','superuser') and p.key=:key ON CONFLICT(role_id,permission_id) DO NOTHING"), {"key": PERMISSION_KEY})


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM role_permissions USING permissions WHERE role_permissions.permission_id=permissions.id AND permissions.key=:key"), {"key": PERMISSION_KEY})
    conn.execute(sa.text("DELETE FROM permissions WHERE key=:key"), {"key": PERMISSION_KEY})
    op.drop_table("external_qa_practice_provisioning")
    op.drop_constraint("ck_users_account_classification", "users", type_="check")
    op.create_check_constraint("ck_users_account_classification", "users", "account_classification in ('PRODUCTION_USER','GOVERNED_QA_INHOUSE')")
