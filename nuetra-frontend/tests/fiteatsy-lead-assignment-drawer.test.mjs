import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workspace = readFileSync(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');

const drawerStart = workspace.indexOf('export function FiteatsyLeadAssignmentDrawer');
const drawerEnd = workspace.indexOf('export function ProfessionalAssignmentPage');
const drawer = workspace.slice(drawerStart, drawerEnd);

test('Fiteatsy lead Assign opens the selected-client drawer without route navigation', () => {
  assert.match(workspace, /setAssignmentClient\(\{ userId: lead\.userId/);
  assert.match(workspace, /initialClient=\{assignmentClient\}/);
  const leadsStart = workspace.indexOf('export function SuperAdminFiteatsyLeadsPage');
  const leads = workspace.slice(leadsStart, drawerStart);
  assert.doesNotMatch(leads, /onOpenAssignments/);
});

test('Fiteatsy lead request failures do not render a false empty state', () => {
  const leadsStart = workspace.indexOf('export function SuperAdminFiteatsyLeadsPage');
  const leads = workspace.slice(leadsStart, drawerStart);
  assert.match(leads, /!loading && !error && leads\.length === 0/);
});

test('drawer verifies the lead and lists only active consultant identities', () => {
  assert.match(drawer, /listAllFiteatsyClientAllocationPool\(\{ assignment: 'all' \}\)/);
  assert.match(drawer, /find\(\(item\) => item\.userId === initialClient\.userId\)/);
  assert.match(drawer, /listFiteatsyAssignmentProfessionals\('CONSULTANT'\)/);
  assert.match(drawer, /String\(item\.status\)\.toUpperCase\(\) === 'ACTIVE'/);
});

test('drawer uses the governed assignment contract and confirms reassignment', () => {
  assert.match(drawer, /createFiteatsyProfessionalAssignment\(\{/);
  assert.match(drawer, /professionalType: 'CONSULTANT'/);
  assert.match(drawer, /relationshipType: 'CLIENT_CARE'/);
  assert.match(drawer, /allowReassignment: isReassignment/);
  assert.match(drawer, /window\.confirm/);
  assert.match(drawer, /preserve the previous assignment in history/);
});

test('drawer distinguishes load and submission failures from success', () => {
  assert.match(drawer, /Assignment unavailable/);
  assert.match(drawer, /Client assignment failed\. No success was recorded/);
  assert.match(drawer, /onSuccess\?\.\(\{ client, consultant \}\)/);
  assert.doesNotMatch(drawer, /catch[^}]+onSuccess/s);
});
