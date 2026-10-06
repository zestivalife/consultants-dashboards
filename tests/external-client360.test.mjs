import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const component = readFileSync(new URL('../nuetra-frontend/components/external/ExternalClient360.jsx', import.meta.url), 'utf8');
const workspace = readFileSync(new URL('../nuetra-frontend/components/external/ExternalConsultantWorkspace.jsx', import.meta.url), 'utf8');
const api = readFileSync(new URL('../nuetra-frontend/lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8');

test('external workspace opens the canonical Client 360', () => {
  assert.match(workspace, /<ExternalClient360/);
  assert.match(component, /getExternalClient360/);
});
test('Client 360 exposes six professional tabs and partial states', () => {
  for (const label of ['Overview', 'Health Profile', 'Nutrition', 'Measurements', 'Reports', 'Timeline', 'Not provided', 'Missing:']) assert.ok(component.includes(label));
});
test('Client 360 presents provenance, completeness, women health, documents and timeline', () => {
  for (const contract of ['sourceLabel', 'profileCompleteness', "overview.gender === 'FEMALE'", 'downloadExternalClientDocument', 'Consent status', 'operational history']) assert.ok(component.includes(contract));
});
test('Client 360 API client uses governed endpoints', () => {
  for (const endpoint of ['/360', '/profile', '/timeline', '/documents/']) assert.ok(api.includes(endpoint));
});
test('Client 360 preserves invitation and status quick actions', () => {
  for (const action of ['Invite client', 'Regenerate', 'Revoke', 'Copy secure link', 'onStatus']) assert.ok(component.includes(action));
});
