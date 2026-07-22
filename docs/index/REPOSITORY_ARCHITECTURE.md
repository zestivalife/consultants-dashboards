Document ID: RIA-REPOSITORY-ARCHITECTURE
Title: Repository Architecture
Owner: Zestiva Engineering
Status: ACTIVE
Lifecycle: ACTIVE
Scope: Repository-wide information architecture
Applies To: Documentation, services, products, platform capabilities, milestones, and AI agents
Last Updated: 2026-07-22
Supersedes: None
Depends On: AGENTS.md
Related Documents: docs/index/DOCUMENT_REGISTRY.md, SOURCE_OF_TRUTH_MATRIX.md, OWNERSHIP_MATRIX.md, NAMING_CONVENTIONS.md

# Repository Architecture

## Purpose

This document defines the long-term Repository Information Architecture for the Zestiva One Platform.

The repository is designed to scale across multiple products, services, engineering teams, and AI agents while preserving discoverability and governance.

## Root Responsibilities

The repository root is intentionally minimal.

Allowed permanent root files:

- `AGENTS.md`
- `README.md`

Allowed permanent root folders:

- `apps/`
- `services/`
- `packages/`
- `infra/`
- `scripts/`
- `tests/`
- `docs/`

Configuration files may remain at root when required by tooling.

Root must not contain milestone documents, temporary notes, implementation summaries, fix reports, audit notes, or duplicate documentation.

## Documentation Structure

```text
docs/
  index/
  governance/
  architecture/
    enterprise/
    domains/
    api/
    data/
    security/
  platform/
  products/
  services/
  operations/
  delivery/
  milestones/
  adr/
  archive/
```

## Folder Responsibilities

### `docs/index/`

Repository navigation and source-of-truth discovery.

Belongs here:

- Document registry
- Repository architecture
- Source-of-truth matrix
- Ownership matrix
- Status legend
- Naming conventions
- Document classification

Must not contain product specifications, milestone plans, or implementation notes.

### `docs/governance/`

Project-wide engineering rules, policies, quality gates, and operating standards.

Must not contain milestone-specific implementation detail.

### `docs/architecture/`

Enterprise architecture and durable architectural specifications.

Subfolders separate enterprise, domain, API, data, and security architecture.

Must not contain temporary delivery notes or milestone execution plans.

### `docs/platform/`

Reusable platform capability specifications.

Examples:

- Authentication
- RBAC
- Audit
- Notification
- File storage
- People & Access

Products consume platform capabilities; they must not duplicate them.

### `docs/products/`

Product-specific documentation for Nuetra, FitEatsy, and future Zestiva products.

Must not redefine platform-wide capabilities.

### `docs/services/`

Service-level documentation for deployable runtime services.

Each service may contain:

- `README.md`
- `SERVICE_SPECIFICATION.md`
- `API.md`
- `DATA_OWNERSHIP.md`
- `RUNBOOK.md`
- `ENVIRONMENT.md`
- `RELEASE_NOTES.md`
- `INCIDENTS.md`

### `docs/operations/`

Production operations, deployment diagnostics, runbooks, service matrices, incident reports, and operational readiness.

### `docs/delivery/`

Roadmaps, release plans, release engineering, testing strategy, and acceptance checklists.

### `docs/milestones/`

Temporary milestone execution containers.

Milestone documents guide execution but are not permanent architecture.

Durable knowledge discovered during a milestone must be promoted into architecture, platform, domain, governance, or operations before milestone closure.

### `docs/adr/`

Architecture Decision Records.

Any approved architecture decision with long-term impact belongs here.

### `docs/archive/`

Historical, superseded, duplicate, temporary, or investigation documents.

Archived documents are retained for traceability but are not authoritative.

