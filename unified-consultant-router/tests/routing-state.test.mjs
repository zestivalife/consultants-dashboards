import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';
import { issueRoutingState, resolveProductLine, verifyRoutingState } from '../lib/routing-state.mjs';

const secret = 'router-test-secret-that-is-at-least-thirty-two-characters';
const payload = (tenantType, membershipStatus = 'ACTIVE') => ({ data: { currentTenant: { tenantType, membershipStatus } } });

test('canonical tenant types select the correct isolated origin', () => {
  assert.equal(resolveProductLine(payload('ZESTIVA_INTERNAL')), 'IN_HOUSE');
  assert.equal(resolveProductLine(payload('INDEPENDENT_CONSULTANT')), 'EXTERNAL');
  assert.equal(resolveProductLine(payload('PRACTICE')), 'EXTERNAL');
  assert.equal(resolveProductLine(payload('CLINIC')), 'EXTERNAL');
});

test('missing, unknown, and inactive tenant context fail closed', () => {
  assert.equal(resolveProductLine({ data: {} }), null);
  assert.equal(resolveProductLine(payload('UNKNOWN')), null);
  assert.equal(resolveProductLine(payload('ZESTIVA_INTERNAL', 'SUSPENDED')), null);
});

test('signed routing state verifies and expires', async () => {
  const state = await issueRoutingState('EXTERNAL', secret, 1_000);
  assert.equal(await verifyRoutingState(state, secret, 2_000), 'EXTERNAL');
  assert.equal(await verifyRoutingState(state, secret, 1_000 + 16 * 60 * 1_000), null);
});

test('tampered routing state fails closed', async () => {
  const state = await issueRoutingState('IN_HOUSE', secret, 1_000);
  assert.equal(await verifyRoutingState(`${state}x`, secret, 2_000), null);
});

test('login is the canonical routing-state cleanup boundary', () => {
  const middleware = fs.readFileSync(new URL('../middleware.js', import.meta.url), 'utf8');
  assert.match(middleware, /pathname === '\/login'/);
  assert.match(middleware, /clearRoutingCookies\(rewrite\(request, inHouseOrigin\)\)/);
  assert.match(middleware, /response\.cookies\.delete\(ROUTING_COOKIE\)/);
  assert.match(middleware, /response\.cookies\.delete\(PUBLIC_ORIGIN_COOKIE\)/);
});

test('authenticated routes never fall back to either product without valid routing state', () => {
  const middleware = fs.readFileSync(new URL('../middleware.js', import.meta.url), 'utf8');
  assert.match(middleware, /if \(!productLine\)/);
  assert.match(middleware, /resolver\.pathname = '\/__router\/resolve'/);
  assert.doesNotMatch(middleware, /!productLine[^]*rewrite\(request, inHouseOrigin\)/);
});
