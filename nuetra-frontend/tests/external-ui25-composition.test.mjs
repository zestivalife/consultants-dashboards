import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const dashboard=await readFile(new URL('../components/external/ExternalIntelligentHome.jsx',import.meta.url),'utf8');
const workspace=await readFile(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const client360=await readFile(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');

test('UI-2.5 uses asymmetric bento composition instead of eight equal KPI cards',()=>{
  for(const token of ['FeaturedPriority','OnboardingProgress','PracticeSnapshot','Primary practice metrics','Secondary practice metrics'])assert.match(dashboard,new RegExp(token));
  assert.match(dashboard,/lg:col-span-7/);
  assert.match(dashboard,/lg:col-span-5/);
  assert.match(dashboard,/xl:col-span-4/);
  assert.doesNotMatch(dashboard,/KPI\.map/);
});

test('UI-2.5 keeps intelligence and onboarding source truth unchanged',()=>{
  assert.match(dashboard,/buildDashboardIntelligence\(\{clients,resources:data\.resources,notifications:data\.notifications\}\)/);
  assert.match(workspace,/deriveOnboardingState\(client\)/);
  assert.match(workspace,/onboarding\.completionPercent/);
  assert.match(dashboard,/No completion rate is inferred/);
});

test('UI-2.5 integrates premium External-only surfaces and preserves Client360 workflows',()=>{
  assert.match(workspace,/lg:pl-56/);
  assert.match(workspace,/bg-\[#ecebe6\]/);
  assert.match(client360,/Health progress/);
  assert.match(client360,/active === 'Diet Plan'/);
  assert.match(client360,/active === 'Health Records'/);
  assert.match(client360,/active === 'Biomarkers'/);
});
