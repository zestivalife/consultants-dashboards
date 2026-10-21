import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const workspace = readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx', import.meta.url), 'utf8');

test('global Diet Plans navigation and renderer fail closed behind canonical capability state', () => {
  assert.match(workspace, /client360CapabilityState\(practiceConfig\)\.dietPlan/);
  assert.match(workspace, /id!==['"]plans['"]\|\|dietPlanEnabled/);
  assert.match(workspace, /next===['"]plans['"]&&!dietPlanEnabled\?['"]dashboard['"]:next/);
  assert.match(workspace, /view===['"]plans['"]&&dietPlanEnabled\?<PlanHistory/);
});
