import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const page=fs.readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/clientPortalApi.js',import.meta.url),'utf8');

test('P11 portal has mobile-first IA and truthful states',()=>{
  for(const label of ['Home','My plan','Tasks','Appointments','Progress','Resources','Documents'])assert.match(page,new RegExp(label));
  for(const state of ['loading','error','No tasks have been assigned','No upcoming appointment'])assert.ok(page.includes(state));
  assert.ok(page.includes('min-h-11'));
  assert.ok(page.includes('overflow-x-auto'));
});

test('P11 client API uses only scoped public portal routes',()=>{
  assert.ok(api.includes('/api/gateway/api/v1/client-portal'));
  assert.ok(api.includes('/tasks/'));
  assert.ok(!api.includes('private'));
});
