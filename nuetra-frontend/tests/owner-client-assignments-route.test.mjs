import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');

test('platform owner exposes the governed client assignment workflow on a canonical route', () => {
  const routes = read('lib/ownerConsoleRoutes.js');
  const page = read('components/platform/OwnerConsolePage.jsx');
  const workspace = read('components/platform/PlatformWorkspace.jsx');
  const api = read('lib/fiteatsyConsultantsApi.js');
  const roles = read('lib/roleRoutes.js');

  assert.match(routes, /slug: 'client-assignments', moduleKey: 'client-assignments', label: 'Client Assignments'/);
  assert.match(routes, /assignments: 'client-assignments'/);
  assert.match(page, /case 'client-assignments':[\s\S]*<ProfessionalAssignmentPage/);
  assert.match(page, /onOpenAssignments=\{\(\) => router\.push\('\/dashboard\/owner\/client-assignments'\)\}/);
  assert.match(workspace, /export function ProfessionalAssignmentPage\(\)/);
  assert.match(workspace, /createFiteatsyProfessionalAssignment/);
  assert.match(api, /apiRequest\(`?\/platform\/fiteatsy\/professional-assignments\/clients\/pool/);
  assert.match(api, /apiRequest\(`?\/platform\/fiteatsy\/professional-assignments\/professionals/);
  assert.match(api, /apiRequest\('\/platform\/fiteatsy\/professional-assignments'/);
  assert.doesNotMatch(api, /requestFiteatsy(?:Json)?\(`?\/v1\/professional-assignments/);
  assert.match(roles, /match\(\/\^\\\/workspace\\\/\(\[\^\/\]\+\)\//);
  assert.match(roles, /isCanonicalWorkspaceAllowed\(user, workspaceMatch\[1\], tenant \|\| null\)/);
});
