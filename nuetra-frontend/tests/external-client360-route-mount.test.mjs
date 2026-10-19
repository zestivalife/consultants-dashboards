import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { resolveClient360Navigation } from '../lib/client360Capabilities.mjs';
import { resolveConsultantWorkspace, TENANT_CONTEXT_STATUS } from '../lib/tenantContext.mjs';

const read = path => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');
const adapter = read('components/external/ExternalConsultantWorkspaceRoute.jsx');
const consultantRoute = read('pages/dashboard/consultant.js');
const providerRoute = read('pages/dashboard/provider.js');
const externalClient360 = read('components/external/ExternalClient360.jsx');
const sharedWorkspace = read('components/platform/PlatformWorkspace.jsx');

test('all consultant landing routes use the external-only tenant adapter', () => {
  assert.match(consultantRoute, /ExternalConsultantWorkspaceRoute/);
  assert.match(providerRoute, /ExternalConsultantWorkspaceRoute/);
  assert.match(adapter, /workspace === 'EXTERNAL'.*<ExternalSaaSWorkspace/s);
  assert.match(adapter, /workspace === 'IN_HOUSE'.*<ConsultantWorkspace/s);
  assert.equal(resolveConsultantWorkspace({ status: TENANT_CONTEXT_STATUS.READY, tenantType: 'PRACTICE', membershipStatus: 'active' }), 'EXTERNAL');
  assert.equal(resolveConsultantWorkspace({ status: TENANT_CONTEXT_STATUS.READY, tenantType: 'ZESTIVA_INTERNAL', membershipStatus: 'active' }), 'IN_HOUSE');
});

test('senior, admin, mentor and organization entry points remain outside the external adapter', () => {
  for (const route of ['senior-consultant', 'admin', 'mentor', 'corporate-admin']) {
    assert.doesNotMatch(read(`pages/dashboard/${route}.js`), /ExternalConsultantWorkspaceRoute/);
  }
  assert.doesNotMatch(sharedWorkspace, /ExternalConsultantWorkspaceRoute/);
});

test('external Client360 keeps five responsive primary sections without horizontal navigation', () => {
  assert.match(externalClient360, /grid-cols-5/);
  assert.match(externalClient360, /Client 360 primary sections/);
  assert.doesNotMatch(externalClient360, /client360-navigation[^>]*overflow-x-auto/);
  const navigation = resolveClient360Navigation({ profession: 'HEALTH_COACH', capabilities: ['GOALS_PROGRESS'], professionWorkspace: true });
  assert.deepEqual(navigation.map(section => section.label), ['Overview', 'Health', 'Care', 'Progress', 'Documents & Admin']);
});

test('canonical capabilities prevent diet leakage and expose nutrition modules only when governed', () => {
  const healthCoach = resolveClient360Navigation({ profession: 'HEALTH_COACH', capabilities: ['GOALS_PROGRESS'], professionWorkspace: true }).flatMap(section => section.modules);
  assert.equal(healthCoach.includes('Nutrition'), false);
  assert.equal(healthCoach.includes('Diet Plan'), false);
  assert.equal(healthCoach.includes('Biomarkers'), false);

  const nutritionist = resolveClient360Navigation({ profession: 'NUTRITIONIST', capabilities: ['BIOMARKERS', 'MEASUREMENTS', 'DIET_PLAN_AUTHORING', 'GOALS_PROGRESS', 'PROGRESS_REPORTS'], professionWorkspace: true }).flatMap(section => section.modules);
  for (const module of ['Biomarkers', 'Nutrition', 'Diet Plan', 'Health Records', 'Reports', 'Progress Reports']) assert.equal(nutritionist.includes(module), true);
  assert.match(externalClient360, /showNutritionWorkspace=\{capabilityState\.dietPlan\}/);
  assert.match(externalClient360, /showNutritionWorkspace&&<section/);
});
