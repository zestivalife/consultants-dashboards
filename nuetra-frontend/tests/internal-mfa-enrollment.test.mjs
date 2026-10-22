import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

test('internal privileged routing enforces password change before MFA enrollment', () => {
  const routes = readFileSync(new URL('../lib/roleRoutes.js', import.meta.url), 'utf8');
  assert.match(routes, /must_change_password[\s\S]*change-temporary-password/);
  assert.match(routes, /internal_super_admin[\s\S]*mfa_enabled[\s\S]*auth\/enrol-mfa/);
});

test('MFA enrollment uses authenticated start and confirmation endpoints', () => {
  const page = readFileSync(new URL('../pages/auth/enrol-mfa.js', import.meta.url), 'utf8');
  const api = readFileSync(new URL('../lib/api.js', import.meta.url), 'utf8');
  assert.match(page, /beginInternalMfaEnrollment/);
  assert.match(page, /confirmInternalMfaEnrollment/);
  assert.match(page, /one-time-code/);
  assert.match(api, /auth\/internal-mfa\/enrol/);
  assert.match(api, /auth\/internal-mfa\/confirm/);
});
