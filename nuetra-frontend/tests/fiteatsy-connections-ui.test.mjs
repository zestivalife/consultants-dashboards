import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const component=fs.readFileSync(new URL('../components/external/ExternalFiteatsyConnections.jsx',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('connection UI has explicit secure lifecycle states',()=>{
  for(const text of ['Generate Connection PIN','Shown once','Copy PIN','Share via WhatsApp','Revoke PIN','Disconnect','Connections are not enabled yet'])assert.match(component,new RegExp(text));
});

test('connection UI exposes no raw PIN persistence',()=>{
  assert.doesNotMatch(component,/localStorage|sessionStorage/);
  assert.match(component,/createFiteatsyConnectionInvitation/);
});

test('API client exposes governed consultant operations',()=>{
  for(const name of ['listFiteatsyConnections','createFiteatsyConnectionInvitation','revokeFiteatsyConnectionInvitation','revokeFiteatsyConnection'])assert.match(api,new RegExp(`export function ${name}`));
});
