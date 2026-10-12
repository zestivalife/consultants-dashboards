import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workspace=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');

test('Client 360 exposes the external Diet Plan action and dedicated tab',()=>{assert.match(workspace,/Create Diet Plan/);assert.match(workspace,/active === 'Diet Plan'/);assert.match(workspace,/getExternalDietPlan/);});
test('external authoring uses seven-head Common Food result and exact 35-option persistence',()=>{assert.match(workspace,/snapshot\.meals\.map/);assert.match(workspace,/meal\.options\.map/);assert.match(workspace,/flatMap\(meal=>meal\.options\)/);assert.match(api,/diet-plan\/generate/);assert.match(api,/diet-plan\/draft/);});
test('publication is explicit and does not expose a Senior approval action',()=>{assert.match(workspace,/Publish this exact Diet Plan version to the client/);assert.match(workspace,/External Consultant self-publish workflow/);assert.doesNotMatch(workspace,/Submit for Senior|Request Senior/);});
test('practice-branded DOCX export remains available',()=>{assert.match(workspace,/exportDietPlanDocx/);assert.match(workspace,/practiceName\|\|'Consultant practice'/);assert.match(workspace,/Export DOCX/);});
test('completed intake optional sections are not presented as missing requirements',()=>{assert.match(workspace,/Optional information not provided/);assert.match(workspace,/Missing required information/);});
