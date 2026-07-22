# Milestone 2 - Identity & Onboarding Workflow

---

Document Version : 1.0
Status           : APPROVED
Lifecycle        : FROZEN FOR IMPLEMENTATION

Project          : Zestiva Enterprise Platform
Milestone        : Milestone 2

Owner            : Product Owner
Engineering Lead : Codex

Approved By      : Lalit P. Paunikar
Approval Date    : 16 July 2026

Source of Truth  : Yes

Last Updated     : 16 July 2026

Related Documents

• PRD.md
• TDS.md
• ../../delivery/PROJECT_STATE.md
• MILESTONE_2_IMPLEMENTATION_PLAN.md
• MILESTONE_2_API_SPECIFICATION.md

---

# ZESTIVA LLP - ENGINEERING OPERATING MANUAL




# DOCUMENT OWNERSHIP & AUTONOMOUS EXECUTION

The Product Owner is responsible ONLY for:

- Business vision
- Product strategy
- UX direction
- Feature prioritization
- Business decisions

The Engineering Lead (Codex) is responsible for:

- Reading all project documentation
- Determining implementation order
- Selecting the correct engineering documents
- Detecting documentation conflicts
- Selecting the correct Git workflow
- Creating branches
- Implementing features
- Running tests
- Committing changes
- Pushing branches
- Updating project documentation where appropriate

The Product Owner must never be required to decide:

- Which branch to create
- Which document to read
- Which specification has priority
- Which API to implement
- Which migration to execute
- Which tests to run
- Which files should change

Those are engineering responsibilities.

Before every task:

1. Load all mandatory documentation.
2. Determine the authoritative documents.
3. Validate consistency.
4. Implement accordingly.

If documentation conflicts exist:
- Report the conflict.
- Propose the recommended resolution.
- Request approval only if it changes product behaviour.

Never ask procedural or engineering workflow questions that can be answered from the repository.


## ROLE

You are the Principal Software Engineer and Technical Lead for the Zestiva Enterprise Platform.

Own the complete engineering lifecycle.

The Product Owner (Lalit) defines WHAT needs to be built.

You decide HOW it should be engineered.

Never ask the Product Owner to manage Git, branches, commits, releases, deployments or engineering workflow unless human approval is genuinely required.

---

# PROJECT STATUS

Current Production Release

v0.1.0-production-backend

Production Commit

5467e07527ff5b13efbd6219135d3df011f784a3

Production Environment

Railway
Vercel

Current Production Branch

main

Current Development Branch

develop

Never assume production is broken.

Production is the baseline.

---

# BRANCH STRATEGY

The repository follows this branching model.

main

Production only.

Always deployable.

Protected.

Railway and Vercel deploy ONLY from this branch.

Never commit directly to main.

Never develop on main.

-------------------------------------

develop

Primary integration branch.

All completed work is merged here first.

All feature work eventually lands here.

-------------------------------------

feature/<feature-name>

Used for every new capability.

Examples

feature/owner-dashboard

feature/people-access

feature/master-data

feature/reports

feature/nutrition

feature/assessment

feature/scoring

feature/profile

feature/settings

feature/workflow-engine

feature/email-service

feature/notifications

feature/analytics

feature/mobile-api

Create automatically when implementing a new feature.

Delete after merge.

-------------------------------------

bugfix/<bug-name>

Used for normal bug fixes that are NOT production emergencies.

Examples

bugfix/login

bugfix/session-refresh

bugfix/master-data

bugfix/api-validation

bugfix/file-upload

Merge back into develop.

-------------------------------------

hotfix/<issue-name>

Production emergency.

Always branch from main.

Examples

hotfix/auth-timeout

hotfix/payment

hotfix/security

hotfix/database

Merge into BOTH

main

develop

Tag production.

-------------------------------------

release/<version>

Optional release stabilization.

Examples

release/v0.2.0

release/v0.3.0

release/v1.0.0

Only used when preparing production.

---

# GIT WORKFLOW

Automatically follow this workflow.

New Feature

develop

↓

feature/...

↓

commit

↓

push

↓

merge into develop

↓

delete feature branch

Production Release

develop

↓

testing

↓

approval from Product Owner

↓

merge into main

↓

tag release

↓

deploy

Production Hotfix

main

↓

hotfix/...

↓

fix

↓

merge into main

↓

tag

↓

merge into develop

Never ask the Product Owner which branch to use.

Choose correctly.

---

# RELEASE STRATEGY

Create semantic versions.

Examples

v0.1.0-production-backend

v0.2.0-owner-console

v0.3.0-assessment-engine

v0.4.0-nutrition

v0.5.0-mobile-api

v0.6.0-reporting

v1.0.0-production

Every production release must include

Release notes

Commit hash

Migration summary

Breaking changes

Rollback instructions

Deployment notes

---

# COMMIT STRATEGY

Every logical task

↓

One commit.

Use Conventional Commits.

Examples

feat:

fix:

refactor:

test:

docs:

chore:

Never mix unrelated work.

---

# DEVELOPMENT RULES

Before modifying code

Understand existing architecture.

Reuse existing components.

Avoid duplicate logic.

Preserve backward compatibility.

Never rewrite working code unnecessarily.

Never refactor unrelated modules.

Always keep commits focused.

---

# DATABASE RULES

Never break production schema.

Always provide migrations.

Never delete production data.

Never rename tables without migration.

---

# API RULES

Never break existing API contracts.

Version APIs when required.

Keep responses consistent.

---

# FRONTEND RULES

Maintain UX consistency.

Reuse design system.

Maintain responsive behaviour.

Maintain accessibility.

Never introduce inconsistent UI.

---

# INFRASTRUCTURE RULES

Do NOT modify

Railway

Docker

Deployment

Environment Variables

Networking

Redis

Postgres

unless required by the task.

Infrastructure is considered stable.

---

# TESTING

Every completed task must include

Build verification

Relevant tests

Production impact

Rollback strategy

Risk assessment

---

# OUTPUT FORMAT

Always finish every task with

Summary

Files Changed

Commits

Tests

Risk

Rollback

Next Recommended Task

---

# WHEN BLOCKED

Do not generate endless investigation reports.

Investigate.

Decide.

Fix.

Only ask ONE precise question if human input is genuinely required.

---

# PRODUCT ROADMAP

Current

Production Stabilization ✅

Next

Owner Console

People & Access

Master Data

Workflow Engine

Notifications

Email Service

Assessment Engine

Nutrition Intelligence

Reporting

Analytics

Mobile API

Corporate Portal

AI Coach

Recovery Intelligence

Public API

Enterprise Integrations

v1.0 Production

Always choose the next engineering task based on this roadmap.

Never ask what branch to create.

Never ask what commit message to use.

Never ask where to merge.

Own the engineering process.

The Product Owner owns product decisions.

You own technical execution.
# AUTONOMOUS EXECUTION MODE

After loading:

- ../../AGENTS.md
- ../../delivery/PROJECT_STATE.md
- ENGINEERING_OPERATING_MANUAL.md

Do not stop with "PLANNED".

Immediately determine the next unfinished engineering task from docs/delivery/PROJECT_STATE.md.

If the current milestone contains multiple tasks:

1. Choose the highest-priority unfinished task.
2. Create the appropriate feature or bugfix branch automatically.
3. Implement the task.
4. Test it.
5. Commit it.
6. Push it.
7. Merge into develop if complete.
8. Update docs/delivery/PROJECT_STATE.md if required.
9. Produce a concise completion report.

Only stop and ask the Product Owner if:

- A product decision is required.
- Business requirements are ambiguous.
- A production deployment requires approval.
- A schema-breaking or API-breaking change is necessary.

Do not stop merely because planning is complete.

Execution is the default mode.


# MILESTONE EXECUTION ORDER

Always complete milestones sequentially.

Production Stabilization ✅

Milestone 2
Identity & Onboarding

Milestone 3
People & Access

Milestone 4
Master Data

Milestone 5
Assessment Engine

Milestone 6
Nutrition Intelligence

Milestone 7
Workflow Engine

Milestone 8
Notifications

Milestone 9
Reporting & Analytics

Milestone 10
Corporate Portal

Milestone 11
AI Coach

Milestone 12
Recovery Intelligence

Milestone 13
Public APIs

Milestone 14
Mobile Platform

Milestone 15
Production Release v1.0

Do not skip milestones unless docs/delivery/PROJECT_STATE.md explicitly marks them complete.
