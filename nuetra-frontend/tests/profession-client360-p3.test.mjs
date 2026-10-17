import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const component=fs.readFileSync(new URL('../components/external/ProfessionClient360.jsx',import.meta.url),'utf8');
const client360=fs.readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('P3 uses one tenant-scoped profession projection API',()=>{assert.match(api,/getProfessionClient360/);assert.match(api,/profession-view/);assert.match(component,/getProfessionClient360\(clientId\)/)});
test('P3 has capability navigation and explicit loading error and confirmed-empty states',()=>{for(const value of ['ProfessionCapabilityNavigation','Loading profession workspace','Profession workspace could not load','confirmed empty state','capability is not enabled'])assert.match(component,new RegExp(value))});
test('new professions receive a specific Client360 without exposing Diet Plan authoring',()=>{assert.match(client360,/usesProfessionWorkspace/);assert.match(client360,/active === 'Profession'/);assert.match(client360,/!usesProfessionWorkspace&&<button onClick=\{\(\)=>setActive\('Diet Plan'\)\}/)});
test('frozen Dietitian and Nutritionist retain the established tab set',()=>{assert.match(client360,/usesProfessionWorkspace\?\['Overview','Profession'/);assert.match(client360,/:tabs,/)});
