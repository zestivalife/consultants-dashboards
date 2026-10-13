import assert from 'node:assert/strict';
import test from 'node:test';
import { EXTERNAL_P1_MODULES, ASSESSMENT_CONTROLS, EXPORT_FORMATS } from '../components/external/p1/externalP1Catalog.mjs';
import { buildAnalyticsViewModel, buildModuleViewModel, buildRenewalAttention, safeCommunicationPreview } from '../components/external/p1/externalP1ViewModels.mjs';
import { createExternalP1Adapter, ExternalP1CapabilityError } from '../components/external/p1/externalP1Adapter.mjs';

test('catalog covers every external P1 product module and builder/export contracts', () => {
  assert.deepEqual(Object.keys(EXTERNAL_P1_MODULES), ['clientPortal', 'team', 'billing', 'renewals', 'analytics', 'templates', 'assessments', 'communication', 'referrals', 'progressReport', 'export', 'audit']);
  assert.ok(ASSESSMENT_CONTROLS.includes('CONDITIONAL_SECTION'));
  assert.deepEqual(EXPORT_FORMATS.diet_plan_history, ['PDF', 'DOCX']);
});

test('disabled capabilities never expose supplied records', () => {
  const model = buildModuleViewModel({ moduleKey: 'billing', capabilities: {}, records: [{ id: 'private-invoice' }] });
  assert.equal(model.capability.state, 'UNAVAILABLE');
  assert.deepEqual(model.records, []);
});

test('analytics displays connected source values only and never invents metrics', () => {
  const model = buildAnalyticsViewModel({ capabilities: { practice_analytics: true }, metrics: { active: { label: 'Active clients', value: 12, source: 'CONNECTED' }, revenue: { label: 'Revenue' }, guessed: { value: 99, source: 'ESTIMATE' } } });
  assert.deepEqual(model.metrics, [{ key: 'active', label: 'Active clients', value: 12, period: null }]);
  assert.equal(buildAnalyticsViewModel({ capabilities: { practice_analytics: true } }).isEmpty, true);
});

test('renewals use factual expiry and communication previews redact clinical details', () => {
  assert.equal(buildRenewalAttention({ expiryDate: '2026-10-20' }, new Date('2026-10-13T00:00:00Z')).daysRemaining, 7);
  assert.doesNotMatch(safeCommunicationPreview('Diagnosis: diabetes. Your appointment is tomorrow.'), /diabetes/i);
});

test('adapter fails closed for internal tenants and requires idempotency for writes', async () => {
  const internal = createExternalP1Adapter({ transport: async () => ({}), getContext: async () => ({ tenantId: 't1', tenantType: 'ZESTIVA_INTERNAL', capabilities: { client_portal: true } }) });
  await assert.rejects(() => internal.loadModule('client_portal', 'portal'), ExternalP1CapabilityError);
  const external = createExternalP1Adapter({ transport: async (path, options) => ({ path, options }), getContext: async () => ({ tenantId: 't2', tenantType: 'PRACTICE', capabilities: { practice_templates: true } }) });
  assert.throws(() => external.execute('practice_templates', 'templates', 'archive', {}), /idempotencyKey/);
  const result = await external.execute('practice_templates', 'templates', 'archive', { id: 'x' }, 'once-1');
  assert.equal(result.options.headers['X-Tenant-Id'], undefined);
  assert.equal(result.options.credentials, 'include');
  assert.equal(result.options.headers['Idempotency-Key'], 'once-1');
});
