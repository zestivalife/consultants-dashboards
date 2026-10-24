import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const assessment=fs.readFileSync(new URL('../components/external/ExternalNutritionAssessment.jsx',import.meta.url),'utf8');
const page=fs.readFileSync(new URL('../pages/client-information/[token].js',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('consultant receives server-authoritative completeness and scoped request actions',()=>{
  for(const value of ['Client Information Completeness','Request Missing Information','Copy secure link','getClientInformationCompleteness','createClientInformationRequest'])assert.match(assessment,new RegExp(value));
  assert.match(api,/information-completeness/);assert.match(api,/information-requests/);
});

test('client page renders only server-approved fields with save/resume and submission',()=>{
  assert.match(page,/state\.data\.fields\.map/);
  for(const value of ['Update Your Health Information','Only the information requested','Save and resume','Submit update','expected_version'])assert.match(page,new RegExp(value));
  assert.doesNotMatch(page,/all 14|medicalHistory|womensHealth/);
});

test('selective flow communicates privacy, expiry and professional review',()=>{
  assert.match(page,/scoped to one client and the fields selected/);
  assert.match(page,/expires automatically/);
  assert.match(page,/consultant will review/);
});
