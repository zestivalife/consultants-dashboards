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
alembic upgrade head
echo "Current auth-service Alembic revision after upgrade:"
alembic current
