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
