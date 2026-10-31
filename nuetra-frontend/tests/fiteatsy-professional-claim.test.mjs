import assert from 'node:assert/strict';
import test from 'node:test';

import { needsFiteatsyProfessionalClaimRefresh } from '../lib/fiteatsyProfessionalClaim.js';

function token(payload) {
  const encode = value => Buffer.from(JSON.stringify(value)).toString('base64url');
  return `${encode({ alg: 'none' })}.${encode(payload)}.`;
}

test('external consultant sessions refresh when the canonical identity claim is absent', () => {
  assert.equal(needsFiteatsyProfessionalClaimRefresh({
    token: token({ sub: 'external-user' }),
    user: { currentTenant: { tenantType: 'INDEPENDENT_CONSULTANT' } },
  }), true);
});

test('external consultant sessions do not refresh when the canonical claim is present', () => {
  assert.equal(needsFiteatsyProfessionalClaimRefresh({
    token: token({ sub: 'external-user', fiteatsy_professional_id: 'ext_00000000-0000-4000-8000-000000000001' }),
    user: { currentTenant: { tenantType: 'PRACTICE' } },
  }), false);
});

test('internal and privileged sessions are never refreshed by the external mapping recovery', () => {
  for (const user of [
    { role: 'consultant', currentTenant: { tenantType: 'ZESTIVA_INTERNAL' } },
    { role: 'senior_consultant', currentTenant: { tenantType: 'ZESTIVA_INTERNAL' } },
    { role: 'platform_owner' },
    { role: 'admin' },
  ]) {
    assert.equal(needsFiteatsyProfessionalClaimRefresh({ token: token({ sub: 'user' }), user }), false);
  }
});

test('malformed external access tokens request a safe refresh', () => {
  assert.equal(needsFiteatsyProfessionalClaimRefresh({
    token: 'not-a-jwt',
    user: { currentTenant: { tenantType: 'INDEPENDENT_CONSULTANT' } },
  }), true);
});
