import assert from 'node:assert/strict';
import test from 'node:test';
import { projectAssignedClient360 } from '../lib/connectedClient360.mjs';

test('assigned unconnected clients receive a consent-pending projection without health data', () => {
  const result = projectAssignedClient360({
    id: 'client-1', displayName: 'Assigned client', email: 'visible@example.test',
    relationshipStatus: 'ASSIGNED_CONNECTION_PENDING', status: 'ASSIGNED',
  });
  assert.equal(result.overview.id, 'client-1');
  assert.equal(result.overview.name, 'Assigned client');
  assert.equal(result.consent.status, 'ASSIGNED_CONNECTION_PENDING');
  assert.deepEqual(result.overview.dietPlanWarnings, ['CONSENT_PENDING']);
  assert.deepEqual(result.documents, []);
  assert.deepEqual(result.sections.medicalHistory, {});
  assert.deepEqual(result.sections.nutrition, {});
  assert.deepEqual(result.sections.measurements, {});
  assert.equal(result.derived.bmi.status, 'NOT_AVAILABLE');
});

test('assigned projection does not infer unavailable identity or health fields', () => {
  const result = projectAssignedClient360({ id: 'client-2' });
  assert.equal(result.overview.name, 'Client');
  assert.equal(result.overview.email, null);
  assert.equal(result.overview.primaryContact, null);
  assert.equal(result.overview.documentCount, null);
  assert.equal(result.overview.fiteatsyAssessment, null);
});
