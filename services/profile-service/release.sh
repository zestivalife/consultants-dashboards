#!/bin/sh
set -eu

echo "Running profile-service migrations..."
alembic upgrade head
