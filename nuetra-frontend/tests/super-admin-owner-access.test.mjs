import assert from 'node:assert/strict';
import test from 'node:test';

import {
  OWNER_ACCESS_POLICY,
  getPostAuthPathForUser,
  isAccessAllowed,
} from '../lib/roleRoutes.js';

for (const role of ['superuser', 'super_admin', 'platform_owner']) {
  test(`${role} reaches the owner workspace without tenant enrichment`, () => {
    const user = { role, status: 'ACTIVE', permissions: [], access_profile: null };

    assert.equal(getPostAuthPathForUser(user), '/dashboard/owner');
    assert.equal(isAccessAllowed(user, OWNER_ACCESS_POLICY), true);
  });
}

test('a non-platform role is not admitted by the owner policy', () => {
  const user = { role: 'consultant', status: 'ACTIVE', permissions: [] };

  assert.equal(isAccessAllowed(user, OWNER_ACCESS_POLICY), false);
});
