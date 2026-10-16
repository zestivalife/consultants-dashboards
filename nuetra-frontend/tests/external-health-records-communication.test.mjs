import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

const health=readFileSync(new URL('../components/external/ExternalHealthRecords.jsx',import.meta.url),'utf8');
const client360=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/externalTransientReportApi.js',import.meta.url),'utf8');
const communication=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('Client360 exposes additive Health Records without replacing Biomarkers or frozen Diet Plan',()=>{
  assert.match(client360,/Health Records/);
  assert.match(client360,/ExternalHealthRecords/);
  assert.match(client360,/ExternalBiomarkerHistory/);
  assert.match(client360,/ExternalDietPlan/);
});

test('Health Records supports governed removal and comparison modes',()=>{
  assert.match(health,/Remove Health Record/);
  assert.match(health,/quarantined, never hard-deleted/);
  assert.match(health,/Compare any two records/);
  assert.match(health,/Full trends/);
  assert.match(api,/health-records\/compare/);
  assert.match(api,/health-records\/trends/);
});

test('comparison communicates incompatible units without clinical diagnosis language',()=>{
  assert.match(health,/item\.message/);
  assert.doesNotMatch(health,/cured|treatment successful|condition worsened/i);
});

test('generic WhatsApp is independent from onboarding-link authority',()=>{
  assert.match(client360,/GENERAL_MESSAGE/);
  assert.match(client360,/General communication does not require an onboarding link/);
  assert.match(client360,/SHARE_ONBOARDING_LINK/);
  assert.doesNotMatch(client360,/const shareOnWhatsApp/);
  assert.match(communication,/WHATSAPP_OPENED|whatsapp-opened/);
});

test('published plan sharing is fail-closed for drafts and records open rather than sent',()=>{
  assert.match(client360,/Only a self-published Diet Plan can be shared/);
  assert.match(client360,/shareable_type:'PUBLISHED_DIET_PLAN'/);
  assert.doesNotMatch(client360,/event_type\s*:\s*['"](?:MESSAGE_SENT|DELIVERED|READ)['"]/);
});

test('profile completeness remains separate from optional evidence coverage',()=>{
  assert.match(client360,/Profile completeness and evidence coverage are separate/);
  assert.match(client360,/Lab data is optional/);
  assert.match(client360,/Health profile may need review/);
});

test('mobile surfaces use touch-safe controls and no source download',()=>{
  assert.match(health,/min-h-11/);
  assert.match(health,/overflow-x-auto/);
  assert.match(health,/source file not retained/i);
  assert.doesNotMatch(health,/download/i);
});
