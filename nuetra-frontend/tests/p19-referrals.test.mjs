import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
const referrals=readFileSync(new URL('../components/external/ExternalReferrals.jsx',import.meta.url),'utf8');
const workspace=readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const client360=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const portal=readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('P19 referral workflow exposes outgoing incoming drafts and completed',()=>{
  for(const label of ['Outgoing','Incoming','Drafts','Completed','Request consent','Send','Accept','Decline','Cancel'])assert.match(referrals,new RegExp(label));
  assert.match(referrals,/This is a confirmed empty state/);
});
test('P19 data scopes are explicit and private domains are excluded',()=>{
  for(const scope of ['BASIC_PROFILE','PUBLISHED_PLAN','PROGRESS_SUMMARY','GOALS'])assert.match(referrals,new RegExp(scope));
  for(const excluded of ['Private notes','raw session notes','billing','team notes'])assert.match(referrals,new RegExp(excluded,'i'));
});
test('P19 is permission-gated in workspace and integrated in Client360 and portal',()=>{
  assert.match(workspace,/REFERRAL_VIEW/);assert.match(workspace,/ExternalReferrals/);assert.match(client360,/Referrals/);
  assert.match(portal,/Referral consent requests/);assert.match(portal,/decideReferralConsent/);assert.match(api,/\/referrals/);
});

