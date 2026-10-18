import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const ui=fs.readFileSync(new URL('../components/external/ExternalForms.jsx',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const workspace=fs.readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
test('P21 exposes builder, governed views and every field type',()=>{for(const value of ['Templates','My Forms','Assigned Forms','Responses','REPEAT_GROUP','CONSENT_CHECKBOX','BODY_REGION'])assert.match(ui,new RegExp(value));assert.match(ui,/role="dialog"/);assert.match(ui,/Confirmed empty/)});
test('P21 API covers create publish assignment and response',()=>{for(const value of ['createForm','publishForm','assignForm','listFormAssignments','saveFormResponse'])assert.match(api,new RegExp(value))});
test('P21 forms are permission gated in the existing workspace',()=>{assert.match(workspace,/TEMPLATE_VIEW/);assert.match(workspace,/\['forms', 'Forms'/)});
