const parameter = /\{[^/]+\}/g;
export const canonicalPath = (value) => String(value).replace(parameter, '{}').replace(/\/+$/, '') || '/';

export function validateContractCompatibility(registry, inventory) {
  const failures = [];
  const operations = inventory.operations || [];
  for (const contract of registry.contracts || []) {
    const samePath = operations.filter((operation) => operation.provider === contract.provider && canonicalPath(operation.path) === canonicalPath(contract.service_endpoint));
    if (samePath.length === 0) { failures.push({ code: 'MISSING_PROVIDER_OPERATION', contract: contract.id, operation: `${contract.method} ${contract.service_endpoint}` }); continue; }
    const provider = samePath.find((operation) => operation.method === contract.method);
    if (!provider) { failures.push({ code: 'METHOD_MISMATCH', contract: contract.id, expected: contract.method, actual: [...new Set(samePath.map((item) => item.method))].sort() }); continue; }
    const provided = new Set(provider.required_response_fields || []);
    const missingFields = (contract.required_response_fields || []).filter((field) => !provided.has(field));
    if (missingFields.length) failures.push({ code: 'RESPONSE_SCHEMA_INCOMPATIBLE', contract: contract.id, missingFields });
    if (contract.gateway_prefix && !(inventory.gateway_prefixes || []).includes(contract.gateway_prefix)) failures.push({ code: 'MISSING_GATEWAY_MAPPING', contract: contract.id, gatewayPrefix: contract.gateway_prefix });
  }
  return failures;
}

export function assertContractCompatibility(registry, inventory) {
  const failures = validateContractCompatibility(registry, inventory);
  if (!failures.length) return;
  const error = new Error(`API contract compatibility failed:\n${failures.map((item) => JSON.stringify(item)).join('\n')}`);
  error.failures = failures;
  throw error;
}
