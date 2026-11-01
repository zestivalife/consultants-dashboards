import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

import { externalClient360Base, externalConnectedBiomarkers } from '../lib/externalClientProfile.mjs';

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
  assert.equal(result.basicProfile.name.value, 'QA Client');
  assert.equal(result.basicProfile.name.sourceLabel, 'Fiteatsy');
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

test('nested Fiteatsy profile, measurements and nutrition populate the original Client 360 contract', () => {
  const result = externalClient360Base({ displayName: 'Connected Client' }, {
    profile: {
      client: { dob: '1992-03-04', gender: 'FEMALE' },
      onboarding: {
        goal: 'Improve energy', activityLevel: 'ACTIVE', medicalConditions: ['asthma'],
        nutrition: { dietaryPreference: 'VEGETARIAN', foodAllergies: ['peanut'] },
        lifestyle: { sleepHours: 7, stressLevel: 'MODERATE' },
        healthHistory: { medications: ['inhaler'] },
      },
    },
    measurements: { heightCm: 165, weightKg: 62 },
  });
  assert.equal(result.overview.dateOfBirth, '1992-03-04');
  assert.deepEqual(result.sections.conditionsSymptoms.conditions, ['asthma']);
  assert.equal(result.sections.nutrition.dietaryPreference, 'VEGETARIAN');
  assert.deepEqual(result.sections.allergiesFamilyHistory.allergies, ['peanut']);
  assert.equal(result.sections.measurements.weightKg, 62);
});

test('consented Fiteatsy biomarkers retain clinical values in the original biomarker contract', () => {
  const result = externalConnectedBiomarkers({ biomarkers: [{ biomarkerId: 'hba1c', name: 'HbA1c', value: 5.6, unit: '%', clinicalStatus: 'NORMAL', testDate: '2026-10-01', referenceRange: '4.0–5.6' }] });
  assert.equal(result.length, 1);
  assert.equal(result[0].canonicalBiomarkerId, 'hba1c');
  assert.equal(result[0].observationDate, '2026-10-01');
  assert.equal(result[0].reviewStatus, 'CONFIRMED');
  assert.equal(result[0].source, 'FITEATSY_CONNECTION');
});
