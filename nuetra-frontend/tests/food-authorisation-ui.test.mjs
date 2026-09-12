import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const page=readFileSync(new URL('../components/platform/FoodAuthorisationPage.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');
const workspace=readFileSync(new URL('../components/platform/PlatformWorkspace.jsx',import.meta.url),'utf8');
const roleRoutes=readFileSync(new URL('../lib/roleRoutes.js',import.meta.url),'utf8');
const authContext=readFileSync(new URL('../context/AuthContext.js',import.meta.url),'utf8');
const ownerLayout=readFileSync(new URL('../components/platform/OwnerConsoleLayout.jsx',import.meta.url),'utf8');

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
 const capabilityRoles=roleRoutes.match(/FOOD_AUTHORISATION_ROLE_KEYS = new Set\(\[([^\]]+)]\)/)?.[1]||'';
 for(const role of ['platform_owner','super_admin','superuser']) assert.ok(capabilityRoles.includes(`'${role}'`),role);
 for(const role of ['consultant','senior_consultant','client','user']) assert.equal(capabilityRoles.includes(`'${role}'`),false,role);
 assert.match(workspace,/canAccessFoodAuthorisation\(resolvedRole\)/);
 assert.match(workspace,/isSuperAdmin \? <FoodAuthorisationPage/);
});

test('owner navigation exposes one canonical Food Authorisation CTA',()=>{
 assert.match(ownerLayout,/canAccessFoodAuthorisation\(user\)/);
 assert.equal((ownerLayout.match(/href="\/dashboard\/admin\?view=food-authorisation"/g)||[]).length,1);
});

test('authorised Food Authorisation route is distinct from the default owner landing',()=>{
 assert.match(roleRoutes,/platform_owner:\s*'\/dashboard\/owner'/);
 assert.match(roleRoutes,/pathname === '\/dashboard\/admin'/);
 assert.match(roleRoutes,/view === 'food-authorisation'/);
 assert.match(authContext,/!canAccessDashboardLocation\(nextUser, router\.pathname, router\.query\)/);
 assert.match(workspace,/roleKind !== 'admin'/);
 assert.match(workspace,/adminNav\.some\(\(item\) => item\.id === queryView\)/);
});
