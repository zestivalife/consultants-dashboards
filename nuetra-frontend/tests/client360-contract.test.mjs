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

test('active assignment opens the canonical Client 360 workspace without a consent interception layer', () => {
  assert.doesNotMatch(api, /CONSULTANT_ACCESS_CONSENT_REQUIRED|protectedAccess/);
  assert.doesNotMatch(
    api.match(/export async function getFiteatsyConsultantClientProfile[\s\S]*?\n}/)?.[0] || '',
    /Promise\.all|nutrition-intelligence/,
    'opening Client 360 must remain a single canonical workspace request'
  );
  assert.doesNotMatch(workspace, /protectedAccessDenied|renderProtectedAccessGate|renderAssignmentSafe/);
  assert.match(workspace, /Overview: renderOverview/);
  assert.match(workspace, /Profile: renderProfile/);
  assert.match(workspace, /Health: renderHealth/);
  assert.match(workspace, /Nutrition: renderNutritionSummary/);
  assert.match(workspace, /'Diet Plan': renderNutrition/);
  assert.match(workspace, /Reports: renderReports/);
  assert.match(workspace, /Care: renderCare/);
  assert.match(workspace, /Timeline: renderTimeline/);
  assert.doesNotMatch(workspace, /if \(!isOpen \|\| protectedAccessDenied/);
});

test('the assigned-client header exposes the canonical workspace status without consent branches', () => {
  assert.match(workspace, /clientHeaderCollapsed && publishedPlanVersionNumber/);
  assert.match(workspace, /clientHeaderCollapsed && editablePlanVersionNumber/);
  assert.match(workspace, /clientPhoneIdentity/);
  assert.match(workspace, /healthStatus/);
  assert.match(workspace, /profileStrength/);
  assert.doesNotMatch(workspace, /Protected data requires consent|Awaiting consultant consent/);
});

test('Care exposes the complete assigned-client operation set through one backend request', () => {
  assert.doesNotMatch(care, /protectedAccessDenied|type !== 'NOTE'|key !== 'NOTE'/);
  assert.match(care, /await listFiteatsyClientOperations\(clientId\)/);
  assert.match(care, /consultations, follow-ups, goals, tasks, and notes/);
  assert.match(care, /visibleTypes\.map/);
});

test('assignment authorization failures remain global and fail closed', () => {
  assert.match(api, /requestFiteatsyJson\(`\/v1\/consultants\/clients\/\$\{encodedClientId\}\/workspace`\)/);
  assert.match(workspace, /if \(error\.status === 403\) return 'An active client assignment is required';/);
});
