import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workspace = readFileSync(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');
const owner = readFileSync(new URL('../components/platform/OwnerConsoleModules.jsx', import.meta.url), 'utf8');
const api = readFileSync(new URL('../lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8');

test('People & Access exposes Assign Clients for consultant rows', () => {
  assert.match(owner, /Assign Clients/);
  assert.match(owner, /setAssignmentConsultant/);
});

test('Fiteatsy Leads preserves the selected lead when opening the shared drawer', () => {
  assert.match(workspace, /initialClient=\{assignmentClient\}/);
  assert.match(workspace, /new Set\(initialClient\?\.userId/);
});

test('drawer supports masked contacts, search, pagination and multiple selection', () => {
  assert.match(workspace, /Search name, mobile or email/);
  assert.match(workspace, /maskedMobileNumber/);
  assert.match(workspace, /maskedEmail/);
  assert.match(workspace, /Page \{page \+ 1\}/);
  assert.match(workspace, /selectedClientMap/);
});

test('drawer distinguishes loading, empty, error and retry states', () => {
  assert.match(workspace, /Loading eligible clients/);
  assert.match(workspace, /No eligible clients match this search/);
  assert.match(workspace, /role="alert"/);
  assert.match(workspace, />Retry</);
});

test('reassignment requires explicit confirmation and an explicit API flag', () => {
  assert.match(workspace, /window\.confirm/);
  assert.match(workspace, /allowReassignment:/);
  assert.match(workspace, /preserve prior assignments in history/);
});

test('submission failure keeps the drawer open and never emits false success', () => {
  assert.match(workspace, /setError\(reason\?\.message \|\| 'Client assignment failed/);
  assert.match(workspace, /if \(results\.length !== selected\.length\) throw new Error\('The server did not atomically confirm every assignment/);
  assert.doesNotMatch(workspace, /catch \([^)]*\) \{\s*onSuccess/);
});

test('multiple selections use one authoritative atomic batch request', () => {
  assert.match(api, /createFiteatsyProfessionalAssignmentsBatch/);
  assert.match(api, /professional-assignments\/batch/);
  assert.match(workspace, /clientUserIds: selected\.map/);
  assert.doesNotMatch(workspace.slice(workspace.indexOf('export function ClientAssignmentDrawer'), workspace.indexOf('export function SuperAdminFiteatsyLeadsPage')), /for \(const client of selected\)/);
});

test('Zestiva consultants resolve to an active authoritative Fiteatsy identity', () => {
  assert.match(workspace, /listFiteatsyAssignmentProfessionals\('CONSULTANT'\)/);
  assert.match(workspace, /String\(item\.email \|\| ''\).*=== expectedIdentifier/);
  assert.match(workspace, /does not have an active Fiteatsy professional identity/);
});

test('Connection PIN consent is not created by administrative assignment', () => {
  const drawerStart = workspace.indexOf('export function ClientAssignmentDrawer');
  const drawerEnd = workspace.indexOf('export function SuperAdminFiteatsyLeadsPage');
  const drawer = workspace.slice(drawerStart, drawerEnd);
  assert.doesNotMatch(drawer, /consent|Connection PIN|connection-pin/i);
});
