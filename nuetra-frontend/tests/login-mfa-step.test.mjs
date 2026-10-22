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
  assert.match(loginPage, /isBackendAuthEnabled && mfaStep/);
  assert.doesNotMatch(loginPage, /privileged Internal accounts/);
});

test('authenticator step appears only after an explicit backend MFA requirement', () => {
  assert.match(loginPage, /result\?\.error && \/MFA code required\/i/);
  assert.match(loginPage, /setMfaStep\(true\)/);
  assert.match(loginPage, /required\s+value=\{form\.mfaCode\}/);
});

test('backend MFA enforcement remains limited to internal_super_admin', () => {
  assert.match(authService, /user\.role\.name == "internal_super_admin"/);
  assert.match(authService, /verify_totp\(user, mfa_code\)/);
  assert.doesNotMatch(authService, /user\.role\.name == "superuser"[\s\S]{0,200}verify_totp/);
});
