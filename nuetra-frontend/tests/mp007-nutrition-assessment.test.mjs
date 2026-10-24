import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

const component=readFileSync(new URL('../components/external/ExternalNutritionAssessment.jsx',import.meta.url),'utf8');
const client360=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const migration=readFileSync(new URL('../../services/practice-operations-service/alembic/versions/0055_nutrition_assessment_readiness.py',import.meta.url),'utf8');

test('MP-007 mounts the real Nutrition Assessment inside capability-gated Client360',()=>{
  assert.match(client360,/ExternalNutritionAssessment/);
  assert.match(client360,/active === 'Nutrition'/);
  for(const value of ['Nutrition Assessment','Diet Plan readiness','Save draft','Submit for review','Mark reviewed','Assessment history','Existing client information'])assert.match(component,new RegExp(value));
});

test('MP-007 uses persisted server-governed workflow contracts',()=>{
  assert.match(api,/export function saveNutritionAssessment/);
  assert.match(api,/export function transitionNutritionAssessment/);
  assert.match(component,/expected_version/);
  assert.match(component,/getNutritionAssessment/);
  for(const state of ['NOT_STARTED','INCOMPLETE','NEEDS_REVIEW','READY','BLOCKED'])assert.match(migration,new RegExp(state));
});

test('MP-007 retains accessible responsive and honest context states',()=>{
  assert.match(component,/aria-live/);
  assert.match(component,/role="status"/);
  assert.match(component,/sm:grid-cols-2/);
  assert.match(component,/Not provided/);
  assert.match(component,/clinical safety guarantee/);
  assert.match(component,/CONFIRMED_CLIENT_BIOMARKER/);
  assert.doesNotMatch(component,/placeholder data|mock client|fake/i);
});
