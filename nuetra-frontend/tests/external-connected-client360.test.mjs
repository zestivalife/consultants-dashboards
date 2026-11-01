import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

import { externalClient360Base } from '../lib/externalClientProfile.mjs';

const component = fs.readFileSync(new URL('../components/external/ExternalClient360.jsx', import.meta.url), 'utf8');

test('connected external Client 360 uses the consented Practice Operations health context', () => {
  assert.match(component, /getFiteatsyConnectionHealthContext\(client\.connectionId\)/);
  const initialLoad = component.match(/const load = async \(\) => \{[\s\S]*?\n  const loadPendingReportReviews/)?.[0] || '';
  assert.doesNotMatch(initialLoad, /getExternalClient360\(client\.id\)/);
});

test('directory and consented health data produce an explicit Client 360 base projection', () => {
  const result = externalClient360Base({
    id: 'client-1',
    displayName: 'QA Client',
    status: 'CONNECTED_CONSENT_ACTIVE',
    email: 'qa@example.test',
    consentedScopes: ['PROFILE', 'HEALTH_SUMMARY'],
  }, {
    generatedAt: '2026-11-01T12:00:00Z',
    profile: { dateOfBirth: '1990-01-02', gender: 'FEMALE' },
    healthProfile: { medicalHistory: { conditions: ['asthma'] } },
    reports: [{ id: 'report-1', reportType: 'medical_report' }],
    timeline: [{ id: 'event-1' }],
  });

  assert.equal(result.overview.name, 'QA Client');
  assert.equal(result.overview.documentCount, 1);
  assert.equal(result.sections.medicalHistory.conditions[0], 'asthma');
  assert.equal(result.documents[0].id, 'report-1');
  assert.equal(result.consent.source, 'FITEATSY_CONNECTION');
});

test('an unconnected directory client does not receive fabricated health data', () => {
  const result = externalClient360Base({ id: 'client-2', name: 'Directory Client' });
  assert.equal(result.overview.name, 'Directory Client');
  assert.deepEqual(result.documents, []);
  assert.deepEqual(result.sections.medicalHistory, {});
  assert.equal(result.consent.source, 'PRACTICE_DIRECTORY');
});
