import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';
import {loadAuthorizedClient360,projectAssignedClient360,projectConnectedClient360} from '../lib/connectedClient360.mjs';

test('assigned unconnected client exposes directory identity but no health data', async () => {
  let calls=0;
  const result=await loadAuthorizedClient360({id:'client-1',displayName:'Assigned client',email:'visible@example.test',status:'ASSIGNED'},async()=>{calls+=1;});
  assert.equal(calls,0);
  assert.equal(result.overview.name,'Assigned client');
  assert.equal(result.overview.email,'visible@example.test');
  assert.deepEqual(result.overview.dietPlanWarnings,['CONSENT_PENDING']);
  assert.deepEqual(result.sections.medicalHistory,{});
  assert.deepEqual(result.sections.measurements,{});
  assert.deepEqual(result.documents,[]);
});

test('connected client uses its exact connection for consent-controlled health context', async () => {
  const calls=[];
  const result=await loadAuthorizedClient360({id:'client-2',connectionId:'connection-2',status:'CONNECTED_CONSENT_ACTIVE'},async(id)=>{
    calls.push(id);
    return {profile:{client:{name:'Connected client',dob:'1990-01-01'},onboarding:{height:170,weight:70,goal:'Improve health'}},foodPreferences:{profile:{dietType:'VEGETARIAN'}}};
  });
  assert.deepEqual(calls,['connection-2']);
  assert.equal(result.overview.name,'Connected client');
  assert.equal(result.sections.nutrition.dietPreference,'VEGETARIAN');
});

for (const [name,status] of [['revoked consent',403],['expired consent',410],['cross-tenant access',404],['Fiteatsy unavailable',503],['missing backend route',404]]) {
  test(`${name} remains a real request failure`, async () => {
    const failure=Object.assign(new Error(name),{status});
    await assert.rejects(loadAuthorizedClient360({id:'client-3',connectionId:'connection-3'},async()=>{throw failure;}),(error)=>error===failure);
  });
}

test('valid projections preserve known health data and never fabricate unavailable values', () => {
  const assigned=projectAssignedClient360({id:'client-4'});
  assert.equal(assigned.overview.documentCount,null);
  const connected=projectConnectedClient360({id:'client-5'},{profile:{client:{name:'Valid client'},onboarding:{}},reports:[]});
  assert.equal(connected.overview.name,'Valid client');
  assert.equal(connected.overview.documentCount,0);
});

test('frontend cannot silently restore the unsupported Fiteatsy Client 360 route', () => {
  const component=fs.readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
  const clientApi=fs.readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');
  assert.doesNotMatch(component,/getExternalClient360/);
  assert.doesNotMatch(clientApi,/external\/clients\/\$\{encodeURIComponent\(clientId\)\}\/360/);
  assert.match(component,/getFiteatsyConnectionHealthContext/);
  assert.match(clientApi,/practice-operations\/clients/);
});
