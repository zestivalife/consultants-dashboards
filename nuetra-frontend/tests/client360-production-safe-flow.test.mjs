import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import {loadConnectedClientDirectory} from '../lib/connectedClientDirectory.mjs';
import {loadAuthorizedClient360} from '../lib/connectedClient360.mjs';

const connection = {
  id: 'connection-rest-fit',
  consultant_client_id: 'client-rest-fit',
  state: 'ACTIVE',
  consented_scopes: ['PROFILE', 'ASSESSMENTS', 'FOOD_PREFERENCES'],
  connected_at: '2026-11-01T10:00:00Z',
};

const healthContext = {
  profile: { client: { name: 'Rest fit', email: 'test@fit.com', mobile: '9876533333', dob: '1988-04-10' }, onboarding: { height: 175, weight: 80, goal: 'Weight management' } },
  foodPreferences: { profile: { dietType: 'Non-Vegetarian', proteins: ['Eggs', 'Chicken'], cuisines: ['Maharashtrian'] } },
  reports: [],
  biomarkers: [
    { id: 'hba1c', canonicalBiomarkerId: 'HBA1C', name: 'HbA1c', value: 6.2, unit: '%', reviewStatus: 'CONFIRMED' },
    { id: 'ldl', canonicalBiomarkerId: 'LDL', name: 'LDL', value: 125, unit: 'mg/dL', reviewStatus: 'REVIEW_REQUIRED' },
  ],
};

test('actual workspace directory loader preserves the active connection and real connection id', async () => {
  const requests = [];
  const directory = await loadConnectedClientDirectory({
    listConnections: async () => ({ connections: [connection, { ...connection, id: 'revoked', state: 'REVOKED' }] }),
    getHealthContext: async (connectionId) => { requests.push(connectionId); return healthContext; },
  }, { limit: 100 });

  assert.equal(directory.clients.length, 1);
  assert.equal(directory.clients[0].id, 'client-rest-fit');
  assert.equal(directory.clients[0].connectionId, 'connection-rest-fit');
  assert.equal(directory.clients[0].connectionState, 'ACTIVE');
  assert.deepEqual(requests, ['connection-rest-fit']);
});

test('workspace-selected connected client loads consent-controlled health context by connection id', async () => {
  const directory = await loadConnectedClientDirectory({
    listConnections: async () => ({ connections: [connection] }),
    getHealthContext: async () => healthContext,
  });
  const requests = [];
  const client360 = await loadAuthorizedClient360(directory.clients[0], async (connectionId) => {
    requests.push(`/fiteatsy-connections/${connectionId}/health-context`);
    return healthContext;
  });

  assert.deepEqual(requests, ['/fiteatsy-connections/connection-rest-fit/health-context']);
  assert.equal(client360.overview.name, 'Rest fit');
  assert.equal(client360.sections.nutrition.dietPreference, 'Non-Vegetarian');
  assert.equal(client360.biomarkers.latest.length, 2);
  assert.equal(client360.biomarkers.pendingReviewCount, 1);
});

test('unconnected client remains directory-only and never requests health data', async () => {
  let called = false;
  const client360 = await loadAuthorizedClient360({ id: 'assigned-only', displayName: 'Assigned client', status: 'ASSIGNED_CONNECTION_PENDING' }, async () => { called = true; });
  assert.equal(called, false);
  assert.equal(client360.overview.name, 'Assigned client');
  assert.deepEqual(client360.sections.medicalHistory, {});
  assert.equal(client360.consent.status, 'ASSIGNED_CONNECTION_PENDING');
});

for (const connectionState of ['REVOKED', 'EXPIRED', 'CONSENT_REVOKED', 'CONSENT_EXPIRED']) {
  test(`${connectionState} consent cannot request or expose health data`, async () => {
    let called = false;
    const client360 = await loadAuthorizedClient360({ id: 'client-rest-fit', connectionId: 'connection-rest-fit', connectionState, displayName: 'Rest fit' }, async () => { called = true; return healthContext; });
    assert.equal(called, false);
    assert.deepEqual(client360.sections.nutrition, {});
    assert.equal(client360.consent.status, connectionState);
  });
}

test('cross-tenant or unavailable health-context failures remain failures', async () => {
  const selected = { id: 'client-rest-fit', connectionId: 'connection-rest-fit', connectionState: 'ACTIVE', status: 'ACTIVE' };
  await assert.rejects(() => loadAuthorizedClient360(selected, async () => { const error = new Error('You do not have permission to access this client.'); error.status = 403; throw error; }), /permission/);
  await assert.rejects(() => loadAuthorizedClient360(selected, async () => { const error = new Error('Practice service is temporarily unavailable.'); error.status = 503; throw error; }), /unavailable/);
});

test('active Client 360 mount uses authorised Practice Operations contracts only', async () => {
  const source = await readFile(new URL('../components/external/ExternalClient360.jsx', import.meta.url), 'utf8');
  const activeComponent = source.split('function LegacyExternalDietPlan')[0];

  assert.doesNotMatch(activeComponent, /getExternalClient360\s*\(/);
  assert.doesNotMatch(activeComponent, /getExternalDietPlan\s*\(/);
  assert.doesNotMatch(activeComponent, /getExternalClientBiomarkers\s*\(/);
  assert.doesNotMatch(activeComponent, /getExternalTransientBiomarkers\s*\(/);
  assert.doesNotMatch(activeComponent, /getPendingExternalReportAnalyses\s*\(/);
  assert.doesNotMatch(activeComponent, /\/v1\/external\/clients\/.*\/360/);
  assert.match(activeComponent, /loadAuthorizedClient360\(client,getFiteatsyConnectionHealthContext\)/);
  assert.match(activeComponent, /usesProfessionIntakeApi=usesProfessionWorkspace\|\|professionConfig\?\.profession==='DIETITIAN'/);
});
