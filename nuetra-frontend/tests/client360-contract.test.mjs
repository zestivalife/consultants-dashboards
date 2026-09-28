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
  assert.match(workspace, /Profile: protectedAccessDenied \? renderAssignmentSafeProfile : renderProfile/);
  assert.match(workspace, /Health: renderProtectedTab\(renderHealth\)/);
  assert.match(workspace, /Nutrition: renderProtectedTab\(renderNutritionSummary\)/);
  assert.match(workspace, /'Diet Plan': protectedAccessDenied \? renderAssignmentSafeDietPlan : renderNutrition/);
  assert.match(workspace, /Reports: renderProtectedTab\(renderReports\)/);
  assert.match(workspace, /Care: renderCare/);
  assert.match(workspace, /Timeline: protectedAccessDenied \? renderAssignmentSafeTimeline : renderTimeline/);
  assert.match(workspace, /The client shell remains available because this client is assigned to you\./);
  assert.match(workspace, /if \(!isOpen \|\| protectedAccessDenied \|\| !summaryClient\?\.id\) return;/);
});

test('assigned clients without consent see only assignment-safe identity and operational fields', () => {
  assert.match(workspace, /renderAssignmentSafeProfile/);
  assert.match(workspace, /Personal health, measurements, medical history,[\s\S]*medications, and lifestyle details remain protected/);
  assert.match(workspace, /renderAssignmentSafeDietPlan/);
  assert.match(workspace, /Nutrition targets, meal content, clinical restrictions,[\s\S]*plan versions, and authoring actions remain protected/);
  assert.match(workspace, /renderAssignmentSafeTimeline/);
  assert.match(workspace, /Protected health and clinical events remain hidden until consent is granted/);
  assert.match(workspace, /Protected data requires consent/);
  assert.match(workspace, /clientHeaderCollapsed && !protectedAccessDenied && publishedPlanVersionNumber/);
  assert.match(workspace, /clientHeaderCollapsed && !protectedAccessDenied && editablePlanVersionNumber/);
  assert.doesNotMatch(
    workspace.match(/!clientHeaderCollapsed && protectedAccessDenied \? \([\s\S]*?\) : !clientHeaderCollapsed \? <>/)?.[0] || '',
    /clientPhoneIdentity|healthStatus|profileStrength|lastSynced|publishedPlanVersionNumber/,
    'the no-consent header must not disclose protected contact, health, sync, or plan data'
  );
});

test('Care keeps assignment-safe operations visible while consent-protected notes remain hidden', () => {
  assert.match(care, /protectedAccessDenied = false/);
  assert.match(care, /protectedAccessDenied[\s\S]*?type !== 'NOTE'[\s\S]*?listFiteatsyClientOperations\(clientId, type\)/);
  assert.match(care, /key !== 'NOTE'/);
  assert.match(care, /item\.operationType !== 'NOTE'/);
  assert.match(care, /Clinical notes remain protected until consultant access is granted/);
  assert.match(care, /visibleTypes\.map/);
  assert.match(workspace, /protectedAccessDenied=\{protectedAccessDenied\}/);
});

test('non-consent authorization failures remain global and fail closed', () => {
  assert.match(api, /if \(error\?\.status !== 403 \|\| errorCode !== 'CONSULTANT_ACCESS_CONSENT_REQUIRED'\) \{\s*throw error;/);
  assert.match(workspace, /if \(error\.status === 403\) return 'Consultant access required';/);
});
