import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { assertCurrentClientBinding, resolveClientDietChartAction } from '../lib/clientDietChartBinding.mjs';
import { resolveClient360Tabs } from '../lib/client360Capabilities.mjs';

const client360 = readFileSync(new URL('../components/external/ExternalClient360.jsx', import.meta.url), 'utf8');
const workspace = readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx', import.meta.url), 'utf8');

test('current-client Diet Chart action is state-aware', () => {
  assert.equal(resolveClientDietChartAction(), 'Generate Diet Chart');
  assert.equal(resolveClientDietChartAction({ plan: { id: 'draft-a', status: 'DRAFT' } }), 'Continue Diet Chart');
  assert.equal(resolveClientDietChartAction({ plan: { id: 'published-a', status: 'PUBLISHED' } }), 'View Diet Chart');
});

test('Diet Chart authoring fails closed on cross-client state', () => {
  assert.equal(assertCurrentClientBinding('client-a', 'client-a'), 'client-a');
  assert.equal(assertCurrentClientBinding('client-b', 'client-b'), 'client-b');
  assert.throws(() => assertCurrentClientBinding('client-a', 'client-b'), /DIET_CHART_CLIENT_CONTEXT_MISMATCH/);
});

test('active workspace passes its authoritative profession configuration into Client360', () => {
  assert.match(workspace, /practiceConfiguration:practiceConfig/);
  assert.match(client360, /const professionConfig=client\.practiceConfiguration/);
  assert.doesNotMatch(client360, /getPracticeConfiguration/);
});

test('nutrition capabilities expose Biomarkers and Diet Plan for the open client only', () => {
  const tabs = resolveClient360Tabs({
    profession: 'NUTRITIONIST',
    capabilities: ['BIOMARKERS', 'DIET_PLAN_AUTHORING'],
  });
  assert.ok(tabs.includes('Biomarkers'));
  assert.ok(tabs.includes('Diet Plan'));
  assert.match(client360, /getExternalClientBiomarkers\(client\.id\)/);
  assert.match(client360, /getExternalTransientBiomarkers\(client\.id\)/);
  assert.match(client360, /getExternalDietPlan\(client\.id\)/);
  assert.match(client360, /clientId=\{dietPlanClientId\}/);
});

test('non-diet professions do not inherit the Diet Chart action', () => {
  for (const profession of ['HEALTH_COACH', 'PSYCHOLOGIST', 'PHYSIOTHERAPIST']) {
    const tabs = resolveClient360Tabs({ profession, capabilities: ['GOALS_PROGRESS'] });
    assert.equal(tabs.includes('Diet Plan'), false);
    assert.equal(tabs.includes('Biomarkers'), false);
  }
});
