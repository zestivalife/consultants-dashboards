from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


TEMPORARY_PASSWORD_VALID_DAYS = 30

STATUS_INVITED = "INVITED"
STATUS_FIRST_LOGIN = "FIRST_LOGIN"
STATUS_ONBOARDING_IN_PROGRESS = "ONBOARDING_IN_PROGRESS"
STATUS_ONBOARDING_COMPLETED = "ONBOARDING_COMPLETED"
STATUS_UNDER_REVIEW = "UNDER_REVIEW"
STATUS_APPROVED = "APPROVED"
STATUS_PASSWORD_CHANGE_REQUIRED = "PASSWORD_CHANGE_REQUIRED"
STATUS_ACTIVE = "ACTIVE"
STATUS_REJECTED = "REJECTED"
STATUS_ON_HOLD = "ON_HOLD"
STATUS_SUSPENDED = "SUSPENDED"
STATUS_LOCKED = "LOCKED"
STATUS_EXPIRED = "EXPIRED"
STATUS_DEACTIVATED = "DEACTIVATED"
STATUS_ARCHIVED = "ARCHIVED"
STATUS_DELETED = "DELETED"
LEGACY_STATUS_PENDING_PROFILE = "PENDING_PROFILE"
LEGACY_STATUS_PENDING_VERIFICATION = "PENDING_VERIFICATION"

CREDENTIAL_TEMPORARY = "TEMPORARY"
CREDENTIAL_PERMANENT = "PERMANENT"

AUTHENTICATABLE_STATUSES = {
    STATUS_INVITED,
    STATUS_FIRST_LOGIN,
    STATUS_ONBOARDING_IN_PROGRESS,
    STATUS_ONBOARDING_COMPLETED,
    STATUS_UNDER_REVIEW,
    STATUS_APPROVED,
    STATUS_PASSWORD_CHANGE_REQUIRED,
    STATUS_ACTIVE,
    LEGACY_STATUS_PENDING_PROFILE,
    LEGACY_STATUS_PENDING_VERIFICATION,
}

DASHBOARD_ELIGIBLE_STATUSES = {STATUS_ACTIVE}

INACTIVE_STATUSES = {
    STATUS_REJECTED,
    STATUS_ON_HOLD,
    STATUS_SUSPENDED,
    STATUS_LOCKED,
    STATUS_EXPIRED,
    STATUS_DEACTIVATED,
    STATUS_ARCHIVED,
    STATUS_DELETED,
}

ONBOARDING_STATUSES = {
    STATUS_INVITED,
    STATUS_FIRST_LOGIN,
    STATUS_ONBOARDING_IN_PROGRESS,
    LEGACY_STATUS_PENDING_PROFILE,
}

REVIEW_STATUSES = {
    STATUS_ONBOARDING_COMPLETED,
    STATUS_UNDER_REVIEW,
}

PASSWORD_REQUIRED_STATUSES = {
    STATUS_APPROVED,
    STATUS_PASSWORD_CHANGE_REQUIRED,
}


@dataclass(frozen=True, slots=True)
class NextAccountAction:
    type: str
    route: str
    reason: str


def normalize_status(status: object | None, fallback: str = STATUS_ACTIVE) -> str:
    value = str(status or fallback).strip().upper()
    return value or fallback


def temporary_password_expiry(now: datetime | None = None) -> datetime:
    current_time = now or datetime.now(timezone.utc)
    return current_time + timedelta(days=TEMPORARY_PASSWORD_VALID_DAYS)


def is_temporary_password_expired(user, now: datetime | None = None) -> bool:
    expires_at = getattr(user, "temporary_password_expires_at", None)
    if expires_at is None:
        return False
    current_time = now or datetime.now(timezone.utc)
    return expires_at <= current_time


def next_action_for_user(user) -> NextAccountAction:
    status = normalize_status(getattr(user, "status", None))

    if getattr(user, "must_change_password", False) or status in PASSWORD_REQUIRED_STATUSES:
        return NextAccountAction(
            type="PASSWORD_CHANGE_REQUIRED",
            route="/auth/change-temporary-password",
            reason="Permanent password must be created before workspace access.",
        )

    if status in ONBOARDING_STATUSES:
        return NextAccountAction(
            type="ONBOARDING_REQUIRED",
            route="/profile",
            reason="Onboarding must be completed before workspace access.",
        )

    if status in REVIEW_STATUSES:
        return NextAccountAction(
            type="ACCOUNT_UNDER_REVIEW",
            route="/profile",
            reason="Account is awaiting administrator review.",
        )

    if status == STATUS_ACTIVE:
        return NextAccountAction(
            type="DASHBOARD",
            route="",
            reason="Account is active.",
        )

    return NextAccountAction(
        type="ACCESS_BLOCKED",
        route="/unauthorized",
        reason=f"Account status {status} is not eligible for workspace access.",
    )
