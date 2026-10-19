import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const ui=fs.readFileSync(new URL('../components/external/ExternalPracticeSettings.jsx',import.meta.url),'utf8');const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
test('subscription UI is truthful and separate from profession authority',()=>{for(const x of ['SaaS subscription','SUBSCRIPTION_PAYMENT_PROVIDER','Product entitlement remains separate','Downgrades preserve historical data'])assert.match(ui,new RegExp(x));});
test('subscription APIs expose practice and governed admin plan surfaces',()=>{assert.match(api,/getPracticeSubscription/);assert.match(api,/listAdminSaasPlans/);});
