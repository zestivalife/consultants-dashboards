#!/bin/bash

echo "🚀 Running migrations for all services..."

services=(
  "nuetra-auth-service-1"
  "nuetra-profile-service-1"
  "nuetra-assessment-service-1"
  "nuetra-scoring-engine-service-1"
  "nuetra-nutrition-service-1"
)

for service in "${services[@]}"
do
  echo "📦 Migrating $service ..."
  docker exec $service bash -c "cd /app && python -m alembic upgrade head" && echo "✅ $service migration successful" || echo "❌ $service migration failed"
done

echo ""
echo "✅ Migration process completed!"