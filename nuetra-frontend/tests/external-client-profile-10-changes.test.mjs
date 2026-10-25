import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

import {
  calculateExternalBmi,
  calculateExternalWaistHipRatio,
  composeExternalClientProfile,
  formatDateOnlyDDMMYYYY,
  normalizeExternalDateOnly,
} from '../lib/externalClientProfile.mjs';

test('date-only presentation is DD/MM/YYYY and never includes a timestamp', () => {
  assert.equal(formatDateOnlyDDMMYYYY('1990-04-23T00:00:00.000Z'), '23/04/1990');
  assert.equal(formatDateOnlyDDMMYYYY(''), 'Not available');
  assert.equal(normalizeExternalDateOnly('1990-04-23T23:30:00.000Z'), '1990-04-23');
  assert.equal(normalizeExternalDateOnly('not-a-date'), null);
});

test('legacy timestamp DOB is normalized before form editing and overview rendering', () => {
  const profile = composeExternalClientProfile({ overview: { dateOfBirth: '1990-01-15T00:00:00.000Z' }, sections: {} }, {});
  assert.equal(profile.overview.dateOfBirth, '1990-01-15');
  assert.equal(formatDateOnlyDDMMYYYY(profile.overview.dateOfBirth), '15/01/1990');
});

test('BMI and waist-to-hip ratio are derived only from valid measurements', () => {
  assert.equal(calculateExternalBmi(170, 70), 24.2);
  assert.equal(calculateExternalBmi(undefined, 70), null);
  assert.equal(calculateExternalBmi(0, 70), null);
  assert.equal(calculateExternalWaistHipRatio(80, 100), 0.8);
  assert.equal(calculateExternalWaistHipRatio(80, 0), null);
});

test('profile and evidence completion reflect actual saved information', () => {
  const incomplete = composeExternalClientProfile({ overview: {}, sections: {} }, {});
  assert.equal(incomplete.overview.profileCompleteness, 0);
  assert.equal(incomplete.evidenceCompleteness, 0);
  const complete = composeExternalClientProfile({ overview: {}, sections: {} }, {
    date_of_birth: '1990-04-23',
    goals: ['Improve nutrition', 'Improve energy', 'Better sleep'],
    medical_history_narrative: 'No prior surgery.',
    sleep_stress_narrative: 'Seven hours sleep.',
    measurements: { height_cm: 170, weight_kg: 70, waist_cm: 80, hip_cm: 100 },
    health_record_dates: { record: { report_date: '2026-10-01', confirmation_date: '2026-10-02' } },
  });
  assert.equal(complete.overview.profileCompleteness, 100);
  assert.equal(complete.evidenceCompleteness, 100);
  assert.deepEqual(complete.sections.goals.selectedGoals, ['Improve nutrition', 'Improve energy', 'Better sleep']);
  assert.equal(complete.derived.bmi.value, 24.2);
  assert.equal(complete.derived.waistHipRatio, 0.8);
});

test('External Client360 renders ordinary-text editors and dedicated anthropometrics', () => {
  const component = fs.readFileSync(new URL('../components/external/ExternalClientProfileEnhancements.jsx', import.meta.url), 'utf8');
  assert.match(component, /3 selected/);
  assert.match(component, /Medical History/);
  assert.match(component, /Sleep & Stress/);
  assert.match(component, /Measurements & anthropometrics/);
  assert.match(component, /Waist-to-hip ratio/);
  assert.doesNotMatch(component, /JSON\.parse/);
});

test('all selected goals are passed into the persisted Diet Plan snapshot', () => {
  const component = fs.readFileSync(new URL('../components/external/ExternalMultiDietPlan.jsx', import.meta.url), 'utf8');
  assert.match(component, /health_goals: valueList\(context\?\.goals\)\.slice\(0, 3\)/);
  assert.match(component, /Health & wellness goals/);
});

test('Health Record dates are editable and enrichment uses the tenant-scoped Practice API', () => {
  const records = fs.readFileSync(new URL('../components/external/ExternalHealthRecords.jsx', import.meta.url), 'utf8');
  const api = fs.readFileSync(new URL('../lib/practiceOperationsApi.js', import.meta.url), 'utf8');
  assert.match(records, /report_date/);
  assert.match(records, /confirmation_date/);
  assert.match(api, /profile-enrichment/);
});
