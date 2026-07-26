
# CODEX.md
Version: 1.0
Status: ACTIVE

# Purpose
This file is the master instruction loaded before every Codex implementation task.

## Primary Objective
Build a world-class Consultant Platform for Nuetra & FitEatsy.

The repository exists to support the product. Do not optimise the repository at the expense of product delivery.

---

# Engineering Priorities

1. Correctness
2. Simplicity
3. Maintainability
4. Performance
5. Security
6. Documentation

---

# Required Reading Order

Before implementing any task, load only:

1. .ai/PROJECT_STATE.md
2. .ai/ACTIVE_MODULE.md
3. .ai/FILE_MAP.md
4. Relevant PRD
5. Relevant Technical Design
6. Relevant API specification

Do not scan the entire repository unless explicitly instructed.

---

# Context Optimisation Rules

- Read only files required for the current task.
- Never analyse unrelated modules.
- Reuse existing components before creating new ones.
- Prefer modifying existing code over duplication.

---

# Implementation Workflow

1. Understand the task.
2. Identify affected modules.
3. Read only required files.
4. Produce an implementation plan.
5. Implement.
6. Add/Update tests.
7. Verify.
8. Report completion.

---

# Git Workflow

- Work on the requested branch.
- Keep commits atomic.
- Use meaningful commit messages.
- Never rewrite published history unless instructed.

Commit format:

type(scope): summary

Examples:

feat(auth): add invitation acceptance
fix(rbac): resolve permission inheritance
docs(api): update onboarding endpoints

---

# Coding Standards

- Follow existing project conventions.
- Keep functions focused.
- Avoid deep nesting.
- Remove dead code.
- Prefer composition over duplication.

---

# API Rules

- REST-first.
- Version endpoints.
- Validate inputs.
- Return consistent error models.
- Never break existing contracts without approval.

---

# Database Rules

- Use migrations.
- Never modify production schema manually.
- Preserve referential integrity.
- Index searchable fields.

---

# Security Rules

- Validate all input.
- Enforce RBAC.
- Never expose secrets.
- Protect PII.
- Audit privileged operations.

---

# Testing Requirements

Every completed feature should include:

- Unit tests
- Integration tests (where applicable)
- Regression verification

---

# Documentation Rules

Update documentation only when implementation changes behaviour.

Update:
- PROJECT_STATE.md
- DECISION_LOG.md (if architecture changes)
- API documentation (if endpoints change)

---

# Completion Checklist

Before marking a task complete:

- Build passes
- Tests pass
- No obvious regressions
- Documentation updated
- Acceptance criteria satisfied

---

# Standard Completion Report

## Summary
## Files Modified
## Tests
## Risks
## Next Recommended Task

---

# Never Do

- Rewrite the repository unnecessarily.
- Rename modules without approval.
- Duplicate business logic.
- Ignore coding standards.
- Modify protected files listed in DO_NOT_TOUCH.md.

---

# Guiding Principle

Spend engineering effort on building the Consultant Platform.
Minimise context usage.
Maximise implementation quality.
