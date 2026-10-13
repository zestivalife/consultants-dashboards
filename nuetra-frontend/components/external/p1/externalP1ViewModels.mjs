import { getModuleDefinition } from './externalP1Catalog.mjs';

export const CAPABILITY_STATE = Object.freeze({ READY: 'READY', UNAVAILABLE: 'UNAVAILABLE', LOADING: 'LOADING', ERROR: 'ERROR' });

const hasValue = (value) => value !== null && value !== undefined;

export function buildCapabilityState(capabilities, capability, options = {}) {
  if (options.loading) return { state: CAPABILITY_STATE.LOADING, message: 'Loading authorised data…' };
  if (options.error) return { state: CAPABILITY_STATE.ERROR, message: 'This information could not be loaded. Try again.' };
  const entry = capabilities?.[capability];
  if (entry === true || entry?.enabled === true) return { state: CAPABILITY_STATE.READY, message: null };
  return { state: CAPABILITY_STATE.UNAVAILABLE, message: entry?.reason || 'This capability is not connected for your practice.' };
}

export function buildModuleViewModel({ moduleKey, capabilities = {}, records, loading = false, error = null }) {
  const definition = getModuleDefinition(moduleKey);
  const capability = buildCapabilityState(capabilities, definition.capability, { loading, error });
  const authorisedRecords = Array.isArray(records) ? records.filter((record) => record?.authorised !== false) : [];
  return {
    moduleKey,
    title: definition.title,
    sections: definition.sections,
    capability,
    records: capability.state === CAPABILITY_STATE.READY ? authorisedRecords : [],
    isEmpty: capability.state === CAPABILITY_STATE.READY && authorisedRecords.length === 0,
    emptyMessage: definition.empty,
  };
}

export function buildAnalyticsViewModel({ capabilities = {}, metrics, loading = false, error = null }) {
  const base = buildModuleViewModel({ moduleKey: 'analytics', capabilities, records: [], loading, error });
  const verifiedMetrics = metrics && typeof metrics === 'object'
    ? Object.entries(metrics).filter(([, metric]) => hasValue(metric?.value) && metric?.source === 'CONNECTED').map(([key, metric]) => ({ key, label: metric.label || key, value: metric.value, period: metric.period || null }))
    : [];
  return { ...base, metrics: base.capability.state === CAPABILITY_STATE.READY ? verifiedMetrics : [], isEmpty: base.capability.state === CAPABILITY_STATE.READY && verifiedMetrics.length === 0 };
}

export function buildRenewalAttention(packageRecord, today = new Date()) {
  if (!packageRecord?.expiryDate) return null;
  const daysRemaining = Math.ceil((new Date(packageRecord.expiryDate).getTime() - today.getTime()) / 86400000);
  if (daysRemaining > 30) return null;
  return { kind: daysRemaining < 0 ? 'EXPIRED' : 'EXPIRING_SOON', daysRemaining, label: daysRemaining < 0 ? 'Package expired' : `Package expires in ${daysRemaining} day${daysRemaining === 1 ? '' : 's'}` };
}

export function safeCommunicationPreview(message) {
  if (!message) return '';
  return String(message)
    .replace(/\b(?:diagnosis|hba1c|medication|biomarker|medical history)\s*:\s*[^.!?\n]+/gi, '[private health detail]')
    .slice(0, 160);
}
