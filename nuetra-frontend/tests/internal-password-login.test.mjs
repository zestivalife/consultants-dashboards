import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

test('login UI and API use identifier plus password without an authenticator challenge', () => {
  const page = readFileSync(new URL('../pages/login.js', import.meta.url), 'utf8');
  const api = readFileSync(new URL('../lib/api.js', import.meta.url), 'utf8');
  const context = readFileSync(new URL('../context/AuthContext.js', import.meta.url), 'utf8');

  assert.doesNotMatch(page, /Authenticator code|mfaCode|one-time-code/);
  assert.doesNotMatch(api, /mfa_code|mfaCode/);
  assert.doesNotMatch(context, /mfaCode/);
});

test('privileged invitation activation preserves password replacement without TOTP', () => {
  const activation = readFileSync(new URL('../pages/internal-admin/activate.js', import.meta.url), 'utf8');

  assert.doesNotMatch(activation, /authenticator|confirm-mfa|otp_auth_uri|one-time-code|6-digit/i);
  assert.match(activation, /temporary password/i);
  assert.match(activation, /replace it/i);
});
