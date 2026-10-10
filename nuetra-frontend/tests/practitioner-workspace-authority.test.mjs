import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const roleRoutes = readFileSync(new URL('../lib/roleRoutes.js', import.meta.url), 'utf8');
const providerPage = readFileSync(new URL('../pages/dashboard/provider.js', import.meta.url), 'utf8');

const consultantPolicy = roleRoutes.match(/CONSULTANT_ACCESS_POLICY = \{\s*roles: \[([^\]]+)]/)?.[1] || '';
const professionalRoutes = roleRoutes.match(/PROFESSIONAL_ROUTE_MAP = \{([\s\S]*?)\n\};/)?.[1] || '';
const platformRoles = roleRoutes.match(/FOOD_AUTHORISATION_ROLE_KEYS = new Set\(\[([^\]]+)]\)/)?.[1] || '';

test('practitioner uses the existing provider professional workspace', () => {
  assert.match(professionalRoutes, /practitioner:\s*'\/dashboard\/provider'/);
  assert.match(providerPage, /CONSULTANT_ACCESS_POLICY/);
  assert.ok(consultantPolicy.includes("'practitioner'"));
});

test('existing delivery roles remain admitted', () => {
  for (const role of ['consultant', 'provider', 'dietician', 'senior_consultant']) {
    assert.ok(consultantPolicy.includes(`'${role}'`), role);
  }
});

test('mentor and platform roles are not widened into practitioner workspace policy', () => {
  for (const role of ['mentor', 'admin', 'organization_admin', 'platform_owner', 'super_admin']) {
    assert.equal(consultantPolicy.includes(`'${role}'`), false, role);
  }
});

test('practitioner does not gain platform authority', () => {
  assert.equal(platformRoles.includes("'practitioner'"), false);
});
