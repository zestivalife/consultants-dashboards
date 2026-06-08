#!/bin/bash
# Database Migration Initialization Script
# This script runs Alembic migrations for all microservices to initialize the database schema

set -e

echo "======================================================"
echo "Nuetra Database Migration Initialization"
echo "======================================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SERVICES=(
  "auth-service"
  "profile-service"
  "assessment-service"
  "scoring-engine-service"
  "nutrition-service"
)

DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-nuetra}"
DB_PASSWORD="${DB_PASSWORD:-nuetra_secret}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Check if docker-compose services are running
if ! docker ps | grep -q postgres; then
    echo -e "${YELLOW}⚠️  PostgreSQL container not found. Starting services...${NC}"
    docker-compose up -d postgres redis
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 5
fi

echo -e "${YELLOW}Starting database migrations...${NC}\n"

# Run migrations for each service
for SERVICE in "${SERVICES[@]}"; do
    SERVICE_DIR="services/$SERVICE"
    
    if [ ! -d "$SERVICE_DIR" ]; then
        echo -e "${YELLOW}⊘ Skipping $SERVICE (directory not found)${NC}"
        continue
    fi
    
    echo -e "${YELLOW}→ Running migrations for $SERVICE...${NC}"
    
    # Run alembic upgrade head inside the service container
    docker run --rm \
        --network nuetra-net \
        -e DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/nuetra_${SERVICE%-service}" \
        -v $(pwd)/$SERVICE_DIR:/app \
        -w /app \
        python:3.11-slim \
        bash -c "
            pip install -q sqlalchemy alembic asyncpg postgresql > /dev/null 2>&1
            alembic upgrade head
        " && \
    echo -e "${GREEN}✓ $SERVICE migrations completed${NC}" || \
    echo -e "${RED}✗ $SERVICE migrations failed${NC}"
    
    echo ""
done

echo -e "${GREEN}======================================================"
echo "✓ Database migrations completed!"
echo "======================================================${NC}"
echo ""
echo "Next steps:"
echo "1. Start all services: docker-compose up"
echo "2. Verify services are running: docker-compose ps"
echo "3. Check service logs: docker-compose logs -f"
