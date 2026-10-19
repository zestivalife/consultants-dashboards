import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const ui=fs.readFileSync(new URL('../components/external/ExternalBilling.jsx',import.meta.url),'utf8');const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
test('billing explains non-destructive credit notes and evidence-gated refund truth',()=>{for(const x of ['credit notes','requested, approved, processing, refunded, or failed','requires provider or manual settlement evidence'])assert.match(ui,new RegExp(x,'i'));});
test('refund API supports request and governed transition only',()=>{assert.match(api,/createRefundRequest/);assert.match(api,/transitionRefund/);});
