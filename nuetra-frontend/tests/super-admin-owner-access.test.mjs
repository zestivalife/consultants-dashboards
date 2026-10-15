import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import {
  OWNER_ACCESS_POLICY,
  getPostAuthPathForUser,
  isAccessAllowed,
} from '../lib/roleRoutes.js';

const authContextSource = readFileSync(new URL('../context/AuthContext.js', import.meta.url), 'utf8');

test('governed post-login routing imports its account-action dependency', () => {
  assert.match(
    authContextSource,
    /import\s*\{[\s\S]*?getAccountActionRoute[\s\S]*?\}\s*from\s*['"]\.\.\/lib\/roleRoutes['"]/,
  );
  assert.match(authContextSource, /const accountActionRoute = getAccountActionRoute\(user\);/);
});

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
