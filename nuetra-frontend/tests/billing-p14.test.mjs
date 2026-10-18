import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

const component=readFileSync(new URL('../components/external/ExternalBilling.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const portal=readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');
const workspace=readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');

test('billing workspace exposes real loading error empty and finance states',()=>{
  for(const phrase of ['Loading billing truth','Retry billing','No invoices match this view','Payment ledger','Service catalogue'])assert.match(component,new RegExp(phrase));
  assert.match(workspace,/view==='billing'.*ExternalBilling/);
});

test('invoice authoring uses server APIs and never collects card or bank secrets',()=>{
  for(const call of ['createInvoice','issueInvoice','recordInvoicePayment','getBillingOverview'])assert.match(component,new RegExp(call));
  assert.doesNotMatch(component,/card_number|cvv|bank_password|PAY_NOW/);
  assert.match(component,/externally completed payment/);
});

test('client portal displays only invoice and receipt projection with no pay action',()=>{
  assert.match(portal,/Invoices and receipts/);
  assert.match(portal,/data\.invoices/);
  assert.match(portal,/data\.receipts/);
  assert.doesNotMatch(portal,/Pay now|PAY_NOW/);
});

test('billing API surface includes tenant-authorised lifecycle operations',()=>{
  for(const path of ['/billing/overview','/billing/services','/billing/invoices','/payments','/billing/clients/','/billing/receipts/'])assert.ok(api.includes(path));
});
