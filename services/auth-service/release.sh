#!/bin/sh
set -eu

echo "Running auth-service migrations..."
alembic upgrade head
