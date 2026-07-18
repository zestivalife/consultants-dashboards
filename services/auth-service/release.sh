#!/bin/sh
set -eu

echo "Running auth-service migrations..."
echo "Current auth-service Alembic revision before upgrade:"
alembic current || true
echo "Available auth-service Alembic head(s):"
alembic heads
alembic upgrade head
echo "Current auth-service Alembic revision after upgrade:"
alembic current
