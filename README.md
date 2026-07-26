# Nuetra - AI-Powered Wellness Intelligence Platform

Microservices backend built with **FastAPI**, **SQLAlchemy 2.0**,
**PostgreSQL**, and **Redis**.

> **Repository Classification**
>
> Enterprise Engineering Repository • AI-Native Product Platform •
> Microservices Architecture • Knowledge-Driven Development

------------------------------------------------------------------------

# Enterprise AI Engineering Governance

This repository is governed by the **Codex Enterprise Operating
Constitution**.

## AI Engineering Authority

Before performing **any** engineering, architecture, documentation,
repository, or implementation task, every AI engineering agent (Codex,
ChatGPT, Claude, Gemini, Cursor, Windsurf, etc.) SHALL load and comply
with:

``` text
ai/constitution/CODEX_ENTERPRISE_OPERATING_CONSTITUTION.md
```

The Constitution is the **highest authority** governing:

-   Repository organisation
-   Enterprise Architecture
-   Product Engineering
-   Documentation Standards
-   Engineering Standards
-   AI Engineering Standards
-   Repository Governance
-   Source of Truth Management
-   Quality Gates
-   Security Reviews
-   Repository Rationalisation
-   Enterprise Validation

If repository content conflicts with the Constitution, the Constitution
prevails unless explicitly overridden by the Product Owner.

------------------------------------------------------------------------

## AI Engineering Governance

All AI-assisted engineering work within this repository is governed by:

ai/constitution/CODEX_ENTERPRISE_OPERATING_CONSTITUTION.md

Every AI agent must load and comply with the Constitution before analysing, designing, implementing or restructuring any part of the repository.


## Repository Vision

This repository is not merely a software codebase.

It is the canonical **Enterprise Knowledge Platform** for the Zestiva
ecosystem and serves as the Single Source of Truth for:

-   Product Vision
-   Enterprise Architecture
-   Engineering Standards
-   Product Bible
-   Business Capabilities
-   Domain Models
-   API Specifications
-   Security Standards
-   AI Operating System
-   Platform Governance
-   Product Delivery
-   Operations

Repository organisation is based on **Enterprise Architecture**,
**Domain-Driven Design**, **Business Capabilities**, and **Engineering
Governance**, rather than historical filesystem structure.

------------------------------------------------------------------------

## Architecture

``` text
Client (Next.js / Mobile)
        │
        ▼
   API Gateway (:8000)
        │
        ▼
   Microservices (:8001–:8012)
        │
        ▼
 PostgreSQL + Redis
```

## Quick Start

### Prerequisites

-   Docker & Docker Compose
-   Python 3.11+

### Run with Docker

``` bash
docker compose up --build
```

Gateway:

    http://localhost:8000

### Local Development

``` bash
python3.11 -m venv .venv
source .venv/bin/activate

pip install -r services/auth-service/requirements.txt

cd services/auth-service
uvicorn app.main:app --reload --port 8001
```

------------------------------------------------------------------------

# Project Structure

``` text
nuetra/
├── ai/
│   ├── constitution/
│   │   └── CODEX_ENTERPRISE_OPERATING_CONSTITUTION.md
│   ├── governance/
│   ├── architecture/
│   ├── prompts/
│   └── playbooks/
├── api-gateway/
├── services/
├── architecture/
├── engineering/
├── governance/
├── product/
├── platform/
├── operations/
└── README.md
```

> **Note:** The repository hierarchy may evolve as part of enterprise
> repository rationalisation. AI agents are authorised to restructure
> folders and documentation when compliant with the Constitution while
> preserving knowledge, traceability and repository integrity.

------------------------------------------------------------------------

# Creating a New Service

``` bash
cp -r services/_template services/my-new-service
```

Update configuration, docker-compose and database migrations before
exposing routes through the API Gateway.

------------------------------------------------------------------------

# API Gateway Routes

  Path                        Service                    Port
  --------------------------- ------------------------ ------
  `/api/v1/auth/*`            auth-service               8001
  `/api/v1/profile/*`         profile-service            8002
  `/api/v1/assessments/*`     assessment-service         8003
  `/api/v1/scoring/*`         scoring-engine-service     8004
  `/api/v1/nutrition/*`       nutrition-service          8005
  `/api/v1/consultations/*`   consultation-service       8006
  `/api/v1/pathology/*`       pathology-service          8007
  `/api/v1/wearables/*`       wearable-service           8008
  `/api/v1/analytics/*`       analytics-service          8009
  `/api/v1/admin/*`           admin-service              8010
  `/api/v1/notifications/*`   notification-service       8011
  `/api/v1/payments/*`        payment-service            8012

------------------------------------------------------------------------

# Authentication

Public endpoints:

-   POST `/api/v1/auth/login`
-   POST `/api/v1/auth/register`
-   POST `/api/v1/auth/refresh`
-   POST `/api/v1/auth/forgot-password`
-   GET `/health`
-   GET `/ready`

Protected endpoints require:

    Authorization: Bearer <token>

Gateway forwards:

-   X-User-Id
-   X-User-Role
-   X-Request-Id

------------------------------------------------------------------------

# Standard Response

``` json
{
  "success": true,
  "message": "OK",
  "data": {},
  "error": null,
  "request_id": "uuid"
}
```

------------------------------------------------------------------------

# Health Checks

  Endpoint    Purpose
  ----------- -----------
  `/health`   Liveness
  `/ready`    Readiness

------------------------------------------------------------------------

# Environment

See each service's `.env.example`.

------------------------------------------------------------------------

# Tech Stack

-   Python 3.11
-   FastAPI
-   SQLAlchemy 2.0
-   PostgreSQL
-   Redis
-   Alembic
-   Docker
-   Docker Compose

------------------------------------------------------------------------

# Repository Maturity

## Platform

-   Enterprise Foundation ✓
-   AI Runtime ✓
-   Governance ✓
-   Roles ✓
-   Agents ✓
-   Orchestration ✓
-   Registry ✓
-   Context Engine ✓
-   Memory ✓
-   RAG ✓
-   Workflows ✓
-   Templates ✓
-   Evaluation ✓

## Enterprise Engineering

-   Enterprise Constitution ✓
-   Repository Governance ✓
-   Architecture Governance ✓
-   Product Governance ✓
-   Documentation Standards ✓
-   Knowledge Platform ◐
-   Repository Rationalisation ◐
-   Enterprise Operating System ◐

## Status

**Architecture:** Frozen

**Implementation:** Ready

**Repository Evolution:** Active

**Knowledge Platform:** In Progress

**AI Engineering:** Constitution Driven
