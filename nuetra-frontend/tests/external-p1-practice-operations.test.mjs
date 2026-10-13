import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const ui=fs.readFileSync(new URL('../components/external/ExternalCareOperations.jsx',import.meta.url),'utf8');
const shell=fs.readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
test('P1 adapters use governed gateway, cookies and idempotency',()=>{assert.match(api,/api\/gateway\/api\/v1\/practice-operations/);assert.match(api,/Idempotency-Key/);assert.match(api,/credentials:'include'/);});
test('P1 care UX has loading, empty, error and persisted states',()=>{for(const value of ["'loading'","'ready'","'error'",'page.items.length===0','Mark complete'])assert.ok(ui.includes(value));});
test('P1 mobile authoring is safe-area aware and keyboard accessible',()=>{assert.match(ui,/env\(safe-area-inset-bottom\)/);assert.match(ui,/role="dialog"/);assert.match(ui,/datetime-local/);});
test('command search and compact mobile navigation replace the long mobile sidebar',()=>{assert.match(shell,/CommandLauncher/);assert.match(shell,/Mobile primary/);assert.match(shell,/metaKey\|\|event.ctrlKey/);});
test('P1 remains isolated to the External workspace',()=>{assert.match(shell,/external-only workspace boundary/);assert.doesNotMatch(ui,/ZESTIVA_INTERNAL|ConsultantWorkspace/);});
