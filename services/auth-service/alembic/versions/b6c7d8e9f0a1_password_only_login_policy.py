"""Remove mandatory TOTP from the governed login and activation policy.

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
"""

from alembic import op


revision = "b6c7d8e9f0a1"
down_revision = "a5b6c7d8e9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Accounts that had already proved invitation ownership but were waiting on
    # TOTP must enter the existing mandatory password-replacement boundary.
    # No other inactive, pending-approval, revoked, or expired identity changes.
    op.execute(
        """
        UPDATE users AS u
        SET is_active = TRUE,
            status = 'PASSWORD_CHANGE_REQUIRED',
            must_change_password = TRUE,
            credential_status = 'TEMPORARY',
            temporary_password_created_at = COALESCE(u.temporary_password_created_at, now()),
            temporary_password_expires_at = COALESCE(u.temporary_password_expires_at, now() + interval '30 days'),
            temporary_password_consumed_at = NULL,
            mfa_enabled = FALSE,
            mfa_secret_encrypted = NULL,
            mfa_last_accepted_step = NULL,
            updated_at = now()
        FROM internal_privileged_invitations AS invitation
        WHERE invitation.user_id = u.id
          AND invitation.status = 'ENROLLING_MFA'
          AND u.status = 'PENDING_MFA'
          AND lower(invitation.role_name) = 'internal_super_admin'
        """
    )
    op.execute(
        """
        UPDATE internal_privileged_invitations
        SET status = 'ACTIVE',
            activated_at = COALESCE(activated_at, now()),
            activation_hash = NULL,
            token_hash = NULL
        WHERE status = 'ENROLLING_MFA'
          AND lower(role_name) = 'internal_super_admin'
        """
    )


def downgrade() -> None:
    # The migration intentionally does not recreate TOTP secrets or reverse
    # completed credential changes. Re-enabling MFA requires a separately
    # governed enrolment workflow rather than unsafe synthetic credentials.
    pass
