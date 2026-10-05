import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { canonicalMobile } from '../lib/mobileIdentity.mjs';

const read=(path)=>fs.readFileSync(new URL(`../${path}`,import.meta.url),'utf8');

test('public signup creates a governed workspace without verification-first UX',()=>{
  const page=read('pages/signup.js');
  const api=read('lib/api.js');
  assert.match(page,/registerExternalConsultant/);
  assert.match(page,/Mobile number/);
  assert.match(page,/Professional role/);
  assert.match(page,/Years of experience/);
  assert.match(page,/Active clients/);
  assert.match(page,/Create Workspace/);
  assert.match(page,/RecaptchaCheckbox/);
  assert.match(page,/canonicalMobile/);
  assert.doesNotMatch(page,/Professional email|new-password|Password<\/span>/);
  assert.doesNotMatch(page,/Send OTP|Verify OTP|Resend OTP|startExternalSignup|verifyExternalSignup|resendExternalSignup/);
  assert.match(api,/\/auth\/external-signup\/register/);
  assert.doesNotMatch(page,/localStorage|access_token|bearer/i);
});

test('reCAPTCHA waits for the explicit Google readiness callback before rendering',()=>{
  const component=read('components/auth/RecaptchaCheckbox.jsx');
  assert.match(component,/onload=\$\{READY_CALLBACK\}&render=explicit/);
  assert.match(component,/typeof api\?\.render !== 'function'/);
  assert.match(component,/onReady=\{render\}/);
  assert.doesNotMatch(component,/!window\.grecaptcha \|\| widgetRef/);
});

test('signup includes the complete governed professional role catalogue and conditional practice data',()=>{
  const page=read('pages/signup.js');
  for (const role of ['DIETITIAN_NUTRITIONIST','HEALTH_COACH','WELLNESS_COACH','PSYCHOLOGIST','COUNSELLOR_THERAPIST','PHYSIOTHERAPIST','FITNESS_TRAINER','YOGA_MEDITATION_COACH','DIABETES_EDUCATOR','WOMENS_HEALTH_PRACTITIONER','LIFESTYLE_MEDICINE_PRACTITIONER','MENTOR','DOCTOR_PHYSICIAN','OTHER_HEALTHCARE_PROFESSIONAL']) {
    assert.match(page,new RegExp(role));
  }
  assert.match(page,/Practice name/);
  assert.match(page,/Primary qualification/);
  assert.match(page,/Professional registration number/);
  assert.match(page,/label="Profession"/);
});

test('all governed mobile formatting variants resolve to one canonical identity',()=>{
  for (const value of ['+919762006688','919762006688','+91 97620 06688','91 97620 06688','9762006688']) {
    assert.equal(canonicalMobile(value), '+919762006688');
  }
  assert.equal(canonicalMobile('123'), null);
});

test('login exposes canonical mobile OTP entry without changing existing internal sign-in authority',()=>{
  const login=read('pages/login.js');
  assert.match(login,/href="\/signup"/);
  assert.match(login,/Continue with mobile OTP/);
  assert.match(login,/New and returning external consultants/);
  assert.match(login,/await login\(form\)/);
});
