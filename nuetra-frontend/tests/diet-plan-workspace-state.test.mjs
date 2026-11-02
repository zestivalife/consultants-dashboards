import assert from 'node:assert/strict';
import test from 'node:test';

import { createdDraftPresentation, loadDietPlanWorkspace } from '../lib/dietPlanWorkspaceState.mjs';

const detail = (id) => ({ plan: { id, title: `Plan ${id}` } });
const project = (value) => ({ id: value.plan.id, name: value.plan.title });
const api = (overrides = {}) => ({
  list: async () => ({ items: [{ id: 'plan-1' }] }),
  assessment: async () => ({ readiness_status: 'READY', id: 'assessment-1', version: 2 }),
  context: async () => ({ measurement_context: {} }),
  detail: async (id) => detail(id),
  ...overrides,
});

test('successful listing and detail retrieval selects and renders the created draft', async () => {
  const result = await loadDietPlanWorkspace({ clientId: 'client-1', preferredId: 'plan-1', api: api(), projectDetail: project });
  assert.equal(result.plansStatus, 'ready');
  assert.equal(result.preferredLoaded, true);
  assert.equal(result.readiness.outcome, 'READY');
  assert.deepEqual(result.plans.map((plan) => plan.id), ['plan-1']);
  assert.equal(createdDraftPresentation('plan-1', result).state, 'ready');
});

test('plan listing failure is not converted into an empty plan list and readiness still resolves', async () => {
  const denied = Object.assign(new Error('Denied'), { status: 403 });
  const result = await loadDietPlanWorkspace({ clientId: 'client-1', api: api({ list: async () => { throw denied; } }), projectDetail: project });
  assert.equal(result.plansStatus, 'error');
  assert.equal(result.plans, null);
  assert.equal(result.readiness.outcome, 'READY');
  assert.equal(result.loadError, 'Diet plans could not be loaded.');
});

test('assessment failures leave loading with explicit unavailable and error outcomes', async () => {
  const unavailable = await loadDietPlanWorkspace({ clientId: 'client-1', api: api({ assessment: async () => { throw Object.assign(new Error('Missing'), { status: 404 }); } }), projectDetail: project });
  assert.equal(unavailable.readiness.outcome, 'UNAVAILABLE');
  const failed = await loadDietPlanWorkspace({ clientId: 'client-1', api: api({ assessment: async () => { throw Object.assign(new Error('Down'), { status: 503 }); } }), projectDetail: project });
  assert.equal(failed.readiness.outcome, 'ERROR');
});

test('creation success followed by retrieval failure preserves the authoritative plan id', async () => {
  const result = await loadDietPlanWorkspace({
    clientId: 'client-1',
    preferredId: 'created-plan',
    api: api({ list: async () => ({ items: [{ id: 'created-plan' }] }), detail: async () => { throw Object.assign(new Error('Reload failed'), { status: 500 }); } }),
    projectDetail: project,
  });
  const presentation = createdDraftPresentation('created-plan', result);
  assert.equal(presentation.state, 'reload_failed');
  assert.equal(presentation.createdId, 'created-plan');
  assert.match(presentation.message, /do not create another one/i);
});

test('existing draft details can partially load without fabricating missing plans', async () => {
  const result = await loadDietPlanWorkspace({
    clientId: 'client-1',
    currentId: 'plan-1',
    api: api({ list: async () => ({ items: [{ id: 'plan-1' }, { id: 'plan-2' }] }), detail: async (id) => id === 'plan-2' ? Promise.reject(new Error('Failed')) : detail(id) }),
    projectDetail: project,
  });
  assert.equal(result.plansStatus, 'partial');
  assert.deepEqual(result.plans.map((plan) => plan.id), ['plan-1']);
  assert.match(result.loadError, /1 Diet Plan detail could not be loaded/);
});
