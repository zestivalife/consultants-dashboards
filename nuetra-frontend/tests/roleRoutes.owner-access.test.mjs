import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const source = await readFile(new URL('../lib/roleRoutes.js', import.meta.url), 'utf8');
const roleRoutes = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

function ownerUser(overrides = {}) {
  return {
    role: 'platform_owner',
    permissions: [
      'fiteatsy.qa.identity.create',
      'fiteatsy.qa.session.issue',
    ],
    access_profile: {
      active_product: {
        name: 'FitEatsy',
        status: 'ACTIVE',
      },
      workspace: {
        id: 'care-delivery',
        landing_page: '/dashboard/provider',
      },
    },
    ...overrides,
  };
}

const canonicalOwner = ownerUser();
assert.equal(roleRoutes.isAccessAllowed(canonicalOwner, roleRoutes.OWNER_ACCESS_POLICY), true);
assert.equal(roleRoutes.getDashboardPathForUser(canonicalOwner), '/dashboard/owner');

assert.equal(
  roleRoutes.isAccessAllowed(ownerUser({ role: 'superuser' }), roleRoutes.OWNER_ACCESS_POLICY),
  false,
  'legacy superuser must not satisfy the canonical owner contract',
);
assert.equal(
  roleRoutes.isAccessAllowed(ownerUser({ role: 'senior_consultant' }), roleRoutes.OWNER_ACCESS_POLICY),
  false,
  'Senior Consultant must remain denied',
);
assert.equal(
  roleRoutes.isAccessAllowed(ownerUser({ role: 'admin' }), roleRoutes.OWNER_ACCESS_POLICY),
  false,
  'Admin must not inherit Platform Owner access',
);
assert.equal(
  roleRoutes.isAccessAllowed(ownerUser({ role: 'consultant' }), roleRoutes.OWNER_ACCESS_POLICY),
  false,
  'Consultant must remain denied',
);

const missingEntitlement = ownerUser({
  access_profile: {
    active_product: null,
    workspace: { id: 'platform-operations', landing_page: '/dashboard/owner' },
  },
});
assert.equal(roleRoutes.isAccessAllowed(missingEntitlement, roleRoutes.OWNER_ACCESS_POLICY), false);
assert.equal(roleRoutes.getDashboardPathForUser(missingEntitlement), '/dashboard/team-member');

const inactiveEntitlement = ownerUser({
  access_profile: {
    active_product: { name: 'FitEatsy', status: 'INACTIVE' },
    workspace: { id: 'platform-operations', landing_page: '/dashboard/owner' },
  },
});
assert.equal(roleRoutes.isAccessAllowed(inactiveEntitlement, roleRoutes.OWNER_ACCESS_POLICY), false);

const wrongProduct = ownerUser({
  access_profile: {
    active_product: { name: 'Nuetra', status: 'ACTIVE' },
    workspace: { id: 'platform-operations', landing_page: '/dashboard/owner' },
  },
});
assert.equal(roleRoutes.isAccessAllowed(wrongProduct, roleRoutes.OWNER_ACCESS_POLICY), false);

assert.equal(
  roleRoutes.isAccessAllowed(
    ownerUser({ permissions: ['fiteatsy.qa.identity.create'] }),
    roleRoutes.OWNER_ACCESS_POLICY,
  ),
  true,
  'workspace visibility is role plus entitlement; operation permissions remain route-specific',
);

console.log('Platform Owner role + FitEatsy entitlement access matrix: PASS');
