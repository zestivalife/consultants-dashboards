import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const workspace = fs.readFileSync(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');
const care = fs.readFileSync(new URL('../components/platform/Client360CareWorkspace.jsx', import.meta.url), 'utf8');
const api = fs.readFileSync(new URL('../lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8');

test('Client 360 exposes exactly the governed eight top-level destinations', () => {
  const declaration = workspace.match(/const workspaceTabs = \[([\s\S]*?)\];/);
  assert.ok(declaration, 'Client 360 tab declaration must exist');
  const labels = [...declaration[1].matchAll(/'([^']+)'/g)].map((match) => match[1]);
  assert.deepEqual(labels, ['Overview', 'Profile', 'Health', 'Nutrition', 'Diet Plan', 'Reports', 'Care', 'Timeline']);
  assert.equal(labels.includes('Biomarkers'), false, 'Biomarkers belongs inside Health, not in top-level navigation');
});

test('care operations use the authenticated backend contract rather than browser storage', () => {
  assert.match(care, /listFiteatsyClientOperations/);
  assert.match(care, /createFiteatsyClientOperation/);
  assert.match(care, /updateFiteatsyClientOperation/);
  assert.doesNotMatch(care, /localStorage|sessionStorage/);
  assert.match(api, /Idempotency-Key/);
  assert.match(care, /expectedVersion: item\.version/);
});

test('consultant-wide operations use the same backend authority', () => {
  assert.match(api, /listFiteatsyConsultantOperations/);
  assert.match(api, /getFiteatsyConsultantAvailability/);
  assert.match(api, /updateFiteatsyConsultantAvailability/);
  assert.match(workspace, /refreshConsultantOperations/);
  assert.match(workspace, /createFiteatsyClientOperation/);
  assert.match(workspace, /updateFiteatsyClientOperation/);
  assert.doesNotMatch(workspace, /readConsultantWorkspaceState|local operational memory/);
  assert.doesNotMatch(workspace, /consultantWorkspaceStorageKey\}\`\s*,\s*JSON\.stringify/);
});

test('real client directory queries remain server-side and bounded', () => {
  assert.match(api, /new URLSearchParams\(\{[\s\S]*q: query[\s\S]*status[\s\S]*pageSize/);
  assert.match(workspace, /listFiteatsyConsultantClients\(\{[\s\S]*pageSize: 100/);
});
