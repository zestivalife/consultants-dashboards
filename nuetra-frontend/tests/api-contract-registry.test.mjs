import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { assertContractCompatibility, validateContractCompatibility } from '../lib/apiContractCompatibility.mjs';

const root = path.resolve(import.meta.dirname, '..', '..');
const load = async (name) => JSON.parse(await readFile(path.join(root, 'nuetra-frontend/contracts', name), 'utf8'));
const registry = await load('external-consultant-api-registry.json');
const inventory = await load('provider-route-inventory.json');
const copy = (value) => structuredClone(value);

test('ten critical consumer operations are compatible with registered provider and gateway contracts', async () => {
  assert.equal(registry.registry_version, 2);
  assert.equal(registry.contracts.length, 10);
  assert.doesNotThrow(() => assertContractCompatibility(registry, inventory));
  for (const contract of registry.contracts) {
    const source = await readFile(path.join(root, contract.consumer_source), 'utf8');
    assert.ok(source.includes(contract.consumer_operation), `${contract.id} consumer operation is absent`);
  }
});

test('negative fixture: removing a backend operation fails compatibility', () => {
  const broken = copy(inventory);
  broken.operations = broken.operations.filter((item) => item.path !== '/api/v1/practice-operations/diet-plans');
  const failures = validateContractCompatibility(registry, broken);
  assert.deepEqual(failures.filter((item) => item.contract === 'diet-plan-create').map((item) => item.code), ['MISSING_PROVIDER_OPERATION']);
  assert.throws(() => assertContractCompatibility(registry, broken), /MISSING_PROVIDER_OPERATION/);
});

test('negative fixture: changing an HTTP method fails compatibility', () => {
  const broken = copy(inventory);
  broken.operations.find((item) => item.path.endsWith('/draft')).method = 'PATCH';
  const failures = validateContractCompatibility(registry, broken);
  assert.deepEqual(failures.filter((item) => item.contract === 'diet-plan-draft').map((item) => item.code), ['METHOD_MISMATCH']);
  assert.throws(() => assertContractCompatibility(registry, broken), /METHOD_MISMATCH/);
});

test('negative fixture: removing a required response field fails compatibility', () => {
  const broken = copy(inventory);
  const publish = broken.operations.find((item) => item.path.endsWith('/publish'));
  publish.required_response_fields = publish.required_response_fields.filter((field) => field !== 'data.publication_basis');
  const failures = validateContractCompatibility(registry, broken);
  assert.deepEqual(failures.find((item) => item.contract === 'diet-plan-publish'), { code: 'RESPONSE_SCHEMA_INCOMPATIBLE', contract: 'diet-plan-publish', missingFields: ['data.publication_basis'] });
  assert.throws(() => assertContractCompatibility(registry, broken), /RESPONSE_SCHEMA_INCOMPATIBLE/);
});

test('unsupported unconnected Client 360 route cannot silently reappear as a supported contract', async () => {
  const forbidden = registry.forbidden_consumer_operations.find((item) => item.id === 'unsupported-unconnected-client360');
  assert.equal(forbidden.endpoint, '/v1/external/clients/{clientId}/360');
  assert.equal(inventory.operations.some((item) => item.provider === 'fiteatsy' && item.path === forbidden.endpoint), false);
  assert.equal(registry.contracts.some((item) => item.service_endpoint === forbidden.endpoint), false);
  const source = await readFile(path.join(root, forbidden.consumer_source), 'utf8');
  assert.equal(source.includes(forbidden.operation), false);
  assert.equal(source.includes('/360'), false);
});
