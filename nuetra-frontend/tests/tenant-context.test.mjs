import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { normalizeCanonicalTenant, resolveConsultantWorkspace, TENANT_CONTEXT_STATUS } from '../lib/tenantContext.mjs';

const read=(path)=>fs.readFileSync(new URL(`../${path}`,import.meta.url),'utf8');

test('frontend hydrates automatic server-issued tenant context without a switcher',()=>{
  const source=read('context/TenantContext.js');
  const app=read('pages/_app.js');
  assert.match(source,/getFiteatsyTenantContext/);
  assert.match(source,/requestGeneration/);
  assert.match(source,/controller\.abort/);
  assert.match(source,/setState\(\{currentTenant:null,status:TENANT_CONTEXT_STATUS\.IDLE,error:null\}\)/);
  assert.match(source,/\[authLoading,isBackendAuthEnabled,user\?\.id\]/);
  assert.match(source,/tenantId/);
  assert.match(source,/tenantName/);
  assert.match(source,/tenantType/);
  assert.match(source,/currentMembershipRole/);
  assert.doesNotMatch(source,/switchTenant|tenant switcher/i);
  assert.match(app,/TenantProvider/);
});

test('canonical backend tenant response is normalized with active membership semantics',()=>{
  const currentTenant=normalizeCanonicalTenant({currentTenant:{tenantId:'tenant-a',tenantName:'QA Practice',tenantType:'INDEPENDENT_CONSULTANT',currentMembershipRole:'OWNER',resolutionPath:'MEMBERSHIP'}});
  assert.deepEqual(currentTenant,{tenantId:'tenant-a',tenantName:'QA Practice',tenantType:'INDEPENDENT_CONSULTANT',currentMembershipRole:'OWNER',membershipStatus:'active',resolutionPath:'MEMBERSHIP'});
});

test('workspace routing is explicit and fails closed',()=>{
  assert.equal(resolveConsultantWorkspace({status:TENANT_CONTEXT_STATUS.READY,tenantType:'INDEPENDENT_CONSULTANT',membershipStatus:'active'}),'EXTERNAL');
  assert.equal(resolveConsultantWorkspace({status:TENANT_CONTEXT_STATUS.READY,tenantType:'ZESTIVA_INTERNAL',membershipStatus:'active'}),'IN_HOUSE');
  assert.equal(resolveConsultantWorkspace({status:TENANT_CONTEXT_STATUS.READY,tenantType:null,membershipStatus:null}),'UNAVAILABLE');
  assert.equal(resolveConsultantWorkspace({status:TENANT_CONTEXT_STATUS.UNAVAILABLE,tenantType:'ZESTIVA_INTERNAL',membershipStatus:null}),'UNAVAILABLE');
  assert.equal(resolveConsultantWorkspace({status:TENANT_CONTEXT_STATUS.READY,tenantType:'INDEPENDENT_CONSULTANT',membershipStatus:'inactive'}),'UNAVAILABLE');
  assert.equal(resolveConsultantWorkspace({status:TENANT_CONTEXT_STATUS.LOADING,tenantType:null,membershipStatus:null}),'LOADING');
  assert.equal(resolveConsultantWorkspace({status:TENANT_CONTEXT_STATUS.IDLE,tenantType:'ZESTIVA_INTERNAL',membershipStatus:'active'}),'LOADING');
  assert.equal(resolveConsultantWorkspace({status:TENANT_CONTEXT_STATUS.READY,tenantType:'UNKNOWN',membershipStatus:'active'}),'UNAVAILABLE');
});
