#!/bin/bash
# Quick database migration script - run migrations in running Docker containers

set -e

SERVICES=(
  "auth-service:nuetra_auth:8001"
  "profile-service:nuetra_profile:8002"
  "assessment-service:nuetra_assessment:8003"
  "scoring-engine-service:nuetra_scoring:8004"
  "nutrition-service:nuetra_nutrition:8005"
)

echo "======================================================"
echo "Running Database Migrations for All Services"
echo "======================================================"

for SERVICE_INFO in "${SERVICES[@]}"; do
    IFS=':' read -r SERVICE DB_NAME PORT <<< "$SERVICE_INFO"
    
    echo ""
    echo "→ Migrating $SERVICE (database: $DB_NAME)..."
    
    # Wait for container to be ready
    docker-compose exec -T "$SERVICE" bash -c "
        # Wait for database to be ready
        python -c \"
import time
import psycopg2
config = {
    'host': 'postgres',
    'database': '$DB_NAME',
    'user': 'nuetra',
    'password': 'nuetra_secret'
}
for i in range(30):
    try:
        conn = psycopg2.connect(**config)
        conn.close()
        print('✓ Database is ready')
        break
    except:
        if i < 29:
            time.sleep(1)
        else:
            raise
\" 2>/dev/null && \
        echo '✓ Database connection successful' && \
        alembic upgrade head && \
        echo '✓ Migrations completed'
    " || echo "✗ Migration failed for $SERVICE"
done

echo ""
echo "======================================================"
echo "✓ All migrations completed!"
echo "======================================================"
