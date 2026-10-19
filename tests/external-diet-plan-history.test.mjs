import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const ui=readFileSync(new URL('../nuetra-frontend/components/external/ExternalDietPlanHistory.jsx',import.meta.url),'utf8');
const client360=readFileSync(new URL('../nuetra-frontend/components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../nuetra-frontend/lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');

test('external Client 360 renders current, draft and immutable historical plan surfaces',()=>{
  assert.match(client360,/ExternalDietPlanHistory/);
  assert.match(ui,/Current published plan/);
  assert.match(ui,/Current draft/);
  assert.match(ui,/Historical plans/);
  assert.match(ui,/Immutable historical snapshot/);
});

test('version actions use governed history APIs and expose compare without raw JSON',()=>{
  for(const path of ['diet-plan/history','diet-plan/compare','diet-plan/versions/'])assert.match(api,new RegExp(path.replace('/','\\/')));
  assert.match(ui,/Compare selected/);
  assert.match(ui,/Create Revision/);
  assert.match(ui,/DOCX/);
  assert.match(ui,/Added/);
  assert.match(ui,/Removed/);
  assert.match(ui,/Changed/);
  assert.doesNotMatch(ui,/JSON\.stringify/);
});
