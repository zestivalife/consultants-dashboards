import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');

test('platform owner exposes the governed client assignment workflow on a canonical route', () => {
  const routes = read('lib/ownerConsoleRoutes.js');
  const page = read('components/platform/OwnerConsolePage.jsx');
  const workspace = read('components/platform/PlatformWorkspace.jsx');

  assert.match(routes, /slug: 'client-assignments', moduleKey: 'client-assignments', label: 'Client Assignments'/);
  assert.match(routes, /assignments: 'client-assignments'/);
  assert.match(page, /case 'client-assignments':[\s\S]*<ProfessionalAssignmentPage/);
  assert.match(page, /onOpenAssignments=\{\(\) => router\.push\('\/dashboard\/owner\/client-assignments'\)\}/);
  assert.match(workspace, /export function ProfessionalAssignmentPage\(\)/);
  assert.match(workspace, /createFiteatsyProfessionalAssignment/);
});
