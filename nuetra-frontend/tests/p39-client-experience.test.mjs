import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const portal=fs.readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');
const portalApi=fs.readFileSync(new URL('../lib/clientPortalApi.js',import.meta.url),'utf8');
const practiceApi=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const dashboard=fs.readFileSync(new URL('../components/external/ExternalIntelligentHome.jsx',import.meta.url),'utf8');
const client360=fs.readFileSync(new URL('../components/external/ProfessionClient360.jsx',import.meta.url),'utf8');

test('portal offers accessible private experience feedback',()=>{
  assert.match(portal,/Share your experience/);assert.match(portal,/private to this practice/);
  assert.match(portal,/\$\{value\} out of 5/);assert.match(portal,/Public reviews are a separate, optional process/);
});
test('Client360 shows tenant-scoped read-only feedback history',()=>{assert.match(client360,/getClientFeedback/);assert.match(client360,/Read-only history/);assert.match(client360,/No empty history is inferred/);});
test('feedback API separates portal and practitioner workflows',()=>{
  for(const value of ['openPortalFeedback','submitPortalFeedback'])assert.match(portalApi,new RegExp(value));
  for(const value of ['createFeedbackRequest','getClientFeedback','createFeedbackAction','getFeedbackAnalytics'])assert.match(practiceApi,new RegExp(value));
});
test('command centre renders non-clinical feedback signals',()=>{
  assert.match(dashboard,/Private experience feedback/);assert.match(dashboard,/No clinical-effectiveness score/);
  assert.match(dashboard,/sections\.feedback/);assert.doesNotMatch(dashboard,/clinical outcome score/i);
});
