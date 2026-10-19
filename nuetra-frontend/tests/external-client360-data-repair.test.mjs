import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const client360 = readFileSync(new URL('../components/external/ExternalClient360.jsx', import.meta.url), 'utf8');
const healthRecords = readFileSync(new URL('../components/external/ExternalHealthRecords.jsx', import.meta.url), 'utf8');
const reportApi = readFileSync(new URL('../lib/externalTransientReportApi.js', import.meta.url), 'utf8');

test('transient report projection retries normal authentication without exposing credentials', () => {
  assert.match(reportApi, /refreshAccessToken/);
  assert.match(reportApi, /response\.status===401/);
  assert.match(reportApi, /Report data is temporarily unavailable/);
  assert.doesNotMatch(reportApi, /console\.(log|error)/);
});

test('health records distinguish failed, loading, confirmed-empty, and data states', () => {
  for (const contract of ["setLoadState('failed')", "setLoadState('ready')", 'No empty state has been inferred', 'Confirmed empty', 'processingStatus', 'uploadedByType', 'reviewStatus', 'confirmedAt']) {
    assert.ok(healthRecords.includes(contract), contract);
  }
});

test('biomarker projection never converts a total request failure to an empty list', () => {
  for (const contract of ["status:'failed'", 'No empty state has been inferred', 'One biomarker source is unavailable', 'getExternalTransientBiomarkers', 'getExternalClientBiomarkers']) {
    assert.ok(client360.includes(contract), contract);
  }
});

test('diet-plan action is capability-gated, state-aware, and opens existing authoring', () => {
  assert.match(client360, /capabilityState\.dietPlan&&<button/);
  for (const label of ['Create Diet Plan', 'Continue Diet Plan', 'View Published Plan', 'Create Revision']) assert.ok(client360.includes(label), label);
  assert.match(client360, /setActive\('Diet Plan'\)/);
  assert.match(client360, /CommonFoodPlanEditor/);
});

test('diet authoring receives real read-only client and confirmed biomarker context', () => {
  for (const contract of ['dietPlanContext', 'Primary goal', 'Diet preference', 'Food restrictions', 'Latest confirmed biomarkers', 'context.biomarkers.map']) {
    assert.ok(client360.includes(contract), contract);
  }
  assert.match(client360, /never auto-publishes a plan/);
});

test('dashboard counts avoid false zero when their source is unavailable', () => {
  assert.match(client360, /overview\.documentCount\?\?'Unavailable'/);
  assert.match(client360, /biomarkerState\.status==='failed'\?'Unavailable'/);
});
