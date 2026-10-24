#!/bin/sh
set -eu

# Application startup must never mutate the database. Migrations are an
# independently approved operation performed through migrate.sh.
if [ "${RUN_DATABASE_MIGRATIONS:-0}" != "0" ] || \
   [ "${AUTH_SCHEMA_RECONCILE:-0}" != "0" ] || \
   [ "${AUTH_SCHEMA_RECONCILE_ON_FAILURE:-0}" != "0" ]; then
  echo "Refusing startup: database migration/reconciliation flags are not valid for application startup." >&2
  exit 1
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8001}"
