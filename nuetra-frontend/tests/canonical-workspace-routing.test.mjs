import assert from 'node:assert/strict';
import test from 'node:test';

import {
  getDashboardPathForUser,
  getEligibleWorkspaceIds,
  isCanonicalWorkspaceAllowed,
} from '../lib/roleRoutes.js';

const tenant = (tenantType) => ({ tenantId: 'tenant-1', tenantType, currentMembershipRole: 'OWNER', membershipStatus: 'ACTIVE', resolutionPath: 'MEMBERSHIP' });
const user = (role, tenantType, extra = {}) => ({ role, status: 'ACTIVE', currentTenant: tenantType ? tenant(tenantType) : null, ...extra });

test('routes backend-authorised consultant memberships to canonical workspaces', () => {
  assert.deepEqual(getEligibleWorkspaceIds(user('consultant', 'ZESTIVA_INTERNAL')), ['internal-consultant']);
  assert.deepEqual(getEligibleWorkspaceIds(user('consultant', 'PRACTICE')), ['external-consultant']);
  assert.deepEqual(getEligibleWorkspaceIds(user('senior_consultant', 'ZESTIVA_INTERNAL')), ['senior-consultant']);
  assert.equal(getDashboardPathForUser(user('consultant', 'PRACTICE')), '/workspace/external-consultant');
});

test('manual URL switching cannot grant another workspace', () => {
  const external = user('consultant', 'PRACTICE');
  assert.equal(isCanonicalWorkspaceAllowed(external, 'external-consultant'), true);
  assert.equal(isCanonicalWorkspaceAllowed(external, 'internal-consultant'), false);
  assert.equal(isCanonicalWorkspaceAllowed(external, 'super-admin'), false);
});

test('missing, inactive, or non-membership tenant authority fails closed', () => {
  assert.deepEqual(getEligibleWorkspaceIds(user('consultant')), []);
  const inactive = user('consultant', 'PRACTICE');
  inactive.currentTenant.membershipStatus = 'INACTIVE';
  assert.deepEqual(getEligibleWorkspaceIds(inactive), []);
  const untrusted = user('consultant', 'PRACTICE');
  untrusted.currentTenant.resolutionPath = 'URL';
  assert.deepEqual(getEligibleWorkspaceIds(untrusted), []);
});
