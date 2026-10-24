import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const plan=fs.readFileSync(new URL('../components/external/ExternalMultiDietPlan.jsx',import.meta.url),'utf8');
const client=fs.readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');

test('diet plan loads server-authoritative health context',()=>{
  assert.match(api,/getDietPlanHealthContext/);
  assert.match(plan,/Promise\.allSettled\(\[listConsultantDietPlans\(clientId\),getNutritionAssessment\(clientId\),getDietPlanHealthContext\(clientId\)\]\)/);
  assert.match(plan,/Health Context for Diet Planning/);
  assert.match(plan,/target methodology/i);
  assert.match(plan,/Calories and protein are never prescribed from BMI alone/);
});

test('changed and legacy measurement contexts remain visible and review-gated',()=>{
  assert.match(plan,/measurement_context_changed/);
  assert.match(plan,/requires_professional_confirmation/);
  assert.match(plan,/Re-review the Nutrition Assessment/);
  assert.match(plan,/Review measurements in Client360/);
});

test('Client360 navigation owns the measurement review action',()=>{
  assert.match(client,/onReviewMeasurements=\{\(\)=>setActive\('Measurements'\)\}/);
});
