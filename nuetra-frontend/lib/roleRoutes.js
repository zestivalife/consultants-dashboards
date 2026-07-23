const ROLE_ROUTES_MAP = {
  practitioner: '/dashboard/practitioner',
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
  employee: '/dashboard/team-member',
  superuser: '/dashboard/owner',
  super_admin: '/dashboard/owner',
  platform_owner: '/dashboard/owner',
  team_member: '/dashboard/team-member',
  member: '/dashboard/team-member',
};

export const DELIVERY_WORKSPACE_ROLES = [
  'practitioner',
  'consultant',
  'provider',
  'dietician',
  'team_member',
  'member',
  'employee',
  'senior_consultant',
  'admin',
  'superuser',
  'super_admin',
  'platform_owner',
];

export const MENTOR_WORKSPACE_ROLES = ['mentor', 'team_lead', 'admin', 'superuser', 'super_admin', 'platform_owner'];
export const ORGANIZATION_WORKSPACE_ROLES = [
  'organization_admin',
  'corporate_admin',
  'corporate_client',
  'admin',
  'superuser',
  'super_admin',
  'platform_owner',
];
export const ADMIN_WORKSPACE_ROLES = ['admin', 'superuser', 'super_admin', 'platform_owner'];

export function getDashboardPathForRole(role, fallback = '/dashboard/provider') {
  const roleKey = getRoleKey(role);
  if (!roleKey) return fallback;
  return ROLE_ROUTES_MAP[roleKey] || fallback;
}

export function getRoleKey(role) {
  if (!role) return '';
  const rawRole = typeof role === 'string' ? role : role.name || role.key || role.slug || role.id || '';
  return String(rawRole).trim().toLowerCase().replace(/[\s-]+/g, '_');
}

export function isRoleAllowed(role, allowedRoles = []) {
  if (!allowedRoles.length) return true;
  const roleKey = getRoleKey(role);
  return allowedRoles.map(getRoleKey).includes(roleKey);
}

export default ROLE_ROUTES_MAP;
