# DATA MODEL

Core Entities

Organisation
User
Role
Permission
Invitation
Client
Assessment
Appointment
NutritionPlan
WellnessPlan
Task
Notification
AuditLog

Relationships
Organisation -> Users
User -> Roles
Consultant -> Clients
Client -> Assessments
Assessment -> Wellness Plan
