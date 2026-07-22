# Backend Production Audit

## Current architecture

- `api-gateway`
- `services/auth-service`
- `services/profile-service`
- `services/assessment-service`
- `services/scoring-engine-service`
- `services/nutrition-service`
- shared PostgreSQL
- shared Redis
- Vercel frontend in `nuetra-frontend`

The implemented repository is a microservice backend, not a unified backend.

## Mandatory MVP services

- API Gateway
- Auth Service
- Profile Service
- Assessment Service
- Scoring Engine Service
- Nutrition Service
- PostgreSQL
- Redis

## Audit findings before hardening

- Dockerfiles were binding to fixed ports instead of Railway `PORT`.
- Service configs still defaulted to localhost-era database and Redis values.
- API Gateway still contained dead upstream configuration for non-implemented services.
- Health and readiness payloads were inconsistent across services.
- No per-service Railway release command existed for Alembic migrations.
- Database engines did not use `pool_pre_ping` or pool timeout protection.
- Trusted host and security headers were missing.

## Hardening applied

- Dynamic `PORT` binding added to every deployable Dockerfile.
- Railway-friendly env aliases added for `PORT`, `DATABASE_URL`, and `REDIS_URL`.
- Defaults switched to internal service networking (`postgres`, `redis`, service DNS).
- Trusted host middleware and baseline security headers added.
- Gateway route table reduced to implemented services only.
- Gateway Redis rate limiting now uses Redis instead of in-memory state.
- `/health` and `/ready` responses standardized across gateway and services.
- DB engines now use `pool_pre_ping`, `pool_timeout`, and `pool_use_lifo`.
- `release.sh` added to each data-owning microservice for Railway migration execution.
- Verification scripts added for deployment structure, health checks, migrations, and smoke tests.

## Remaining live-environment verification

- Railway service URLs must be wired into gateway environment variables.
- PostgreSQL logical databases must exist and be reachable from each service.
- Redis must be reachable from gateway, auth, scoring, and readiness checks.
- Live Alembic execution still needs a shell with `alembic` installed.
- API smoke tests still need deployed URLs and real runtime connectivity.
- Nutrition upload backend should move from local storage to object storage for durable production uploads.

## Recommended Railway deployment order

1. PostgreSQL
2. Redis
3. Auth Service
4. Profile Service
5. Assessment Service
6. Nutrition Service
7. Scoring Engine Service
8. API Gateway

## Recommended migration strategy

Use Railway per-service Release Command:

- Auth: `./release.sh`
- Profile: `./release.sh`
- Assessment: `./release.sh`
- Scoring: `./release.sh`
- Nutrition: `./release.sh`

This is the safest fit for the existing architecture because each service owns its own schema and Alembic history.
