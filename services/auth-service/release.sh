#!/bin/sh
set -eu

echo "Running auth-service migrations..."
if [ "${AUTH_SCHEMA_RECONCILE:-0}" = "1" ]; then
  echo "Reconciling auth-service schema before Alembic upgrade..."
  python scripts/reconcile_auth_schema.py
fi
echo "Current auth-service Alembic revision before upgrade:"
alembic current || true
echo "Available auth-service Alembic head(s):"
alembic heads
if ! alembic upgrade head; then
  echo "Auth-service Alembic upgrade failed."
  if [ "${AUTH_SCHEMA_RECONCILE_ON_FAILURE:-1}" != "1" ]; then
    echo "Schema reconciliation fallback is disabled; failing release."
    exit 1
  fi
  echo "Running additive auth schema reconciliation fallback..."
  python scripts/reconcile_auth_schema.py
  echo "Stamping reconciled auth schema to current Alembic head..."
  alembic stamp head
fi
echo "Current auth-service Alembic revision after upgrade:"
alembic current
