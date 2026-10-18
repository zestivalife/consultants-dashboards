import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const page=fs.readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');
test('P27 extends the existing portal with all available modules',()=>{for(const label of ['Forms','Consents','Notifications','Activity','Documents','Appointments','Billing','Resources','Referral consent','Shared reports'])assert.match(page,new RegExp(label));assert.match(page,/savePortalForm/);assert.match(page,/decidePortalConsent/)});
test('P27 remains mobile and truthful',()=>{assert.match(page,/overflow-x-auto/);assert.match(page,/min-h-11/);assert.match(page,/Portal unavailable/);assert.match(page,/No documents have been submitted or shared/)});
