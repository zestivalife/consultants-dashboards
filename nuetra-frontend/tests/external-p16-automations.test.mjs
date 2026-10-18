import test from 'node:test';import assert from 'node:assert/strict';import{readFileSync}from'node:fs';
const ui=readFileSync(new URL('../components/external/ExternalAutomations.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const workspace=readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
test('P16 automation builder exposes governed When If Then controls',()=>{for(const value of ['Guided builder','WHEN','IF','THEN','Add condition','Add action','Save draft'])assert.match(ui,new RegExp(value));assert.doesNotMatch(ui,/payload JSON|SQL expression|JavaScript code/)});
test('P16 has templates dry-run history and confirmation queue',()=>{for(const value of ['Templates','Dry-run preview','Execution History','Confirmation Queue','Approve','Dismiss','No writes performed'])assert.match(ui,new RegExp(value));});
test('P16 uses protected APIs and remains additive to navigation',()=>{for(const value of ['listAutomations','createAutomation','dryRunAutomation','listAutomationHistory','listPendingAutomationActions','decideAutomationAction'])assert.match(api,new RegExp(`function ${value}`));assert.match(workspace,/\['automations', 'Automations', Workflow\]/);});
test('P16 distinguishes loading failure and confirmed empty truth',()=>{for(const value of ['loading','error','No empty state is shown','Confirmed empty'])assert.match(ui,new RegExp(value,'i'));});
