const WORKSPACE_POLICIES = {
  platformOperations: {
    id: 'platform-operations',
    landingPage: '/dashboard/owner',
    permissionsAny: [
      'audit.view',
      'notifications.manage',
      'packages.manage',
      'services.manage',
      'settings.manage',
      'subscriptions.manage',
    ],
  },
  organizationOperations: {
    id: 'organization-operations',
    landingPage: '/dashboard/corporate-admin',
    permissionsAny: [
      'organizations.manage',
      'users.create',
      'users.edit',
      'users.export',
      'users.invite',
    ],
  },
  careSupervision: {
    id: 'care-supervision',
    landingPage: '/dashboard/team-lead',
    personaMarkers: ['mentor', 'team_lead'],
    permissionsAny: ['reports.view'],
  },
  careDelivery: {
    id: 'care-delivery',
    landingPage: '/dashboard/provider',
    personaMarkers: ['consultant', 'provider', 'dietician', 'senior_consultant'],
    permissionsAny: ['reports.view', 'users.read'],
  },
  memberWorkspace: {
    id: 'member-workspace',
    landingPage: '/dashboard/team-member',
    permissionsAny: [],
  },
};

export const OWNER_ACCESS_POLICY = {
  workspaces: ['platform-operations'],
  permissionsAny: WORKSPACE_POLICIES.platformOperations.permissionsAny,
};

export const ORGANIZATION_ACCESS_POLICY = {
  workspaces: ['platform-operations', 'organization-operations'],
  permissionsAny: [
    ...WORKSPACE_POLICIES.platformOperations.permissionsAny,
    ...WORKSPACE_POLICIES.organizationOperations.permissionsAny,
  ],
};

export const DELIVERY_ACCESS_POLICY = {
  workspaces: ['platform-operations', 'organization-operations', 'care-supervision', 'care-delivery'],
  permissionsAny: ['reports.view', 'users.read'],
};

export const CONSULTANT_ACCESS_POLICY = {
  roles: ['consultant', 'provider', 'dietician', 'senior_consultant'],
  workspaces: ['care-delivery'],
  personaMarkers: WORKSPACE_POLICIES.careDelivery.personaMarkers,
};

export const MEMBER_ACCESS_POLICY = {
  roles: ['practitioner', 'team_member', 'member', 'employee', 'client', 'corporate_client'],
  workspaces: ['member-workspace'],
};

export const MENTOR_ACCESS_POLICY = {
  workspaces: ['platform-operations', 'care-supervision'],
  personaMarkers: ['mentor', 'team_lead'],
  permissionsAny: ['reports.view'],
};

export const ADMIN_ACCESS_POLICY = {
  workspaces: ['platform-operations', 'organization-operations'],
  permissionsAny: [
    ...WORKSPACE_POLICIES.platformOperations.permissionsAny,
    ...WORKSPACE_POLICIES.organizationOperations.permissionsAny,
  ],
};

// Backward-compatible exports for pages still passing legacy role arrays.
export const DELIVERY_WORKSPACE_ROLES = DELIVERY_ACCESS_POLICY;
export const MENTOR_WORKSPACE_ROLES = MENTOR_ACCESS_POLICY;
export const ORGANIZATION_WORKSPACE_ROLES = ORGANIZATION_ACCESS_POLICY;
export const ADMIN_WORKSPACE_ROLES = ADMIN_ACCESS_POLICY;

export function getRoleKey(role) {
  if (!role) return '';
  const rawRole = typeof role === 'string' ? role : role.name || role.key || role.slug || role.id || '';
  return String(rawRole).trim().toLowerCase().replace(/[\s-]+/g, '_');
}

function getAccessProfile(user) {
  return user?.access_profile || user?.accessProfile || null;
}

function unique(values) {
  return Array.from(new Set(values.filter(Boolean)));
}

export function getUserPermissions(user) {
  const profile = getAccessProfile(user);
  return unique([
    ...(user?.permissions || []),
    ...(profile?.permissions || []),
    ...(profile?.capabilities || []),
  ]);
}

function hasAnyPermission(user, permissions = []) {
  if (!permissions.length) return false;
  const permissionSet = new Set(getUserPermissions(user));
  return permissions.some((permission) => permissionSet.has(permission));
}

function hasAllPermissions(user, permissions = []) {
  if (!permissions.length) return true;
  const permissionSet = new Set(getUserPermissions(user));
  return permissions.every((permission) => permissionSet.has(permission));
}

function getWorkspaceFromProfile(user) {
  const workspace = getAccessProfile(user)?.workspace;
  if (!workspace) return null;
  return {
    id: workspace.id,
    label: workspace.label,
    landingPage: workspace.landing_page || workspace.landingPage,
  };
}

function fallbackWorkspaceFromAccess(user) {
  const roleKey = getRoleKey(getAccessProfile(user)?.role || user?.role);
  const hasProduct = Boolean(getAccessProfile(user)?.active_product || getAccessProfile(user)?.activeProduct);

  if (hasAnyPermission(user, WORKSPACE_POLICIES.platformOperations.permissionsAny)) {
    return WORKSPACE_POLICIES.platformOperations;
  }

  if (hasAnyPermission(user, WORKSPACE_POLICIES.organizationOperations.permissionsAny)) {
    return WORKSPACE_POLICIES.organizationOperations;
  }

  if (WORKSPACE_POLICIES.careSupervision.personaMarkers.includes(roleKey)) {
    return WORKSPACE_POLICIES.careSupervision;
  }

  if (MEMBER_ACCESS_POLICY.roles.includes(roleKey)) {
    return WORKSPACE_POLICIES.memberWorkspace;
  }

  if (
    WORKSPACE_POLICIES.careDelivery.personaMarkers.includes(roleKey)
    || (hasProduct && WORKSPACE_POLICIES.careDelivery.personaMarkers.includes(roleKey))
  ) {
    return WORKSPACE_POLICIES.careDelivery;
  }

  return WORKSPACE_POLICIES.memberWorkspace;
}

export function resolveUserWorkspace(user) {
  return getWorkspaceFromProfile(user) || fallbackWorkspaceFromAccess(user);
}

export function getDashboardPathForUser(user, fallback = '/dashboard/team-member') {
  if (!user) return fallback;
  return resolveUserWorkspace(user)?.landingPage || fallback;
}

export function getAccountActionRoute(user) {
  if (!user) return null;
  const action = user.next_action || user.nextAction;
  const actionRoute = action?.route;
  const actionType = String(action?.type || '').toUpperCase();

  if (actionRoute && actionType && actionType !== 'DASHBOARD') {
    return actionRoute;
  }

  if (user.must_change_password) {
    return '/auth/change-temporary-password';
  }

  const status = String(user.status || 'ACTIVE').trim().toUpperCase();
  if (['INVITED', 'FIRST_LOGIN', 'ONBOARDING_IN_PROGRESS', 'PENDING_PROFILE'].includes(status)) {
    return '/profile';
  }
  if (['ONBOARDING_COMPLETED', 'UNDER_REVIEW'].includes(status)) {
    return '/profile';
  }
  if (['APPROVED', 'PASSWORD_CHANGE_REQUIRED'].includes(status)) {
    return '/auth/change-temporary-password';
  }
  if (status && status !== 'ACTIVE') {
    return '/unauthorized';
  }
  return null;
}

export function getPostAuthPathForUser(user, fallback = '/dashboard/team-member') {
  return getAccountActionRoute(user) || getDashboardPathForUser(user, fallback);
}

export function isDashboardEligible(user) {
  const status = String(user?.status || 'ACTIVE').trim().toUpperCase();
  return status === 'ACTIVE' && !getAccountActionRoute(user);
}

// Legacy fallback only. New code should pass the authenticated user to
// getDashboardPathForUser() so routing is based on resolved access context.
export function getDashboardPathForRole(role, fallback = '/dashboard/provider') {
  const roleKey = getRoleKey(role);
  if (!roleKey) return fallback;
  if (roleKey.includes('owner') || roleKey.includes('super')) return '/dashboard/owner';
  if (roleKey.includes('admin') || roleKey.includes('corporate') || roleKey.includes('organization')) {
    return '/dashboard/corporate-admin';
  }
  if (roleKey.includes('mentor') || roleKey.includes('lead')) return '/dashboard/team-lead';
  if (roleKey.includes('employee') || roleKey.includes('member') || roleKey.includes('client') || roleKey.includes('practitioner')) {
    return '/dashboard/team-member';
  }
  return fallback;
}

export function isRoleAllowed(role, allowedRoles = []) {
  if (!Array.isArray(allowedRoles) || !allowedRoles.length) return true;
  const roleKey = getRoleKey(role);
  return allowedRoles.map(getRoleKey).includes(roleKey);
}

function normalizePolicy(policy) {
  if (!policy) return {};
  if (Array.isArray(policy)) return policy.length ? { roles: policy } : {};
  return policy;
}

export function isAccessAllowed(user, policy = {}) {
  const normalized = normalizePolicy(policy);
  if (!Object.keys(normalized).length) return true;

  if (normalized.roles?.length && isRoleAllowed(user?.role, normalized.roles)) {
    return true;
  }

  if (normalized.permissionsAll?.length && !hasAllPermissions(user, normalized.permissionsAll)) {
    return false;
  }

  if (normalized.permissionsAny?.length && hasAnyPermission(user, normalized.permissionsAny)) {
    return true;
  }

  const workspace = resolveUserWorkspace(user);
  if (normalized.workspaces?.length && normalized.workspaces.includes(workspace?.id)) {
    return true;
  }

  const roleKey = getRoleKey(getAccessProfile(user)?.role || user?.role);
  if (normalized.personaMarkers?.length && normalized.personaMarkers.includes(roleKey)) {
    return true;
  }

  return Boolean(normalized.permissionsAll?.length && !normalized.permissionsAny?.length);
}

export default WORKSPACE_POLICIES;
