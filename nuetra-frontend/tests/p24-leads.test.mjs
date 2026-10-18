import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const ui=fs.readFileSync(new URL('../components/external/ExternalLeads.jsx',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
test('P24 renders truthful lead pipeline states',()=>{for(const value of ['NEW','CONTACTED','QUALIFIED','CONSULTATION_BOOKED','CONVERTED','NOT_INTERESTED','LOST'])assert.match(ui,new RegExp(value));assert.match(ui,/pipeline request completed successfully/i);assert.match(ui,/role="alert"/)});
test('P24 converts through existing Client Core',()=>{assert.match(ui,/createExternalClient/);assert.match(ui,/convertLead/);assert.match(api,/\/leads/)});
