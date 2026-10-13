import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const client360=fs.readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const intake=fs.readFileSync(new URL('../components/external/ExternalClientHealthIntake.jsx',import.meta.url),'utf8');
const entry=fs.readFileSync(new URL('../pages/intake/[token].js',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');

test('Consultant sees a focused missing-information editor rather than full onboarding',()=>{
  assert.match(client360,/Complete Missing Information/);
  assert.match(client360,/Only missing important information is shown/);
  assert.match(client360,/Save &amp; Recheck/);
  assert.match(client360,/missingRequiredFields/);
  assert.doesNotMatch(client360,/onboarding\/consultant/);
});

test('focused editor reuses canonical intake controls and persists through one eligibility contract',()=>{
  assert.match(client360,/FocusedRequiredFieldControl/);
  assert.match(intake,/PILL_SINGLE|FocusedRequiredFieldControl/);
  assert.match(intake,/STRUCTURED_NUMBER|CURRENT_WEIGHT/);
  assert.match(api,/diet-eligibility/);
});

test('returning client enters missing-only flow while first-time intake remains complete',()=>{
  assert.match(entry,/missingOnly=\{Boolean\(state\.entry\?\.resume\)\}/);
  assert.match(intake,/Completed sections are skipped/);
  assert.match(intake,/missingFields\.filter\(field=>field\.clientCanEdit\)/);
});

test('external profile warnings are non-blocking and target validation remains the generation gate',()=>{
  assert.match(client360,/dietPlanWarnings/);
  assert.match(client360,/Client consent is pending/);
  assert.match(client360,/Continue to Diet Plan/);
  assert.doesNotMatch(client360,/overview\.dietPlanEligible &&/);
  assert.doesNotMatch(client360,/Diet Plan generation remains unavailable/);
  assert.match(client360,/const validTargets=/);
  assert.match(client360,/800–6000 kcal and 20–400 g protein/);
  assert.doesNotMatch(client360,/overview\.intakeStatus='REQUIRED_INFORMATION_MISSING'/);
});
