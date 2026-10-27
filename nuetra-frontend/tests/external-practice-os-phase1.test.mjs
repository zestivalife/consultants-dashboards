import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

const root=new URL('../',import.meta.url);
const workspace=readFileSync(new URL('components/external/ExternalSaaSWorkspace.jsx',root),'utf8');
const operations=readFileSync(new URL('components/external/ExternalCareOperations.jsx',root),'utf8');
const communication=readFileSync(new URL('components/external/ExternalCommunicationWorkspace.jsx',root),'utf8');
const calendar=readFileSync(new URL('components/external/ExternalCalendarWorkspace.jsx',root),'utf8');
const api=readFileSync(new URL('lib/practiceOperationsApi.js',root),'utf8');
const whatsappLaunch=readFileSync(new URL('lib/whatsappLaunch.mjs',root),'utf8');

test('Phase 1 remains behind the External workspace boundary',()=>{
  assert.match(workspace,/external-only workspace boundary/);
  assert.match(workspace,/ExternalCommunicationWorkspace/);
  assert.match(workspace,/ExternalCalendarWorkspace/);
  assert.doesNotMatch(workspace,/senior-consultant/);
});

test('profession terminology drives consultation and goal labels',()=>{
  assert.match(operations,/terminology\.consultation/);
  assert.match(operations,/terminology\.goal/);
  assert.doesNotMatch(operations,/profession\s*===\s*['"]DIETITIAN/);
});

test('WhatsApp is explicit, editable and never claims message delivery',()=>{
  assert.match(communication,/You will review the message in WhatsApp and press Send yourself/);
  assert.match(communication,/Activity records that WhatsApp was opened—not sent, delivered, or read/);
  assert.match(whatsappLaunch,/https:\/\/wa\.me/);
  assert.match(api,/reserveWhatsAppWindow/);
  assert.match(api,/whatsapp-opened/);
  assert.doesNotMatch(communication,/message sent/i);
});

test('calendar exposes touch-safe agenda day week and month views',()=>{
  for(const view of ['AGENDA','DAY','WEEK','MONTH'])assert.match(calendar,new RegExp(view));
  assert.match(calendar,/min-h-11/);
  assert.match(calendar,/overflow-x-auto/);
});

test('mobile surfaces use safe areas and avoid hover-only primary actions',()=>{
  assert.match(communication,/env\(safe-area-inset-bottom\)/);
  assert.match(workspace,/Mobile primary/);
  assert.match(operations,/sm:hidden/);
});

test('practice operations forwards the consultant bearer token through the same-origin gateway proxy',()=>{
  assert.match(api,/import \{getToken,refreshAccessToken\} from '\.\/api'/);
  assert.match(api,/X-Nuetra-Authorization/);
  assert.match(api,/response\.status===401/);
  assert.match(api,/refreshAccessToken\(\)/);
});

test('client API failure never renders an authoritative empty client state',()=>{
  assert.match(workspace,/Promise\.allSettled\(\[listExternalClients/);
  assert.match(workspace,/Array\.isArray\(clientResult\.value\?\.clients\)/);
  assert.match(workspace,/setClientLoadState\('error'\)/);
  assert.match(workspace,/clientLoadState==='error'/);
  assert.match(workspace,/No empty client state is shown because the authoritative client request did not complete successfully/);
  assert.doesNotMatch(workspace,/Promise\.all\(\[listExternalClients/);
});
