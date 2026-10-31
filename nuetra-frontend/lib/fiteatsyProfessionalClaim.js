const EXTERNAL_TENANT_TYPES = new Set(['INDEPENDENT_CONSULTANT', 'PRACTICE']);

function decodeJwtPayload(token) {
  const parts = String(token || '').split('.');
  if (parts.length !== 3) return null;

  try {
    const normalized = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
    const decoded = globalThis.atob(padded);
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

export function needsFiteatsyProfessionalClaimRefresh({ token, user }) {
  const tenantType = String(user?.currentTenant?.tenantType || '').trim().toUpperCase();
  if (!EXTERNAL_TENANT_TYPES.has(tenantType)) return false;

  const payload = decodeJwtPayload(token);
  return !String(payload?.fiteatsy_professional_id || '').trim();
}
