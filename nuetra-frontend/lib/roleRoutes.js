const ROLE_ROUTES_MAP = {
  consultant: '/dashboard/provider',
  provider: '/dashboard/provider',
  dietician: '/dashboard/provider',
  senior_consultant: '/dashboard/senior-consultant',
  admin: '/dashboard/admin',
  mentor: '/dashboard/team-lead',
  team_lead: '/dashboard/team-lead',
  organization_admin: '/dashboard/corporate-admin',
  corporate_admin: '/dashboard/corporate-admin',
  corporate_client: '/dashboard/corporate-admin',
  superuser: '/dashboard/owner',
  platform_owner: '/dashboard/owner',
  team_member: '/dashboard/provider',
  member: '/dashboard/provider',
};

export function getDashboardPathForRole(role, fallback = '/dashboard/provider') {
  if (!role) return fallback;
  return ROLE_ROUTES_MAP[String(role).toLowerCase()] || fallback;
}

export default ROLE_ROUTES_MAP;
