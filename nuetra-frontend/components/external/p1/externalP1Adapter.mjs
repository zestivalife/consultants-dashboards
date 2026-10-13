export class ExternalP1CapabilityError extends Error {
  constructor(capability, message = 'Capability unavailable') {
    super(message);
    this.name = 'ExternalP1CapabilityError';
    this.code = 'CAPABILITY_UNAVAILABLE';
    this.capability = capability;
  }
}

export function createExternalP1Adapter({ transport, getContext }) {
  if (typeof transport !== 'function') throw new TypeError('transport must be provided');

  async function request(capability, path, options = {}) {
    const context = await getContext?.();
    if (!context?.tenantId || context.tenantType === 'ZESTIVA_INTERNAL') throw new ExternalP1CapabilityError(capability, 'External tenant context required');
    const flag = context.capabilities?.[capability];
    if (!(flag === true || flag?.enabled === true)) throw new ExternalP1CapabilityError(capability, flag?.reason);
    return transport(path, {
      ...options,
      credentials: 'include',
      headers: { ...options.headers, 'X-Correlation-Id': options.correlationId || crypto.randomUUID() },
    });
  }

  return Object.freeze({
    loadModule: (capability, moduleKey, query = '') => request(capability, `/v1/external/${encodeURIComponent(moduleKey)}${query}`),
    execute: (capability, moduleKey, action, body, idempotencyKey) => {
      if (!idempotencyKey) throw new TypeError('idempotencyKey is required for mutations');
      return request(capability, `/v1/external/${encodeURIComponent(moduleKey)}/${encodeURIComponent(action)}`, { method: 'POST', headers: { 'Idempotency-Key': idempotencyKey, 'Content-Type': 'application/json' }, body: JSON.stringify(body ?? {}) });
    },
  });
}
