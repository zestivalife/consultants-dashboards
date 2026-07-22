# Critical Fixes Applied - Database & Frontend Issues

## Summary of Issues Fixed

### 1. ✅ Database Schema Missing Tables & Columns
**Problem**: 
- `relation "user_profiles" does not exist` - Profile service
- `column users.first_name does not exist` - Auth service

**Root Cause**: 
Database migrations have not been executed to create/update the schema.

**Solution**: 
Run Alembic migrations on each microservice to update the database schema.

---

## 2. ✅ Frontend Dashboard Redirect Issues  
**Problem**: 
- Sidebar pages (Privacy Policy, Terms of Service, Profile, Settings) were using inconsistent role mappings
- Some pages used UPPERCASE roles, others used lowercase
- Backend returns lowercase roles (e.g., `admin`, `team_member`, `corporate_admin`)
- Frontend pages were looking for UPPERCASE roles (e.g., `ADMIN`, `TEAM_MEMBER`)

**Solution Applied**:
1. Created unified role routing utility: `/lib/roleRoutes.js`
2. Updated all sidebar pages to use `getDashboardPathForRole()`:
   - `pages/privacy-policy.js` ✓
   - `pages/terms-of-service.js` ✓
   - `pages/profile.js` ✓
   - `pages/settings.js` ✓

**Key Improvements**:
- Centralized role-to-path mapping
- Handles both lowercase and uppercase role names (backward compatible)
- Proper null-checking for missing authUser
- Consistent fallback behavior

---

## 3. ✅ AuthContext Verification
**Status**: Already properly implemented
- AuthContext correctly loads user data on mount
- Provides ROLE_ROUTES mapping for role-based redirection
- Token validation and refresh handling working

---

## How to Apply Fixes

### Step 1: Start Docker Services
```bash
cd /home/vector/projects/nuetra
docker-compose up -d
```

Wait for all services to be healthy:
```bash
docker-compose ps
```

### Step 2: Run Database Migrations

**Option A: Using the migration script (Recommended)**
```bash
chmod +x scripts/run-migrations.sh
./scripts/run-migrations.sh
```

**Option B: Manual migration per service**
```bash
# Auth Service
docker-compose exec -T auth-service alembic upgrade head

# Profile Service  
docker-compose exec -T profile-service alembic upgrade head

# Assessment Service
docker-compose exec -T assessment-service alembic upgrade head

# Scoring Engine Service
docker-compose exec -T scoring-engine-service alembic upgrade head

# Nutrition Service
docker-compose exec -T nutrition-service alembic upgrade head
```

**Option C: Direct database migration (Development)**
```bash
# If running locally without containers
cd services/auth-service
alembic upgrade head

cd ../profile-service
alembic upgrade head

# ... repeat for other services
```

### Step 3: Verify Migrations
```bash
# Check auth-service users table
docker-compose exec -T postgres psql -U nuetra -d nuetra_auth -c "\\d users;"

# Check profile-service user_profiles table
docker-compose exec -T postgres psql -U nuetra -d nuetra_profile -c "\\d user_profiles;"
```

### Step 4: Test Frontend
1. Clear browser cache/cookies
2. Login as a corporate client user
3. Navigate to Profile page → should see "Back to Dashboard" link
4. Click the link → should redirect to corporate admin dashboard
5. Test other sidebar pages (Privacy Policy, Terms of Service, Settings)

---

## Role Mapping Reference

The new `getDashboardPathForRole()` function handles these roles (case-insensitive):

```javascript
{
  'superuser'        → '/dashboard/superuser',
  'admin'            → '/dashboard/admin',
  'dietician'        → '/dashboard/provider',
  'provider'         → '/dashboard/provider',
  'corporate_client' → '/dashboard/corporate-admin',
  'corporate_admin'  → '/dashboard/corporate-admin',
  'team_lead'        → '/dashboard/team-lead',
  'team_member'      → '/dashboard/team-member',
  'member'           → '/dashboard/team-member',
}
```

---

## Files Modified

### Frontend Files
1. **Created**: `nuetra-frontend/lib/roleRoutes.js` - Centralized role routing utility
2. **Updated**: `nuetra-frontend/pages/privacy-policy.js`
3. **Updated**: `nuetra-frontend/pages/terms-of-service.js`
4. **Updated**: `nuetra-frontend/pages/profile.js`
5. **Updated**: `nuetra-frontend/pages/settings.js`

### Database Files (No changes needed - already exist)
- `services/auth-service/alembic/versions/` - Contains all migration files
- `services/profile-service/alembic/versions/` - Contains all migration files
- And other services...

---

## Troubleshooting

### Issue: "alembic: command not found"
**Solution**: Ensure the service container is running and has alembic installed (it's in requirements.txt)

### Issue: "relation does not exist" errors persist after migration
**Solution**: 
1. Check if migrations actually ran: `docker-compose exec -T postgres psql -U nuetra -d nuetra_auth -c "SELECT * FROM alembic_version;"`
2. If alembic_version table is empty, migrations didn't run
3. Verify database URL is correct in service environment variables
4. Check service logs: `docker-compose logs auth-service`

### Issue: "Connection refused" when running migrations
**Solution**: 
1. Ensure PostgreSQL is running: `docker-compose ps postgres`
2. Wait for health check to pass: `docker-compose exec postgres pg_isready`
3. Verify network: `docker network inspect nuetra-net`

### Issue: Frontend still not redirecting correctly  
**Solution**:
1. Clear browser cache and local storage
2. Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
3. Check browser console for errors
4. Verify authUser.role value using DevTools > Console: `localStorage.getItem('token')`
5. Check /auth/me endpoint response in Network tab

---

## Next Steps & Recommendations

1. **Set up automatic migrations on startup**
   - Add migration step to service entrypoint scripts in Dockerfile
   - Or use a dedicated migration sidecar

2. **Add environment-specific role mappings**
   - Consider moving ROLE_ROUTES to environment config for different deployments

3. **Add role-based access control (RBAC) middleware**
   - Validate user roles before rendering sensitive data
   - Add audit logging for role-based actions

4. **Database connection pooling**
   - Implement SQLAlchemy connection pooling for better performance
   - Consider PgBouncer for connection management

5. **Add comprehensive error logging**
   - Implement structured logging in migration scripts
   - Add monitoring for migration health

---

## Questions or Issues?

Check the following:
1. Docker logs: `docker-compose logs [service-name]`
2. Database logs: `docker-compose logs postgres`  
3. Frontend logs: Browser DevTools Console
4. Recent git changes: `git log --oneline -20`
