import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { validateProfessionalAssignmentPayload } from '../lib/professionalAssignmentValidation.js';

const workspace = readFileSync(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');
const owner = readFileSync(new URL('../components/platform/OwnerConsoleModules.jsx', import.meta.url), 'utf8');
const api = readFileSync(new URL('../lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8');
const apiCore = readFileSync(new URL('../lib/api.js', import.meta.url), 'utf8');
const validation = readFileSync(new URL('../lib/professionalAssignmentValidation.js', import.meta.url), 'utf8');

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

test('assignment APIs use the authenticated Zestiva gateway instead of forwarding a browser token to Fiteatsy', () => {
  const assignmentSection = api.slice(api.indexOf('export async function listFiteatsyClientAllocationPool'), api.indexOf('export async function getFiteatsyConsultantClientProfile'));
  assert.match(assignmentSection, /apiRequest\(`?\/platform\/fiteatsy\/professional-assignments/);
  assert.doesNotMatch(assignmentSection, /requestFiteatsy\(/);
  assert.doesNotMatch(assignmentSection, /requestFiteatsyJson\(/);
  assert.match(assignmentSection, /Idempotency-Key/);
});

test('drawer preserves selected clients across downstream errors and does not conceal failures as empty state', () => {
  const drawerStart = workspace.indexOf('export function ClientAssignmentDrawer');
  const drawerEnd = workspace.indexOf('export function SuperAdminFiteatsyLeadsPage');
  const drawer = workspace.slice(drawerStart, drawerEnd);
  assert.match(drawer, /setError\(reason\?\.message/);
  assert.match(drawer, /!loading && !error && !clients\.length/);
  assert.doesNotMatch(drawer, /catch[^}]+setClients\(\[\]\)/s);
  assert.match(drawer, /selectedClientMap/);
});

test('assignment requests validate canonical client and professional identities before submission', () => {
  assert.match(validation, /POSTGRES_UUID_PATTERN/);
  assert.match(api, /validateProfessionalAssignmentPayload\(payload, true\)/);
  const payload = { clientUserIds: ['11111111-1111-f111-1111-111111111111'], professionalUserId: '22222222-2222-f222-1222-222222222222', professionalType: 'CONSULTANT', relationshipType: 'CLIENT_CARE', reason: 'Assignment', allowReassignment: false };
  assert.equal(validateProfessionalAssignmentPayload(payload, true), payload);
  assert.throws(() => validateProfessionalAssignmentPayload({ ...payload, professionalUserId: 'invalid' }, true), /canonical professional identity/);
  assert.throws(() => validateProfessionalAssignmentPayload({ ...payload, clientUserIds: ['invalid'] }, true), /canonical assignable identity/);
});

test('API errors surface backend field-level validation without exposing submitted values', () => {
  assert.match(apiCore, /details\?\.fieldErrors/);
  assert.match(apiCore, /validationMessage/);
  assert.match(apiCore, /err\.fieldErrors = fieldErrors/);
});
