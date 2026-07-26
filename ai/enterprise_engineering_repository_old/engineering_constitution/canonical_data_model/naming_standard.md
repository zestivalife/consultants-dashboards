# Enterprise AI Operating System (EAIOS)

# Naming Standard

| Attribute | Value |
|-----------|-------|
| Document ID | EC-CDM-011 |
| Version | 1.0.0 |
| Status | APPROVED |
| Classification | Enterprise Engineering Standard |
| Owner | Enterprise Architecture Office |
| Priority | P1 |
| Lifecycle | Living Document |

---

# 1. Purpose

## 1.1 Objective

This standard defines the canonical naming conventions for all business, technical and operational artefacts within the Enterprise AI Operating System (EAIOS).

The objective is to ensure that every artefact is:

- Consistent
- Unambiguous
- Human-readable
- Machine-readable
- Discoverable
- Technology Neutral

---

# 2. Scope

This standard applies to:

- Business Domains
- Canonical Entities
- Attributes
- Value Objects
- Relationships
- APIs
- Services
- Events
- Message Topics
- Databases
- Tables
- Columns
- Indexes
- Constraints
- Files
- Documents
- Repositories
- Source Code
- AI Agents
- AI Workflows
- Prompts
- Embeddings
- Environment Variables
- Configuration Keys
- Metrics
- Logs
- Dashboards
- Feature Flags

---

# 3. Naming Principles

Names SHALL be:

- Business-oriented
- Descriptive
- Stable
- Concise
- Unique within scope
- Technology independent
- Free from unnecessary abbreviations
- Free from implementation details

---

# 4. Canonical Naming Hierarchy

```
Business Domain

↓

Capability

↓

Entity

↓

Attribute

↓

Relationship

↓

API

↓

Service

↓

Runtime Component
```

Each level SHALL inherit terminology from its parent.

---

# 5. General Rules

Names SHALL:

- Use singular nouns for entities.
- Use plural nouns only for collections.
- Avoid acronyms unless defined in the Engineering Glossary.
- Avoid vendor names.
- Avoid version numbers.
- Avoid temporary terminology.

---

# 6. Business Domains

Business domains SHALL use Title Case.

Examples

```
Identity

Clinical Services

Corporate Wellness

Nutrition

Billing

Knowledge Management
```

---

# 7. Canonical Entities

Entity names SHALL use singular nouns.

Examples

```
Patient

Organisation

Assessment

Consultant

Invoice

Notification
```

The following SHALL NOT be used.

```
Patients

TblPatient

PatientMaster

PatientData
```

---

# 8. Attributes

Attributes SHALL use lower_snake_case.

Examples

```
first_name

last_name

date_of_birth

email_address

tenant_identifier

created_timestamp
```

---

# 9. Value Objects

Value Objects SHALL use PascalCase.

Examples

```
PostalAddress

Money

Measurement

GeoLocation

ContactInformation
```

---

# 10. Relationships

Relationship names SHALL use verbs.

Examples

```
belongs_to

assigned_to

reports_to

contains

owns

references
```

---

# 11. APIs

API resources SHALL use plural nouns.

Examples

```
/patients

/appointments

/consultants

/notifications
```

Actions SHALL use verbs only when necessary.

Examples

```
POST /appointments

POST /appointments/{id}/cancel

POST /users/{id}/activate
```

---

# 12. Services

Service names SHALL end with "-service".

Examples

```
identity-service

notification-service

assessment-service

knowledge-service

billing-service
```

---

# 13. Events

Events SHALL use the format:

```
<Entity><PastTenseVerb>
```

Examples

```
PatientCreated

AssessmentCompleted

InvoiceIssued

ConsultantInvited

UserActivated
```

---

# 14. Event Topics

Topics SHALL use lower_snake_case.

Examples

```
patient_created

assessment_completed

invoice_issued
```

---

# 15. Database Objects

## Tables

Plural lower_snake_case.

Examples

```
patients

appointments

consultants

assessment_results
```

---

## Columns

Lower snake_case.

Examples

```
patient_identifier

created_timestamp

status

version
```

---

## Primary Keys

```
patient_identifier

organisation_identifier

invoice_identifier
```

Generic names such as `id` SHALL NOT be used in canonical schemas.

---

## Foreign Keys

```
patient_identifier

organisation_identifier

appointment_identifier
```

Foreign key names SHALL match the referenced primary key.

---

# 16. Indexes

Indexes SHALL follow:

```
idx_<table>_<column>

Example

idx_patients_email_address
```

---

# 17. Constraints

Primary Key

```
pk_patients
```

Foreign Key

```
fk_appointments_patients
```

Unique

```
uk_users_email_address
```

Check

```
chk_invoice_total
```

---

# 18. Files

Engineering documents SHALL use lower_snake_case.

Examples

```
api_standard.md

runtime_standard.md

security_policy.md
```

---

# 19. Git Repositories

Repositories SHALL use lower-kebab-case.

Examples

```
identity-service

knowledge-platform

api-gateway

event-router
```

---

# 20. Environment Variables

Environment variables SHALL use UPPER_SNAKE_CASE.

Examples

```
DATABASE_URL

JWT_SECRET

REDIS_HOST

AI_MODEL_PROVIDER
```

---

# 21. Configuration Keys

Configuration keys SHALL use lower_snake_case.

Examples

```
session_timeout

default_locale

token_expiry

retry_interval
```

---

# 22. AI Artefacts

AI Agents

```
ClinicalAssessmentAgent

NutritionRecommendationAgent

KnowledgeSearchAgent
```

Prompt Templates

```
clinical_assessment_prompt

nutrition_summary_prompt
```

Embedding Collections

```
clinical_documents

wellness_articles

knowledge_base
```

---

# 23. Metrics

Metrics SHALL use dot notation.

Examples

```
api.requests.total

authentication.failures

database.query.duration

ai.inference.latency
```

---

# 24. Logs

Log fields SHALL use lower_snake_case.

Examples

```
tenant_identifier

request_identifier

trace_identifier

service_name

user_identifier
```

---

# 25. Feature Flags

Feature flags SHALL use lower_snake_case.

Examples

```
enable_ai_assistant

enable_new_dashboard

enable_sso
```

---

# 26. Reserved Words

The following SHALL NOT be used as canonical names.

```
data

master

temp

new

old

test

object

item

record

misc

general
```

---

# 27. Anti-Patterns

The following are prohibited.

- Mixed naming conventions.
- Language-specific abbreviations.
- Vendor prefixes.
- Table prefixes such as `tbl_`.
- Hungarian notation.
- Random acronyms.
- Temporary suffixes.
- Spaces in identifiers.

---

# 28. Compliance

Compliance SHALL verify:

- Correct naming convention
- Canonical terminology
- Uniqueness
- Reserved word avoidance
- Consistency across related artefacts
- Cross-reference integrity

Naming violations SHALL be corrected before approval.

---

# 29. References

## Normative

- engineering_glossary.md
- canonical_data_model_standard.md
- identifier_standard.md
- metadata_standard.md

## Informative

- ISO/IEC 11179
- RFC 3986
- RFC 9562

---

# 30. Revision History

| Version | Date | Author | Description |
|----------|------|--------|-------------|
| 1.0.0 | YYYY-MM-DD | Enterprise Architecture Office | Initial release |
