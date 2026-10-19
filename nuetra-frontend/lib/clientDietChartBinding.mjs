export function resolveClientDietChartAction({ loading = false, unavailable = false, plan = null } = {}) {
  if (loading) return 'Loading Diet Chart…';
  if (unavailable) return 'Diet Chart unavailable';
  if (plan?.status === 'PUBLISHED') return 'View Diet Chart';
  if (plan) return 'Continue Diet Chart';
  return 'Generate Diet Chart';
}

export function assertCurrentClientBinding(sourceClientId, authoringClientId) {
  if (!sourceClientId || String(sourceClientId) !== String(authoringClientId)) {
    throw new Error('DIET_CHART_CLIENT_CONTEXT_MISMATCH');
  }
  return String(authoringClientId);
}
