import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const workspace = readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx', import.meta.url), 'utf8');

test('external Diet Plans navigation is assignment-authorised without profession entitlement gating', () => {
  assert.match(workspace, /client360CapabilityState\(practiceConfig,\{externalConsultant:true\}\)\.dietPlan/);
  assert.match(workspace, /id!==['"]plans['"]\|\|dietPlanEnabled/);
  assert.match(workspace, /next===['"]plans['"]&&!dietPlanEnabled\?['"]dashboard['"]:next/);
  assert.match(workspace, /view===['"]plans['"]&&dietPlanEnabled\?<PlanHistory/);
});
