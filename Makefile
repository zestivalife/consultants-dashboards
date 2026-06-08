# Start services
up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Stop services
down:
	docker compose down

# Rebuild
build:
	docker compose up -d --build

# Logs
logs:
	docker compose logs -f

# Migrate all services
migrate:
	docker exec -it nuetra-auth-service-1 alembic upgrade head
	docker exec -it nuetra-profile-service-1 alembic upgrade head
	docker exec -it nuetra-assessment-service-1 alembic upgrade head
	docker exec -it nuetra-scoring-engine-service-1 alembic upgrade head
	docker exec -it nuetra-nutrition-service-1 alembic upgrade head

# Enter containers
auth:
	docker exec -it nuetra-auth-service-1 bash

profile:
	docker exec -it nuetra-profile-service-1 bash

assessment:
	docker exec -it nuetra-assessment-service-1 bash

scoring:
	docker exec -it nuetra-scoring-engine-service-1 bash

nutrition:
	docker exec -it nuetra-nutrition-service-1 bash

db:
	docker exec -it nuetra-postgres-1 bash

# Restart all
restart:
	docker compose down && docker compose up -d