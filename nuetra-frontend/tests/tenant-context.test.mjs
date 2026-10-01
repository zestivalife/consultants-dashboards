import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const read=(path)=>fs.readFileSync(new URL(`../${path}`,import.meta.url),'utf8');

test('frontend adds only automatic server-issued tenant context without a switcher',()=>{
  const source=read('context/TenantContext.js');
  const app=read('pages/_app.js');
  assert.match(source,/user\?\.currentTenant/);
  assert.match(source,/tenantId/);
  assert.match(source,/tenantName/);
  assert.match(source,/tenantType/);
  assert.match(source,/currentMembershipRole/);
  assert.doesNotMatch(source,/switchTenant|tenant switcher/i);
  assert.match(app,/TenantProvider/);
});
