"""added corporate client fields

Revision ID: 53600889d4d8
Revises: 0002
Create Date: 2026-03-28 11:31:03.229601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53600889d4d8'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the stale index (from original autogenerate)
    op.drop_index('ix_auth_audit_logs_user_id', table_name='auth_audit_logs')

    # Add corporate registration fields to users
    op.add_column('users', sa.Column('company_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('employees', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('industry', sa.String(255), nullable=True))

    # Seed the corporate_client role
    op.execute(
        "INSERT INTO roles (id, name, description, created_at, updated_at) "
        "VALUES (gen_random_uuid(), 'corporate_client', 'Corporate client who can manage their team', now(), now()) "
        "ON CONFLICT (name) DO NOTHING"
    )


def downgrade() -> None:
    op.drop_column('users', 'industry')
    op.drop_column('users', 'employees')
    op.drop_column('users', 'location')
    op.drop_column('users', 'company_name')
    op.create_index('ix_auth_audit_logs_user_id', 'auth_audit_logs', ['user_id'], unique=False)
