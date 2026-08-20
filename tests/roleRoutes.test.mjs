import assert from 'node:assert/strict';
import test from 'node:test';
import { getDashboardPathForUser, getEffectiveWorkspaceRole, isAccessAllowed } from '../nuetra-frontend/lib/roleRoutes.js';

test('professional roles route correctly', () => {
  assert.equal(getDashboardPathForUser({ role: 'senior_consultant' }), '/dashboard/senior-consultant');
  assert.equal(getDashboardPathForUser({ role: 'consultant' }), '/dashboard/consultant');
  assert.equal(getDashboardPathForUser({ role: 'practitioner' }), '/dashboard/provider');
  assert.equal(getDashboardPathForUser({ role: 'mentor' }), '/dashboard/mentor');
  assert.equal(getDashboardPathForUser({ role: 'corporate_admin' }), '/dashboard/corporate-admin');
});

test('product professional role precedes organization context', () => {
  const user = { role: 'organization_admin', access_profile: { role: 'organization_admin', workspace: { id: 'organization-operations', landing_page: '/dashboard/corporate-admin' }, active_product: { role: 'senior_consultant' } } };
  assert.equal(getEffectiveWorkspaceRole(user), 'senior_consultant');
  assert.equal(getDashboardPathForUser(user), '/dashboard/senior-consultant');
  assert.equal(isAccessAllowed(user, { workspaceRoles: ['senior_consultant'] }), true);
  assert.equal(isAccessAllowed(user, { workspaceRoles: ['corporate_admin'] }), false);
});

test('unknown roles do not default to corporate admin', () => {
  const user = { role: 'unrecognised_role', permissions: [] };
  assert.equal(getDashboardPathForUser(user), '/dashboard/team-member');
  assert.equal(isAccessAllowed(user, { workspaceRoles: ['corporate_admin'] }), false);
});
