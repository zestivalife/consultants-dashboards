#!/bin/sh
set -eu

echo "Running nutrition-service migrations..."
alembic upgrade head
