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

test('assigned clients without consent retain the Client 360 shell while protected tabs stay gated', () => {
  assert.match(api, /errorCode !== 'CONSULTANT_ACCESS_CONSENT_REQUIRED'/);
  assert.match(api, /status: 'CONSENT_REQUIRED'/);
  assert.doesNotMatch(
    api.match(/export async function getFiteatsyConsultantClientProfile[\s\S]*?\n}/)?.[0] || '',
    /Promise\.all|nutrition-intelligence/,
    'opening Client 360 must not eagerly request a second protected nutrition endpoint'
  );
  assert.match(workspace, /protectedAccessDenied = profile\?\.protectedAccess\?\.status === 'CONSENT_REQUIRED'/);
  assert.match(workspace, /Overview: protectedAccessDenied \? renderAssignmentSafeOverview : renderOverview/);
  assert.match(workspace, /Health: renderProtectedTab\(renderHealth\)/);
  assert.match(workspace, /Nutrition: renderProtectedTab\(renderNutritionSummary\)/);
  assert.match(workspace, /Reports: renderProtectedTab\(renderReports\)/);
  assert.match(workspace, /The client shell remains available because this client is assigned to you\./);
  assert.match(workspace, /if \(!isOpen \|\| protectedAccessDenied \|\| !summaryClient\?\.id\) return;/);
});

test('non-consent authorization failures remain global and fail closed', () => {
  assert.match(api, /if \(error\?\.status !== 403 \|\| errorCode !== 'CONSULTANT_ACCESS_CONSENT_REQUIRED'\) \{\s*throw error;/);
  assert.match(workspace, /if \(error\.status === 403\) return 'Consultant access required';/);
});
