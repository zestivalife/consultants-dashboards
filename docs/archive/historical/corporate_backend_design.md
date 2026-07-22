# Corporate Admin Backend Design

## 1. Database Schema
The database models must support organizations, their teams, employees, and sessions.

**`User` (Existing)**
- Added: `company_id` (UUID, Foreign Key) pointing to another `User` record that has the Corporate Admin role.
- Added: `status` (Active, Invited, Suspended)
- Note: Corporate Admins manage users whose `company_id` matches the admin's `id`.

**`Team` (Existing)**
- `id`: UUID
- `name`: String
- `description`: Text
- `company_id`: UUID
- `lead_id`: UUID
- `created_at`: DateTime

**`SessionRequest` (Existing)**
- `id`: UUID
- `title`: String
- `type`: String (MINDFULNESS, PHYSICAL, etc)
- `mode`: String (ONLINE / OFFLINE)
- `scheduled_at`: DateTime
- `target_audience`: expected participants
- `team_id`: UUID (optional, to restrict session to a team)
- `company_id`: UUID
- `status`: String

**New `Metric` (or Engagement/Wellness log)**
- To remove hardcoding in `/dashboard/stats` and `/analytics`, we need a way to track engagement. 
- *Alternatively, for the scope of the Corporate Admin API, `User` or `Team` could have a `computed_engagement_score` or we can aggregate child records from a `Metric` table.*

## 2. API Routes (FastAPI under `/corporate-admin`)

- **GET `/dashboard/stats`**
  Queries DB to count `total_employees`, `active_teams`, `sessions_completed`. Computes average wellness scores by aggregating user wellness logs belonging to the `company_id`.

- **POST `/teams` / GET `/teams`**
  Manage structural groups of users. For `GET /teams`, runs a `GROUP BY` to return `total_members` (Count of users with matching `team_id`).

- **POST `/employees` / POST `/employees/bulk`**
  Handles user insertion with a generated temporary password and triggers `smtplib` to send the invite email. Automatically sets `company_id` to the calling Admin's ID.

- **GET `/employees`**
  Lists users filtered by `company_id`.

- **POST `/sessions` / GET `/sessions`**
  Allows Corporate Admins to create "Company Wellness Sessions" and view their execution status.

## 3. Integration Points
- Frontend automatically injects JWT Bearer tokens to hit these endpoints via `apiRequest`.
- `auth-service` utilizes the Role checking dependency to assert roles such as `corporate_admin`.
- Background tasks (Celery/RQ) could be implemented for "bulk email invites" so the API does not block on `smtplib` I/O.
- Engagement scores are calculated either via synchronous aggregate queries or an asynchronous cron job building a materialized view.
