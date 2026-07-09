#!/bin/sh
set -eu

echo "Running scoring-engine-service migrations..."
alembic upgrade head
