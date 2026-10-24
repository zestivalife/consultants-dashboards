import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const loginPage = readFileSync(new URL('../pages/login.js', import.meta.url), 'utf8');
const authService = readFileSync(
  new URL('../../services/auth-service/app/services/auth_service.py', import.meta.url),
  'utf8',
);

test('initial login requests only identifier and password', () => {
  assert.match(loginPage, /Email or mobile number/);
  assert.match(loginPage, /Enter your password/);
  assert.doesNotMatch(loginPage, /mfaStep|mfaCode|Authenticator code|one-time-code/);
});

test('backend preserves privileged isolation without an MFA runtime dependency', () => {
  assert.match(authService, /user\.role\.name == "internal_super_admin"/);
  assert.match(authService, /assert_no_external_entitlement/);
  assert.doesNotMatch(authService, /verify_totp|mfa_code|mfa_assured/);
});
