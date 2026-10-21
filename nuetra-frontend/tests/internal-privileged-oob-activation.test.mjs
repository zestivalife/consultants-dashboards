import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const source = fs.readFileSync(new URL('../pages/internal-admin/activate.js', import.meta.url), 'utf8');

test('internal privileged activation accepts a secure one-time handoff without email', () => {
  assert.match(source, /One-time enrolment credential/);
  assert.match(source, /minLength=\{40\}/);
  assert.match(source, /body:\{token:enrolmentToken,password\}/);
  assert.match(source, /setEnrolmentToken\(''\)/);
});

test('query credentials are removed from browser history before activation', () => {
  assert.match(source, /window\.history\.replaceState\(\{\},'', '\/internal-admin\/activate'\)/);
  assert.doesNotMatch(source, /localStorage|sessionStorage/);
});

test('MFA remains mandatory after password enrolment', () => {
  assert.match(source, /MFA is confirmed/);
  assert.match(source, /\/auth\/internal-privileged-invitations\/confirm-mfa/);
  assert.match(source, /pattern="\[0-9\]\{6\}"/);
});
