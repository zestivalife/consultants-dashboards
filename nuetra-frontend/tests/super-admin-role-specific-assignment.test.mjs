import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workspace = readFileSync(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');
const api = readFileSync(new URL('../lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8');
const gateway = readFileSync(new URL('../../api-gateway/app/routers/fiteatsy_bridge.py', import.meta.url), 'utf8');

test('lead drawer separates internal Senior and External Consultant assignment authorities', () => {
  assert.match(workspace, /assignmentAuthority === 'EXTERNAL_PRACTICE'/);
  assert.match(workspace, /createFiteatsyExternalPracticeReferral/);
  assert.match(workspace, /relationshipType: 'CLIENT_CARE'/);
  assert.match(workspace, /Connection PIN and consent flow/);
});

test('external referrals use a dedicated Gateway operation', () => {
  assert.match(api, /external-practice-referrals\/professionals/);
  assert.match(api, /external-practice-referrals'/);
  assert.match(gateway, /external-practice-referrals\/professionals/);
  assert.match(gateway, /external_practice_referral/);
});
