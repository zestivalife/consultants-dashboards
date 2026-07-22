Document ID: RIA-SOURCE-OF-TRUTH-MATRIX
Title: Source of Truth Matrix
Owner: Zestiva Engineering
Status: ACTIVE
Lifecycle: ACTIVE
Scope: Repository-wide documentation authority
Applies To: All documentation and implementation work
Last Updated: 2026-07-22
Supersedes: None
Depends On: REPOSITORY_ARCHITECTURE.md
Related Documents: docs/index/DOCUMENT_REGISTRY.md, DOCUMENT_CLASSIFICATION.md, OWNERSHIP_MATRIX.md

# Source of Truth Matrix

Every engineering topic must have exactly one canonical home.

| Topic | Canonical Location | Notes |
|---|---|---|
| AI engineering operating contract | `AGENTS.md` | Root-level entry point for AI agents. |
| Repository navigation | `docs/index/` | Registry, ownership, classification, naming, status. |
| Product strategy | `docs/products/zestiva-one-platform/product-bible/` | Business and product authority. |
| Enterprise architecture | `docs/architecture/enterprise/` | Platform-wide architecture. |
| Domain architecture | `docs/architecture/domains/` | Durable domain rules and models. |
| API architecture and standards | `docs/architecture/api/` | API contracts, guidelines, gateway conventions. |
| Data architecture and standards | `docs/architecture/data/` | Database, schema ownership, data governance. |
| Security architecture and standards | `docs/architecture/security/` | IAM, threat models, compliance, secrets, security policy. |
| Platform capabilities | `docs/platform/` | Reusable capability specifications. |
| Product-specific behavior | `docs/products/` | Product-specific docs that reference platform capabilities. |
| Service-specific behavior | `docs/services/` | Service contracts, runbooks, environment, incidents. |
| Operations and runtime | `docs/operations/` | Railway, Vercel, production diagnostics, runbooks. |
| Roadmap and release planning | `docs/delivery/` | Project state, roadmap, release, testing, acceptance. |
| Milestone execution | `docs/milestones/` | Temporary execution docs. |
| Architecture decisions | `docs/adr/` | Approved ADRs. |
| Historical records | `docs/archive/` | Not authoritative. |

## Duplicate Handling

When duplicate documents exist:

1. Identify the canonical document.
2. Preserve non-canonical copies in `docs/archive/duplicates/`.
3. Update references to the canonical document.
4. Do not delete historical content.

