import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const api=fs.readFileSync(new URL('../nuetra-frontend/lib/practiceOperationsApi.js',import.meta.url),'utf8');
const ui=fs.readFileSync(new URL('../nuetra-frontend/components/external/ExternalCareOperations.jsx',import.meta.url),'utf8');
const shell=fs.readFileSync(new URL('../nuetra-frontend/components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
test('practice adapters use the governed gateway and idempotency',()=>{assert.match(api,/api\/gateway\/api\/v1\/practice-operations/);assert.match(api,/Idempotency-Key/);assert.match(api,/credentials:'include'/);});
test('care operations implement real loading empty error and success states',()=>{for(const value of ["'loading'","'ready'","'error'",'page.items.length===0','Mark complete'])assert.match(ui,new RegExp(value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));});
test('mobile operation authoring is safe area aware and not hover dependent',()=>{assert.match(ui,/env\(safe-area-inset-bottom\)/);assert.match(ui,/sm:hidden/);assert.match(ui,/role="dialog"/);});
test('external wiring does not alter the frozen in-house workspace',()=>{assert.match(shell,/external-only workspace boundary/);assert.doesNotMatch(ui,/ZESTIVA_INTERNAL|ConsultantWorkspace/);});
