import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';

const root = path.resolve(import.meta.dirname, '..', '..');
const registryPath = path.join(root, 'nuetra-frontend/contracts/external-consultant-api-registry.json');
const registry = JSON.parse(await readFile(registryPath, 'utf8'));

const required = [
  'id', 'workflow', 'frontend', 'client', 'browser_endpoint', 'method', 'gateway',
  'owner', 'service_endpoint', 'authentication', 'authorization',
  'database_dependency', 'request_schema_source', 'response_schema_source',
  'expected_statuses', 'source_contract_markers'
];

test('critical API registry is complete, unique and source-backed', async () => {
  assert.equal(registry.registry_version, 1);
  assert.equal(registry.compatibility_policy.breaking_changes_require_tested_strategy, true);
  assert.deepEqual(registry.compatibility_policy.expected_error_statuses_must_be_preserved, [400, 401, 403, 404]);
  assert.ok(registry.contracts.length >= 10);

  const ids = new Set();
  const operations = new Set();
  for (const contract of registry.contracts) {
    for (const field of required) assert.ok(contract[field], `${contract.id || 'unknown'} missing ${field}`);
    assert.match(contract.method, /^(GET|POST|PUT|PATCH|DELETE)$/);
    assert.ok(contract.expected_statuses.every((status) => Number.isInteger(status) && status >= 200 && status < 600));
    assert.ok(!ids.has(contract.id), `duplicate contract id ${contract.id}`);
    ids.add(contract.id);

    const operation = `${contract.method} ${contract.browser_endpoint}`;
    assert.ok(!operations.has(operation), `duplicate browser operation ${operation}`);
    operations.add(operation);

    const [frontend, client] = await Promise.all([
      readFile(path.join(root, contract.frontend), 'utf8'),
      readFile(path.join(root, contract.client), 'utf8')
    ]);
    const source = `${frontend}\n${client}`;
    for (const marker of contract.source_contract_markers) {
      assert.ok(source.includes(marker), `${contract.id} source no longer contains ${marker}`);
    }
  }
});

test('registry covers the ten production-critical workflows', () => {
  const workflows = registry.contracts.map((contract) => contract.workflow.toLowerCase()).join('\n');
  for (const expected of [
    'client management', 'client 360', 'assessment', 'diet chart generation',
    'diet chart editor', 'draft management', 'self-approval', 'publication',
    'mobile diet synchronisation', 'delegated health context'
  ]) assert.ok(workflows.includes(expected), `missing workflow coverage: ${expected}`);
});
