import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeCanonicalTenant, resolveConsultantWorkspace, TENANT_CONTEXT_STATUS } from '../nuetra-frontend/lib/tenantContext.mjs';

const ready=(tenantType,membershipStatus='active')=>({status:TENANT_CONTEXT_STATUS.READY,tenantType,membershipStatus});

test('external membership selects only the external workspace',()=>{
  assert.equal(resolveConsultantWorkspace(ready('INDEPENDENT_CONSULTANT')),'EXTERNAL');
  assert.equal(resolveConsultantWorkspace(ready('PRACTICE')),'EXTERNAL');
});

test('in-house membership selects only the frozen in-house workspace',()=>{
  assert.equal(resolveConsultantWorkspace(ready('ZESTIVA_INTERNAL')),'IN_HOUSE');
});

test('missing, inactive, failed, or unknown tenant context never leaks a workspace',()=>{
  assert.equal(resolveConsultantWorkspace(ready(null)),'UNAVAILABLE');
  assert.equal(resolveConsultantWorkspace(ready('ZESTIVA_INTERNAL','inactive')),'UNAVAILABLE');
  assert.equal(resolveConsultantWorkspace({status:TENANT_CONTEXT_STATUS.UNAVAILABLE,tenantType:'ZESTIVA_INTERNAL',membershipStatus:'active'}),'UNAVAILABLE');
  assert.equal(resolveConsultantWorkspace(ready('UNRECOGNIZED')),'UNAVAILABLE');
});

test('malformed canonical responses do not create tenant authority',()=>{
  assert.equal(normalizeCanonicalTenant(null),null);
  assert.equal(normalizeCanonicalTenant({currentTenant:{tenantId:'tenant-a',tenantType:'PRACTICE'}}),null);
});
