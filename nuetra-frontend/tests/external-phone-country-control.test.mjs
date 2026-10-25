import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const phone=fs.readFileSync(new URL('../components/external/PhoneNumberField.jsx',import.meta.url),'utf8');
const clients=fs.readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const leads=fs.readFileSync(new URL('../components/external/ExternalLeads.jsx',import.meta.url),'utf8');
const locations=fs.readFileSync(new URL('../components/external/ExternalLocations.jsx',import.meta.url),'utf8');

test('client and lead creation expose an accessible country code control',()=>{
  assert.match(phone,/aria-label={`\$\{label\} country code`}/);
  assert.match(phone,/India.*\+91/s);
  assert.match(phone,/inputMode="numeric"/);
  assert.match(clients,/PhoneNumberField/);
  assert.match(leads,/PhoneNumberField/);
  assert.match(locations,/PhoneNumberField/);
});

test('phone values are submitted as canonical E.164 values',()=>{
  assert.match(phone,/export function toE164/);
  assert.match(clients,/mobile:toE164/);
  assert.match(leads,/phone:toE164/);
  assert.match(locations,/phone: toE164/);
});
