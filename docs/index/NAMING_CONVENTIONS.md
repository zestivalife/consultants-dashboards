Document ID: RIA-NAMING-CONVENTIONS
Title: Naming Conventions
Owner: Zestiva Engineering
Status: ACTIVE
Lifecycle: ACTIVE
Scope: Repository documentation naming
Applies To: All documentation files
Last Updated: 2026-07-22
Supersedes: None
Depends On: REPOSITORY_ARCHITECTURE.md
Related Documents: docs/index/DOCUMENT_REGISTRY.md, DOCUMENT_CLASSIFICATION.md

# Naming Conventions

## Approved Names

- `README.md` for folder indexes.
- `*_ARCHITECTURE.md` for architectural documents.
- `*_SPECIFICATION.md` for implementable specifications.
- `*_GUIDELINES.md` for guidance.
- `*_POLICY.md` for mandatory rules.
- `*_RUNBOOK.md` for operational procedures.
- `*_CHECKLIST.md` for verification gates.
- `ADR-XXXX-title.md` for Architecture Decision Records.

## Forbidden Names

- `copy.md`
- temporary filenames
- duplicate PRDs
- duplicate TDS files
- unclear one-off notes at repository root

## Case Standard

Use uppercase snake case for enterprise documents:

`PEOPLE_ACCESS_SPECIFICATION.md`

Use numbered ADR IDs:

`ADR-0001-single-application-architecture.md`

