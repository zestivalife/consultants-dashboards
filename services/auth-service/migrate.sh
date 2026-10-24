#!/bin/sh
set -eu

if [ "${MIGRATION_OPERATION_APPROVED:-}" != "YES" ]; then
  echo "Migration blocked: MIGRATION_OPERATION_APPROVED=YES is required." >&2
  exit 1
fi

if [ -z "${MIGRATION_APPROVAL_REFERENCE:-}" ]; then
  echo "Migration blocked: MIGRATION_APPROVAL_REFERENCE is required." >&2
  exit 1
fi

if [ -z "${EXPECTED_CURRENT_REVISION:-}" ] || [ -z "${TARGET_REVISION:-}" ]; then
  echo "Migration blocked: EXPECTED_CURRENT_REVISION and TARGET_REVISION are required." >&2
  exit 1
fi

if [ "${TARGET_REVISION}" = "head" ] || [ "${TARGET_REVISION}" = "heads" ]; then
  echo "Migration blocked: TARGET_REVISION must be an explicit reviewed revision." >&2
  exit 1
fi

current_revision="$(alembic current 2>/dev/null | awk 'NR == 1 { print $1 }')"
if [ "${current_revision}" != "${EXPECTED_CURRENT_REVISION}" ]; then
  echo "Migration blocked: current revision does not match the approved precondition." >&2
  exit 1
fi

echo "Running separately approved Auth migration ${MIGRATION_APPROVAL_REFERENCE}."
alembic upgrade "${TARGET_REVISION}"

result_revision="$(alembic current 2>/dev/null | awk 'NR == 1 { print $1 }')"
if [ "${result_revision}" != "${TARGET_REVISION}" ]; then
  echo "Migration verification failed: target revision was not reached." >&2
  exit 1
fi

echo "Auth migration completed at the explicitly approved revision."
