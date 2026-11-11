import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const api = readFileSync(new URL('../lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8');
const workspace = readFileSync(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');

test('Senior allocation uses the tenant-scoped Fiteatsy contract instead of the owner-only Gateway bridge', () => {
  assert.match(api, /listAllFiteatsySeniorClientAllocationPool/);
  assert.match(api, /requestFiteatsyJson\(`\/v1\/professional-assignments\/clients\/pool/);
  assert.match(api, /requestFiteatsyJson\(`\/v1\/professional-assignments\/professionals/);
  assert.match(api, /requestFiteatsy\('\/v1\/professional-assignments'/);
  assert.match(workspace, /listAllFiteatsySeniorClientAllocationPool\(\{ query, assignment: view \}\)/);
  assert.match(workspace, /createFiteatsySeniorProfessionalAssignment/);
  assert.match(workspace, /revokeFiteatsySeniorProfessionalAssignment/);
});

test('Platform Owner assignment remains on the signed delegated Gateway contract', () => {
  assert.match(api, /apiRequest\(`\/platform\/fiteatsy\/professional-assignments\/clients\/pool/);
  assert.match(api, /apiRequest\(`\/platform\/fiteatsy\/professional-assignments\/professionals/);
  assert.match(api, /apiRequest\('\/platform\/fiteatsy\/professional-assignments'/);
});
