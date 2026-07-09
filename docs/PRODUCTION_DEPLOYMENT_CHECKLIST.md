# Production Deployment Checklist

## Infrastructure

- Create Railway project for backend services.
- Provision one PostgreSQL instance.
- Provision one Redis instance.
- Provision Vercel project for `nuetra-frontend`.
- Reserve production domains for frontend and API.

## PostgreSQL

- Create logical databases:
  - `nuetra_auth`
  - `nuetra_profile`
  - `nuetra_assessment`
  - `nuetra_scoring`
  - `nuetra_nutrition`
- Generate service-specific `DATABASE_URL` values.
- Enable backups and verify retention policy.

## Redis

- Provision shared Redis.
- Capture `REDIS_URL`.
- Verify connectivity from Railway services.

## Railway Services

- Deploy:
  - `api-gateway`
  - `services/auth-service`
  - `services/profile-service`
  - `services/assessment-service`
  - `services/scoring-engine-service`
  - `services/nutrition-service`
- For each service set:
  - Root Directory
  - Build Command
  - Start Command
  - Health Check Path

## Root Directories

- `api-gateway`
- `services/auth-service`
- `services/profile-service`
- `services/assessment-service`
- `services/scoring-engine-service`
- `services/nutrition-service`

## Build Commands

```bash
pip install -r requirements.txt
```

## Start Commands

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Health Checks

- Gateway: `/health`
- Gateway readiness: `/ready`
- Services: `/api/v1/health`
- Services readiness: `/api/v1/ready`

## Environment Variables

### Shared

- `APP_ENV=production`
- `APP_DEBUG=false`
- `LOG_LEVEL=INFO`
- `LOG_FORMAT=json`
- `REDIS_URL=...`

### API Gateway

- `JWT_SECRET_KEY=...`
- `JWT_ALGORITHM=HS256`
- `RATE_LIMIT_PER_MINUTE=60`
- `CORS_ORIGINS=https://consultants-dashboards.vercel.app`
- `AUTH_SERVICE_URL=...`
- `PROFILE_SERVICE_URL=...`
- `ASSESSMENT_SERVICE_URL=...`
- `SCORING_SERVICE_URL=...`
- `NUTRITION_SERVICE_URL=...`

### Auth Service

- `DATABASE_URL=...nuetra_auth`
- `FRONTEND_URL=https://consultants-dashboards.vercel.app`
- `JWT_SECRET_KEY=...`
- `JWT_ALGORITHM=HS256`
- `JWT_ACCESS_EXPIRY_MINUTES=15`
- `JWT_REFRESH_EXPIRY_DAYS=7`
- `MAX_FAILED_LOGIN_ATTEMPTS=5`
- `ACCOUNT_LOCK_MINUTES=15`
- `OTP_EXPIRY_SECONDS=300`
- `EMAIL_PROVIDER=sendgrid`
- `SENDGRID_API_KEY=...`
- `SMTP_HOST=smtp.sendgrid.net`
- `SMTP_PORT=587`
- `SMTP_USER=apikey`
- `SMTP_PASSWORD=...`
- `SMTP_FROM_EMAIL=admin@nuetra.in`
- `SMTP_FROM_NAME=Nuetra`
- `SMTP_USE_TLS=true`
- `SMTP_USE_SSL=false`
- `LOGIN_RATE_LIMIT_MAX=10`
- `LOGIN_RATE_LIMIT_WINDOW_SECONDS=60`

### Profile Service

- `DATABASE_URL=...nuetra_profile`

### Assessment Service

- `DATABASE_URL=...nuetra_assessment`

### Scoring Engine

- `DATABASE_URL=...nuetra_scoring`
- `PROFILE_SERVICE_URL=...`
- `ASSESSMENT_SERVICE_URL=...`
- `CACHE_TTL_SECONDS=600`
- `SCORING_IDEMPOTENCY_MINUTES=5`
- `SCORE_VERSION=v1`
- `ALGORITHM_VERSION=2026-03`

### Nutrition Service

- `DATABASE_URL=...nuetra_nutrition`
- `UPLOAD_BACKEND=s3`
- `S3_BUCKET=...`
- `S3_REGION=...`
- `S3_ACCESS_KEY=...`
- `S3_SECRET_KEY=...`
- `S3_ENDPOINT_URL=...`

## Database Migrations

- Run Alembic migrations for each service against its own logical database.
- Verify migrations complete before opening traffic.

## Vercel

- Root directory: `nuetra-frontend`
- Framework: Next.js
- Build command: `npm run build`
- Install command: `npm install`
- Environment variable:
  - `NEXT_PUBLIC_API_URL=https://api.<your-domain>/api/v1`

## DNS

- Point frontend domain to Vercel.
- Point API domain to Railway `api-gateway`.
- Enable SSL on both.

## Smoke Tests

- `GET /health`
- `GET /ready`
- Login
- OTP flow
- Profile create/read/update
- Assessment submit/history
- Scoring compute/me/timeline
- Nutrition upload/assign/my-plan
- Consultant creation via `/corporate-admin/consultants`

## Rollback Procedure

- Keep previous Railway deployments available.
- Roll back service-by-service if a health check fails.
- Restore DB from backup only if migration rollback is not possible.

## Backup Strategy

- Enable managed Postgres backups.
- Snapshot before production migrations.
- Document Redis persistence expectations separately.
