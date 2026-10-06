import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');

test('external Consultant login resumes governed onboarding before workspace access', () => {
  const auth = read('context/AuthContext.js');
  const api = read('lib/api.js');
  const fiteatsyApi = read('lib/fiteatsyConsultantsApi.js');
  const canonicalPage = read('pages/onboarding/index.js');
  const page = read('pages/onboarding/consultant.js');
  assert.match(auth, /getGovernedPostLoginPath/);
  assert.match(auth, /getFiteatsyConsultantOnboarding/);
  assert.match(auth, /: '\/onboarding';/);
  assert.match(fiteatsyApi, /getFiteatsyConsultantOnboarding/);
  assert.match(fiteatsyApi, /requestFiteatsy\('\/v1\/consultants\/onboarding'/);
  assert.match(fiteatsyApi, /requestFiteatsy\('\/v1\/consultants\/onboarding\/complete'/);
  assert.doesNotMatch(api, /apiRequest\('\/consultants\/onboarding/);
  assert.match(canonicalPage, /export \{ default \} from '\.\/consultant';/);
  assert.match(page, /completeFiteatsyConsultantOnboarding/);
  assert.match(page, /Client health intake is separate/);
});

test('P0.2 onboarding contains Consultant practice fields and no client account flow', () => {
  const page = read('pages/onboarding/consultant.js');
  for (const field of ['Consultant name', 'Professional title', 'Speciality', 'Practice name', 'Country', 'Timezone']) {
    assert.match(page, new RegExp(field));
  }
  assert.doesNotMatch(page, /HealthKit|Health Connect|client password|client signup/i);
});

test('canonical onboarding route preserves governed access and completion routing', () => {
  const auth = read('context/AuthContext.js');
  const page = read('pages/onboarding/consultant.js');
  const signup = read('pages/signup.js');

  assert.match(signup, /: '\/onboarding'/);
  assert.match(page, /if \(!user\) \{ router\.replace\('\/login'\); return; \}/);
  assert.match(page, /value\?\.workspaceReady/);
  assert.match(page, /router\.replace\('\/dashboard\/consultant'/);
  assert.doesNotMatch(page, /mobile_verified|email_verified|mobileVerified|emailVerified/);
  assert.doesNotMatch(page, /createClient|dummy client|seed client/i);
  assert.match(auth, /authAPI\.me\(\)/);
  assert.match(auth, /clearTokens\(\)/);
});
