import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const read = (path) => fs.readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');

test('external Consultant login resumes governed onboarding before workspace access', () => {
  const auth = read('context/AuthContext.js');
  const api = read('lib/api.js');
  const page = read('pages/onboarding/consultant.js');
  assert.match(auth, /getGovernedPostLoginPath/);
  assert.match(auth, /getConsultantOnboarding/);
  assert.match(api, /\/consultants\/onboarding/);
  assert.match(page, /completeConsultantOnboarding/);
  assert.match(page, /Client health intake is separate/);
});

test('P0.2 onboarding contains Consultant practice fields and no client account flow', () => {
  const page = read('pages/onboarding/consultant.js');
  for (const field of ['Consultant name', 'Professional title', 'Speciality', 'Practice name', 'Country', 'Timezone']) {
    assert.match(page, new RegExp(field));
  }
  assert.doesNotMatch(page, /HealthKit|Health Connect|client password|client signup/i);
});
