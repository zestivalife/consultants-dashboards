#!/bin/sh
set -eu

echo "Running assessment-service migrations..."
alembic upgrade head
