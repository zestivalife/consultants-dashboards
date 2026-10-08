export const TENANT_CONTEXT_STATUS = Object.freeze({
  IDLE: 'IDLE',
  LOADING: 'LOADING',
  READY: 'READY',
  UNAVAILABLE: 'UNAVAILABLE',
});

const EXTERNAL_TENANT_TYPES = new Set([
  'INDEPENDENT_CONSULTANT',
  'PRACTICE',
  'CLINIC',
  'ENTERPRISE',
]);

export function normalizeCanonicalTenant(payload) {
  const tenant = payload?.currentTenant ?? payload?.data?.currentTenant ?? null;
  if (!tenant || typeof tenant !== 'object') return null;

  const tenantId = String(tenant.tenantId || '').trim();
  const tenantType = String(tenant.tenantType || '').trim().toUpperCase();
  const currentMembershipRole = String(tenant.currentMembershipRole || '').trim().toUpperCase();
  if (!tenantId || !tenantType || !currentMembershipRole) return null;

  return {
    tenantId,
    tenantName: String(tenant.tenantName || '').trim() || null,
    tenantType,
    currentMembershipRole,
    membershipStatus: 'active',
    resolutionPath: tenant.resolutionPath || 'MEMBERSHIP',
  };
}

export function resolveConsultantWorkspace({ status, tenantType, membershipStatus }) {
  if (status === TENANT_CONTEXT_STATUS.LOADING || status === TENANT_CONTEXT_STATUS.IDLE) return 'LOADING';
  if (status !== TENANT_CONTEXT_STATUS.READY || membershipStatus !== 'active') return 'UNAVAILABLE';
  if (tenantType === 'ZESTIVA_INTERNAL') return 'IN_HOUSE';
  if (EXTERNAL_TENANT_TYPES.has(tenantType)) return 'EXTERNAL';
  return 'UNAVAILABLE';
}
