# Railway Service Matrix

This repository should be deployed to Railway as six services plus managed infrastructure.

## Managed infrastructure

- PostgreSQL: one instance with isolated logical databases per microservice, or separate Railway Postgres services if stricter isolation is required.
- Redis: one shared Redis instance for OTPs, rate limiting, scoring cache, and gateway coordination.

## Deployable services

| Service | Root Directory | Builder | Start Command | Release Command | Health Path |
| --- | --- | --- | --- | --- | --- |
| API Gateway | `api-gateway` | `Dockerfile` | container default | none | `/health` |
| Auth Service | `services/auth-service` | `Dockerfile` | container default | `./release.sh` | `/api/v1/health` |
| Profile Service | `services/profile-service` | `Dockerfile` | container default | `./release.sh` | `/api/v1/health` |
| Assessment Service | `services/assessment-service` | `Dockerfile` | container default | `./release.sh` | `/api/v1/health` |
| Scoring Engine Service | `services/scoring-engine-service` | `Dockerfile` | container default | `./release.sh` | `/api/v1/health` |
| Nutrition Service | `services/nutrition-service` | `Dockerfile` | container default | `./release.sh` | `/api/v1/health` |

## Required environment variables

### API Gateway

- `PORT`
- `APP_ENV`
- `JWT_SECRET_KEY`
- `REDIS_URL`
- `CORS_ORIGINS`
- `TRUSTED_HOSTS`
- `AUTH_SERVICE_URL`
- `PROFILE_SERVICE_URL`
- `ASSESSMENT_SERVICE_URL`
- `SCORING_SERVICE_URL`
- `NUTRITION_SERVICE_URL`

### Auth Service

- `PORT`
- `APP_ENV`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `FRONTEND_URL`
- `EMAIL_PROVIDER`
- `SENDGRID_API_KEY` or SMTP credentials

### Profile / Assessment / Scoring / Nutrition

- `PORT`
- `APP_ENV`
- `DATABASE_URL`
- `REDIS_URL`
- `TRUSTED_HOSTS`

### Scoring only

- `PROFILE_SERVICE_URL`
- `ASSESSMENT_SERVICE_URL`

### Nutrition only

- `UPLOAD_BACKEND`
- `UPLOAD_LOCAL_DIR` or S3 credentials depending on storage strategy

## Recommended deployment order

1. PostgreSQL
2. Redis
3. Auth Service
4. Profile Service
5. Assessment Service
6. Nutrition Service
7. Scoring Engine Service
8. API Gateway
