import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';
import {canonicalAssessmentFromOnboarding,reconcileCompleteness,resolveNutritionAssessment} from '../lib/nutritionAssessmentSync.mjs';

const assessment=fs.readFileSync(new URL('../components/external/ExternalNutritionAssessment.jsx',import.meta.url),'utf8');
const page=fs.readFileSync(new URL('../pages/client-information/[token].js',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('consultant receives server-authoritative completeness and scoped request actions',()=>{
  for(const value of ['Assessment Link','Create Assessment Link','Copy secure link','getClientInformationCompleteness','createClientInformationRequest'])assert.match(assessment,new RegExp(value));
  assert.match(api,/information-completeness/);assert.match(api,/information-requests/);
});

test('client page renders only server-approved fields with save/resume and submission',()=>{
  assert.match(page,/visibleFields\.map/);
  for(const value of ['Complete the missing information','Only information requested','Save and resume','Submit update','expected_version'])assert.match(page,new RegExp(value));
  assert.doesNotMatch(page,/all 14|medicalHistory|womensHealth/);
});

test('completed onboarding pre-populates nutrition assessment without save',()=>{
  const sections={nutrition:{dietPreference:'NON_VEGETARIAN',restrictions:['NO_ONION_GARLIC'],mealsPerDay:'3',skipMeals:'NEVER'},activityHydration:{waterIntakeMl:2500},conditionsSymptoms:{conditions:['DIABETES']},goals:{goals:['LOSE_WEIGHT','BLOOD_SUGAR']}};
  const value=canonicalAssessmentFromOnboarding(sections);
  assert.equal(value.dietary_preference,'NON_VEGETARIAN');assert.deepEqual(value.food_restrictions,['NO_ONION_GARLIC']);assert.equal(value.water_intake,'2.5 L/day');assert.deepEqual(value.nutrition_medical_conditions,['DIABETES']);assert.deepEqual(value.weight_management_goals,['LOSE_WEIGHT']);assert.deepEqual(value.recovery_disease_management_goals,['BLOOD_SUGAR']);
});

test('professional values take precedence and client provenance remains visible',()=>{
  const resolved=resolveNutritionAssessment({nutrition:{dietPreference:'NON_VEGETARIAN',restrictions:['JAIN']}},{dietary_preference:'VEGETARIAN'},{dietary_preference:{source:'CONSULTANT_CONFIRMED',confirmed:true}});
  assert.equal(resolved.values.dietary_preference,'VEGETARIAN');assert.deepEqual(resolved.values.food_restrictions,['JAIN']);assert.equal(resolved.provenance.dietary_preference.confirmed,true);assert.equal(resolved.provenance.food_restrictions.source,'CLIENT_SUBMITTED');
});

test('missing detection excludes fields resolved from onboarding',()=>{
  const resolved=resolveNutritionAssessment({nutrition:{dietPreference:'NON_VEGETARIAN'}},{});
  const server={fields:[{field_id:'dietary_preference',status:'MISSING',blocks_readiness:true},{field_id:'meal_timing_frequency',status:'MISSING',blocks_readiness:true}],counts:{MISSING:2,CAPTURED:0},readiness:'NEEDS_INFORMATION'};
  const next=reconcileCompleteness(server,resolved);assert.equal(next.fields[0].status,'CAPTURED');assert.equal(next.fields[1].status,'MISSING');assert.deepEqual(next.blocking_fields,['meal_timing_frequency']);
});

test('non-weight health goals satisfy the health-goal completeness field',()=>{
  const resolved=resolveNutritionAssessment({goals:{selectedGoals:['BLOOD_SUGAR']}},{});
  const server={fields:[{field_id:'health_goals',status:'MISSING',blocks_readiness:true}],counts:{MISSING:1,CAPTURED:0}};
  const next=reconcileCompleteness(server,resolved);assert.equal(next.fields[0].status,'CAPTURED');assert.deepEqual(next.blocking_fields,[]);
});

test('structured client goal values are normalised before assessment and Diet Chart rendering',()=>{
  const value=canonicalAssessmentFromOnboarding({goals:{selectedGoals:{code:'BLOOD_SUGAR',label:'Blood sugar'}}});
  assert.deepEqual(value.recovery_disease_management_goals,['BLOOD_SUGAR']);
  assert.match(assessment,/Client information received/);
  assert.match(assessment,/Edit assessment/);
});

test('selective client form uses governed choices rather than comma-separated entry',()=>{
  assert.match(page,/role=\{field\.kind==='list'\?'checkbox':'radio'\}/);assert.doesNotMatch(page,/Separate items with commas/);assert.match(page,/completed health profile is not restarted/);
});

test('selective flow communicates privacy, expiry and professional review',()=>{
  assert.match(page,/scoped to one client and the fields selected/);
  assert.match(page,/expires automatically/);
  assert.match(page,/consultant will review/);
});
