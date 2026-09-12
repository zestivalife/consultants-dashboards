import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const page=readFileSync(new URL('../components/platform/FoodAuthorisationPage.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');
const workspace=readFileSync(new URL('../components/platform/PlatformWorkspace.jsx',import.meta.url),'utf8');

test('Super Admin Food Authorisation exposes the minimal filters and bulk actions',()=>{
 for(const label of ['Search foods','Category','Authorisation status','Nutrition completeness','Select all on page','Deselect all','Authorise selected','Do not authorise'])assert.ok(page.includes(label),label);
 assert.match(page,/disabled={!selected\.size \|\| state\.saving}/);
});

test('Food Authorisation uses server pagination and the single bulk API',()=>{
 assert.match(api,/\/v1\/admin\/food-authorisation\?/);
 assert.match(api,/\/v1\/admin\/food-authorisation\/bulk/);
  assert.match(page,/patchFilter\('offset', filters\.offset \+ filters\.limit\)/);
});

test('Food Authorisation navigation is restricted to Super Admin roles',()=>{
 assert.match(workspace,/super_admin/);
 assert.match(workspace,/isSuperAdmin \? <FoodAuthorisationPage/);
});
