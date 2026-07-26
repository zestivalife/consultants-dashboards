
# CONSULTANT_PLATFORM_PRODUCT_BIBLE.md

Version: 1.0
Status: FOUNDATION

# 1. Vision
Build a world-class Consultant Platform for Nuetra & FitEatsy that enables consultants, practitioners, mentors and administrators to deliver digital health and wellness services from a single platform.

# 2. Business Goals
- Unified consultant workspace
- Multi-tenant architecture
- Secure role-based access
- AI-assisted workflows
- Scalable enterprise platform

# 3. Personas
- Super Admin
- Corporate Admin
- Consultant
- Practitioner
- Mentor
- Client

# 4. Core Modules
## Foundation
- Authentication
- Organisation Management
- User Management
- Invitations
- Profile Management
- RBAC
- Notifications
- Audit Logs

## Consultant
- Dashboard
- Calendar
- Tasks
- Clients
- Appointments
- Assessments
- Nutrition
- Wellness Plans
- Documents
- Messages

## Administration
- Organisations
- Users
- Permissions
- Reports
- Settings

# 5. User Journeys
1. Organisation onboarding
2. Invite consultant
3. User activation
4. Login
5. Dashboard
6. Client onboarding
7. Assessment
8. Care plan
9. Follow-up
10. Reporting

# 6. RBAC
- Super Admin
- Corporate Admin
- Consultant
- Practitioner
- Mentor
- Client

Every module must define:
- Create
- Read
- Update
- Delete
- Approve
- Export

# 7. Navigation
- Dashboard
- Clients
- Appointments
- Assessments
- Nutrition
- Wellness Plans
- Tasks
- Reports
- Settings

# 8. High-Level Data Model
Core entities:
- Organisation
- User
- Role
- Permission
- Client
- Appointment
- Assessment
- Nutrition Plan
- Wellness Plan
- Task
- Notification
- Audit Log

# 9. API Domains
/api/v1/auth
/api/v1/users
/api/v1/roles
/api/v1/organisations
/api/v1/clients
/api/v1/appointments
/api/v1/assessments
/api/v1/nutrition
/api/v1/wellness
/api/v1/tasks

# 10. AI Capabilities
- Assessment summaries
- Recommendation engine
- Nutrition suggestions
- Follow-up reminders
- Smart search
- Document summarisation

# 11. Integrations
- Email
- WhatsApp
- SMS
- Payment Gateway
- Calendar
- Health Connect
- Wearables

# 12. Non-Functional Requirements
- Enterprise security
- Auditability
- High availability
- Performance
- Accessibility
- Scalability

# 13. Milestones
M1 Identity & Access
M2 Consultant Management
M3 Client Management
M4 Assessments
M5 Appointments
M6 Nutrition
M7 Wellness Plans
M8 Reports
M9 AI
M10 Enterprise Administration

# 14. Success Criteria
- Modular architecture
- Production-ready APIs
- Consistent UX
- Secure RBAC
- Comprehensive audit logging
- Enterprise-grade quality
