# Nuetra - AI-Powered Wellness Intelligence Platform

Microservices backend built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, and **Redis**.

## Architecture

```
Client (Next.js / Mobile)
        │
        ▼
   API Gateway (:8000)
   ┌──────────────────────────────────┐
   │ Request ID → CORS → JWT → Rate  │
   │ Limit → Proxy to upstream       │
   └──────────────────────────────────┘
        │
        ▼
   Microservices (:8001–:8012)
   ┌──────────────────────────────────┐
   │ auth · profile · assessment     │
   │ scoring · nutrition · consult   │
   │ pathology · wearable · analytics│
   │ admin · notification · payment  │
   └──────────────────────────────────┘
        │
        ▼
   PostgreSQL + Redis
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

### Run with Docker

```bash
# Clone and enter the project
cd nuetra

# Start everything (gateway + auth-service + postgres + redis)
docker compose up --build
```

The API gateway will be available at `http://localhost:8000`.

### Local Development (without Docker)

```bash
# Create a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies for a service
pip install -r services/auth-service/requirements.txt

# Run the service
cd services/auth-service
uvicorn app.main:app --reload --port 8001
```

## Project Structure

```
nuetra/
├── api-gateway/               # FastAPI reverse proxy
│   ├── app/
│   │   ├── main.py            # App entry point
│   │   ├── config.py          # Settings (env vars)
│   │   ├── middleware/        # JWT, CORS, rate limit, request ID
│   │   └── routers/           # Proxy routing logic
│   └── Dockerfile
│
├── services/
│   ├── _template/             # Reusable microservice skeleton
│   │   ├── app/
│   │   │   ├── main.py        # FastAPI app with lifespan
│   │   │   ├── config.py      # Pydantic settings
│   │   │   ├── api/v1/        # Versioned routes
│   │   │   ├── core/          # Logging, exceptions, response format
│   │   │   ├── db/            # SQLAlchemy async engine & session
│   │   │   ├── repositories/  # Data access layer
│   │   │   ├── services/      # Business logic layer
│   │   │   └── schemas/       # Pydantic request/response schemas
│   │   ├── alembic/           # Database migrations
│   │   └── Dockerfile
│   │
│   └── auth-service/          # First service (from template)
│
├── docker-compose.yml
└── README.md
```

## Creating a New Service

```bash
# Copy the template
cp -r services/_template services/my-new-service

# Edit config defaults
# services/my-new-service/app/config.py → change app_name, database_url, app_port

# Add to docker-compose.yml following the auth-service pattern

# Run database migrations
cd services/my-new-service
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

## API Gateway Routes

| Path                      | Upstream Service           | Port |
|---------------------------|----------------------------|------|
| `/api/v1/auth/*`          | auth-service               | 8001 |
| `/api/v1/profile/*`       | profile-service            | 8002 |
| `/api/v1/assessments/*`   | assessment-service         | 8003 |
| `/api/v1/scoring/*`       | scoring-engine-service     | 8004 |
| `/api/v1/nutrition/*`     | nutrition-service          | 8005 |
| `/api/v1/consultations/*` | consultation-service       | 8006 |
| `/api/v1/pathology/*`     | pathology-service          | 8007 |
| `/api/v1/wearables/*`     | wearable-service           | 8008 |
| `/api/v1/analytics/*`     | analytics-service          | 8009 |
| `/api/v1/admin/*`         | admin-service              | 8010 |
| `/api/v1/notifications/*` | notification-service       | 8011 |
| `/api/v1/payments/*`      | payment-service            | 8012 |

## Authentication

All requests pass through the gateway's JWT middleware.

**Public endpoints** (no token required):
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/forgot-password`
- `GET  /health`, `GET /ready`

**Protected endpoints** require `Authorization: Bearer <token>` header.

The gateway decodes the JWT and forwards these headers to upstream services:
- `X-User-Id` — the authenticated user's ID
- `X-User-Role` — the user's role (member, admin, etc.)
- `X-Request-Id` — unique request correlation ID

## Standard Response Format

All services return responses in this format:

```json
{
  "success": true,
  "message": "OK",
  "data": { },
  "error": null,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Health Checks

| Endpoint  | Type       | Description                            |
|-----------|------------|----------------------------------------|
| `/health` | Liveness   | Returns 200 if process is running      |
| `/ready`  | Readiness  | Checks DB and Redis connectivity       |

## Environment Variables

See `.env.example` files in each service and the gateway for the full list of configurable variables.

Key variables:
- `DATABASE_URL` — PostgreSQL async connection string
- `REDIS_URL` — Redis connection string
- `JWT_SECRET_KEY` — Shared secret for JWT signing/validation
- `LOG_LEVEL` — INFO, DEBUG, WARNING, ERROR
- `CORS_ORIGINS` — Comma-separated allowed origins (gateway only)
- `RATE_LIMIT_PER_MINUTE` — Max requests per minute per user/IP (gateway only)

## Tech Stack

- **Python 3.11** / **FastAPI**
- **SQLAlchemy 2.0** (async) / **Alembic**
- **PostgreSQL 16** / **Redis 7**
- **structlog** (structured JSON logging)
- **Docker** / **Docker Compose**
