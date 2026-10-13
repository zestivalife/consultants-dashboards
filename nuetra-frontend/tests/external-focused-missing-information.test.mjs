import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const client360=fs.readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const intake=fs.readFileSync(new URL('../components/external/ExternalClientHealthIntake.jsx',import.meta.url),'utf8');
const entry=fs.readFileSync(new URL('../pages/intake/[token].js',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');

test('Consultant sees a focused missing-information editor rather than full onboarding',()=>{
  assert.match(client360,/View Missing Information/);
  assert.match(client360,/Only required information preventing Diet Plan generation is shown/);
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

test('canonical eligibility reasons are separated from target validation',()=>{
  assert.match(client360,/dietPlanEligibilityReasons/);
  assert.match(client360,/Client consent is required/);
  assert.match(client360,/overview\.dietPlanEligible &&/);
  assert.match(client360,/Enter daily calorie and protein targets to generate the plan/);
  assert.doesNotMatch(client360,/overview\.intakeStatus='REQUIRED_INFORMATION_MISSING'/);
});
