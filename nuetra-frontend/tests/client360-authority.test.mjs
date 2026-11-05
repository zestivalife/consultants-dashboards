import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';
import {loadAuthorizedClient360,projectAssignedClient360,projectConnectedClient360} from '../lib/connectedClient360.mjs';
import {normalizePracticeClientDirectory} from '../lib/practiceClientDirectory.mjs';

const directoryFixture=JSON.parse(fs.readFileSync(new URL('./fixtures/practice-client-directory.json',import.meta.url),'utf8'));

test('deployed Practice Operations directory envelope preserves pagination and real connection state', () => {
  const directory=normalizePracticeClientDirectory(directoryFixture);
  assert.deepEqual(directory.pagination,{total:3,limit:100,offset:0});
  assert.equal(directory.practiceWide,false);
  assert.equal(directory.clients[0].connectionId,'connection-active');
  assert.equal(directory.clients[0].displayName,'Connected Client');
  assert.equal(directory.clients[1].connectionId,null);
  assert.equal(directory.clients[1].status,'ASSIGNED_CONNECTION_PENDING');
  assert.equal(directory.clients[2].connectionId,'connection-revoked');
  assert.equal(directory.clients[2].healthDataAuthorized,false);
});

test('directory normalization fails closed for missing collections and pagination fields', () => {
  assert.throws(()=>normalizePracticeClientDirectory({pagination:{total:0,limit:100,offset:0}}),/clients collection/);
  assert.throws(()=>normalizePracticeClientDirectory({clients:[],pagination:{total:0,limit:100}}),/pagination.offset/);
});

test('actual Clients screen selection keeps unconnected directory data out of health-context calls', async () => {
  const directory=normalizePracticeClientDirectory(directoryFixture);
  const calls=[];
  const assigned=await loadAuthorizedClient360(directory.clients[1],async(id)=>{calls.push(id);});
  assert.deepEqual(calls,[]);
  assert.equal(assigned.overview.name,'Assigned Client');
  assert.deepEqual(assigned.overview.dietPlanWarnings,['CONSENT_PENDING']);

  const connected=await loadAuthorizedClient360(directory.clients[0],async(id)=>{
    calls.push(id);
    return {profile:{client:{name:'Connected Client'},onboarding:{}},reports:[]};
  });
  assert.deepEqual(calls,['connection-active']);
  assert.equal(connected.overview.name,'Connected Client');
});

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
  const workspace=fs.readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
  const practiceApi=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
  const clientApi=fs.readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');
  assert.doesNotMatch(component,/getExternalClient360/);
  assert.doesNotMatch(clientApi,/external\/clients\/\$\{encodeURIComponent\(clientId\)\}\/360/);
  assert.match(component,/getFiteatsyConnectionHealthContext/);
  assert.match(workspace,/listPracticeClients/);
  assert.doesNotMatch(workspace,/listConnectedFiteatsyClients/);
  assert.match(practiceApi,/request\(`\/clients\?\$\{query\}`\)/);
});
