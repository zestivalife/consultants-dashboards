# Nuetra Backend Architecture

> A developer's guide to understanding the Nuetra wellness intelligence platform backend.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Service Responsibilities](#3-service-responsibilities)
4. [Request Flow Examples](#4-request-flow-examples)
5. [Data Flow Pipeline](#5-data-flow-pipeline)
6. [Infrastructure](#6-infrastructure)
7. [API Gateway Design](#7-api-gateway-design)
8. [Database Strategy](#8-database-strategy)
9. [Folder Structure](#9-folder-structure)
10. [Learning Notes](#10-learning-notes)
11. [Mind Map](#11-mind-map)
12. [Development Workflow](#12-development-workflow)

---

## 1. System Overview

Nuetra is an AI-powered holistic wellness intelligence platform. The backend powers
lifestyle analysis, stress measurement, nutrition planning, pathology tracking, and
corporate analytics through a suite of independent microservices.

### Why Microservices?

| Concern | Monolith | Microservices (Nuetra) |
|---------|----------|------------------------|
| Deployment | Ship everything at once | Deploy auth-service without touching scoring |
| Scaling | Scale the whole app | Scale only the scoring engine during peak loads |
| Database | Single shared schema | Each service owns its data — no cross-service joins |
| Team ownership | Everyone touches everything | One team owns nutrition, another owns scoring |
| Failure isolation | One bug crashes everything | A scoring bug doesn't block logins |
| Technology freedom | Locked to one stack | Could rewrite nutrition in Go without touching auth |

Each service is a self-contained FastAPI application with its own database, Alembic
migrations, Docker image, and API surface. Services communicate exclusively through
HTTP calls and share no database tables.

---

## 2. High-Level Architecture

```
                          ┌─────────────┐
                          │   Client    │
                          │ (Web / App) │
                          └──────┬──────┘
                                 │  HTTPS
                                 ▼
                       ┌─────────────────┐
                       │   API Gateway   │ :8000
                       │  (FastAPI)      │
                       │                 │
                       │  • JWT validate │
                       │  • Rate limit   │
                       │  • CORS         │
                       │  • Route proxy  │
                       └────────┬────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
   ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
   │ Auth Service │     │   Profile    │     │  Assessment  │
   │    :8001     │     │   Service    │     │   Service    │
   │              │     │    :8002     │     │    :8003     │
   │  • Register  │     │              │     │              │
   │  • Login     │     │  • Profile   │     │  • Brain St. │
   │  • JWT       │     │  • Biomarks  │     │  • Focus     │
   │  • OTP       │     │  • Lifestyle │     │  • PSS-10    │
   │  • Roles     │     │  • Body meas │     │  • Phys Ease │
   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
          │                    │                     │
          │   nuetra_auth      │   nuetra_profile    │   nuetra_assessment
          ▼                    ▼                     ▼
   ┌──────────────────────────────────────────────────────────┐
   │                     PostgreSQL :5432                      │
   │   (nuetra_auth │ nuetra_profile │ nuetra_assessment │    │
   │    nuetra_scoring │ nuetra_nutrition)                     │
   └──────────────────────────────────────────────────────────┘
          ▲                    ▲                     ▲
          │   nuetra_scoring   │   nuetra_nutrition  │
   ┌──────┴───────┐     ┌─────┴──────┐              │
   │   Scoring    │────▶│  Nutrition  │              │
   │   Engine     │     │   Service   │              │
   │    :8004     │     │    :8005    │              │
   │              │     │             │              │
   │  • Compute   │     │  • Diet     │              │
   │  • Timeline  │     │  • Meals    │              │
   │  • Formulas  │     │  • Upload   │              │
   └──────┬───────┘     └─────────────┘
          │
          │  HTTP (fetches profile + assessments)
          │
   ┌──────┴───────┐
   │    Redis     │ :6379
   │              │
   │  • OTP TTL   │
   │  • Rate lim  │
   │  • Score     │
   │    cache     │
   │  • Dist lock │
   └──────────────┘
```

### Port Map

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| PostgreSQL | 5433 | 5432 |
| Redis | 6379 | 6379 |
| API Gateway | 8000 | 8000 |
| Auth Service | 8001 | 8001 |
| Profile Service | 8002 | 8002 |
| Assessment Service | 8003 | 8003 |
| Scoring Engine | 8004 | 8004 |
| Nutrition Service | 8005 | 8005 |

---

## 3. Service Responsibilities

### 3.1 Auth Service (`:8001`)

**Purpose:** User identity — registration, login, JWT tokens, OTP verification, roles.

**Database: `nuetra_auth`**

| Table | Key Columns |
|-------|-------------|
| `roles` | `id`, `name`, `description` |
| `users` | `id`, `email`, `password_hash`, `role_id` (FK), `is_verified`, `failed_login_attempts`, `lock_until` |
| `refresh_tokens` | `id`, `user_id` (FK), `token_hash`, `expires_at`, `revoked_at` |
| `otp_verifications` | `id`, `user_id` (FK), `purpose`, `verified_at` |
| `consents` | `id`, `user_id` (FK), `consent_type`, `version`, `accepted_at` |
| `auth_audit_logs` | `id`, `user_id`, `event_type`, `ip_address`, `user_agent` |

**API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/register` | Create user, hash password, send OTP |
| `POST` | `/api/v1/auth/verify-otp` | Verify email OTP, mark verified |
| `POST` | `/api/v1/auth/login` | Validate credentials, issue JWT + refresh token |
| `POST` | `/api/v1/auth/refresh` | Exchange refresh token for new JWT |
| `POST` | `/api/v1/auth/logout` | Revoke refresh token |
| `GET`  | `/api/v1/auth/me` | Get current user (from `X-User-Id` header) |
| `GET`  | `/api/v1/auth/roles` | List available roles |

**Dependencies:** Redis (OTP storage, login rate limiting), SMTP (email delivery).

---

### 3.2 Profile Service (`:8002`)

**Purpose:** Store user profile data, body measurements, biomarkers, and lifestyle baseline
collected during onboarding.

**Database: `nuetra_profile`**

| Table | Key Columns |
|-------|-------------|
| `user_profiles` | `user_id` (unique), `age`, `sex`, `height`, `weight`, `body_fat_percent` |
| `body_measurements` | `user_id` (unique), `arm_circumference`, `thigh_circumference`, `calf_circumference` |
| `biomarkers` | `user_id` (unique), `vitamin_d`, `hba1c`, `tsh`, `b12`, `hdl`, `ldl`, `triglycerides`, `ferritin`, `hemoglobin`, `crp` |
| `lifestyle_baseline` | `user_id` (unique), `activity_level`, `exercise_frequency`, `daily_steps`, `sleep_duration`, `water_intake`, `food_type` |

**API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/profile` | Create full profile (all 4 sections) |
| `GET`  | `/api/v1/profile/me` | Retrieve current user's profile |
| `PUT`  | `/api/v1/profile/me` | Update profile sections |

**Dependencies:** None. Reads `X-User-Id` from gateway.

---

### 3.3 Assessment Service (`:8003`)

**Purpose:** Store raw questionnaire responses. Does **not** compute scores — that is
the scoring engine's job.

**Database: `nuetra_assessment`**

| Table | Key Columns |
|-------|-------------|
| `brain_state_responses` | `user_id`, `question_id`, `response_value`, `submitted_at` |
| `focus_mode_responses` | (same structure) |
| `pss10_responses` | (same structure) |
| `physical_ease_responses` | (same structure) |

**API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/assessments/brain-state` | Submit Brain State answers |
| `POST` | `/api/v1/assessments/focus-mode` | Submit Focus Mode answers |
| `POST` | `/api/v1/assessments/pss10` | Submit PSS-10 answers |
| `POST` | `/api/v1/assessments/physical-ease` | Submit Physical Ease answers |
| `GET`  | `/api/v1/assessments/history` | Get submission summary |

**Dependencies:** None. Reads `X-User-Id` from gateway.

---

### 3.4 Scoring Engine Service (`:8004`)

**Purpose:** Compute wellness scores by fetching data from profile-service and
assessment-service, running formula modules, and storing results.

**Database: `nuetra_scoring`**

| Table | Key Columns |
|-------|-------------|
| `health_scores` | `user_id`, `bmi_score`, `whr_score`, `muscle_score`, `stress_score`, `lifestyle_score`, `total_health_score`, `score_version`, `algorithm_version`, `computed_at` |
| `physical_ease_scores` | `user_id`, `score`, `interpretation`, `score_version`, `algorithm_version`, `computed_at` |
| `active_performance_scores` | `user_id`, `energy_balance`, `body_support`, `nourishment`, `recovery`, `active_performance_score`, `score_version`, `algorithm_version`, `computed_at` |
| `medical_index_scores` | `user_id`, `vitamin_d`, `hba1c`, `thyroid`, `b12`, `lipid_profile`, `ferritin`, `hemoglobin`, `crp`, `medical_index`, `score_version`, `algorithm_version`, `computed_at` |

**API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/scoring/compute?force=false` | Compute all scores (idempotent) |
| `GET`  | `/api/v1/scoring/me` | Get latest scores |
| `GET`  | `/api/v1/scoring/timeline?limit=30` | Get historical scores |

**Dependencies:**
- **profile-service** — HTTP GET to fetch profile + biomarkers
- **assessment-service** — HTTP GET to fetch submission history
- **Redis** — caches upstream responses (600s TTL), distributed scoring lock, idempotency

**Key features:**
- **Idempotency:** If scores were computed within `SCORING_IDEMPOTENCY_MINUTES` (default 5),
  returns existing scores without recomputing. Override with `?force=true`.
- **Distributed lock:** `SET scoring_lock:{user_id} 1 EX 10 NX` prevents concurrent
  computation for the same user.
- **Atomic transactions:** All four score inserts run inside `session.begin()` — if any
  formula fails, all are rolled back.
- **Score versioning:** `score_version` and `algorithm_version` columns allow upgrading
  formulas without corrupting historical data.

---

### 3.5 Nutrition Service (`:8005`)

**Purpose:** Manage diet plans, meal templates, user diet assignments, and health report uploads.

**Database: `nuetra_nutrition`**

| Table | Key Columns |
|-------|-------------|
| `diet_plans` | `id`, `name`, `description`, `calorie_target`, `protein_target`, `fat_target`, `carb_target` |
| `meal_templates` | `diet_plan_id` (FK), `meal_type` (breakfast/lunch/dinner/snack), `meal_name`, `calories`, `protein`, `carbs`, `fats` |
| `user_diet_plans` | `user_id`, `diet_plan_id` (FK), `assigned_by`, `assigned_at` |
| `health_reports` | `user_id`, `file_url`, `uploaded_at` |

**API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/nutrition/diet-plan` | Create diet plan with meals |
| `GET`  | `/api/v1/nutrition/templates` | List all diet plans |
| `POST` | `/api/v1/nutrition/assign` | Assign plan to a user |
| `GET`  | `/api/v1/nutrition/my-plan` | Get current user's plan |
| `POST` | `/api/v1/nutrition/upload-report` | Upload health report (PDF/JPG) |

**Dependencies:** S3-compatible storage (or local filesystem for dev).

---

## 4. Request Flow Examples

### 4.1 User Registration Flow

```
Client                Gateway              Auth Service            Redis           SMTP
  │                      │                      │                    │               │
  │  POST /api/v1/       │                      │                    │               │
  │  auth/register       │                      │                    │               │
  │  {email, password}   │                      │                    │               │
  │─────────────────────▶│                      │                    │               │
  │                      │  (skip JWT — public) │                    │               │
  │                      │  proxy POST          │                    │               │
  │                      │─────────────────────▶│                    │               │
  │                      │                      │                    │               │
  │                      │                      │ 1. validate        │               │
  │                      │                      │    password policy │               │
  │                      │                      │ 2. hash password   │               │
  │                      │                      │    (bcrypt)        │               │
  │                      │                      │ 3. INSERT user     │               │
  │                      │                      │ 4. generate OTP    │               │
  │                      │                      │───────────────────▶│               │
  │                      │                      │    SETEX otp:email │               │
  │                      │                      │    300s            │               │
  │                      │                      │ 5. send OTP email  │               │
  │                      │                      │──────────────────────────────────▶│
  │                      │                      │                    │               │
  │                      │◀─────────────────────│                    │               │
  │◀─────────────────────│  201 Created         │                    │               │
  │                      │  "OTP sent"          │                    │               │
```

### 4.2 User Profile Creation

```
Client                Gateway              Profile Service         PostgreSQL
  │                      │                      │                      │
  │  POST /api/v1/       │                      │                      │
  │  profile             │                      │                      │
  │  + Bearer JWT        │                      │                      │
  │─────────────────────▶│                      │                      │
  │                      │ 1. validate JWT      │                      │
  │                      │ 2. extract user_id   │                      │
  │                      │ 3. proxy POST        │                      │
  │                      │    + X-User-Id       │                      │
  │                      │    + X-User-Role     │                      │
  │                      │─────────────────────▶│                      │
  │                      │                      │ 4. read X-User-Id    │
  │                      │                      │ 5. INSERT into       │
  │                      │                      │    user_profiles     │
  │                      │                      │    body_measurements │
  │                      │                      │    biomarkers        │
  │                      │                      │    lifestyle_baseline│
  │                      │                      │─────────────────────▶│
  │                      │                      │                      │
  │                      │◀─────────────────────│  201 full profile    │
  │◀─────────────────────│                      │                      │
```

### 4.3 Assessment Submission

```
Client                Gateway              Assessment Service      PostgreSQL
  │                      │                      │                      │
  │  POST /api/v1/       │                      │                      │
  │  assessments/pss10   │                      │                      │
  │  {answers: [...]}    │                      │                      │
  │─────────────────────▶│                      │                      │
  │                      │ validate JWT         │                      │
  │                      │ proxy + X-User-Id    │                      │
  │                      │─────────────────────▶│                      │
  │                      │                      │                      │
  │                      │                      │  bulk INSERT into    │
  │                      │                      │  pss10_responses     │
  │                      │                      │  (one row per        │
  │                      │                      │   question)          │
  │                      │                      │─────────────────────▶│
  │                      │                      │                      │
  │                      │◀─────────────────────│  201 submission_id   │
  │◀─────────────────────│                      │                      │
```

### 4.4 Score Computation

```
Client         Gateway        Scoring Engine     Redis       Profile Svc    Assessment Svc
  │               │                 │               │             │               │
  │ POST /api/v1/ │                 │               │             │               │
  │ scoring/      │                 │               │             │               │
  │ compute       │                 │               │             │               │
  │──────────────▶│                 │               │             │               │
  │               │ proxy           │               │             │               │
  │               │────────────────▶│               │             │               │
  │               │                 │               │             │               │
  │               │                 │ 1. IDEMPOTENCY CHECK        │               │
  │               │                 │    latest health_score      │               │
  │               │                 │    computed < 5min ago?      │               │
  │               │                 │    → return existing         │               │
  │               │                 │               │             │               │
  │               │                 │ 2. ACQUIRE LOCK             │               │
  │               │                 │───────────────▶│             │               │
  │               │                 │ SET scoring_   │             │               │
  │               │                 │ lock:{uid}     │             │               │
  │               │                 │ NX EX 10       │             │               │
  │               │                 │               │             │               │
  │               │                 │ 3. CHECK CACHE │             │               │
  │               │                 │───────────────▶│             │               │
  │               │                 │ GET profile:   │             │               │
  │               │                 │ {user_id}      │             │               │
  │               │                 │               │             │               │
  │               │                 │ 4a. CACHE MISS — fetch from service          │
  │               │                 │────────────────────────────▶│               │
  │               │                 │  GET /api/v1/profile/me     │               │
  │               │                 │◀────────────────────────────│               │
  │               │                 │               │             │               │
  │               │                 │ 4b. Cache response          │               │
  │               │                 │───────────────▶│             │               │
  │               │                 │ SETEX 600s     │             │               │
  │               │                 │               │             │               │
  │               │                 │ 5. Fetch assessments (same pattern)          │
  │               │                 │──────────────────────────────────────────────▶│
  │               │                 │◀─────────────────────────────────────────────│
  │               │                 │               │             │               │
  │               │                 │ 6. COMPUTE (inside session.begin)            │
  │               │                 │    ├─ health_score.compute()                 │
  │               │                 │    ├─ physical_ease_score.compute()          │
  │               │                 │    ├─ active_performance_score.compute()     │
  │               │                 │    └─ medical_index_score.compute()          │
  │               │                 │    (all-or-nothing transaction)              │
  │               │                 │               │             │               │
  │               │                 │ 7. RELEASE LOCK             │               │
  │               │                 │───────────────▶│             │               │
  │               │                 │ DEL scoring_   │             │               │
  │               │                 │ lock:{uid}     │             │               │
  │               │                 │               │             │               │
  │               │◀────────────────│ 201 scores     │             │               │
  │◀──────────────│                 │               │             │               │
```

---

## 5. Data Flow Pipeline

This is the core intelligence pipeline — how raw user data becomes wellness scores.

```
┌────────────────────────────────────────────────────────────────────┐
│                      DATA COLLECTION LAYER                         │
│                                                                    │
│  ┌──────────────┐    ┌───────────────┐    ┌──────────────────┐    │
│  │ Onboarding   │    │ Questionnaires│    │ Health Reports   │    │
│  │ (Profile Svc)│    │ (Assess. Svc) │    │ (Nutrition Svc)  │    │
│  │              │    │               │    │                  │    │
│  │ • Age, sex   │    │ • Brain State │    │ • Blood work PDF │    │
│  │ • Height, wt │    │ • Focus Mode  │    │ • Lab results    │    │
│  │ • Biomarkers │    │ • PSS-10      │    │                  │    │
│  │ • Lifestyle  │    │ • Phys. Ease  │    │                  │    │
│  └──────┬───────┘    └───────┬───────┘    └──────────────────┘    │
│         │                    │                                     │
└─────────┼────────────────────┼─────────────────────────────────────┘
          │                    │
          ▼                    ▼
┌────────────────────────────────────────────────────────────────────┐
│                     SCORING & INTELLIGENCE LAYER                   │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   Scoring Engine Service                     │  │
│  │                                                             │  │
│  │  profile + biomarkers ──┐                                   │  │
│  │                         ├──▶ health_score.compute()         │  │
│  │  PSS-10 responses ──────┘       → BMI, WHR, muscle,        │  │
│  │                                   stress, lifestyle         │  │
│  │                                                             │  │
│  │  physical ease responses ──▶ physical_ease_score.compute()  │  │
│  │                                 → score + interpretation    │  │
│  │                                                             │  │
│  │  profile data ──▶ active_performance_score.compute()        │  │
│  │                      → energy, body support, nourishment,   │  │
│  │                        recovery                             │  │
│  │                                                             │  │
│  │  biomarkers ──▶ medical_index_score.compute()               │  │
│  │                    → per-marker scores + composite index     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────────────────┐
│                        RESULTS LAYER                               │
│                                                                    │
│  GET /api/v1/scoring/me        → latest composite scores          │
│  GET /api/v1/scoring/timeline  → historical trend data            │
│                                                                    │
│  Each result carries: score_version, algorithm_version,            │
│  computed_at — enabling formula upgrades without data loss.        │
└────────────────────────────────────────────────────────────────────┘
```

---

## 6. Infrastructure

### 6.1 Docker

Every service has a multi-stage `Dockerfile`:

```
python:3.11-slim (base)
  └─ deps stage: pip install requirements.txt
       └─ runtime stage: COPY app code, run as non-root appuser
```

`docker-compose.yml` orchestrates all services on a shared `nuetra-net` bridge network.
Services discover each other by container name (e.g. `http://auth-service:8001`).

### 6.2 PostgreSQL

A single Postgres 16 instance hosts separate databases per service:

| Database | Owner Service |
|----------|---------------|
| `nuetra_auth` | auth-service |
| `nuetra_profile` | profile-service |
| `nuetra_assessment` | assessment-service |
| `nuetra_scoring` | scoring-engine-service |
| `nuetra_nutrition` | nutrition-service |

Host port is **5433** (remapped to avoid conflicts with local Postgres).

### 6.3 Redis

Redis 7 serves multiple purposes across the platform:

| Use Case | Key Pattern | TTL | Service |
|----------|-------------|-----|---------|
| OTP codes | `otp:{email}` | 300s | auth |
| Login rate limit | `rate_limit:{key}` | sliding window | auth |
| Profile cache | `profile:{user_id}` | 600s | scoring |
| Assessment cache | `assessment:{user_id}` | 600s | scoring |
| Scoring lock | `scoring_lock:{user_id}` | 10s | scoring |

### 6.4 Environment Variables

Every service reads config from environment variables via Pydantic `BaseSettings`.
Common variables across all services:

| Variable | Purpose | Example |
|----------|---------|---------|
| `APP_NAME` | Service identifier for logs | `auth-service` |
| `APP_ENV` | Environment name | `development` |
| `APP_DEBUG` | Enable Swagger UI | `true` |
| `APP_PORT` | Uvicorn listen port | `8001` |
| `DATABASE_URL` | Async Postgres connection | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `LOG_FORMAT` | Log output format | `json` |

Service-specific variables are documented in each service's `.env.example`.

---

## 7. API Gateway Design

The gateway (`api-gateway/`, port 8000) is the single entry point for all client traffic.

### 7.1 JWT Validation

The `JWTMiddleware` intercepts every request:

1. **Public paths are skipped:** `/health`, `/ready`, `/docs`, `/openapi.json`,
   `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/refresh`
2. **Extract token** from `Authorization: Bearer <token>` or `X-Access-Token` header
3. **Decode and verify** using `PyJWT` with `JWT_SECRET_KEY` (HS256)
4. **Inject headers** into the upstream request:
   - `X-User-Id` — the authenticated user's UUID
   - `X-User-Role` — the user's role name

Downstream services **never decode JWTs themselves** — they trust the gateway's
`X-User-Id` header.

### 7.2 Request ID Propagation

`RequestIdMiddleware` runs on every request:
- Reads `X-Request-Id` from the incoming request, or generates a UUID
- Binds it to `structlog` context (appears in all log entries)
- Passes it downstream so logs can be correlated across services

### 7.3 Rate Limiting

`RateLimitMiddleware` uses an in-memory sliding window:
- Key: `user:{user_id}` for authenticated requests, `ip:{client_ip}` otherwise
- Default: 60 requests per minute (configurable via `RATE_LIMIT_PER_MINUTE`)
- Returns `429 Too Many Requests` when exceeded

### 7.4 Routing Rules

The proxy router matches request paths to upstream services:

| Path Prefix | Upstream Service |
|-------------|------------------|
| `/api/v1/auth` | `http://auth-service:8001` |
| `/api/v1/profile` | `http://profile-service:8002` |
| `/api/v1/assessments` | `http://assessment-service:8003` |
| `/api/v1/scoring` | `http://scoring-engine-service:8004` |
| `/api/v1/nutrition` | `http://nutrition-service:8005` |
| `/api/v1/consultations` | `http://consultation-service:8006` |
| `/api/v1/pathology` | `http://pathology-service:8007` |
| `/api/v1/wearables` | `http://wearable-service:8008` |
| `/api/v1/analytics` | `http://analytics-service:8009` |
| `/api/v1/admin` | `http://admin-service:8010` |
| `/api/v1/notifications` | `http://notification-service:8011` |
| `/api/v1/payments` | `http://payment-service:8012` |

The proxy forwards the full request (method, headers, body, query params) using
`httpx.AsyncClient` and streams the response back.

### 7.5 Middleware Execution Order

```
Request  →  RequestIdMiddleware  →  CORSMiddleware  →  JWTMiddleware  →  RateLimitMiddleware  →  Proxy
Response ←  RequestIdMiddleware  ←  CORSMiddleware  ←  JWTMiddleware  ←  RateLimitMiddleware  ←  Proxy
```

---

## 8. Database Strategy

### Database-per-Service Pattern

Each microservice owns a private database. No service reads or writes another service's
tables.

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  auth-service │     │profile-service│     │  assess-svc   │
│               │     │               │     │               │
│  nuetra_auth  │     │nuetra_profile │     │nuetra_assess  │
│  ┌─────────┐  │     │  ┌─────────┐  │     │  ┌─────────┐  │
│  │ users   │  │     │  │profiles │  │     │  │pss10_   │  │
│  │ roles   │  │     │  │biomarks │  │     │  │responses│  │
│  │ tokens  │  │     │  │measures │  │     │  │brain_st │  │
│  │ otp     │  │     │  │lifestyle│  │     │  │focus    │  │
│  │ audit   │  │     │  └─────────┘  │     │  │phys_ease│  │
│  │ consent │  │     │               │     │  └─────────┘  │
│  └─────────┘  │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
```

**Why?**

| Benefit | Explanation |
|---------|-------------|
| Independent migrations | auth can add columns without coordinating with nutrition |
| Failure isolation | If nuetra_scoring is corrupted, users can still log in |
| Scaling | Profile reads are heavy? Scale that database independently |
| Schema freedom | Assessment tables are append-only; scoring tables need versioning columns |
| Clear ownership | Every table belongs to exactly one team |

**Trade-off:** Cross-service queries require HTTP calls instead of SQL joins.
The scoring engine, for example, fetches profile data via HTTP rather than
joining `user_profiles` directly. Redis caching mitigates the latency cost.

### Migrations

Each service uses Alembic for async migrations (`asyncpg` driver). Migration files
live in `service/alembic/versions/`. The template provides a pre-configured
`alembic/env.py` that reads `DATABASE_URL` from the service's `Settings`.

---

## 9. Folder Structure

Every microservice follows the same layered structure inherited from `services/_template/`:

```
services/{service-name}/
│
├── app/
│   ├── main.py                    # FastAPI app factory, lifespan, middleware
│   ├── config.py                  # Pydantic Settings (reads .env / env vars)
│   │
│   ├── api/v1/
│   │   ├── router.py              # Aggregates all route modules
│   │   ├── dependencies.py        # Shared FastAPI dependencies (get_user_id)
│   │   └── routes/
│   │       ├── health.py          # GET /health, GET /ready
│   │       └── {domain}.py        # Domain-specific endpoints
│   │
│   ├── services/
│   │   └── {domain}_service.py    # Business logic (orchestration)
│   │
│   ├── repositories/
│   │   └── {model}_repository.py  # Database queries (SQLAlchemy)
│   │
│   ├── schemas/
│   │   └── {domain}.py            # Pydantic request/response models
│   │
│   ├── db/
│   │   ├── base.py                # SQLAlchemy DeclarativeBase
│   │   ├── session.py             # Engine, session factory, get_db dependency
│   │   └── models/
│   │       ├── __init__.py        # Re-exports all models (for Alembic)
│   │       └── {table}.py         # One file per SQLAlchemy model
│   │
│   └── core/
│       ├── exceptions.py          # AppException hierarchy + global handlers
│       ├── response.py            # success_response / error_response helpers
│       └── logging.py             # structlog configuration
│
├── alembic/
│   ├── env.py                     # Async migration runner
│   ├── script.py.mako             # Migration template
│   └── versions/
│       └── 0001_*.py              # Migration files
│
├── Dockerfile                     # Multi-stage build
├── alembic.ini                    # Alembic config
├── requirements.txt               # Pinned dependencies
└── .env.example                   # Documented environment variables
```

### Layer Responsibilities

```
Request
  │
  ▼
Routes          ← HTTP concerns: parse request, validate input, return response
  │
  ▼
Services        ← Business logic: orchestrate operations, enforce rules
  │
  ▼
Repositories    ← Data access: SQLAlchemy queries, no business logic
  │
  ▼
Models          ← Schema: table definitions, relationships, column types
```

**Rule:** Routes never import repositories directly. Services never execute raw SQL.
Repositories never import from routes.

---

## 10. Learning Notes

### 10.1 FastAPI

FastAPI is an async Python web framework built on Starlette and Pydantic.

- **Dependency injection** via `Depends()` — used for `get_db` (database sessions)
  and `get_user_id` (header extraction)
- **Automatic validation** — Pydantic schemas validate request bodies and generate
  OpenAPI docs
- **Lifespan context** — the `@asynccontextmanager` in `main.py` runs setup/teardown
  code (logging, engine disposal)
- **Middleware** — Starlette middleware classes wrap every request/response cycle

### 10.2 SQLAlchemy 2.0 Async

The project uses SQLAlchemy's async engine with `asyncpg`:

```python
engine = create_async_engine("postgresql+asyncpg://...")
async with AsyncSession(engine) as session:
    result = await session.execute(select(User).where(...))
```

Key patterns:
- `Mapped[type]` with `mapped_column()` for type-safe column definitions
- `async_sessionmaker` creates session factories
- `get_db()` is an async generator dependency that commits on success, rolls back on error
- `session.begin()` creates a SAVEPOINT for nested transactions

### 10.3 Alembic

Alembic manages database schema migrations:

```bash
# Inside a service container:
alembic upgrade head        # Apply all migrations
alembic revision --autogenerate -m "add column"  # Generate migration
alembic downgrade -1        # Rollback one step
```

Each service's `alembic/env.py` uses `create_async_engine` to run migrations
asynchronously. Models must be imported in `env.py` so Alembic discovers them
via `Base.metadata`.

### 10.4 Redis Caching

The scoring engine caches upstream HTTP responses to avoid hammering profile-service
and assessment-service on repeated computations:

```python
# Check cache first
profile = await cache.get_cached_profile(user_id)
if not profile:
    # Cache miss — fetch from service
    profile = await http_client.fetch_profile(user_id)
    # Store with TTL
    await cache.set_cached_profile(user_id, profile)
```

Cache keys are simple: `profile:{user_id}`, `assessment:{user_id}`.
TTL is 600 seconds. Data is JSON-serialized.

### 10.5 Idempotency in Scoring

The `/compute` endpoint is idempotent by default:

1. Check `health_scores` for the user's latest `computed_at` timestamp
2. If it's within the idempotency window (default 5 min), return existing scores
   with `recomputed: false` and HTTP 200
3. Otherwise, compute fresh scores, return with `recomputed: true` and HTTP 201
4. `?force=true` bypasses the check entirely

This prevents wasted computation when a client retries or a frontend triggers
multiple requests.

### 10.6 Microservice Communication

Services communicate via synchronous HTTP calls using `httpx.AsyncClient`:

```python
async def fetch_profile(user_id, request_id):
    client = await get_client()
    resp = await client.get(
        f"{PROFILE_SERVICE_URL}/api/v1/profile/me",
        headers={"X-User-Id": str(user_id), "X-Request-Id": request_id},
    )
    return resp.json().get("data")
```

Key design decisions:
- **X-User-Id header** — the calling service impersonates the user by passing the
  header (same mechanism the gateway uses)
- **X-Request-Id propagation** — enables tracing a request across all services in logs
- **Redis caching** — mitigates the latency penalty of HTTP vs direct DB queries
- **Timeout + error handling** — `httpx.Timeout(15.0, connect=5.0)` prevents hanging;
  errors return `None` / empty list so scoring can degrade gracefully

---

## 11. Mind Map

```
                                    NUETRA BACKEND
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 │                       │                       │
           INFRASTRUCTURE           API GATEWAY              SERVICES
                 │                       │                       │
          ┌──────┼──────┐          ┌─────┼─────┐          ┌──────┼──────────┐
          │      │      │          │     │     │          │      │          │
       Docker  Postgres Redis    JWT   CORS  Rate      Auth  Profile  Assessment
          │      │      │       Valid  Ctrl  Limit       │      │          │
       Compose  5 DBs  Cache   Route  ────  ────      Users  4 Tables   4 Types
       8 svcs   Alembic OTP    Proxy               Tokens  Biomarks  Raw Data
                        Lock                       Roles   Lifestyle  History
                        Rate                       OTP
                                                   Audit
                                                     │
                                              ┌──────┼──────┐
                                              │             │
                                          Scoring       Nutrition
                                          Engine         Service
                                              │             │
                                        ┌─────┼─────┐   Diet Plans
                                        │     │     │   Meals
                                     Health  Phys  Active  Assign
                                     Score   Ease  Perf   Upload
                                        │     │     │
                                     Medical Index
                                        │
                                  ┌─────┼─────┐
                                  │           │
                              Idempotent  Versioned
                              + Locked    + Cached
                              + Atomic    + Timeline
```

---

## 12. Development Workflow

### 12.1 Prerequisites

- Docker Engine 20+
- Docker Compose v2+ (the `docker compose` CLI plugin)

### 12.2 Start Everything

```bash
cd /home/vector/projects/nuetra
docker compose up --build -d
```

This builds all images and starts:
- PostgreSQL (port 5433)
- Redis (port 6379)
- API Gateway (port 8000)
- 5 microservices (ports 8001–8005)

### 12.3 Run Migrations

Each service needs its database created and migrations applied:

```bash
# Create databases (run once)
docker compose exec postgres psql -U nuetra -c "CREATE DATABASE nuetra_auth;"
docker compose exec postgres psql -U nuetra -c "CREATE DATABASE nuetra_profile;"
docker compose exec postgres psql -U nuetra -c "CREATE DATABASE nuetra_assessment;"
docker compose exec postgres psql -U nuetra -c "CREATE DATABASE nuetra_scoring;"
docker compose exec postgres psql -U nuetra -c "CREATE DATABASE nuetra_nutrition;"

# Apply migrations
docker compose exec auth-service alembic upgrade head
docker compose exec profile-service alembic upgrade head
docker compose exec assessment-service alembic upgrade head
docker compose exec scoring-engine-service alembic upgrade head
docker compose exec nutrition-service alembic upgrade head
```

### 12.4 Swagger UI

Every service exposes Swagger when `APP_DEBUG=true`:

| Service | Swagger URL |
|---------|------------|
| API Gateway | http://localhost:8000/docs |
| Auth | http://localhost:8001/docs |
| Profile | http://localhost:8002/docs |
| Assessment | http://localhost:8003/docs |
| Scoring Engine | http://localhost:8004/docs |
| Nutrition | http://localhost:8005/docs |

**Tip:** Test individual services directly (ports 8001–8005) to bypass JWT validation.
When testing through the gateway (port 8000), include `Authorization: Bearer <token>`.

### 12.5 Testing a Full Flow

```bash
# 1. Register
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test1234"}'

# 2. Login (after OTP verification)
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test1234"}'
# → returns access_token

# 3. Create profile (directly, bypassing gateway)
curl -X POST http://localhost:8002/api/v1/profile \
  -H "Content-Type: application/json" \
  -H "X-User-Id: <user-uuid>" \
  -d '{"profile": {"age": 30, "sex": "male", "height": 175, "weight": 70}}'

# 4. Submit assessment
curl -X POST http://localhost:8003/api/v1/assessments/pss10 \
  -H "Content-Type: application/json" \
  -H "X-User-Id: <user-uuid>" \
  -d '{"answers": [{"question_id": 1, "response_value": 3}]}'

# 5. Compute scores
curl -X POST http://localhost:8004/api/v1/scoring/compute \
  -H "X-User-Id: <user-uuid>"
```

### 12.6 Viewing Logs

```bash
# All services
docker compose logs -f

# Single service
docker compose logs -f scoring-engine-service

# Logs are structured JSON — pipe through jq for readability
docker compose logs scoring-engine-service --no-log-prefix | jq .
```

### 12.7 Stopping

```bash
docker compose down          # Stop and remove containers
docker compose down -v       # Also remove volumes (deletes all data)
```
