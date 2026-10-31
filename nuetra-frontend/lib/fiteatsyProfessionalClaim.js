const EXTERNAL_TENANT_TYPES = new Set(['INDEPENDENT_CONSULTANT', 'PRACTICE']);

export function needsFiteatsyProfessionalClaimRefresh({ user }) {
  const tenantType = String(user?.currentTenant?.tenantType || '').trim().toUpperCase();
  if (!EXTERNAL_TENANT_TYPES.has(tenantType)) return false;

  // Refresh external-consultant sessions once during application start even
  // when the stored token already contains a syntactically valid mapping.
  // Provisioning can repair or replace the canonical Fiteatsy professional
  // identity after a token was issued; trusting the stale value then produces
  // a valid but empty assignment roster. The refresh endpoint resolves the
  // current immutable mapping from the authoritative provisioning record.
  // Internal/workforce sessions remain excluded above.
  return true;
}
