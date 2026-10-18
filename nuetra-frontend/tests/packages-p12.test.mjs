import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const workspace=fs.readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const packages=fs.readFileSync(new URL('../components/external/ExternalPackages.jsx',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const client360=fs.readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const portal=fs.readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');

test('P12 adds the packages workspace without changing diet plan routing',()=>{
  assert.match(workspace,/\['packages', 'Packages', PackageOpen\]/);
  assert.match(workspace,/view==='packages'\?<ExternalPackages clients=\{clients\}/);
  assert.match(workspace,/view==='plans'\?<PlanHistory/);
});

test('package library supports create edit assignment and renewal truth',()=>{
  for(const name of ['createServicePackage','updateServicePackage','assignClientPackage','listRenewalSignals']) assert.ok(api.includes(name));
  for(const copy of ['Create package','Edit package','Assign package to client','Renewals due','Packages ending soon']) assert.ok(packages.includes(copy));
  assert.ok(packages.includes('Nothing renews automatically'));
});

test('Client360 and portal expose scoped programme information',()=>{
  assert.ok(client360.includes("'Programme'"));
  assert.ok(client360.includes('<ClientPackagePanel clientId={client.id}/>'));
  assert.ok(portal.includes("['programme','Programme']"));
  assert.ok(portal.includes('sessions_remaining'));
  assert.ok(!portal.includes('item.notes'));
});
