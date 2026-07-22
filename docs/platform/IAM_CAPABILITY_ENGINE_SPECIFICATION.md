# IAM_CAPABILITY_ENGINE_SPECIFICATION.md

Version: 1.0
Status: APPROVED
Lifecycle: ACTIVE
Owner: Enterprise Architecture
Applies To: Entire Zestiva One Platform

---

# 1. PURPOSE

This specification defines the Enterprise Identity and Access Management (IAM) architecture for the Zestiva One Platform.

It establishes the single source of truth for:

- Identity
- Authentication
- Authorization
- Capability Resolution
- Permission Resolution
- Product Access
- Organization Access
- Department Access
- Dashboard Resolution
- Navigation Resolution
- API Authorization
- Feature Visibility

All applications, APIs, services, gateways and frontends shall comply with this specification.

---

# 2. DESIGN PRINCIPLES

The IAM platform shall be:

- Identity-driven
- Capability-based
- Context-aware
- Multi-tenant
- Product-aware
- Secure
- Extensible
- Auditable
- Backward compatible

Authorization decisions shall never rely solely on role names.

---

# 3. IDENTITY MODEL

Every authenticated user represents an Identity.

Identity is permanent.

Permissions are contextual.

Identity contains:

- Identity ID
- Person
- Account
- Status
- Authentication Credentials
- Security Profile

Identity does not directly determine permissions.

---

# 4. ACCESS MODEL

Authorization shall be resolved using:

Identity

↓

Organization

↓

Department

↓

Product Assignment

↓

Package Assignment

↓

Role Assignment

↓

Capability Bundle

↓

Permission Set

↓

Feature Flags

↓

Navigation

↓

Routes

↓

Dashboard

↓

Authorized Experience

---

# 5. USER LIFECYCLE

Administrator creates user

↓

Temporary Password Generated

↓

User Activated

↓

Password Change Required

↓

Identity Established

↓

Capabilities Calculated

↓

Dashboard Assigned

↓

Navigation Built

↓

Normal Platform Usage

---

# 6. ORGANIZATION MODEL

A user may belong to one or more organizations.

Organization determines:

- Tenant
- Business Rules
- Available Products
- Policies
- Data Isolation

Organization membership shall be validated before permission resolution.

---

# 7. DEPARTMENT MODEL

Departments further scope access.

Examples:

- HR
- Sales
- Operations
- Clinical
- Nutrition
- Wellness

Department membership may refine permissions but shall not override tenant isolation.

---

# 8. PRODUCT MODEL

A user may have access to multiple products.

Examples:

- FitEatsy
- Corporate Wellness
- Nutrition
- Assessment
- Analytics
- Future Products

Product assignment determines available modules and capabilities.

---

# 9. PACKAGE MODEL

Packages define commercial entitlements.

Examples:

- Free
- Starter
- Professional
- Enterprise

Packages influence feature availability but do not replace permissions.

---

# 10. ROLE MODEL

Roles represent business responsibilities.

Examples:

- Platform Owner
- Corporate Admin
- Consultant
- Practitioner
- Mentor
- Employee
- Future Roles

Roles are assigned through administration.

Roles shall never directly control UI behaviour.

---

# 11. CAPABILITY BUNDLES

Capabilities represent what a user can do.

Examples:

people.read

people.write

assessment.create

assessment.review

nutrition.manage

reports.view

platform.admin

Capabilities are reusable across products.

---

# 12. PERMISSION ENGINE

Permission resolution combines:

Identity

Organization

Department

Product

Package

Role

Capability Bundle

Feature Flags

The output is a unified Permission Context.

---

# 13. PERMISSION CONTEXT

The Permission Context is generated once after authentication.

It contains:

- Visible Modules
- Allowed APIs
- Navigation
- Sidebar
- Dashboards
- Feature Visibility
- Actions
- Restrictions

All platform components consume this context.

---

# 14. AUTHENTICATION

Authentication verifies identity.

Supported mechanisms:

- Username / Password
- JWT
- Refresh Tokens
- Future SSO
- Future OAuth
- Future MFA

Authentication never determines authorization.

---

# 15. AUTHORIZATION

Authorization evaluates:

Permission Context

Requested Resource

Requested Action

Current Tenant

Product Context

If permitted:

ALLOW

Otherwise:

DENY

---

# 16. DASHBOARD RESOLUTION

Dashboard shall be resolved using:

Identity

Status

Organization

Product

Capability Bundle

Permissions

Feature Flags

Role alone shall never determine the landing page.

---

# 17. NAVIGATION RESOLUTION

Navigation shall be generated dynamically from the Permission Context.

Never hardcode menu visibility based on role names.

---

# 18. ROUTE GUARDS

Every protected route validates:

Authentication

↓

Permission Context

↓

Capability

↓

Resource Access

↓

Tenant

↓

Product

↓

Route

Unauthorized requests return Access Denied.

---

# 19. API AUTHORIZATION

Every protected API validates:

JWT

↓

Identity

↓

Tenant

↓

Permission Context

↓

Capability

↓

Requested Action

↓

Business Rules

Only then execute the request.

---

# 20. FEATURE FLAGS

Feature flags may enable or disable:

Modules

Experiments

Beta Features

Customer-specific Features

Feature flags do not grant permissions.

---

# 21. MULTI-TENANT ISOLATION

Every request must validate:

Tenant

Organization

Ownership

Data Scope

No tenant shall access another tenant's data.

---

# 22. SESSION MANAGEMENT

Sessions include:

- Login Time
- Expiration
- Refresh Token
- Device
- IP
- Audit Information

Sessions shall be revocable.

---

# 23. AUDIT

Every security event shall be audited.

Examples:

Login

Logout

Password Change

Role Change

Permission Change

Product Assignment

Organization Assignment

Failed Authorization

Administrative Actions

---

# 24. SECURITY PRINCIPLES

The IAM platform follows:

- Principle of Least Privilege
- Zero Trust
- Defense in Depth
- Explicit Authorization
- Secure Defaults

---

# 25. FUTURE EXTENSIBILITY

The architecture shall support:

- New Products
- New Organizations
- New Departments
- New Roles
- New Capability Bundles
- External Identity Providers
- Multi-region Deployment
- Enterprise Federation

No redesign should be required when introducing new personas or products.

---

# 26. ACCEPTANCE CRITERIA

The IAM platform is compliant when:

✓ Authentication succeeds

✓ Permission Context generated

✓ Dashboard resolved

✓ Navigation resolved

✓ APIs protected

✓ Tenant isolation verified

✓ Products scoped correctly

✓ Packages enforced

✓ Capabilities applied

✓ Audit recorded

✓ Security policies satisfied

---

# 27. CONTINUOUS IMPROVEMENT

The IAM platform shall evolve to improve:

- Security
- Flexibility
- Scalability
- Observability
- Developer Experience
- Administrative Experience
- Enterprise Readiness

Changes must preserve backward compatibility wherever practical.
